"""
Rate Limiter Utility
Simple in-memory rate limiter using a sliding-window algorithm.
No external dependency required.
"""
import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    """
    Per-IP sliding window rate limiter.
    Allows `max_requests` within a `window_seconds` time window.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if the identifier (IP address) is allowed to make a request.
        Returns True if allowed, False if rate-limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            queue = self._requests[identifier]

            # Remove timestamps outside the current window
            while queue and queue[0] < window_start:
                queue.popleft()

            if len(queue) >= self.max_requests:
                return False

            queue.append(now)
            return True

    def get_retry_after(self, identifier: str) -> int:
        """
        Returns how many seconds until the client can retry.
        """
        with self._lock:
            queue = self._requests.get(identifier)
            if not queue:
                return 0
            oldest = queue[0]
            retry_after = int(self.window_seconds - (time.time() - oldest)) + 1
            return max(retry_after, 1)

    def cleanup(self):
        """
        Remove stale entries (clients with no recent requests).
        Call this periodically to prevent unbounded memory growth.
        """
        now = time.time()
        window_start = now - self.window_seconds
        with self._lock:
            stale_keys = []
            for key, queue in self._requests.items():
                # Remove old timestamps
                while queue and queue[0] < window_start:
                    queue.popleft()
                if not queue:
                    stale_keys.append(key)
            for key in stale_keys:
                del self._requests[key]


# Singleton rate limiter instance used across the application
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
