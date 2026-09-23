"""Load generated CSV tables into the project's dedicated PostgreSQL schema."""

import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "dim_date": "full_date,date_key,year,quarter,month,month_name,day_of_week,day_name,is_weekend",
    "dim_product": "product_code,product_description",
    "dim_customer": "customer_id",
    "fact_sales_line": (
        "sale_line_id,invoice_no,product_code,customer_id,date_key,invoice_at,country,quantity,"
        "unit_price_gbp,line_revenue_gbp,is_cancelled,is_return,revenue_eligible"
    ),
}


def load_database(database_url: str, data_dir: Path = ROOT / "data/processed") -> None:
    """Rebuild this project's analytics tables; use a dedicated database/schema."""
    schema_sql = (ROOT / "sql/schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(database_url) as connection:
        connection.execute(schema_sql)
        connection.execute(
            "TRUNCATE retail_analytics.fact_sales_line, retail_analytics.dim_customer, "
            "retail_analytics.dim_product, retail_analytics.dim_date RESTART IDENTITY CASCADE"
        )
        for table, columns in TABLES.items():
            path = data_dir / (table + ".csv")
            if not path.is_file():
                raise FileNotFoundError("Run the analytics pipeline first; missing " + str(path))
            statement = (
                "COPY retail_analytics." + table + " (" + columns + ") "
                "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')"
            )
            with path.open("r", encoding="utf-8", newline="") as source:
                with connection.cursor().copy(statement) as copy:
                    while chunk := source.read(1024 * 1024):
                        copy.write(chunk)


if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Set DATABASE_URL for a dedicated PostgreSQL database first.")
    load_database(url)
    print("Loaded analytics tables into retail_analytics.")
