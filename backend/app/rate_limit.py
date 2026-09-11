"""Chat rate limiting with Upstash and a local-development fallback."""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from app.config import get_settings

_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = asyncio.Lock()


async def enforce_chat_rate_limit(username: str) -> None:
    """Enforce a fixed request window per signed-in user."""
    settings = get_settings()
    key = f"medibot:rate:{username}"
    window = settings.rate_limit_window_seconds

    if settings.upstash_redis_url and settings.upstash_redis_token:
        try:
            from upstash_redis import Redis

            def increment() -> int:
                redis = Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)
                count = int(redis.incr(key))
                if count == 1:
                    redis.expire(key, window)
                return count

            if await asyncio.to_thread(increment) <= settings.rate_limit_requests:
                return
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many chat requests. Please wait and try again.")
        except HTTPException:
            raise
        except Exception:
            # Cache outages should not make the healthcare assistant unavailable.
            pass

    now = time.time()
    async with _lock:
        attempts = _requests[key]
        while attempts and attempts[0] <= now - window:
            attempts.popleft()
        if len(attempts) >= settings.rate_limit_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many chat requests. Please wait and try again.")
        attempts.append(now)
