import pandas as pd

from src.data_cleaning import clean_transactions


def sample_rows():
    return pd.DataFrame(
        [
            [" 10001 ", "00123", "  RED   MUG ", 2, "2011-01-01", 3.5, 101, " united kingdom "],
            [" 10001 ", "00123", "  RED   MUG ", 2, "2011-01-01", 3.5, 101, " united kingdom "],
            ["C10002", "00123", None, -2, "2011-01-02", 3.5, None, "United Kingdom"],
            ["10003", "00456", "Blue cup", -1, "2011-01-03", 4.0, 202, "France"],
            ["10004", "00456", "Blue cup", 1, "2011-01-04", 0.0, None, "France"],
        ],
        columns=["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"],
    )


def test_cleaning_deduplicates_and_preserves_customer_unknowns_and_returns():
    clean, quality = clean_transactions(sample_rows())

    assert len(clean) == 4
    assert quality["clean_exact_duplicate_rows_removed"] == 1
    assert clean.loc[clean["invoice_no"] == "10001", "stock_code"].iloc[0] == "00123"
    assert clean["customer_id"].isna().sum() == 2
    assert clean.loc[clean["invoice_no"] == "C10002", "is_cancelled"].iloc[0]
    assert clean.loc[clean["invoice_no"] == "10003", "is_return"].iloc[0]
    assert clean.loc[clean["invoice_no"] == "10004", "line_revenue_gbp"].iloc[0] == 0


def test_missing_product_description_uses_same_product_description():
    raw = sample_rows().drop(index=1)
    raw.loc[2, "StockCode"] = "00123"
    clean, _ = clean_transactions(raw)
    cancellation = clean.loc[clean["invoice_no"] == "C10002", "description"].iloc[0]
    assert cancellation == "RED MUG"
