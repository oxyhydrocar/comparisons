require 'spec_helper'
require_relative '../token_bucket'

RSpec.describe TokenBucket do
  let(:capacity) do
    5
  end

  let(:refill_rate) do
    2.0
  end

  let(:start_time) do
    Time.at(1_000_000.0)
  end

  before do
    allow(Time).to receive(:now).and_return(start_time)
  end

  let(:bucket) do
    described_class.new(capacity, refill_rate)
  end

  describe '#available_tokens' do
    it 'returns full capacity initially' do
      expect(bucket.available_tokens).to eq(capacity.to_f)
    end

    it 'refills tokens over time based on refill_rate' do
      bucket.consume(capacity)
      expect(bucket.available_tokens).to eq(0.0)

      allow(Time).to receive(:now).and_return(start_time + 1.25)
      expect(bucket.available_tokens).to be_within(1e-9).of(2.5)
    end

    it 'does not exceed capacity when refilling beyond capacity' do
      bucket.consume(1.0)
      allow(Time).to receive(:now).and_return(start_time + 100.0)
      expect(bucket.available_tokens).to eq(capacity.to_f)
    end
  end

  describe '#consume' do
    it 'consumes tokens when available and returns true' do
      result = bucket.consume(2.0)
      expect(result).to be(true)
      expect(bucket.available_tokens).to eq(capacity.to_f - 2.0)
    end

    it 'returns false when not enough tokens are available' do
      bucket.consume(capacity)
      expect(bucket.available_tokens).to eq(0.0)
      result = bucket.consume(1.0)
      expect(result).to be(false)
    end

    it 'supports consuming fractional token amounts' do
      result = bucket.consume(2.5)
      expect(result).to be(true)
      expect(bucket.available_tokens).to be_within(1e-9).of(2.5)
    end

    it 'refills while consuming based on elapsed time' do
      bucket.consume(capacity)
      expect(bucket.available_tokens).to eq(0.0)

      allow(Time).to receive(:now).and_return(start_time + 0.5)
      result = bucket.consume(1.0)
      expect(result).to be(true)
      expect(bucket.available_tokens).to eq(0.0)
    end

    it 'returns true when consuming zero tokens and does not change the balance' do
      before = bucket.available_tokens
      result = bucket.consume(0)
      after = bucket.available_tokens
      expect(result).to be(true)
      expect(after).to eq(before)
    end

    it 'accepts negative token amounts (clamped back to capacity on next refill call)' do
      expect(bucket.available_tokens).to eq(capacity.to_f)
      result = bucket.consume(-1.0)
      expect(result).to be(true)

      # Next available_tokens call will clamp to capacity due to refill logic
      expect(bucket.available_tokens).to eq(capacity.to_f)
    end

    it 'raises an error when amount is not numeric' do
      expect do
        bucket.consume('not-a-number')
      end.to raise_error(ArgumentError)
    end
  end
end

RSpec.describe RateLimiter do
  let(:requests_per_second) do
    3
  end

  let(:start_time) do
    Time.at(2_000_000.0)
  end

  before do
    allow(Time).to receive(:now).and_return(start_time)
  end

  let(:limiter) do
    described_class.new(requests_per_second)
  end

  describe '#allow_request?' do
    it 'allows up to capacity immediate requests and then denies' do
      allowed = []
      requests_per_second.times do
        allowed << limiter.allow_request?
      end
      expect(allowed.all?).to be(true)

      expect(limiter.allow_request?).to be(false)
    end

    it 'allows requests again after sufficient time has passed' do
      requests_per_second.times do
        limiter.allow_request?
      end
      expect(limiter.allow_request?).to be(false)

      allow(Time).to receive(:now).and_return(start_time + 1.0)
      expect(limiter.allow_request?).to be(true)
    end
  end

  describe '#current_capacity' do
    it 'returns current available tokens (not the configured burst size)' do
      expect(limiter.current_capacity).to eq(requests_per_second.to_f)

      2.times do
        limiter.allow_request?
      end
      expect(limiter.current_capacity).to eq(1.0)

      allow(Time).to receive(:now).and_return(start_time + 0.5)
      expect(limiter.current_capacity).to be_within(1e-9).of(2.5)
    end
  end
end
