class TokenBucket
  def initialize(capacity, refill_rate)
    @capacity = capacity
    @refill_rate = refill_rate
    @tokens = capacity.to_f
    @last_refill = Time.now
    @mutex = Mutex.new
  end

  def consume(tokens = 1)
    refill

    @mutex.synchronize do
      if @tokens >= tokens
        @tokens -= tokens
        return true
      end
    end

    false
  end

  def available_tokens
    refill
    @tokens
  end

  private

  def refill
    now = Time.now
    elapsed = now - @last_refill

    @mutex.synchronize do
      tokens_to_add = elapsed * @refill_rate
      @tokens = [@tokens + tokens_to_add, @capacity].min
      @last_refill = now
    end
  end
end

class RateLimiter
  def initialize(requests_per_second)
    @bucket = TokenBucket.new(requests_per_second, requests_per_second)
  end

  def allow_request?
    @bucket.consume
  end

  def current_capacity
    @bucket.available_tokens
  end
end
