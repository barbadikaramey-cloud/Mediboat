"""Logfire + LangSmith observability setup.

Call `setup_observability(app)` once at FastAPI startup.
"""
from __future__ import annotations

import contextlib
import logging
import os
from typing import Any, Iterator

logger = logging.getLogger(__name__)

_logfire_active: bool = False


def setup_observability(app) -> None:  # noqa: ANN001
    """Attach Logfire middleware and configure LangSmith environment variables."""
    global _logfire_active
    from app.config import get_settings

    settings = get_settings()

    # ── Logfire ───────────────────────────────────────────────────────────────
    if settings.logfire_token and settings.logfire_send_to_logfire:
        try:
            import logfire
            # Set LOGFIRE_SEND_TO_LOGFIRE=false for offline local development.
            logfire.configure(
                token=settings.logfire_token,
                send_to_logfire=settings.logfire_send_to_logfire,
            )
            logfire.instrument_fastapi(app)
            try:
                logfire.instrument_httpx()
            except Exception as exc:
                logger.debug("logfire.instrument_httpx notice: %s", exc)
            _logfire_active = True
            logger.info("Logfire instrumentation active (FastAPI + HTTPX)")
        except ImportError:
            logger.warning("logfire not installed — skipping Logfire instrumentation")
        except Exception as exc:
            logger.warning("Logfire setup failed: %s", exc)
    elif settings.logfire_token:
        logger.info("LOGFIRE_SEND_TO_LOGFIRE=false — local Logfire delivery disabled")
    else:
        logger.info("LOGFIRE_TOKEN not set — skipping Logfire")

    # ── LangSmith (LangChain tracing) ─────────────────────────────────────────
    if settings.langchain_api_key:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", settings.langchain_tracing_v2)
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
        logger.info(
            "LangSmith tracing configured for project '%s'", settings.langchain_project
        )
    else:
        logger.info("LANGCHAIN_API_KEY not set — LangSmith tracing disabled")


@contextlib.contextmanager
def logfire_span(name: str, **attributes: Any) -> Iterator[Any]:
    """Safe context manager that creates a Logfire span if active, else no-op.

    CRITICAL: User exceptions must always propagate.  We only catch errors from
    logfire *itself* (import, span creation).  Once ``yield`` is reached, any
    exception raised by user code flows through ``logfire.span.__exit__`` and
    is re-raised — never swallowed.
    """
    if not _logfire_active:
        yield None
        return
    try:
        import logfire
    except ImportError:
        yield None
        return
    # Delegate directly to logfire.span — user exceptions propagate naturally
    with logfire.span(name, **attributes) as span:
        yield span


def logfire_info(msg: str, **attributes: Any) -> None:
    """Safe helper that logs structured events to Logfire and standard Python logger."""
    if _logfire_active:
        try:
            import logfire
            logfire.info(msg, **attributes)
        except Exception:
            pass
    # Log via standard logger for console visibility
    if attributes:
        try:
            formatted = msg.format(**attributes)
            logger.info(formatted)
        except Exception:
            logger.info("%s | %s", msg, attributes)
    else:
        logger.info(msg)
