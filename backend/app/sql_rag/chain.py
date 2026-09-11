"""SQL RAG chain: NL → SQL → execute → NL answer.

Three explicit steps (per spec):
  1. LLM (70B) translates the natural language question → SQL
  2. Strip markdown fences / explanation text → extract bare SQL
  3. Execute against SQLite → pass result back to LLM → natural language answer

Gated to billing_executive and admin roles only (enforced in graph.py).

Supports 4 target analytical questions:
  Q1: Escalated claims submitted last month
  Q2: Top maintenance category by ticket count
  Q3: Average claimed amount by department
  Q4: Open tickets grouped by equipment name
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from groq import Groq
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.observability import logfire_info, logfire_span

logger = logging.getLogger(__name__)

# ── Static schema description (cached as a module constant — never re-fetched) ─
# Token optimization: this string is injected once into the system prompt and
# reused across all requests rather than querying sqlite_master each time.
_SCHEMA_DESCRIPTION = """
Database: mediassist.db — MediAssist Health Network operational data.

Table: claims
  claim_id       TEXT   — unique claim identifier (e.g. CLM-2024-1000)
  patient_id     TEXT   — patient identifier
  patient_name   TEXT   — patient full name
  department     TEXT   — hospital department (e.g. nephrology, cardiology)
  claim_type     TEXT   — type of claim (e.g. reimbursement, cashless)
  diagnosis_code TEXT   — ICD-10 diagnosis code
  insurer        TEXT   — insurance company name
  claimed_amount REAL   — total amount claimed (INR)
  approved_amount REAL  — amount approved (NULL if pending)
  status         TEXT   — pending | approved | rejected | escalated
  submitted_date TEXT   — ISO date (YYYY-MM-DD)
  resolved_date  TEXT   — ISO date or NULL if unresolved

Table: maintenance_tickets
  ticket_id      TEXT   — unique ticket identifier (e.g. TKT-2024-2000)
  equipment_name TEXT   — name of the equipment
  equipment_id   TEXT   — unique equipment identifier
  category       TEXT   — equipment category (e.g. sterilisation, imaging)
  campus         TEXT   — hospital/clinic campus name
  issue_type     TEXT   — preventive_maintenance | corrective | calibration | emergency
  fault_code     TEXT   — manufacturer fault code (may be NULL)
  raised_by      TEXT   — staff name who raised the ticket
  raised_date    TEXT   — ISO date
  resolved_date  TEXT   — ISO date or NULL if open
  status         TEXT   — open | in_progress | resolved | closed
  resolution_note TEXT  — free-text resolution note (may be NULL)
