"""Build date, product, customer, and sales-line tables for analytics."""

from typing import Dict

import numpy as np
import pandas as pd


def build_date_dimension(lines: pd.DataFrame) -> pd.DataFrame:
    dates = pd.Series(pd.to_datetime(lines["invoice_at"].dt.date).drop_duplicates()).sort_values()
    result = pd.DataFrame({"full_date": dates.reset_index(drop=True)})
    result["date_key"] = result["full_date"].dt.strftime("%Y%m%d").astype("int64")
    result["year"] = result["full_date"].dt.year
    result["quarter"] = result["full_date"].dt.quarter
    result["month"] = result["full_date"].dt.month
    result["month_name"] = result["full_date"].dt.strftime("%B")
    result["day_of_week"] = result["full_date"].dt.dayofweek + 1
    result["day_name"] = result["full_date"].dt.strftime("%A")
    result["is_weekend"] = result["full_date"].dt.dayofweek >= 5
    return result


def build_dimensions_and_fact(lines: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    products = (
        lines.groupby("stock_code", as_index=False)["description"]
        .agg(lambda values: values.mode().iloc[0] if not values.mode().empty else values.iloc[0])
        .rename(columns={"stock_code": "product_code", "description": "product_description"})
    )
    customers = (
        lines.dropna(subset=["customer_id"])[["customer_id"]]
        .drop_duplicates()
        .sort_values("customer_id")
        .reset_index(drop=True)
    )
    fact = lines.copy()
    fact.insert(0, "sale_line_id", range(1, len(fact) + 1))
    fact["date_key"] = fact["invoice_at"].dt.strftime("%Y%m%d").astype("int64")
    fact = fact.rename(columns={"stock_code": "product_code"})[
        ["sale_line_id", "invoice_no", "product_code", "customer_id", "date_key", "invoice_at",
         "country", "quantity", "unit_price_gbp", "line_revenue_gbp", "is_cancelled", "is_return",
         "revenue_eligible"]
    ]
    return {"dim_product": products, "dim_customer": customers, "dim_date": build_date_dimension(lines),
            "fact_sales_line": fact}


def build_customer_rfm(lines: pd.DataFrame) -> pd.DataFrame:
    """Create descriptive RFM segments from positive, non-cancelled purchases.

    Monetary value is positive item-level sales only; returns and cancellations
    are excluded. The snapshot date is one day after the last observed date.
    Quantile scores preserve ties using average percentile ranks.
    """
    purchases = lines.loc[
        lines["customer_id"].notna()
        & ~lines["is_cancelled"]
        & (lines["quantity"] > 0)
        & (lines["unit_price_gbp"] > 0)
    ].copy()
    purchases["purchase_revenue_gbp"] = purchases["quantity"] * purchases["unit_price_gbp"]
    grouped = purchases.groupby("customer_id").agg(
        last_purchase_at=("invoice_at", "max"),
        frequency=("invoice_no", "nunique"),
        monetary_gbp=("purchase_revenue_gbp", "sum"),
    ).reset_index()
    snapshot = lines["invoice_at"].max().normalize() + pd.Timedelta(days=1)
    grouped["recency_days"] = (snapshot - grouped["last_purchase_at"].dt.normalize()).dt.days

    def quartile_score(values: pd.Series, higher_is_better: bool) -> pd.Series:
        percentiles = values.rank(method="average", pct=True)
        score = pd.cut(percentiles, bins=[0, .25, .5, .75, 1], labels=[1, 2, 3, 4], include_lowest=True)
        numeric = score.astype("int64")
        return numeric if higher_is_better else 5 - numeric

    grouped["r_score"] = quartile_score(grouped["recency_days"], higher_is_better=False)
    grouped["f_score"] = quartile_score(grouped["frequency"], higher_is_better=True)
    grouped["m_score"] = quartile_score(grouped["monetary_gbp"], higher_is_better=True)
    grouped["rfm_score"] = grouped[["r_score", "f_score", "m_score"]].astype(str).agg("".join, axis=1)

    conditions = [
        (grouped["r_score"] >= 3) & (grouped["f_score"] >= 3) & (grouped["m_score"] >= 3),
        (grouped["r_score"] >= 3) & (grouped["f_score"] >= 3),
        grouped["r_score"] >= 3,
        (grouped["r_score"] <= 2) & (grouped["f_score"] >= 3),
    ]
    grouped["segment"] = np.select(
        conditions,
        ["Champions", "Loyal", "Recent customers", "At risk"],
        default="Occasional / inactive",
    )
    grouped["snapshot_date"] = snapshot.date().isoformat()
    return grouped.sort_values(["segment", "monetary_gbp"], ascending=[True, False]).reset_index(drop=True)
