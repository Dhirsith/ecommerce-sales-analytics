import pandas as pd

from src.analysis import build_analysis


def test_analysis_summary_and_power_bi_exports_are_reproducible(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mpl"))
    lines = pd.DataFrame(
        {
            "invoice_no": ["10001", "10001", "10002", "10003"],
            "stock_code": ["00123", "00123", "00456", "00123"],
            "description": ["Red mug", "Red mug", "Blue cup", "Red mug"],
            "quantity": [2, 1, 1, 1],
            "invoice_at": pd.to_datetime(["2011-01-01", "2011-01-01", "2011-02-01", "2011-03-01"]),
            "unit_price_gbp": [3.5, 3.5, 4.0, 3.5],
            "customer_id": pd.array([101, 101, 202, 101], dtype="Int64"),
            "country": ["United Kingdom", "United Kingdom", "France", "United Kingdom"],
            "is_cancelled": [False, False, False, False],
            "is_return": [False, False, False, False],
            "revenue_eligible": [True, True, True, True],
            "line_revenue_gbp": [7.0, 3.5, 4.0, 3.5],
        }
    )

    summary = build_analysis(lines, tmp_path / "processed", tmp_path / "figures")

    assert summary["revenue_gbp"] == 18.0
    assert summary["orders_with_positive_quantity"] == 3
    assert summary["average_order_value_gbp"] == 6.0
    assert summary["repeat_customers_2_or_more_positive_invoices"] == 1
    assert summary["repeat_customer_share"] == 0.5
    assert summary["top_country_by_net_revenue"] == "United Kingdom"
    assert summary["top_stock_code_by_net_revenue"] == "00123"
    assert (tmp_path / "processed/customer_rfm.csv").is_file()
    assert (tmp_path / "figures/monthly_revenue.png").is_file()
