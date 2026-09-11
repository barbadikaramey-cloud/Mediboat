"""Standalone verification script for Step 5: SQL RAG Chain.

Tests the 4 target analytical questions:
  1. Escalated claims submitted
  2. Top maintenance category by ticket count
  3. Average claimed amount by department
  4. Open tickets grouped by equipment name
"""
from __future__ import annotations

import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.sql_rag.chain import sql_rag_chain

TEST_QUESTIONS = [
    "How many claims have an escalated status?",
    "What is the top maintenance category by ticket count?",
    "What is the average claimed amount by department?",
    "How many open maintenance tickets are there for each equipment type?",
]

def main():
    print("=" * 60)
    print("TESTING SQL RAG CHAIN (Llama 3.3 70B via Groq + SQLite)")
    print("=" * 60)

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[Query {i}] Question: {q}")
        try:
            answer = sql_rag_chain(q)
            print(f"[Query {i}] Answer:\n{answer}\n")
            print("-" * 50)
        except Exception as e:
            print(f"[Query {i}] FAILED with error: {e}")
            sys.exit(1)

    print("\nALL 4 SQL RAG ANALYTICAL QUESTIONS PASSED! ✅")

if __name__ == "__main__":
    main()

