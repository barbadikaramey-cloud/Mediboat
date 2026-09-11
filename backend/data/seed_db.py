"""Seed script — ensures mediassist.db has realistic 2024 demo data.

Run on container startup:
    python data/seed_db.py

Tables:
- claims: insurance claim records (for billing_executive / admin SQL RAG)
- maintenance_tickets: equipment maintenance records (for technician / admin SQL RAG)
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mediassist.db"
SQL_FILE = Path(__file__).parent / "seed_data.sql"


def is_db_seeded(conn: sqlite3.Connection) -> bool:
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM claims")
        c_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM maintenance_tickets")
        m_count = cur.fetchone()[0]
        return c_count > 0 and m_count > 0
    except sqlite3.OperationalError:
        return False


def seed_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        if is_db_seeded(conn):
            print(f"Database at {DB_PATH} is already seeded and healthy. Skipping.")
            return

        print(f"Seeding database at {DB_PATH} from {SQL_FILE}...")
        if SQL_FILE.exists():
            with open(SQL_FILE, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
            print("Successfully seeded mediassist.db with claims and maintenance tickets.")
        else:
            raise FileNotFoundError(f"Seed SQL file not found at {SQL_FILE}")


if __name__ == "__main__":
    seed_database()


