"""In-memory thread-safe Token Bucket Rate Limiter."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate limit check."""

    allowed: bool
    remaining_tokens: float
    retry_after: float


class TokenBucket:
    """Thread-safe token bucket rate limiter using monotonic clock replenishment.

    Args:
        rate: Continuous refill rate in tokens per second (must be > 0.0).
        capacity: Maximum token capacity/burst limit (must be >= 1.0).
    """

    def __init__(self, rate: float, capacity: float) -> None:
        if rate <= 0.0:
            raise ValueError(f"Rate must be positive, got {rate}")
        if capacity < 1.0:
            raise ValueError(f"Capacity must be at least 1.0, got {capacity}")

        self.rate = float(rate)
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self._last_updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> RateLimitResult:
        """Attempt to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens requested (must be > 0.0 and <= capacity).

        Returns:
            RateLimitResult with allowed flag, remaining tokens, and retry_after duration.
        """
        if tokens <= 0.0:
            raise ValueError(f"Tokens requested must be positive, got {tokens}")
        if tokens > self.capacity:
            raise ValueError(
                f"Requested tokens ({tokens}) cannot exceed bucket capacity ({self.capacity})"
            )

        with self._lock:
            now = time.monotonic()
            elapsed = max(0.0, now - self._last_updated)
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_updated = now

            if self._tokens >= tokens:
                self._tokens -= tokens
                return RateLimitResult(
                    allowed=True,
                    remaining_tokens=self._tokens,
                    retry_after=0.0,
                )

            missing_tokens = tokens - self._tokens
            retry_after = missing_tokens / self.rate
            return RateLimitResult(
                allowed=False,
                remaining_tokens=self._tokens,
                retry_after=retry_after,
            )
