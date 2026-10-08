"""Contract tests for the Token Bucket Rate Limiter capability.

Every test binds to an acceptance case_id defined in
.governance/capabilities/rate-limiter/spec.yaml with a '# why:' annotation.
"""

from __future__ import annotations

import concurrent.futures
import time

import pytest
from rate_limiter.limiter import TokenBucket


def test_allow_within_capacity() -> None:
    # case_id: allow-within-capacity
    # why: Verifies that requests within available capacity succeed immediately and decrement tokens.
    limiter = TokenBucket(rate=10.0, capacity=5.0)

    result = limiter.acquire(tokens=2.0)
    assert result.allowed is True
    assert result.remaining_tokens == pytest.approx(3.0, abs=0.01)
    assert result.retry_after == 0.0


def test_reject_when_exhausted() -> None:
    # case_id: reject-when-exhausted
    # why: When token demand exceeds available supply, requests must be denied and provide accurate retry_after.
    limiter = TokenBucket(rate=2.0, capacity=2.0)

    # Exhaust all tokens
    res1 = limiter.acquire(tokens=2.0)
    assert res1.allowed is True

    # Next immediate request must be denied
    res2 = limiter.acquire(tokens=1.0)
    assert res2.allowed is False
    assert res2.remaining_tokens == pytest.approx(0.0, abs=0.01)
    assert res2.retry_after > 0.0
    assert res2.retry_after <= 0.55  # 1 token needed at 2 tokens/sec = 0.5 sec


def test_tokens_never_exceed_capacity() -> None:
    # case_id: tokens-never-exceed-capacity
    # why: Invariant check ensuring idle time accumulation caps strictly at configured burst limit.
    limiter = TokenBucket(rate=100.0, capacity=5.0)

    # Sleep slightly to let potential overfill happen
    time.sleep(0.05)

    result = limiter.acquire(tokens=1.0)
    assert result.allowed is True
    assert result.remaining_tokens <= 4.0


def test_refills_proportionally_over_time() -> None:
    # case_id: refills-proportionally-over-time
    # why: Positive path validating that replenishment math accurately tracks elapsed time.
    limiter = TokenBucket(rate=10.0, capacity=5.0)

    # Drain bucket
    limiter.acquire(tokens=5.0)

    # Wait 0.2s -> should refill ~2 tokens (10 tokens/s * 0.2s = 2.0)
    time.sleep(0.2)

    result = limiter.acquire(tokens=2.0)
    assert result.allowed is True
    assert result.retry_after == 0.0


def test_rejects_invalid_configuration() -> None:
    # case_id: rejects-invalid-configuration
    # why: Negative path ensuring invalid bucket parameters fail fast at initialization.
    with pytest.raises(ValueError, match="Rate must be positive"):
        TokenBucket(rate=0.0, capacity=5.0)

    with pytest.raises(ValueError, match="Rate must be positive"):
        TokenBucket(rate=-1.0, capacity=5.0)

    with pytest.raises(ValueError, match="Capacity must be at least 1.0"):
        TokenBucket(rate=10.0, capacity=0.5)


def test_rejects_invalid_token_request() -> None:
    # case_id: rejects-invalid-token-request
    # why: Boundary/negative path guarding against negative consumption or requests exceeding full bucket capacity.
    limiter = TokenBucket(rate=10.0, capacity=5.0)

    with pytest.raises(ValueError, match="Tokens requested must be positive"):
        limiter.acquire(tokens=0.0)

    with pytest.raises(ValueError, match="Tokens requested must be positive"):
        limiter.acquire(tokens=-2.0)

    with pytest.raises(ValueError, match="cannot exceed bucket capacity"):
        limiter.acquire(tokens=10.0)


def test_thread_safe_concurrent_consumption() -> None:
    # case_id: thread-safe-concurrent-consumption
    # why: Concurrency invariant confirming exact token accounting across parallel worker threads.
    capacity = 100.0
    rate = 1.0  # minimal refill during the sub-second test window
    limiter = TokenBucket(rate=rate, capacity=capacity)

    total_threads = 100
    tokens_per_thread = 1.0

    def worker() -> bool:
        return limiter.acquire(tokens=tokens_per_thread).allowed

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: worker(), range(total_threads)))

    allowed_count = sum(1 for granted in results if granted)
    denied_count = sum(1 for granted in results if not granted)

    # Exactly 100 requests should be granted (or 100 + tiny refill delta), none over-allocated
    assert allowed_count == pytest.approx(100, abs=1)
    assert allowed_count + denied_count == total_threads
