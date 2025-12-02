require 'spec_helper'
require_relative '../connection_pool'

RSpec.describe Connection do
  let(:connection) { described_class.new(1) }

  before do
    allow_any_instance_of(Connection).to receive(:sleep).and_return(nil)
  end

  describe '#initialize' do
    it 'sets id and created_at and starts not in use' do
      expect(connection.id).to eq(1)
      expect(connection.created_at).to be_within(1).of(Time.now)
      expect(connection.in_use?).to be false
    end
  end

  describe '#execute' do
    it 'returns a result string for the query' do
      result = connection.execute('SELECT 1')
      expect(result).to eq('Result for: SELECT 1')
    end
  end

  describe '#mark_in_use' do
    it 'marks the connection as in use' do
      connection.mark_in_use
      expect(connection.in_use?).to be true
    end
  end

  describe '#release' do
    it 'marks the connection as not in use' do
      connection.mark_in_use
      connection.release
      expect(connection.in_use?).to be false
    end
  end

  describe '#in_use?' do
    it 'reflects current usage state' do
      expect(connection.in_use?).to be false
      connection.mark_in_use
      expect(connection.in_use?).to be true
      connection.release
      expect(connection.in_use?).to be false
    end
  end

  describe '#stale?' do
    it 'returns false when max_age is large' do
      expect(connection.stale?(10_000)).to be false
    end

    it 'returns true when created_at is older than max_age' do
      connection.instance_variable_set(:@created_at, Time.now - 60)
      expect(connection.stale?(10)).to be true
      expect(connection.stale?(300)).to be false
    end

    it 'can be true even if the connection is in use (based on created_at only)' do
      connection.instance_variable_set(:@created_at, Time.now - 60)
      connection.mark_in_use
      expect(connection.stale?(10)).to be true
    end
  end
end

RSpec.describe ConnectionPool do
  let(:size) { 2 }
  let(:max_age) { 300 }
  let(:pool) { described_class.new(size, max_age) }

  before do
    allow_any_instance_of(Connection).to receive(:sleep).and_return(nil)
  end

  describe '#initialize' do
    it 'starts with an empty pool' do
      expect(pool.pool_size).to eq(0)
      expect(pool.available_connections).to eq(0)
    end
  end

  describe '#checkout' do
    it 'creates a new connection when capacity allows' do
      conn = pool.checkout
      expect(conn).to be_a(Connection)
      expect(conn.in_use?).to be true
      expect(pool.pool_size).to eq(1)
      pool.checkin(conn)
    end

    it 'reuses an available connection when possible' do
      small_pool = described_class.new(1, 300)
      conn1 = small_pool.checkout
      small_pool.checkin(conn1)
      conn2 = small_pool.checkout
      expect(conn2).to eq(conn1)
      small_pool.checkin(conn2)
    end

    it 'blocks when pool is at capacity until a connection is checked in' do
      blocking_pool = described_class.new(1, 300)
      t1_conn = blocking_pool.checkout

      acquired_at = nil
      start = Time.now
      t2 = Thread.new do
        conn = blocking_pool.checkout
        acquired_at = Time.now
        blocking_pool.checkin(conn)
      end

      hold_time = 0.2
      sleep(hold_time)
      blocking_pool.checkin(t1_conn)
      t2.join

      expect(acquired_at - start).to be >= hold_time - 0.02
    end
  end

  describe '#checkin' do
    it 'releases the connection back to the pool and signals waiters' do
      conn = pool.checkout
      expect(pool.available_connections).to eq(0)
      pool.checkin(conn)
      expect(pool.available_connections).to eq(1)
    end

    it 'does not raise when checking in a connection not from the pool' do
      foreign_conn = Connection.new(999)
      expect do
        pool.checkin(foreign_conn)
      end.not_to raise_error
      expect(pool.pool_size).to eq(0)
    end
  end

  describe '#with_connection' do
    it 'yields a connection and returns the block result' do
      result = pool.with_connection do |conn|
        conn.execute('PING')
      end
      expect(result).to eq('Result for: PING')
      expect(pool.available_connections).to eq(1)
    end

    it 'returns the connection to the pool even if the block raises' do
      expect do
        pool.with_connection do |_conn|
          raise 'boom'
        end
      end.to raise_error(RuntimeError, 'boom')
      expect(pool.available_connections).to eq(1)
    end
  end

  describe '#pool_size' do
    it 'reflects the number of created connections' do
      c1 = pool.checkout
      c2 = pool.checkout
      expect(pool.pool_size).to eq(2)
      pool.checkin(c1)
      pool.checkin(c2)
      expect(pool.pool_size).to eq(2)
    end
  end

  describe '#available_connections' do
    it 'counts only idle connections' do
      c1 = pool.checkout
      expect(pool.available_connections).to eq(0)
      pool.checkin(c1)
      expect(pool.available_connections).to eq(1)
    end
  end

  describe 'stale connection cleanup' do
    it 'removes stale idle connections on checkout and creates a fresh one' do
      stale_pool = described_class.new(2, 0)
      c1 = stale_pool.checkout
      stale_pool.checkin(c1)
      expect(stale_pool.available_connections).to eq(1)

      c2 = stale_pool.checkout
      expect(c2).not_to eq(c1)
      expect(stale_pool.pool_size).to eq(1)
      stale_pool.checkin(c2)
    end

    it 'does not remove in-use connections during cleanup' do
      stale_pool = described_class.new(1, 0)
      c1 = stale_pool.checkout

      acquired = nil
      t = Thread.new do
        acquired = stale_pool.checkout
        stale_pool.checkin(acquired)
      end

      sleep(0.1)
      stale_pool.checkin(c1)
      t.join

      expect(acquired).to be_a(Connection)
      expect(stale_pool.pool_size).to eq(1)
      expect(stale_pool.available_connections).to eq(1)
    end
  end
end
