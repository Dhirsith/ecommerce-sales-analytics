"""Create business aggregates, Power BI-ready tables, and focused charts."""

import json
from pathlib import Path
from typing import Dict, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.feature_engineering import build_customer_rfm


def build_analysis(
    lines: pd.DataFrame, output_dir: Path, figures_dir: Path, summary_path: Optional[Path] = None
) -> Dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    sales = lines.loc[lines["revenue_eligible"]].copy()
    positive_sales = sales.loc[sales["quantity"] > 0].copy()
    sales["month"] = sales["invoice_at"].dt.to_period("M").dt.to_timestamp()

    orders = positive_sales.groupby("invoice_no").agg(
        order_date=("invoice_at", "min"), customer_id=("customer_id", "first")
    )
    orders["net_revenue_gbp"] = sales.groupby("invoice_no")["line_revenue_gbp"].sum()
    monthly = sales.groupby("month", as_index=False).agg(
        revenue_gbp=("line_revenue_gbp", "sum"), line_count=("invoice_no", "size")
    )
    monthly_orders = orders.assign(month=orders["order_date"].dt.to_period("M").dt.to_timestamp()).groupby("month").size()
    monthly["order_count"] = monthly["month"].map(monthly_orders).fillna(0).astype(int)
    monthly["average_order_value_gbp"] = monthly["month"].map(
        sales.groupby("month")["line_revenue_gbp"].sum() / monthly_orders.replace(0, pd.NA)
    )
    monthly.to_csv(output_dir / "monthly_kpis.csv", index=False)

    product = sales.groupby(["stock_code", "description"], as_index=False).agg(
        revenue_gbp=("line_revenue_gbp", "sum"), quantity_net=("quantity", "sum"),
    ).sort_values("revenue_gbp", ascending=False)
    product_orders = positive_sales.groupby(["stock_code", "description"])["invoice_no"].nunique()
    product["invoice_count"] = [
        product_orders.get((code, description), 0)
        for code, description in zip(product["stock_code"], product["description"])
    ]
    product = product.rename(columns={"stock_code": "product_code"})
    product.to_csv(output_dir / "product_performance.csv", index=False)

    country = sales.groupby("country", as_index=False).agg(
        revenue_gbp=("line_revenue_gbp", "sum"),
    ).sort_values("revenue_gbp", ascending=False)
    country_orders = positive_sales.groupby("country").agg(
        invoice_count=("invoice_no", "nunique"), customer_count=("customer_id", "nunique")
    )
    country["invoice_count"] = country["country"].map(country_orders["invoice_count"]).fillna(0).astype(int)
    country["customer_count"] = country["country"].map(country_orders["customer_count"]).fillna(0).astype(int)
    country.to_csv(output_dir / "country_performance.csv", index=False)

    customer_orders = positive_sales.dropna(subset=["customer_id"]).groupby("customer_id")["invoice_no"].nunique()
    identified_ids = positive_sales.loc[positive_sales["customer_id"].notna(), "customer_id"].unique()
    repeat_ids = customer_orders[customer_orders >= 2].index
    rfm = build_customer_rfm(lines)
    rfm.to_csv(output_dir / "customer_rfm.csv", index=False)
    segment_summary = rfm.groupby("segment", as_index=False).agg(
        customer_count=("customer_id", "nunique"), revenue_gbp=("monetary_gbp", "sum"),
        average_frequency=("frequency", "mean"),
    ).sort_values("revenue_gbp", ascending=False)
    segment_summary.to_csv(output_dir / "customer_segments.csv", index=False)

    net_revenue = float(sales["line_revenue_gbp"].sum())
    order_count = int(positive_sales["invoice_no"].nunique())
    known_customer_count = int(len(identified_ids))
    repeat_customer_count = int(len(repeat_ids.intersection(identified_ids)))
    top_country = country.iloc[0]
    top_product = product.iloc[0]
    peak_month = monthly.loc[monthly["revenue_gbp"].idxmax()]
    low_month = monthly.loc[monthly["revenue_gbp"].idxmin()]
    summary: Dict[str, object] = {
        "dataset_rows_after_cleaning": int(len(lines)),
        "revenue_gbp": round(net_revenue, 2),
        "orders_with_positive_quantity": order_count,
        "identified_purchasing_customers": known_customer_count,
        "average_order_value_gbp": round(net_revenue / order_count, 2) if order_count else None,
        "median_order_net_revenue_gbp": round(float(orders["net_revenue_gbp"].median()), 2) if not orders.empty else None,
        "repeat_customers_2_or_more_positive_invoices": repeat_customer_count,
        "repeat_customer_share": round(repeat_customer_count / known_customer_count, 4) if known_customer_count else None,
        "top_country_by_net_revenue": str(top_country["country"]),
        "top_country_revenue_gbp": round(float(top_country["revenue_gbp"]), 2),
        "top_country_revenue_share": round(float(top_country["revenue_gbp"]) / net_revenue, 4) if net_revenue else None,
        "top_stock_code_by_net_revenue": str(top_product["product_code"]),
        "top_stock_code_description": str(top_product["description"]),
        "top_stock_code_revenue_gbp": round(float(top_product["revenue_gbp"]), 2),
        "highest_revenue_month": str(peak_month["month"].date().isoformat()),
        "highest_month_revenue_gbp": round(float(peak_month["revenue_gbp"]), 2),
        "lowest_revenue_month": str(low_month["month"].date().isoformat()),
        "lowest_month_revenue_gbp": round(float(low_month["revenue_gbp"]), 2),
        "date_start": lines["invoice_at"].min().date().isoformat(),
        "date_end": lines["invoice_at"].max().date().isoformat(),
        "revenue_definition": (
            "Sum of quantity * unit price for non-cancellation lines with positive unit price; "
            "negative quantities on non-cancellation lines reduce revenue as returns."
        ),
        "customer_metric_definition": (
            "Customer counts require CustomerID. Repeat means at least two distinct invoices "
            "with positive quantities and positive unit prices."
        ),
        "rfm_snapshot_date": rfm["snapshot_date"].iloc[0] if not rfm.empty else None,
        "rfm_segment_count": int(rfm["segment"].nunique()),
    }
    destination = summary_path or (output_dir / "analysis_summary.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.lineplot(data=monthly, x="month", y="revenue_gbp", marker="o", ax=ax)
    ax.set(title="Monthly net sales revenue", xlabel="Invoice month", ylabel="Revenue (£ GBP)")
    fig.tight_layout()
    fig.savefig(figures_dir / "monthly_revenue.png", dpi=150)
    plt.close(fig)

    top_products = product.head(10).sort_values("revenue_gbp")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_products, x="revenue_gbp", y="product_code", ax=ax, color="#3977a8")
    ax.set(title="Top 10 product codes by net sales revenue", xlabel="Revenue (£ GBP)", ylabel="Product code")
    fig.tight_layout()
    fig.savefig(figures_dir / "top_products.png", dpi=150)
    plt.close(fig)

    top_countries = country.head(10).sort_values("revenue_gbp")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_countries, x="revenue_gbp", y="country", ax=ax, color="#4c956c")
    ax.set(title="Top 10 countries by net sales revenue", xlabel="Revenue (£ GBP)", ylabel="Customer country")
    fig.tight_layout()
    fig.savefig(figures_dir / "country_revenue.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=segment_summary, x="segment", y="customer_count", ax=ax, color="#c78736")
    ax.set(title="Identified customers by descriptive RFM segment", xlabel="RFM segment", ylabel="Customers")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(figures_dir / "customer_segments.png", dpi=150)
    plt.close(fig)
    return summary
