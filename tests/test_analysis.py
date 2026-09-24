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


def test_metrics_exclude_cancelled_and_return_only_customers_from_purchase_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mpl"))
    lines = pd.DataFrame(
        {
            "invoice_no": ["A", "A", "B", "C", "D", "E"],
            "stock_code": ["MUG", "MUG", "MUG", "CUP", "CUP", "RETURN"],
            "description": ["Mug", "Mug", "Mug", "Cup", "Cup", "Return item"],
            "quantity": [2, -1, 2, 3, 5, -2],
            "invoice_at": pd.to_datetime(
                ["2011-01-01", "2011-01-01", "2011-02-01", "2011-03-01", "2011-04-01", "2011-05-01"]
            ),
            "unit_price_gbp": [10.0, 10.0, 5.0, 5.0, 4.0, 3.0],
            "customer_id": pd.array([101, 101, 101, 202, 303, 404], dtype="Int64"),
            "country": ["UK", "UK", "UK", "France", "France", "Spain"],
            "is_cancelled": [False, False, False, False, True, False],
            "is_return": [False, True, False, False, False, True],
            "revenue_eligible": [True, True, True, True, False, True],
            "line_revenue_gbp": [20.0, -10.0, 10.0, 15.0, 0.0, -6.0],
        }
    )

    summary = build_analysis(lines, tmp_path / "processed", tmp_path / "figures")
    products = pd.read_csv(tmp_path / "processed/product_performance.csv").set_index("product_code")
    countries = pd.read_csv(tmp_path / "processed/country_performance.csv").set_index("country")

    # Net revenue retains eligible returns; cancelled invoices contribute nothing.
    assert summary["revenue_gbp"] == 29.0
    assert summary["orders_with_positive_quantity"] == 3
    assert summary["average_order_value_gbp"] == 9.67
    # Customer 404 has a return only; customer 303 has only a cancelled purchase.
    assert summary["identified_purchasing_customers"] == 2
    assert summary["repeat_customers_2_or_more_positive_invoices"] == 1
    assert summary["repeat_customer_share"] == 0.5
    assert products.loc["MUG", "revenue_gbp"] == 20.0
    assert products.loc["MUG", "invoice_count"] == 2
    assert products.loc["RETURN", "invoice_count"] == 0
    assert countries.loc["UK", "revenue_gbp"] == 20.0
    assert countries.loc["UK", "customer_count"] == 1
    assert countries.loc["Spain", "customer_count"] == 0
