"""LangGraph /chat routing graph.

Flow per request:
  input_guard → router → [sql_rag | document_rag] → output_guard → response

Nodes:
  input_guard     — regex + cheap LLM injection screen
  router          — cheap LLM classifies: analytical question vs document question
  document_rag    — hybrid search → rerank → LLM answer with citations
  sql_rag         — NL→SQL→execute→NL (billing_executive / admin only)
  output_guard    — groundedness check + RBAC leak check

Token optimization applied:
  - Cheap 8B model for: input guardrail, router, output groundedness check
  - 70B model only for: final RAG answer generation, NL→SQL
  - Only reranked top-3 chunks enter the LLM prompt (never top-10)
  - Upstash Redis cache: (role, normalized_question) → answer, 10 min TTL
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from typing import Any, TypedDict

from groq import AsyncGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.guardrails.input_guard import GuardrailResult, check_input
from app.guardrails.output_guard import check_output
from app.observability import logfire_info, logfire_span
from app.rbac import build_qdrant_filter, can_use_sql_rag, get_allowed_collections, rbac_refusal_message

logger = logging.getLogger(__name__)

# ── RAG system prompt (static — goes in system message for provider caching) ──
_RAG_SYSTEM = (
    "You are MediBot, a clinical AI assistant for MediAssist Health Network staff.\n\n"
    "MANDATORY NLI & RELEVANCE RULES:\n"
    "1. Topic Relevance Check First:\n"
    "   Before generating an answer, evaluate whether the provided document excerpts explicitly address "
    "the specific disease, condition, drug, or clinical question asked by the user.\n"
    "2. Deterministic Refusal:\n"
    "   If the excerpts do NOT contain direct, relevant information to answer the question, or if they only describe "
    "a different condition (e.g. COPD or asthma excerpts when asked about pneumonia, or dengue excerpts when asked about malaria), "
    "you MUST output EXACTLY this response and nothing else:\n"
    "   'I could not find any relevant information in the accessible clinical and hospital documents to answer your question. "
    "Please verify the query or consult authoritative medical references.'\n"
    "   Do NOT attempt to guess, extrapolate, synthesize, or combine unrelated protocols.\n"
    "3. Strict Sourced Facts:\n"
    "   If the excerpts directly address the question, provide a clear, professional answer using ONLY facts stated in the text. "
    "You may ONLY attach citation tags (e.g. [1], [2], or [1†Section Name]) to statements directly and literally found in that excerpt.\n"
    "4. Zero Fabricated Attributions:\n"
    "   NEVER attach a citation tag to any fact, drug, route, dosage, or availability claim not explicitly written in that excerpt.\n"
    "5. Missing Specifics:\n"
    "   If the excerpt covers the general topic but does not contain a specific detail (e.g. ICU ventilator settings or oral switch agents), "
    "state clearly: 'The provided protocols do not specify [missing item].'\n"
    "6. Be concise, accurate, and professional."
)

# ── Router system prompt ───────────────────────────────────────────────────────
_ROUTER_SYSTEM = (
    "Classify the following user question as either 'analytical' or 'document' taking into account the conversation history.\n"
    "- 'analytical': questions about counts, numbers, totals, averages, statistics, "
    "claims submitted/approved/escalated/rejected, maintenance tickets, equipment faults, "
    "costs, amounts, patient or department breakdowns/segregations, or follow-ups/clarifications to previous "
    "database or analytical answers (e.g. 'but this is only 4', 'you said 9 claims', 'show all records', 'full answer', 'why only 1').\n"
    "- 'document': questions about clinical protocols, medical treatments, drug dosages, "
    "hospital policies, staff handbooks, leave rules, insurance submission procedures, "
    "or general information.\n\n"
    "Reply with exactly one word: analytical OR document."
)

_CONTEXTUALIZE_SYSTEM = (
    "Given a conversation history between a user and an AI assistant, and a new follow-up question from the user, "
    "rewrite the follow-up question into a standalone, self-contained search query suitable for document retrieval. "
    "Resolve any pronouns (e.g. 'it', 'they', 'its', 'these') and incorporate relevant context (e.g. disease name, drug name, policy). "
    "If the question is already fully self-contained or does not depend on the history, return it as is. "
    "Output ONLY the standalone query. Do not include markdown, explanations, or quotes."
)


_ANALYTICAL_PATTERN = re.compile(
    r"\b("
    r"how\s+many|"
    r"total\s+(claims?|tickets?|amount|cost|spend)|"
    r"average\s+(claimed|approved|amount|cost|tickets?)|"
    r"count\s+(of\s+)?(claims?|tickets?)|"
    r"sum\s+(of\s+)?(claims?|amounts?)|"
    r"top\s+\d+|"
    r"open\s+tickets?|"
    r"closed\s+tickets?|"
    r"escalated\s+claims?|"
    r"pending\s+claims?|"
    r"highest\s+(claimed|amount|cost)|"
    r"lowest\s+(claimed|amount|cost)|"
    r"by\s+department|grouped\s+by|"
    r"segregat(ion|e)?|"
    r"breakdown|"
    r"per\s+(patient|department|doctor|hospital|equipment|category|month|insurer)|"
    r"(only|just)\s+\d+|"
    r"full\s+(answer|list|result|records?|table)|"
    r"all\s+(records?|claims?|tickets?|rows?)|"
    r"(list|show)\s+(the\s+)?(claims?|tickets?|records?|breakdown)|"
    r"why\s+only|"
    r"(claims?|tickets?)\s+(in|for|during)\s+(the\s+)?last\s+(month|year|week)|"
    r"(claims?|tickets?)\s+submitted"
    r")\b",
    re.IGNORECASE,
)


# ── Graph state ────────────────────────────────────────────────────────────────
class ChatState(TypedDict):
    question: str
    role: str
    username: str
    history: list[dict]
    # Set during graph execution
    blocked: bool
    block_reason: str
    route: str                          # "sql_rag" | "document_rag" | "blocked"
    retrieved_chunks: list[Any]
    reranked_chunks: list[Any]
    answer: str
    sources: list[dict]
    retrieval_type: str
    cache_key: str
    is_cached: bool


def _normalize_query(q: str) -> str:
    """Normalize query text: lowercase, remove punctuation, collapse whitespace."""
    cleaned = re.sub(r"[^\w\s]", "", q.lower()).strip()
    return " ".join(cleaned.split())


def _make_cache_key(role: str, query: str) -> str:
    """Generate a deterministic Redis cache key based on role and normalized query."""
    norm = _normalize_query(query)
    return hashlib.sha256(f"medibot:v2:{role}:{norm}".encode()).hexdigest()


async def _cache_get(key: str) -> dict | None:
    try:
        with logfire_span("cache.upstash_redis_get", key=key[:16]):
            from upstash_redis import Redis
            settings = get_settings()
            if not settings.upstash_redis_url or not settings.upstash_redis_token:
                return None
            redis = Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)
            val = await asyncio.to_thread(redis.get, key)
            if val is None:
                return None
            if isinstance(val, dict):
                return val
            if isinstance(val, (str, bytes)):
                return json.loads(val)
    except Exception as exc:
        logger.warning("Cache get error: %s", exc)
    return None


async def _cache_set(key: str, value: dict) -> None:
    try:
        with logfire_span("cache.upstash_redis_set", key=key[:16]):
            from upstash_redis import Redis
            settings = get_settings()
            if not settings.upstash_redis_url or not settings.upstash_redis_token:
                return
            redis = Redis(url=settings.upstash_redis_url, token=settings.upstash_redis_token)
            payload = json.dumps(value)
            await asyncio.to_thread(redis.set, key, payload, ex=settings.cache_ttl_seconds)
            logger.info("Cache successfully SET for key=%s (ttl=%ds)", key[:16], settings.cache_ttl_seconds)
    except Exception as exc:
        logger.warning("Cache set error: %s", exc)


# ── Graph nodes ────────────────────────────────────────────────────────────────
async def node_input_guard(state: ChatState) -> dict:
    """Screen question for injection/jailbreak attempts (with conversation history context)."""
    with logfire_span("graph.node_input_guard", role=state["role"], question=state["question"][:100]):
        result: GuardrailResult = await check_input(state["question"], state.get("history"))
        if result.blocked:
            logfire_info(
                "Input guardrail BLOCKED query: reason={reason}",
                reason=result.reason,
            )
            return {
                "blocked": True,
                "block_reason": result.reason,
                "route": "blocked",
            }
        logfire_info("Input guardrail passed (query deemed safe).")
        return {"blocked": False, "block_reason": ""}


async def node_router(state: ChatState) -> dict:
    """Route to sql_rag or document_rag using fast-path regex + cheap 8B model."""
    if state.get("blocked"):
        return {"route": "blocked"}

    question = state["question"]

    with logfire_span("graph.node_router", question=question[:100], role=state["role"]):
        # 1. Fast-path regex check for obvious analytical queries
        if _ANALYTICAL_PATTERN.search(question):
            verdict = "analytical"
            logfire_info("Router fast-path matched analytical regex pattern.")
        else:
            recent_history = [
                {"role": h["role"], "content": h["content"]}
                for h in (state.get("history") or [])[-4:]
                if h.get("role") in ("user", "assistant") and h.get("content")
            ]
            last_assistant = next((h["content"] for h in reversed(recent_history) if h["role"] == "assistant"), "")
            is_followup_to_sql = any(k in last_assistant.lower() for k in ("claim", "ticket", "approved", "claimed", "₹", "inr", "record", "department", "patient id"))
            short_followup_pattern = re.compile(r"\b(why|only|how\s+come|more|full|explain|all|where\s+are|details?|breakdown)\b", re.IGNORECASE)

            if is_followup_to_sql and short_followup_pattern.search(question):
                verdict = "analytical"
                logfire_info("Router fast-path: conversational follow-up to analytical response.")
            else:
                # 2. LLM classifier with sufficient tokens (512) so reasoning tokens don't eat content
                settings = get_settings()
                client = AsyncGroq(api_key=settings.groq_api_key.strip(), timeout=20.0)

                router_messages = [{"role": "system", "content": _ROUTER_SYSTEM}]
                router_messages.extend(recent_history)
                router_messages.append({"role": "user", "content": question})

                try:
                    response = await client.chat.completions.create(
                        model=settings.model_cheap.strip(),
                        messages=router_messages,
                        temperature=0,
                        max_tokens=512,
                    )
                    raw_content = (response.choices[0].message.content or "").strip().lower()
                    raw_reasoning = (getattr(response.choices[0].message, "reasoning", "") or "").lower()
                    combined_verdict = f"{raw_content} {raw_reasoning}"

                    if "analytical" in combined_verdict:
                        verdict = "analytical"
                    else:
                        verdict = "document"
                    logfire_info(
                        "Router LLM verdict: {verdict} (raw_content='{content}')",
                        verdict=verdict,
                        content=raw_content,
                    )
                except Exception as exc:
                    logger.warning("Router LLM failed (%s) — defaulting to document_rag", exc)
                    verdict = "document"

        route = "sql_rag" if verdict == "analytical" else "document_rag"
        logfire_info("Final routing destination: {route}", route=route)
        return {"route": route}


async def node_document_rag(state: ChatState) -> dict:
    """Hybrid retrieval → CrossEncoder rerank → LLM generation."""
    settings = get_settings()
    role = state["role"]
    question = state["question"]
    history = state.get("history", [])

    with logfire_span("rag.document_flow", role=role, question=question[:100]):
        # Check cache: first check direct question cache
        direct_cache_key = _make_cache_key(role, question)
        cached = await _cache_get(direct_cache_key)
        if cached:
            logfire_info("Document RAG cache HIT (direct) for role={role}", role=role)
            return {**cached, "cache_key": direct_cache_key, "reranked_chunks": [], "is_cached": True}

        from app.retrieval.hybrid_search import hybrid_search
        from app.retrieval.rerank import rerank

        # Contextualize query for retrieval if conversation history exists
        retrieval_query = question
        recent_history = [
            {"role": h["role"], "content": h["content"]}
            for h in history[-4:]
            if h.get("role") in ("user", "assistant") and h.get("content")
        ]
        if recent_history:
            try:
                rewrite_client = AsyncGroq(api_key=settings.groq_api_key, timeout=15.0)
                rewrite_messages = [{"role": "system", "content": _CONTEXTUALIZE_SYSTEM}]
                rewrite_messages.extend(recent_history)
                rewrite_messages.append({"role": "user", "content": question})
                rewrite_resp = await rewrite_client.chat.completions.create(
                    model=settings.model_cheap.strip(),
                    messages=rewrite_messages,
                    temperature=0,
                    max_tokens=256,
                )
                raw_rewritten = (rewrite_resp.choices[0].message.content or "").strip()
                if raw_rewritten:
                    retrieval_query = raw_rewritten
                    logfire_info(
                        "Contextualized retrieval query: '{orig}' -> '{rewritten}'",
                        orig=question[:80],
                        rewritten=retrieval_query[:120],
                    )
            except Exception as exc:
                logger.warning("Query contextualization failed (%s) - falling back to original question", exc)

        # If query was rewritten, check if the rewritten query is already cached
        if retrieval_query != question:
            context_cache_key = _make_cache_key(role, retrieval_query)
            cached = await _cache_get(context_cache_key)
            if cached:
                logfire_info("Document RAG cache HIT (contextualized) for role={role}", role=role)
                return {**cached, "cache_key": context_cache_key, "reranked_chunks": [], "is_cached": True}

        logfire_info("Document RAG cache MISS for role={role}. Executing hybrid search.", role=role)

        # Hybrid search (top-20, RBAC filtered server-side) using contextualized query
        chunks = hybrid_search(query=retrieval_query, role=role)
        logfire_info(
            "Hybrid search completed: {count} chunks retrieved",
            count=len(chunks),
        )

        # CrossEncoder rerank → top chunks passing relevance floor
        top_chunks = rerank(query=retrieval_query, chunks=chunks)
        if not top_chunks:
            logfire_info(
                "Document RAG deterministic refusal: zero chunks passed CE floor ({floor:.2f}) for query='{q}'",
                floor=settings.ce_relevance_floor,
                q=retrieval_query[:80],
            )
            return {
                "retrieved_chunks": chunks,
                "reranked_chunks": [],
                "answer": (
                    "I could not find any relevant information in the accessible clinical and hospital documents "
                    "to answer your question. Please verify the query or consult authoritative medical references."
                ),
                "sources": [],
                "retrieval_type": "document_rag",
                "cache_key": direct_cache_key,
                "is_cached": False,
            }

        top_score = top_chunks[0].score if top_chunks else 0.0
        logfire_info(
            "Cross-Encoder rerank completed: {count} chunks selected (top_score={score:.4f})",
            count=len(top_chunks),
            score=top_score,
        )

        # Build prompt with reranked chunks from admitted documents
        context_parts = []
        for i, chunk in enumerate(top_chunks, 1):
            context_parts.append(
                f"[{i}] Source: {chunk.source_document} | Section: {chunk.section_title}\n{chunk.text}"
            )
        context = "\n\n".join(context_parts)

        gen_messages = [{"role": "system", "content": _RAG_SYSTEM}]
        gen_messages.extend(recent_history)
        gen_messages.append({
            "role": "user",
            "content": f"Context from retrieved documents:\n{context}\n\nQuestion: {question}",
        })

        # Generate answer with 70B model
        logfire_info(
            "Dispatching generation prompt to {model} (context_chunks={chunks})",
            model=settings.model_generation.strip(),
            chunks=len(top_chunks),
        )
        client = AsyncGroq(api_key=settings.groq_api_key.strip(), timeout=20.0)
        response = await client.chat.completions.create(
            model=settings.model_generation.strip(),
            messages=gen_messages,
            temperature=0.2,
            max_tokens=1024,
        )
        answer = response.choices[0].message.content or "I was unable to generate an answer."
        logfire_info("LLM generation complete (answer_length={length} chars)", length=len(answer))

        # Automated citation verification (Option B: drop sentences with unsupported citations)
        from app.guardrails.output_guard import verify_and_prune_citations
        chunk_texts = [c.text for c in top_chunks]
        verified_answer, audit_records = await verify_and_prune_citations(answer, chunk_texts)
        if len(verified_answer) != len(answer):
            logfire_info(
                "Citation verification pruned answer (orig_len={orig}, new_len={new})",
                orig=len(answer),
                new=len(verified_answer),
            )
            answer = verified_answer

        if not answer.strip():
            logfire_info("Citation verification pruned all unsupported claims — returning deterministic refusal")
            return {
                "retrieved_chunks": chunks,
                "reranked_chunks": top_chunks,
                "answer": (
                    "I could not find any relevant information in the accessible clinical and hospital documents "
                    "to answer your question. Please verify the query or consult authoritative medical references."
                ),
                "sources": [],
                "retrieval_type": "document_rag",
                "cache_key": direct_cache_key,
                "is_cached": False,
            }

        sources = [
            {
                "id": c.id,
                "document": c.source_document,
                "section": c.section_title,
                "collection": c.collection,
                "score": round(c.score, 4),
                "page_number": c.page_number,
                "chunk_type": c.chunk_type,
                "text": c.text,
            }
            for c in top_chunks
        ]

        result = {
            "retrieved_chunks": chunks,
            "reranked_chunks": top_chunks,
            "answer": answer,
            "sources": sources,
            "retrieval_type": "document_rag",
            "cache_key": direct_cache_key,
            "is_cached": False,
        }

        cache_payload = {
            "answer": answer,
            "sources": sources,
            "retrieval_type": "document_rag",
            "is_cached": True,
        }
        await _cache_set(direct_cache_key, cache_payload)
        if retrieval_query != question:
            await _cache_set(_make_cache_key(role, retrieval_query), cache_payload)
        return result


async def node_sql_rag(state: ChatState) -> dict:
    """SQL RAG: NL → SQL → execute → NL answer."""
    role = state["role"]
    question = state["question"]
    history = state.get("history", [])

    with logfire_span("rag.sql_flow", role=role, question=question[:100]):
        # Gate check (belt-and-suspenders, also enforced in router node)
        if not can_use_sql_rag(role):
            logfire_info("SQL RAG blocked by RBAC: role={role} not authorized", role=role)
            return {
                "answer": rbac_refusal_message(role, "analytical claims data"),
                "sources": [],
                "retrieval_type": "blocked",
                "retrieved_chunks": [],
                "reranked_chunks": [],
                "is_cached": False,
            }

        cache_key = _make_cache_key(role, question)
        cached = await _cache_get(cache_key)
        if cached:
            logfire_info("SQL RAG cache HIT for role={role}", role=role)
            return {**cached, "cache_key": cache_key, "is_cached": True}

        logfire_info("SQL RAG cache MISS for role={role}. Executing NL to SQL chain.", role=role)
        answer = await _run_sql_rag(question, history)

        result = {
            "answer": answer,
            "sources": [],
            "retrieval_type": "sql_rag",
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "cache_key": cache_key,
        }
        cache_payload = {
            "answer": answer,
            "sources": [],
            "retrieval_type": "sql_rag",
            "is_cached": True,
        }
        await _cache_set(cache_key, cache_payload)
        return result


async def _run_sql_rag(question: str, history: list[dict] | None = None) -> str:
    """Async wrapper around the synchronous sql_rag_chain."""
    import asyncio
    from app.sql_rag.chain import sql_rag_chain
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sql_rag_chain, question, history)


async def node_output_guard(state: ChatState) -> dict:
    """Groundedness check on the generated answer."""
    if (
        state.get("blocked")
        or state.get("retrieval_type") == "sql_rag"
        or state.get("is_cached")
        or not state.get("reranked_chunks")
    ):
        # SQL RAG answers and cached answers (already verified) skip groundedness check
        return {}

    with logfire_span("guardrail.output_groundedness", question=state.get("question", "")[:100]):
        chunk_texts = [c.text for c in state.get("reranked_chunks", [])]
        result = await check_output(
            answer=state.get("answer", ""),
            chunks=chunk_texts,
            question=state.get("question", ""),
        )

        if not result.grounded:
            logfire_info(
                "Output guardrail: answer NOT grounded ({reason}) — replacing with refusal",
                reason=result.reason,
            )
            return {
                "answer": (
                    "I could not find any relevant information in the accessible clinical and hospital documents "
                    "to answer your question. Please verify the query or consult authoritative medical references."
                ),
                "sources": [],
            }
        logfire_info("Output guardrail: answer verified grounded.")
        return {}


def _get_next_after_guard(state: ChatState) -> str:
    """Edge function: route after input guard."""
    if state.get("blocked"):
        return "end"
    return "router"


def _get_next_after_router(state: ChatState) -> str:
    """Edge function: route after router decision."""
    route = state.get("route", "document_rag")
    if route == "sql_rag":
        return "sql_rag"
    return "document_rag"


# ── Build the graph ────────────────────────────────────────────────────────────
def build_chat_graph():
    """Construct and compile the LangGraph chat routing graph."""
    builder = StateGraph(ChatState)

    builder.add_node("input_guard", node_input_guard)
    builder.add_node("router", node_router)
    builder.add_node("document_rag", node_document_rag)
    builder.add_node("sql_rag", node_sql_rag)
    builder.add_node("output_guard", node_output_guard)

    builder.set_entry_point("input_guard")

    builder.add_conditional_edges(
        "input_guard",
        _get_next_after_guard,
        {"end": END, "router": "router"},
    )
    builder.add_conditional_edges(
        "router",
        _get_next_after_router,
        {"sql_rag": "sql_rag", "document_rag": "document_rag"},
    )
    builder.add_edge("document_rag", "output_guard")
    builder.add_edge("sql_rag", "output_guard")
    builder.add_edge("output_guard", END)

    return builder.compile()


# Module-level compiled graph singleton
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_chat_graph()
    return _graph


async def run_chat(
    question: str,
    role: str,
    username: str,
    history: list[dict] | None = None,
) -> dict:
    """Entry point for the /chat endpoint.

    Returns a dict with: answer, sources, retrieval_type, role.
    Handles blocked inputs and RBAC refusals gracefully.
    """
    graph = get_graph()

    initial_state: ChatState = {
        "question": question,
        "role": role,
        "username": username,
        "history": history or [],
        "blocked": False,
        "block_reason": "",
        "route": "",
        "retrieved_chunks": [],
        "reranked_chunks": [],
        "answer": "",
        "sources": [],
        "retrieval_type": "document_rag",
        "cache_key": "",
        "is_cached": False,
    }

    final_state = await graph.ainvoke(initial_state)

    if final_state.get("blocked"):
        return {
            "answer": (
                f"Your message was blocked by the safety filter. "
                f"Reason: {final_state.get('block_reason', 'Policy violation.')}"
            ),
            "sources": [],
            "retrieval_type": "blocked",
            "role": role,
            "is_cached": False,
        }

    return {
        "answer": final_state.get("answer", "No answer generated."),
        "sources": final_state.get("sources", []),
        "retrieval_type": final_state.get("retrieval_type", "document_rag"),
        "role": role,
        "is_cached": final_state.get("is_cached", False),
    }
