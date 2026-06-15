"""Sliding-window rate limiter middleware.

Each unique key (``X-API-Key`` when present, otherwise client IP) gets its own
independent counter tracked over a 60-second rolling window.  Responses include
``X-RateLimit-Limit`` and ``X-RateLimit-Remaining`` headers so clients can
self-throttle before hitting 429.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Health is exempt so monitoring probes never consume quota.
_DEFAULT_EXEMPT: frozenset[str] = frozenset({"/health"})


class RateLimiter:
    """Thread-safe per-key sliding-window rate limiter.

    Usage::

        limiter = RateLimiter(requests_per_minute=60)
        allowed, remaining = limiter.is_allowed("api-key-abc")
        if not allowed:
            ...  # return 429
    """

    def __init__(self, requests_per_minute: int = 60) -> None:
        self._rpm = requests_per_minute
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    @property
    def limit(self) -> int:
        return self._rpm

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """Check whether *key* may make another request.

        Returns ``(allowed, remaining)`` where *remaining* is the number of
        additional requests available in the current window.
        """
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            dq = self._windows[key]
            # Evict timestamps outside the 60-second window.
            while dq and dq[0] <= cutoff:
                dq.popleft()
            count = len(dq)
            if count >= self._rpm:
                return False, 0
            dq.append(now)
            return True, self._rpm - count - 1

    def reset(self, key: str | None = None) -> None:
        """Clear the window for *key*, or all keys when *key* is ``None``."""
        with self._lock:
            if key is None:
                self._windows.clear()
            else:
                self._windows.pop(key, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply sliding-window rate limiting to every non-exempt path.

    The rate-limit key is the ``X-API-Key`` header when present (so each
    tenant has its own quota), falling back to the client IP address.

    Parameters
    ----------
    limiter:
        A :class:`RateLimiter` instance shared across all requests.
    exempt_paths:
        Paths that bypass rate limiting.  Defaults to ``/health``.
    """

    def __init__(
        self,
        app,
        limiter: RateLimiter,
        exempt_paths: frozenset[str] = _DEFAULT_EXEMPT,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._exempt_paths = exempt_paths

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        key = request.headers.get("X-API-Key") or (
            request.client.host if request.client else "unknown"
        )
        allowed, remaining = self._limiter.is_allowed(key)

        if not allowed:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self._limiter.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._limiter.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
