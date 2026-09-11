"""MediBot FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from app.auth import Token, TokenData, authenticate_user, create_access_token, get_current_user
from app.config import Settings, get_settings
from app.observability import logfire_info, logfire_span, setup_observability
from app.rate_limit import enforce_chat_rate_limit
from app.rbac import get_allowed_collections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifespan with Background Model Warmup ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MediBot backend starting up")
    
    # Warm up ML models in a background thread so the first user query has zero cold-start delay
    import asyncio
    loop = asyncio.get_event_loop()
    def _warmup_worker():
        try:
            with logfire_span("startup.model_warmup"):
                logfire_info("Background model pre-warming started...")
                from app.retrieval.hybrid_search import _get_dense_model, _get_sparse_model
                _get_dense_model()
                _get_sparse_model()
                if get_settings().use_cross_encoder:
                    from app.retrieval.rerank import _get_cross_encoder
                    _get_cross_encoder()
                logfire_info("Background model pre-warming complete! Cold-start latency eliminated.")
        except Exception as exc:
            logger.warning("Background warmup notice: %s", exc)

    loop.run_in_executor(None, _warmup_worker)
    yield
    logger.info("MediBot backend shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediBot API",
    description="RAG backend for MediAssist Health Network with RBAC",
    version="0.1.0",
    lifespan=lifespan,
)

# Observability (Logfire middleware + LangSmith tracing)
setup_observability(app)

# CORS — restrict to known frontend origins in prod
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []
    # NOTE: role is NOT accepted here — always read from the JWT


class Source(BaseModel):
    id: str | None = None
    document: str
    section: str
    collection: str
    score: float | None = None
    page_number: int | None = None
    chunk_type: str | None = None
    text: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = []
    retrieval_type: str  # "document_rag" | "sql_rag" | "blocked"
    role: str
    is_cached: bool = False


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.post("/login", response_model=Token)
async def login(
    body: LoginRequest,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """Authenticate and return a signed JWT. Role is embedded in the token."""
    with logfire_span("api.login", username=body.username):
        user = authenticate_user(body.username, body.password)
        if not user:
            logfire_info("Login failed: invalid credentials for {username}", username=body.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = create_access_token(body.username, user["role"], settings)
        logfire_info("Login successful: user={username}, role={role}", username=body.username, role=user["role"])
        return Token(access_token=token)


@app.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    """Main RAG endpoint — RBAC enforced server-side from JWT.

    Routes to document_rag or sql_rag via LangGraph based on question type.
    Role is read from the signed JWT — never from the request body.
    """
    from app.graph import run_chat

    with logfire_span(
        "api.chat",
        username=current_user.username,
        role=current_user.role,
        question=body.question[:120],
        history_length=len(body.history),
    ):
        await enforce_chat_rate_limit(current_user.username)
        result = await run_chat(
            question=body.question,
            role=current_user.role,
            username=current_user.username,
            history=[m.model_dump() for m in body.history],
        )
        logfire_info(
            "Chat completed: route={route}, sources={source_count}, answer_len={answer_len}",
            route=result.get("retrieval_type", "unknown"),
            source_count=len(result.get("sources", [])),
            answer_len=len(result.get("answer", "")),
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[Source(**s) for s in result.get("sources", [])],
            retrieval_type=result["retrieval_type"],
            role=result["role"],
            is_cached=result.get("is_cached", False),
        )


@app.get("/collections/{role}")
async def get_collections(
    role: str,
    current_user: Annotated[TokenData, Depends(get_current_user)],
):
    """Return the collections accessible to a role.

    JWT role must match path role, or caller must be admin.
    """
    if current_user.role != "admin" and current_user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only query collections for your own role.",
        )
    return {"role": role, "collections": get_allowed_collections(role)}


@app.get("/health")
async def health():
    """Liveness probe for Render."""
    return {"status": "ok", "service": "medibot"}


@app.get("/", response_class=HTMLResponse)
async def serve_portal():
    """Serve the interactive MediBot Staff Portal Web UI."""
    index_file = Path(__file__).parent / "static" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>MediBot API is running. Visit /docs for Swagger UI.</h1>")
