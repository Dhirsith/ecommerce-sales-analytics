import pandas as pd

from src.feature_engineering import build_customer_rfm, build_dimensions_and_fact
from src.load_postgres import TABLES


def example_lines():
    return pd.DataFrame(
        {
            "invoice_no": ["10001", "10001", "10002", "C10003"],
            "stock_code": ["00123", "00123", "00456", "00456"],
            "description": ["Red mug", "Red mug", "Blue cup", "Blue cup"],
            "quantity": [2, 1, 1, -1],
            "invoice_at": pd.to_datetime(["2011-01-01", "2011-01-01", "2011-02-01", "2011-02-02"]),
            "unit_price_gbp": [3.5, 3.5, 4.0, 4.0],
            "customer_id": pd.array([101, 101, 202, None], dtype="Int64"),
            "country": ["United Kingdom", "United Kingdom", "France", "United Kingdom"],
            "is_cancelled": [False, False, False, True],
            "is_return": [False, False, False, False],
            "revenue_eligible": [True, True, True, False],
            "line_revenue_gbp": [7.0, 3.5, 4.0, 0.0],
        }
    )


def test_star_schema_exports_have_stable_keys_and_foreign_key_values():
    tables = build_dimensions_and_fact(example_lines())
    fact = tables["fact_sales_line"]

    assert fact["sale_line_id"].is_unique
    assert set(fact["product_code"]).issubset(set(tables["dim_product"]["product_code"]))
    assert set(fact["date_key"]).issubset(set(tables["dim_date"]["date_key"]))
    assert fact.loc[fact["invoice_no"] == "C10003", "line_revenue_gbp"].iloc[0] == 0
    assert TABLES["dim_date"].split(",") == list(tables["dim_date"].columns)
    assert TABLES["dim_product"].split(",") == list(tables["dim_product"].columns)
    assert TABLES["dim_customer"].split(",") == list(tables["dim_customer"].columns)
    assert TABLES["fact_sales_line"].split(",") == list(fact.columns)


def test_rfm_uses_distinct_positive_purchase_invoices_and_known_customers():
    rfm = build_customer_rfm(example_lines())

    customer = rfm.loc[rfm["customer_id"] == 101].iloc[0]
    assert customer["frequency"] == 1
    assert customer["monetary_gbp"] == 10.5
    assert set(rfm["segment"]).issubset(
        {"Champions", "Loyal", "Recent customers", "At risk", "Occasional / inactive"}
    )
