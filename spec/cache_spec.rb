require 'spec_helper'
require_relative '../cache'

RSpec.describe Cache do
  let(:max_size) { 3 }
  let(:ttl) { 3600 }
  let(:cache) { Cache.new(max_size, ttl) }

  describe '#set and #get' do
    it 'stores and retrieves a value' do
      cache.set('foo', 'bar')
      expect(cache.get('foo')).to eq('bar')
    end

    it 'returns nil for missing keys' do
      expect(cache.get('missing')).to be_nil
    end

    it 'updates value for an existing key and maintains access order' do
      cache.set('a', 1)
      cache.set('b', 2)
      cache.set('a', 3)
      expect(cache.get('a')).to eq(3)
      expect(cache.size).to eq(2)
    end
  end

  describe 'TTL expiration behavior' do
    let(:ttl) { 5 }

    it 'expires entries after TTL and removes them on get' do
      t0 = Time.utc(2020, 1, 1, 0, 0, 0)
      allow(Time).to receive(:now).and_return(t0)
      cache.set('key', 'val')

      allow(Time).to receive(:now).and_return(t0 + ttl + 1)
      expect(cache.get('key')).to be_nil
      expect(cache.size).to eq(0)
    end

    it 'does not expire when Time.now == expires_at (strict > comparison)' do
      t0 = Time.utc(2020, 1, 1, 0, 0, 0)
      short_cache = Cache.new(10, 0)
      allow(Time).to receive(:now).and_return(t0)
      short_cache.set('k', 'v')
      allow(Time).to receive(:now).and_return(t0)
      expect(short_cache.get('k')).to eq('v')
    end

    it 'size counts expired entries until accessed' do
      t0 = Time.utc(2020, 1, 1, 0, 0, 0)
      short_cache = Cache.new(10, 1)
      allow(Time).to receive(:now).and_return(t0)
      short_cache.set('k', 'v')

      allow(Time).to receive(:now).and_return(t0 + 100)
      expect(short_cache.size).to eq(1)
      expect(short_cache.get('k')).to be_nil
      expect(short_cache.size).to eq(0)
    end
  end

  describe 'eviction (LRU by access order)' do
    let(:max_size) { 2 }

    it 'evicts the least recently used key when capacity is reached (via get)' do
      cache.set('a', 1)
      cache.set('b', 2)
      expect(cache.size).to eq(2)

      expect(cache.get('a')).to eq(1)
      cache.set('c', 3)

      expect(cache.get('b')).to be_nil
      expect(cache.get('a')).to eq(1)
      expect(cache.get('c')).to eq(3)
      expect(cache.size).to eq(2)
    end

    it 'evicts the least recently used key when an existing key is updated (via set)' do
      cache.set('a', 1)
      cache.set('b', 2)
      cache.set('a', 10)
      cache.set('c', 3)

      expect(cache.get('b')).to be_nil
      expect(cache.get('a')).to eq(10)
      expect(cache.get('c')).to eq(3)
    end
  end

  describe '#delete' do
    it 'removes an existing key' do
      cache.set('x', 'y')
      expect(cache.get('x')).to eq('y')
      cache.delete('x')
      expect(cache.get('x')).to be_nil
      expect(cache.size).to eq(0)
    end

    it 'does nothing for a missing key' do
      expect(cache.delete('missing')).to be_nil
      expect(cache.size).to eq(0)
    end
  end

  describe '#clear' do
    it 'clears all entries' do
      cache.set('a', 1)
      cache.set('b', 2)
      expect(cache.size).to eq(2)
      cache.clear
      expect(cache.size).to eq(0)
      expect(cache.get('a')).to be_nil
      expect(cache.get('b')).to be_nil
    end
  end

  describe '#size' do
    it 'returns the number of stored entries' do
      cache.set('a', 1)
      cache.set('b', 2)
      expect(cache.size).to eq(2)
    end
  end

  describe '#fetch' do
    it 'returns existing value without invoking the block' do
      cache.set('k', 'v')
      spy = double('spy')
      expect(spy).not_to receive(:call)
      result = cache.fetch('k') do
        spy.call
      end
      expect(result).to eq('v')
    end

    it 'computes, stores, and returns the value when missing' do
      count = 0
      result1 = cache.fetch('compute') do
        count += 1
        'computed'
      end
      result2 = cache.fetch('compute') do
        count += 1
        'should_not_happen'
      end
      expect(result1).to eq('computed')
      expect(result2).to eq('computed')
      expect(count).to eq(1)
    end

    it 'caches nil results' do
      count = 0
      result1 = cache.fetch('nil_key') do
        count += 1
        nil
      end
      result2 = cache.fetch('nil_key') do
        count += 1
        'should_not_compute'
      end
      expect(result1).to be_nil
      expect(result2).to be_nil
      expect(count).to eq(1)
    end

    it 'raises LocalJumpError when no block is given' do
      expect do
        cache.fetch('no_block')
      end.to raise_error(LocalJumpError)
    end
  end
end

RSpec.describe DistributedCounter do
  let(:counter) { DistributedCounter.new }

  describe '#increment' do
    it 'increments by 1 by default' do
      expect(counter.value).to eq(0)
      counter.increment
      expect(counter.value).to eq(1)
    end

    it 'increments by a specified amount' do
      counter.increment(5)
      expect(counter.value).to eq(5)
    end

    it 'supports concurrent increments across threads' do
      threads = []
      thread_count = 10
      increments_per_thread = 1000

      thread_count.times do
        threads << Thread.new do
          increments_per_thread.times do
            counter.increment
          end
        end
      end

      threads.each(&:join)
      expect(counter.value).to eq(thread_count * increments_per_thread)
    end
  end

  describe '#decrement' do
    it 'decrements by 1 by default' do
      counter.increment(5)
      counter.decrement
      expect(counter.value).to eq(4)
    end

    it 'decrements by a specified amount' do
      counter.increment(10)
      counter.decrement(3)
      expect(counter.value).to eq(7)
    end

    it 'handles negative totals' do
      counter.decrement(2)
      expect(counter.value).to eq(-2)
    end

    it 'supports concurrent increments and decrements' do
      counter.reset
      threads = []
      inc_threads = 5
      dec_threads = 5
      ops_per_thread = 500

      inc_threads.times do
        threads << Thread.new do
          ops_per_thread.times do
            counter.increment
          end
        end
      end

      dec_threads.times do
        threads << Thread.new do
          ops_per_thread.times do
            counter.decrement
          end
        end
      end

      threads.each(&:join)
      expect(counter.value).to eq(0)
    end
  end

  describe '#value' do
    it 'returns the sum across all shards' do
      counter.increment(3)
      counter.increment(2)
      counter.decrement(1)
      expect(counter.value).to eq(4)
    end
  end

  describe '#reset' do
    it 'resets the counter to zero' do
      counter.increment(10)
      expect(counter.value).to eq(10)
      counter.reset
      expect(counter.value).to eq(0)
    end

    it 'is safe to call multiple times' do
      counter.reset
      counter.reset
      expect(counter.value).to eq(0)
    end
  end
end
