import pytest
from fastapi import HTTPException

import app.rate_limit as rate_limit


@pytest.mark.asyncio
async def test_local_rate_limit_blocks_after_configured_threshold(monkeypatch):
    settings = rate_limit.get_settings()
    monkeypatch.setattr(settings, "rate_limit_requests", 1)
    monkeypatch.setattr(settings, "rate_limit_window_seconds", 60)
    monkeypatch.setattr(settings, "upstash_redis_url", "")
    rate_limit._requests.clear()
    await rate_limit.enforce_chat_rate_limit("test-user")
    with pytest.raises(HTTPException) as exc:
        await rate_limit.enforce_chat_rate_limit("test-user")
    assert exc.value.status_code == 429
