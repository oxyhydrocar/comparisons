require 'thread'

class Connection
  attr_reader :id, :created_at

  def initialize(id)
    @id = id
    @created_at = Time.now
    @in_use = false
  end

  def execute(query)
    sleep(rand * 0.1)
    "Result for: #{query}"
  end

  def mark_in_use
    @in_use = true
  end

  def release
    @in_use = false
  end

  def in_use?
    @in_use
  end

  def stale?(max_age)
    Time.now - @created_at > max_age
  end
end

class ConnectionPool
  def initialize(size, max_age = 300)
    @size = size
    @max_age = max_age
    @connections = []
    @mutex = Mutex.new
    @condition = ConditionVariable.new
  end

  def with_connection
    conn = checkout
    begin
      yield conn
    ensure
      checkin(conn)
    end
  end

  def checkout
    @mutex.synchronize do
      loop do
        cleanup_stale_connections

        conn = @connections.find { |c| !c.in_use? }

        if conn
          conn.mark_in_use
          return conn
        elsif @connections.size < @size
          conn = create_connection
          conn.mark_in_use
          @connections << conn
          return conn
        else
          @condition.wait(@mutex)
        end
      end
    end
  end

  def checkin(connection)
    connection.release
    @mutex.synchronize do
      @condition.signal
    end
  end

  def pool_size
    @connections.size
  end

  def available_connections
    @connections.count { |c| !c.in_use? }
  end

  private

  def create_connection
    Connection.new(@connections.size + 1)
  end

  def cleanup_stale_connections
    @connections.reject! do |conn|
      conn.stale?(@max_age) && !conn.in_use?
    end
  end
end
