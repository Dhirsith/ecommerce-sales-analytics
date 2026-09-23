"""Load, audit, and standardize the UCI Online Retail transaction workbook."""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


SOURCE_COLUMNS = {
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_at",
    "UnitPrice": "unit_price_gbp",
    "CustomerID": "customer_id",
    "Country": "country",
}
REQUIRED_COLUMNS = ["invoice_no", "stock_code", "quantity", "invoice_at", "unit_price_gbp", "country"]


def _normalize_code(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text or pd.NA


def load_workbook(path: Path) -> pd.DataFrame:
    """Read the source workbook using string identifiers to preserve leading zeros."""
    return pd.read_excel(
        path,
        dtype={"InvoiceNo": "string", "StockCode": "string", "CustomerID": "Int64"},
        engine="openpyxl",
    )


def clean_transactions(raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Normalize source rows and return an audit of observed quality issues.

    Exact duplicates are removed because the source has no line identifier. Rows
    with missing customer IDs remain available for product and country analysis.
    Cancellation and return rows are retained and explicitly flagged.
    """
    missing_columns = sorted(set(SOURCE_COLUMNS) - set(raw.columns))
    if missing_columns:
        raise ValueError("Source workbook is missing columns: " + ", ".join(missing_columns))

    frame = raw.rename(columns=SOURCE_COLUMNS).copy()
    quality: Dict[str, object] = {
        "raw_rows": int(len(frame)),
        "raw_columns": int(raw.shape[1]),
        "raw_exact_duplicate_rows": int(frame.duplicated().sum()),
        "raw_missing_descriptions": int(frame["description"].isna().sum()),
        "raw_missing_customer_ids": int(frame["customer_id"].isna().sum()),
    }

    frame["invoice_no"] = frame["invoice_no"].astype("string").str.strip().str.upper()
    frame["stock_code"] = frame["stock_code"].map(_normalize_code).astype("string")
    frame["description"] = (
        frame["description"].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    )
    frame["country"] = frame["country"].astype("string").str.replace(r"\s+", " ", regex=True).str.strip().str.title()
    frame["country"] = frame["country"].replace({"Eire": "EIRE", "Usa": "USA", "Uae": "UAE"})
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")
    frame["unit_price_gbp"] = pd.to_numeric(frame["unit_price_gbp"], errors="coerce")
    frame["invoice_at"] = pd.to_datetime(frame["invoice_at"], errors="coerce")
    frame["customer_id"] = pd.to_numeric(frame["customer_id"], errors="coerce").astype("Int64")

    invalid_required = frame[REQUIRED_COLUMNS].isna().any(axis=1)
    quality["rows_missing_required_fields_removed"] = int(invalid_required.sum())
    frame = frame.loc[~invalid_required].copy()

    quality["zero_quantity_rows"] = int((frame["quantity"] == 0).sum())
    quality["zero_or_negative_unit_price_rows"] = int((frame["unit_price_gbp"] <= 0).sum())
    quality["negative_quantity_rows"] = int((frame["quantity"] < 0).sum())
    quality["cancellation_rows"] = int(frame["invoice_no"].str.startswith("C", na=False).sum())

    rows_before_deduplication = len(frame)
    frame = frame.drop_duplicates().reset_index(drop=True)
    frame["is_cancelled"] = frame["invoice_no"].str.startswith("C", na=False)
    frame["is_return"] = (frame["quantity"] < 0) & ~frame["is_cancelled"]
    frame["revenue_eligible"] = (
        ~frame["is_cancelled"] & (frame["quantity"] != 0) & (frame["unit_price_gbp"] > 0)
    )
    frame["line_revenue_gbp"] = (
        frame["quantity"] * frame["unit_price_gbp"]
    ).where(frame["revenue_eligible"], 0.0)

    # A product may have a description on one row and a blank on another.
    descriptions = (
        frame.dropna(subset=["description"])
        .groupby("stock_code")["description"]
        .agg(lambda values: values.mode().iloc[0] if not values.mode().empty else values.iloc[0])
    )
    frame["description"] = frame["description"].fillna(frame["stock_code"].map(descriptions))
    frame["description"] = frame["description"].fillna("Unknown description")

    quality["clean_rows"] = int(len(frame))
    quality["clean_exact_duplicate_rows_removed"] = int(rows_before_deduplication - len(frame))
    quality["clean_missing_customer_ids"] = int(frame["customer_id"].isna().sum())
    quality["clean_missing_descriptions"] = int(frame["description"].isna().sum())
    quality["identified_customers"] = int(frame["customer_id"].nunique())
    quality["distinct_products"] = int(frame["stock_code"].nunique())
    quality["distinct_invoices_including_cancellations"] = int(frame["invoice_no"].nunique())
    quality["date_min"] = frame["invoice_at"].min().isoformat()
    quality["date_max"] = frame["invoice_at"].max().isoformat()
    quality["countries"] = int(frame["country"].nunique())
    return frame, quality
