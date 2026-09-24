import re
from pathlib import Path

from pglast import parse_sql


ROOT = Path(__file__).resolve().parents[1]


def test_postgresql_schema_and_quality_scripts_parse():
    for filename in ("schema.sql", "data_quality.sql", "analysis_queries.sql"):
        sql = (ROOT / "sql" / filename).read_text(encoding="utf-8")
        assert parse_sql(sql)


def test_analysis_queries_use_positive_purchases_for_customer_and_invoice_counts():
    sql = (ROOT / "sql" / "analysis_queries.sql").read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", sql)

    assert (
        "COUNT(DISTINCT customer_id) FILTER ( WHERE customer_id IS NOT NULL "
        "AND quantity > 0 AND revenue_eligible ) AS identified_purchasing_customers"
    ) in normalized
    assert "COUNT(DISTINCT f.invoice_no) FILTER (WHERE f.quantity > 0) AS invoice_count" in normalized
    assert (
        "COUNT(DISTINCT customer_id) FILTER (WHERE customer_id IS NOT NULL AND quantity > 0) "
        "AS identified_purchasing_customers"
    ) in normalized
    assert "WHERE customer_id IS NOT NULL AND revenue_eligible AND quantity > 0 GROUP BY customer_id" in normalized
    assert "CASE WHEN order_count >= 2 THEN 'Repeat' ELSE 'One-time' END" in normalized
    assert "month-over-month comparison to the immediately preceding observed month" in normalized
