from pathlib import Path

from app.sql_rag.chain import _extract_sql, _run_sql


def test_extract_sql_removes_fences_and_explanation():
    sql = _extract_sql("Here is the query:\n```sql\nSELECT COUNT(*) AS total FROM claims;\n```")
    assert sql == "SELECT COUNT(*) AS total FROM claims;"


def test_sqlalchemy_query_reads_seed_database():
    database = Path(__file__).parents[1] / "data" / "mediassist.db"
    rows = _run_sql(str(database), "SELECT COUNT(*) AS total FROM claims")
    assert rows[0]["total"] > 0
