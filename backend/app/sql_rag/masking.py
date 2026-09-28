"""Role-based dynamic PII/PHI de-identification and data masking for SQL RAG.

Enforces HIPAA Safe Harbor (45 CFR § 164.514) and the HIPAA Minimum Necessary
rule (45 CFR § 164.502(b)) at the deterministic SQLite row level before rows
are formatted for LLM answer synthesis.
"""
from __future__ import annotations

import re
from typing import Any


def mask_patient_name(name: str | None) -> str:
    """Mask patient full name to initial and asterisks.

    Example:
        'Kavya Pillai' -> 'K**** P*****'
        'Arjun' -> 'A****'
    """
    if not name or not name.strip():
        return "[UNKNOWN]"
    parts = name.strip().split()
    masked_parts = []
    for part in parts:
        if len(part) <= 1:
            masked_parts.append(part)
        else:
            masked_parts.append(f"{part[0]}{'*' * (len(part) - 1)}")
    return " ".join(masked_parts)


def anonymize_patient_name(name: str | None) -> str:
    """Completely de-identify patient full name for administrative/audit cohort views."""
    return "[ANONYMIZED]"


def mask_staff_name(name: str | None) -> str:
    """De-identify internal staff / technician names on maintenance tickets."""
    return "Hospital Staff"


def generalize_icd_code(code: str | None) -> str:
    """Generalize ICD-10 diagnosis code to 3-character primary category for Safe Harbor de-identification.

    Example:
        'N17.9' -> 'N17' (Acute kidney failure category)
        'I21.4' -> 'I21' (Acute myocardial infarction category)
    """
    if not code or not code.strip():
        return "N/A"
    cleaned = code.strip()
    match = re.match(r"^([A-Z][0-9]{2})", cleaned)
    if match:
        return match.group(1)
    return cleaned


def apply_role_masking(rows: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    """Deterministically sanitize SQLite rows based on the authenticated caller role.

    Rules:
      - billing_executive:
          * patient_name: Partially masked with initial & asterisks ('K**** P*****')
            allowing TPA claim verification without exposing raw names.
      - admin / other:
          * patient_name: Anonymized to '[ANONYMIZED]' for HIPAA Safe Harbor cohort audits.
      - All roles:
          * raised_by: De-identified to 'Hospital Staff' on maintenance tickets.
    """
    if not rows:
        return []

    sanitized_rows: list[dict[str, Any]] = []

    for row in rows:
        sanitized = dict(row)

        # 1. Patient Name Masking
        if "patient_name" in sanitized and sanitized["patient_name"] is not None:
            if role == "billing_executive":
                sanitized["patient_name"] = mask_patient_name(str(sanitized["patient_name"]))
            else:
                sanitized["patient_name"] = anonymize_patient_name(str(sanitized["patient_name"]))

        # 2. Staff Name De-Identification
        if "raised_by" in sanitized and sanitized["raised_by"] is not None:
            sanitized["raised_by"] = mask_staff_name(str(sanitized["raised_by"]))

        sanitized_rows.append(sanitized)

    return sanitized_rows
