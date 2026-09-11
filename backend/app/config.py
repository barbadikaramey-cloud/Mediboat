import os
from functools import lru_cache
from pathlib import Path
from typing import Final

# Ensure cache directories default to D:\ if on Windows with D: drive
if os.name == "nt" and Path("D:/").exists():
    os.environ.setdefault("HF_HOME", "D:/hf_cache")
    os.environ.setdefault("TORCH_HOME", "D:/torch_cache")
    os.environ.setdefault("FASTEMBED_CACHE_PATH", "D:/fastembed_cache")
    os.environ.setdefault("TEMP", "D:/temp")
    os.environ.setdefault("TMP", "D:/temp")

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Groq ──────────────────────────────────────────────────────────────────
    groq_api_key: str = ""

    # Model routing: reserve 120B for generation + NL→SQL, use 20B everywhere else
    model_generation: str = "openai/gpt-oss-120b"   # final answer, NL→SQL
    model_cheap: str = "openai/gpt-oss-20b"         # guardrail, router, groundedness

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "medibot"                  # single collection, role-filtered

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # ── Upstash Redis ─────────────────────────────────────────────────────────
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    cache_ttl_seconds: int = 600                        # 10 min for repeated queries
    rate_limit_requests: int = 20
    rate_limit_window_seconds: int = 60

    # ── Observability ─────────────────────────────────────────────────────────
    logfire_token: str = ""
    logfire_send_to_logfire: bool = True
    langchain_api_key: str = ""                         # LangSmith
    langchain_tracing_v2: str = "true"
    langchain_project: str = "medibot"

    # ── Embedding / reranker ──────────────────────────────────────────────────
    embed_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    use_cross_encoder: bool = False  # False for Render 512MB free tier; True for local/high-RAM
    retrieval_top_k: int = 20    # broad candidates from Qdrant
    rerank_max_docs: int = 3     # cap reranker by max unique documents (all relevant chunks admitted)
    rerank_top_n: int = 3        # fallback ceiling if document capping not used
    ce_relevance_floor: float = -2.0  # minimum CrossEncoder logit score to pass as relevant
    chunk_token_limit: int = 400  # cap per chunk at ingestion

    # ── Database ──────────────────────────────────────────────────────────────
    sqlite_db_path: str = "data/mediassist.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: list[str] = ["http://localhost:3000", "https://*.vercel.app"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton — safe for FastAPI dependency injection."""
    return Settings()
