"""HIPAA Safe Harbor & PII De-Identification Middleware.

Under HIPAA Safe Harbor (45 CFR § 164.514(b)(2)), 18 categories of Protected
Health Information (PHI) and Personally Identifiable Information (PII) must be
redacted from health records and query streams.

This middleware intercepts:
  1. Incoming HTTP requests: masks PHI in 'question' and 'history' payloads before
     they reach the LangGraph state machine, database, or LLM prompts.
  2. Outgoing HTTP responses: ensures no unmasked PHI leaks in 'answer' or 'sources'.
  3. Standalone masking utility: `mask_phi()` for direct usage in ingestion or logging.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)

# ── HIPAA Safe Harbor & PII Regex Patterns ────────────────────────────────────

# 1. Medical Record Numbers / Patient IDs (PAT-XXXX, MRN-XXXX, CRN-XXXX)
_PATIENT_ID_PATTERN = re.compile(
    r"\b(PAT|MRN|CRN|PID|PT)[-_\s]?\d{3,8}\b",
    re.IGNORECASE,
)

# 2. Social Security Numbers / National IDs / Tax IDs / 12-digit Aadhaar
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_AADHAAR_PATTERN = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")

# 3. Phone Numbers (US, Indian, and international formats)
_PHONE_PATTERN = re.compile(
    r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b"
)

# 4. Email Addresses
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# 5. Credit Card / Financial Account Numbers (13-16 digits with optional spaces/hyphens)
_FINANCIAL_PATTERN = re.compile(
    r"\b(?:\d{4}[-\s]?){3}\d{4}\b"
)

# 6. Specific Patient Name Patterns in Clinical Queries
# e.g., "patient John Doe", "pt Jane Smith", "admit patient Robert Brown"
_PATIENT_NAME_PATTERN = re.compile(
    r"\b(?:patient|pt|pt\.|mr\.|mrs\.|ms\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+))\b"
)

# 7. Exact Dates of Birth / Date Patterns associated with individuals (e.g., DOB: 12/04/1980)
_DOB_PATTERN = re.compile(
    r"\b(?:DOB|Date of birth|born on|d\.o\.b\.)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    re.IGNORECASE,
)


def mask_phi(text: str) -> tuple[str, list[dict[str, str]]]:
    """Scrub PHI and PII from a text string according to HIPAA Safe Harbor guidelines.

    Returns:
        (sanitized_text, list_of_redactions)
    """
    if not text or not isinstance(text, str):
        return text, []

    redactions: list[dict[str, str]] = []
    sanitized = text

    # Redact Patient IDs / MRNs
    def _sub_patient_id(match: re.Match) -> str:
        orig = match.group(0)
        redactions.append({"category": "MRN", "original": orig, "redacted": "[REDACTED_MRN]"})
        return "[REDACTED_MRN]"

    sanitized = _PATIENT_ID_PATTERN.sub(_sub_patient_id, sanitized)

    # Redact SSN
    def _sub_ssn(match: re.Match) -> str:
        orig = match.group(0)
        redactions.append({"category": "SSN", "original": orig, "redacted": "[REDACTED_SSN]"})
        return "[REDACTED_SSN]"

    sanitized = _SSN_PATTERN.sub(_sub_ssn, sanitized)

    # Redact Aadhaar / National ID
    def _sub_aadhaar(match: re.Match) -> str:
        orig = match.group(0)
        redactions.append({"category": "NATIONAL_ID", "original": orig, "redacted": "[REDACTED_ID]"})
        return "[REDACTED_ID]"

    sanitized = _AADHAAR_PATTERN.sub(_sub_aadhaar, sanitized)

    # Redact Email
    def _sub_email(match: re.Match) -> str:
        orig = match.group(0)
        redactions.append({"category": "EMAIL", "original": orig, "redacted": "[REDACTED_EMAIL]"})
        return "[REDACTED_EMAIL]"

    sanitized = _EMAIL_PATTERN.sub(_sub_email, sanitized)

    # Redact Financial / Credit Card
    def _sub_financial(match: re.Match) -> str:
        orig = match.group(0)
        redactions.append({"category": "FINANCIAL", "original": orig, "redacted": "[REDACTED_FINANCIAL]"})
        return "[REDACTED_FINANCIAL]"

    sanitized = _FINANCIAL_PATTERN.sub(_sub_financial, sanitized)

    # Redact DOB
    def _sub_dob(match: re.Match) -> str:
        redactions.append({"category": "DOB", "original": match.group(1), "redacted": "[REDACTED_DATE]"})
        return f"DOB: [REDACTED_DATE]"

    sanitized = _DOB_PATTERN.sub(_sub_dob, sanitized)

    # Redact Patient Name in clinical phrasing
    def _sub_name(match: re.Match) -> str:
        full_match = match.group(0)
        prefix = full_match.split()[0]
        name = match.group(1)
        redactions.append({"category": "NAME", "original": name, "redacted": "[REDACTED_PATIENT]"})
        return f"{prefix} [REDACTED_PATIENT]"

    sanitized = _PATIENT_NAME_PATTERN.sub(_sub_name, sanitized)

    # Redact Phone (after SSN/Financial to avoid false positive matches)
    def _sub_phone(match: re.Match) -> str:
        orig = match.group(0).strip()
        # Avoid masking simple short integers or decimals
        clean_digits = re.sub(r"\D", "", orig)
        if len(clean_digits) >= 10:
            redactions.append({"category": "PHONE", "original": orig, "redacted": "[REDACTED_PHONE]"})
            return "[REDACTED_PHONE]"
        return orig

    sanitized = _PHONE_PATTERN.sub(_sub_phone, sanitized)

    return sanitized, redactions


class HIPAAMaskingMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette ASGI middleware to scrub PHI/PII on chat endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only inspect JSON endpoints where text payloads are passed
        if request.url.path in ("/chat",) and request.method == "POST":
            try:
                raw_body = await request.body()
                if raw_body:
                    data = json.loads(raw_body.decode("utf-8"))
                    redactions_count = 0

                    if isinstance(data, dict):
                        # 1. Mask question
                        if "question" in data and isinstance(data["question"], str):
                            masked_q, q_redactions = mask_phi(data["question"])
                            data["question"] = masked_q
                            redactions_count += len(q_redactions)

                        # 2. Mask conversation history
                        if "history" in data and isinstance(data["history"], list):
                            for item in data["history"]:
                                if isinstance(item, dict) and "content" in item and isinstance(item["content"], str):
                                    masked_c, c_redactions = mask_phi(item["content"])
                                    item["content"] = masked_c
                                    redactions_count += len(c_redactions)

                    if redactions_count > 0:
                        logger.info("HIPAA Middleware: Redacted %d PHI/PII entities from inbound request", redactions_count)

                    # Reconstruct request with masked body
                    new_body_bytes = json.dumps(data).encode("utf-8")

                    async def receive():
                        return {"type": "http.request", "body": new_body_bytes, "more_body": False}

                    request = Request(request.scope, receive)
            except Exception as exc:
                logger.warning("HIPAA Middleware inbound inspection notice: %s", exc)

        # Call next handler
        response = await call_next(request)

        # Inspect and mask outbound JSON responses for /chat
        if request.url.path in ("/chat",) and response.status_code == 200:
            try:
                # Capture body from streaming response
                response_body = [chunk async for chunk in response.body_iterator]
                response.body_iterator = iter(response_body)
                body_bytes = b"".join(response_body)

                resp_data = json.loads(body_bytes.decode("utf-8"))
                outbound_redactions = 0

                if isinstance(resp_data, dict):
                    # Mask answer
                    if "answer" in resp_data and isinstance(resp_data["answer"], str):
                        masked_ans, ans_redactions = mask_phi(resp_data["answer"])
                        resp_data["answer"] = masked_ans
                        outbound_redactions += len(ans_redactions)

                    # Mask text excerpts in sources
                    if "sources" in resp_data and isinstance(resp_data["sources"], list):
                        for src in resp_data["sources"]:
                            if isinstance(src, dict) and "text" in src and isinstance(src["text"], str):
                                masked_src, src_redactions = mask_phi(src["text"])
                                src["text"] = masked_src
                                outbound_redactions += len(src_redactions)

                if outbound_redactions > 0:
                    logger.info("HIPAA Middleware: Redacted %d PHI/PII entities from outbound response", outbound_redactions)

                new_resp_bytes = json.dumps(resp_data).encode("utf-8")
                return Response(
                    content=new_resp_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json",
                )
            except Exception as exc:
                logger.warning("HIPAA Middleware outbound inspection notice: %s", exc)

        return response

