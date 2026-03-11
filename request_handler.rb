require_relative 'token_bucket'
require_relative 'connection_pool'

class RequestHandler
  def initialize(requests_per_second, pool_size)
    @rate_limiter = RateLimiter.new(requests_per_second)
    @pool = ConnectionPool.new(pool_size)
    @request_count = 0
    @mutex = Mutex.new
  end

  def handle(request)
    unless @rate_limiter.allow_request?
      return { status: 429, body: 'Rate limit exceeded' }
    end

    increment_counter

    @pool.with_connection do |conn|
      result = conn.execute(request[:query])
      { status: 200, body: result }
    end
  end

  def stats
    {
      total_requests: @request_count,
      available_capacity: @rate_limiter.current_capacity,
      pool_size: @pool.pool_size,
      available_connections: @pool.available_connections
    }
  end

  private

  def increment_counter
    @mutex.synchronize do
      @request_count += 1
    end
  end
end

class AsyncRequestProcessor
  def initialize(handler, num_workers)
    @handler = handler
    @queue = Queue.new
    @results = {}
    @results_mutex = Mutex.new
    @workers = []
    @running = false
    @request_id = 0

    num_workers.times do |i|
      @workers << create_worker(i)
    end
  end

  def start
    @running = true
    @workers.each(&:run)
  end

  def stop
    @running = false
    @workers.size.times { @queue << :shutdown }
    @workers.each { |w| w.join if w.alive? }
  end

  def submit(request)
    id = next_request_id
    @queue << { id: id, request: request }
    id
  end

  def get_result(request_id, timeout = 5)
    deadline = Time.now + timeout

    loop do
      @results_mutex.synchronize do
        if @results.key?(request_id)
          return @results.delete(request_id)
        end
      end

      return nil if Time.now > deadline
      sleep(0.01)
    end
  end

  private

  def next_request_id
    @request_id += 1
  end

  def create_worker(id)
    Thread.new do
      while @running
        item = @queue.pop
        break if item == :shutdown

        result = @handler.handle(item[:request])

        @results_mutex.synchronize do
          @results[item[:id]] = result
        end
      end
    end
  end
end
