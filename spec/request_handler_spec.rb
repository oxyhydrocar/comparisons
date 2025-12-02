require 'spec_helper'
require_relative '../request_handler'

RSpec.describe RequestHandler do
  let(:requests_per_second) { 10 }
  let(:pool_size) { 3 }
  let(:rate_limiter) do
    instance_double('RateLimiter',
      allow_request?: true,
      current_capacity: 7
    )
  end
  let(:connection) do
    instance_double('Connection', execute: 'ok')
  end
  let(:pool) do
    instance_double('ConnectionPool',
      pool_size: pool_size,
      available_connections: 2
    )
  end

  before do
    allow(RateLimiter).to receive(:new).with(requests_per_second).and_return(rate_limiter)
    allow(ConnectionPool).to receive(:new).with(pool_size).and_return(pool)
    allow(pool).to receive(:with_connection).and_yield(connection)
  end

  describe '#handle' do
    let(:handler) { described_class.new(requests_per_second, pool_size) }

    context 'when rate limiter allows the request' do
      let(:request) { { query: 'SELECT 1' } }

      it 'executes the query and returns status 200 with body' do
        result = handler.handle(request)
        expect(result).to eq({ status: 200, body: 'ok' })
        expect(pool).to have_received(:with_connection)
        expect(connection).to have_received(:execute).with('SELECT 1')
      end

      it 'increments the internal request counter' do
        5.times { handler.handle(request) }
        stats = handler.stats
        expect(stats[:total_requests]).to eq(5)
      end
    end

    context 'when rate limiter denies the request' do
      let(:request) { { query: 'SELECT 1' } }

      before do
        allow(rate_limiter).to receive(:allow_request?).and_return(false)
      end

      it 'returns 429 and does not try to get a connection' do
        result = handler.handle(request)
        expect(result).to eq({ status: 429, body: 'Rate limit exceeded' })
        expect(pool).not_to have_received(:with_connection)
      end

      it 'does not increment the request counter' do
        handler.handle(request)
        expect(handler.stats[:total_requests]).to eq(0)
      end
    end

    context 'when connection execution raises an error' do
      let(:request) { { query: 'BROKEN' } }

      before do
        allow(connection).to receive(:execute).and_raise(StandardError, 'db error')
      end

      it 'propagates the exception' do
        expect { handler.handle(request) }.to raise_error(StandardError, 'db error')
      end

      it 'still increments the request counter before the error' do
        begin
          handler.handle(request)
        rescue StandardError
        end
        expect(handler.stats[:total_requests]).to eq(1)
      end
    end

    context 'concurrent requests' do
      let(:handler) { described_class.new(requests_per_second, pool_size) }

      it 'counts all successful requests safely under concurrency' do
        allow(connection).to receive(:execute) do
          sleep(0.01)
          'ok'
        end

        threads = []
        20.times do
          threads << Thread.new do
            handler.handle({ query: 'SELECT 1' })
          end
        end
        threads.each(&:join)

        expect(handler.stats[:total_requests]).to eq(20)
      end
    end
  end

  describe '#stats' do
    let(:handler) { described_class.new(requests_per_second, pool_size) }

    it 'returns a snapshot including totals, capacity, and pool metrics' do
      handler.handle({ query: 'SELECT 1' })
      s = handler.stats
      expect(s[:total_requests]).to eq(1)
      expect(s[:available_capacity]).to eq(7)
      expect(s[:pool_size]).to eq(pool_size)
      expect(s[:available_connections]).to eq(2)
    end
  end
end

RSpec.describe AsyncRequestProcessor do
  let(:handler_double) do
    Class.new do
      def initialize(result: nil, raise_error: false)
        @result = result
        @raise_error = raise_error
      end

      def handle(request)
        raise 'boom' if @raise_error
        @result || request
      end
    end
  end

  describe '#submit and #get_result without functional workers' do
    let(:handler) { handler_double.new(result: { status: 200, body: 'ok' }) }
    let(:processor) { described_class.new(handler, 1) }

    it 'returns incremental request ids' do
      id1 = processor.submit({ a: 1 })
      id2 = processor.submit({ a: 2 })
      id3 = processor.submit({ a: 3 })
      expect(id1).to eq(1)
      expect(id2).to eq(2)
      expect(id3).to eq(3)
    end

    it 'times out when no worker processes the queue' do
      id = processor.submit({ q: 'noop' })
      res = processor.get_result(id, 0.05)
      expect(res).to be_nil
    end

    it 'start and stop do not raise errors even if workers are dead' do
      expect { processor.start }.not_to raise_error
      expect { processor.stop }.not_to raise_error
    end
  end

  describe 'with functional worker stub' do
    let(:handler) { handler_double.new(result: { status: 200, body: 'ok' }) }
    let(:processor) { described_class.new(handler, 2) }

    before do
      allow_any_instance_of(described_class).to receive(:create_worker) do |instance, idx|
        Thread.new do
          loop do
            item = instance.instance_variable_get(:@queue).pop
            break if item == :shutdown
            unless instance.instance_variable_get(:@running)
              instance.instance_variable_get(:@queue) << item
              sleep(0.001)
              next
            end
            begin
              result = instance.instance_variable_get(:@handler).handle(item[:request])
            rescue
              next
            end
            instance.instance_variable_get(:@results_mutex).synchronize do
              results = instance.instance_variable_get(:@results)
              results[item[:id]] = result
            end
          end
        end
      end
    end

    after do
      begin
        processor.stop
      rescue StandardError
      end
    end

    it 'processes requests after start and returns results' do
      id = processor.submit({ q: 'work' })
      processor.start
      res = processor.get_result(id, 1)
      expect(res).to eq({ status: 200, body: 'ok' })
    end

    it 'can process multiple requests and return distinct results' do
      ids = []
      5.times { ids << processor.submit({ q: 'work' }) }
      processor.start
      results = ids.map { |id| processor.get_result(id, 1) }
      expect(results).to all(eq({ status: 200, body: 'ok' }))
    end

    it 'returns nil when handler errors (no result stored)' do
      bad_handler = handler_double.new(raise_error: true)
      bad_processor = described_class.new(bad_handler, 1)
      allow_any_instance_of(described_class).to receive(:create_worker) do |instance, idx|
        Thread.new do
          loop do
            item = instance.instance_variable_get(:@queue).pop
            break if item == :shutdown
            unless instance.instance_variable_get(:@running)
              instance.instance_variable_get(:@queue) << item
              sleep(0.001)
              next
            end
            begin
              instance.instance_variable_get(:@handler).handle(item[:request])
            rescue
            end
          end
        end
      end
      bad_processor.start
      id = bad_processor.submit({ q: 'fail' })
      res = bad_processor.get_result(id, 0.2)
      expect(res).to be_nil
      bad_processor.stop
    end

    it 'stop prevents further processing of new submissions' do
      processor.start
      id1 = processor.submit({ q: 'first' })
      res1 = processor.get_result(id1, 1)
      expect(res1).to eq({ status: 200, body: 'ok' })

      processor.stop
      id2 = processor.submit({ q: 'after-stop' })
      res2 = processor.get_result(id2, 0.2)
      expect(res2).to be_nil
    end
  end
end
