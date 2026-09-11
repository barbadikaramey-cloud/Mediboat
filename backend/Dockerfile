# ── Build stage ────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# System deps for native extensions (bcrypt, sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock* ./

# Install dependencies into /app/.venv (no project itself yet)
RUN uv sync --frozen --no-install-project --no-cache


# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the pre-built venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/
COPY data/ ./data/

# Non-root user for security
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Activate venv by prepending to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["sh", "-c", "python data/seed_db.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info"]
