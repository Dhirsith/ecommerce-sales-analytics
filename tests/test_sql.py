from pathlib import Path

from pglast import parse_sql


ROOT = Path(__file__).resolve().parents[1]


def test_postgresql_schema_and_quality_scripts_parse():
    for filename in ("schema.sql", "data_quality.sql", "analysis_queries.sql"):
        sql = (ROOT / "sql" / filename).read_text(encoding="utf-8")
        assert parse_sql(sql)
