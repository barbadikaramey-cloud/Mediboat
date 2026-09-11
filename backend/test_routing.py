"""Test routing decisions across diverse questions and roles."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.graph import node_router, ChatState

TEST_CASES = [
    # Analytical queries -> MUST route to sql_rag
    ("what is total claims in last month", "admin", "sql_rag"),
    ("How many claims have an escalated status?", "billing_executive", "sql_rag"),
    ("What is the top maintenance category by ticket count?", "admin", "sql_rag"),
    ("What is the average claimed amount by department?", "billing_executive", "sql_rag"),
    ("How many open maintenance tickets are there for each equipment type?", "admin", "sql_rag"),
    ("Count of pending claims by insurer", "billing_executive", "sql_rag"),

    # Document queries -> MUST route to document_rag
    ("What is the recommended antibiotic treatment for pneumonia?", "doctor", "document_rag"),
    ("What is the protocol for STEMI?", "doctor", "document_rag"),
    ("What are the ICU nursing procedures for ventilated patients?", "nurse", "document_rag"),
    ("What is the hospital leave policy?", "doctor", "document_rag"),
    ("What are the sterilisation procedures for surgical instruments?", "technician", "document_rag"),
]


async def run_tests():
    print("=" * 70)
    print("TESTING ROUTER NODE (SQL RAG vs Document RAG)")
    print("=" * 70)

    failed = []
    for question, role, expected_route in TEST_CASES:
        state: ChatState = {
            "question": question,
            "role": role,
            "username": "test_user",
            "blocked": False,
            "block_reason": "",
            "route": "",
            "retrieved_chunks": [],
            "reranked_chunks": [],
            "answer": "",
            "sources": [],
            "retrieval_type": "",
            "cache_key": "",
        }
        res = await node_router(state)
        actual = res.get("route")
        passed = actual == expected_route
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon:4}] Route: {actual:12} (Expected: {expected_route:12}) | \"{question[:50]}\"")
        if not passed:
            failed.append((question, expected_route, actual))

    print("\n" + "=" * 70)
    if failed:
        print(f"FAILED {len(failed)} test(s):")
        for q, exp, act in failed:
            print(f"  - '{q}': expected {exp}, got {act}")
        sys.exit(1)
    else:
        print("ALL ROUTING TESTS PASSED! ✅")


if __name__ == "__main__":
    asyncio.run(run_tests())

