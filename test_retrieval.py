"""Standalone test script to verify Step 2–4 work correctly.

Run after ingestion:
    uv run python backend/test_retrieval.py

Tests:
  1. Hybrid search returns chunks with correct collection for each role
  2. Reranker narrows top-10 to top-3 and logs reordering
  3. RBAC filter: nurse query must NOT return billing chunks even with billing keywords
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Resolve paths before changing the working directory so this script works when
# launched from the repository root, as documented in its usage instructions.
REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from app.config import get_settings
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.rerank import rerank

def test_role(role: str, question: str, forbidden_collections: list[str]):
    print(f"\n{'='*60}")
    print(f"Role: {role} | Q: {question[:50]}")

    chunks = hybrid_search(query=question, role=role, top_k=10)
    print(f"  Retrieved: {len(chunks)} chunks")

    for c in chunks:
        print(f"    [{c.collection:12}] {c.source_document} | score={c.score:.4f}")
        if c.collection in forbidden_collections:
            print(f"  ❌ RBAC VIOLATION: {c.collection} returned for role={role}")
            return False

    top = rerank(query=question, chunks=chunks)
    print(f"  Reranked top-{len(top)}:")
    for c in top:
        print(f"    [{c.collection:12}] {c.section_title[:40]} | CE={c.score:.4f}")

    print(f"  ✅ PASS — no forbidden collections returned")
    return True


if __name__ == "__main__":
    all_pass = True

    # Doctor: can access clinical, nursing, general
    all_pass &= test_role(
        role="doctor",
        question="What is the treatment for septic shock?",
        forbidden_collections=["billing", "equipment"],
    )

    # Nurse: can only access nursing, general — NOT clinical or billing
    all_pass &= test_role(
        role="nurse",
        question="What are the billing codes for ICU admission?",  # adversarial: billing keyword
        forbidden_collections=["billing", "clinical", "equipment"],
    )

    # Billing: can only access billing, general
    all_pass &= test_role(
        role="billing_executive",
        question="What is the drug dosage for vancomycin?",  # adversarial: clinical keyword
        forbidden_collections=["clinical", "nursing", "equipment"],
    )

    # Technician: can only access equipment, general
    all_pass &= test_role(
        role="technician",
        question="What is the protocol for treating a STEMI patient?",  # adversarial
        forbidden_collections=["clinical", "nursing", "billing"],
    )

    print(f"\n{'='*60}")
    print("ALL TESTS PASSED ✅" if all_pass else "SOME TESTS FAILED ❌")
    sys.exit(0 if all_pass else 1)
