require 'thread'

class Cache
  def initialize(max_size = 1000, ttl = 3600)
    @max_size = max_size
    @ttl = ttl
    @store = {}
    @access_order = []
    @mutex = Mutex.new
  end

  def get(key)
    entry = @store[key]
    return nil unless entry

    if expired?(entry)
      delete(key)
      return nil
    end

    @mutex.synchronize do
      @access_order.delete(key)
      @access_order << key
    end

    entry[:value]
  end

  def set(key, value)
    @mutex.synchronize do
      evict_if_needed

      if @store.key?(key)
        @access_order.delete(key)
      end

      @store[key] = { value: value, expires_at: Time.now + @ttl }
      @access_order << key
    end
  end

  def delete(key)
    @mutex.synchronize do
      @store.delete(key)
      @access_order.delete(key)
    end
  end

  def clear
    @mutex.synchronize do
      @store.clear
      @access_order.clear
    end
  end

  def size
    @store.size
  end

  def fetch(key)
    value = get(key)
    return value if value

    value = yield
    set(key, value)
    value
  end

  private

  def expired?(entry)
    Time.now > entry[:expires_at]
  end

  def evict_if_needed
    while @store.size >= @max_size
      oldest_key = @access_order.shift
      @store.delete(oldest_key) if oldest_key
    end
  end
end

class DistributedCounter
  def initialize
    @shards = Array.new(16) { { value: 0, mutex: Mutex.new } }
  end

  def increment(amount = 1)
    shard = @shards[Thread.current.object_id % @shards.size]
    shard[:mutex].synchronize do
      shard[:value] += amount
    end
  end

  def decrement(amount = 1)
    increment(-amount)
  end

  def value
    @shards.sum { |shard| shard[:value] }
  end

  def reset
    @shards.each do |shard|
      shard[:mutex].synchronize do
        shard[:value] = 0
      end
    end
  end
end