""".strip()

_NL2SQL_SYSTEM = (
    "You are an expert SQL assistant for a healthcare database. "
    "Write a single valid SQLite SELECT query to answer the user's question. "
    "Output ONLY the SQL statement — no markdown, no explanation, no comments. "
    "Use only the tables and columns described in the schema.\n"
    "Temporal context: All records in this database are from 2024 (the latest recorded month is December 2024, i.e. '2024-12'). "
    "When the user asks for 'last month', 'recent', or relative time without a year, "
    "interpret it relative to the latest month in the database (e.g. using '2024-12' or "
    "strftime('%Y-%m', submitted_date) = (SELECT strftime('%Y-%m', MAX(submitted_date)) FROM claims))."
)

_ANSWER_SYSTEM = (
    "You are a helpful data analyst for a healthcare network. "
    "Given a SQL query result, provide a concise, clear answer to the original question. "
    "Format numbers readably. Do not mention SQL or technical details."
)


def _extract_sql(raw: str) -> str:
    """Strip markdown fences and explanatory text; return only the SQL statement."""
    # Remove ```sql ... ``` or ``` ... ``` fences
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)

    # Find the first SELECT statement
    match = re.search(r"(SELECT\b.+)", raw, flags=re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        # Truncate at first semicolon
        if ";" in sql:
            sql = sql[: sql.index(";") + 1]
        return sql

    # Fallback: return stripped raw (may still work)
    return raw.strip()


def _run_sql(db_path: str, sql: str) -> list[dict]:
    """Execute a read-only query through SQLAlchemy and return row mappings."""
    db_url = f"sqlite+pysqlite:///{Path(db_path).resolve().as_posix()}"
    engine = create_engine(db_url, future=True)
    try:
        with engine.connect() as connection:
            return [dict(row) for row in connection.execute(text(sql)).mappings().all()]
    finally:
        engine.dispose()


def sql_rag_chain(question: str, history: list[dict] | None = None) -> str:
    """Run the three-step SQL RAG chain and return a natural language answer.

    Steps:
      1. NL → SQL (Llama 3.3 70B, with conversation history context)
      2. Strip SQL from LLM output
      3. Execute → pass result to LLM → NL answer (Llama 3.3 70B)
    """
    settings = get_settings()
    client = Groq(api_key=settings.groq_api_key.strip())

    db_path = str(
        Path(__file__).parent.parent.parent / settings.sqlite_db_path
    )

    recent_history = [
        {"role": h["role"], "content": h["content"]}
        for h in (history or [])[-4:]
        if h.get("role") in ("user", "assistant") and h.get("content")
    ]

    with logfire_span("sql_rag.nl_to_sql_flow", question=question[:100]):
        # ── Step 1: NL → SQL ──────────────────────────────────────────────────
        logfire_info("SQL RAG generating SQL query for question='{question}'", question=question[:80])
        nl2sql_messages = [
            {
                "role": "system",
                "content": f"{_NL2SQL_SYSTEM}\n\nSchema:\n{_SCHEMA_DESCRIPTION}",
            }
        ]
        nl2sql_messages.extend(recent_history)
        nl2sql_messages.append({"role": "user", "content": question})

        with logfire_span("sql_rag.generate_sql_llm"):
            nl2sql_response = client.chat.completions.create(
                model=settings.model_generation.strip(),  # 70B for NL→SQL quality
                messages=nl2sql_messages,
                temperature=0,
                max_tokens=512,
            )
            raw_sql_output = nl2sql_response.choices[0].message.content or ""

        # ── Step 2: Extract bare SQL ───────────────────────────────────────────
        sql = _extract_sql(raw_sql_output)
        logfire_info("Extracted SQL statement: {sql}", sql=sql)

        if not sql.upper().startswith("SELECT"):
            logfire_info("Extracted SQL was invalid or did not start with SELECT: {sql}", sql=sql)
            return (
                "I was unable to translate your question into a valid SQL query. "
                "Please rephrase your question and try again."
            )

        # ── Step 3: Execute + NL answer ───────────────────────────────────────
        with logfire_span("sql_rag.execute_sqlite", sql=sql):
            try:
                rows = _run_sql(db_path, sql)
            except Exception as exc:
                logger.error("SQL execution error: %s | SQL: %s", exc, sql)
                logfire_info("SQL execution error: {error} | SQL: {sql}", error=str(exc), sql=sql)
                return f"The query could not be executed: {exc}. Please rephrase your question."

        logfire_info("SQLite returned {count} rows", count=len(rows))

        if not rows:
            return "The query returned no results. The data may not exist in the current database."

        # Format rows as a readable string for the LLM
        result_str = "\n".join(str(r) for r in rows[:50])  # cap at 50 rows to limit tokens

        answer_messages = [
            {"role": "system", "content": _ANSWER_SYSTEM}
        ]
        answer_messages.extend(recent_history)
        answer_messages.append({
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SQL result ({len(rows)} rows):\n{result_str}"
            ),
        })

        with logfire_span("sql_rag.synthesize_answer_llm"):
            answer_response = client.chat.completions.create(
                model=settings.model_generation.strip(),
                messages=answer_messages,
                temperature=0.2,
                max_tokens=512,
            )
            answer = answer_response.choices[0].message.content or "No answer generated."

        logfire_info("SQL RAG complete (answer_length={length} chars)", length=len(answer))
        return answer
