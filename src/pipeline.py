"""Run the reproducible cleaning, feature, analysis, and export pipeline."""

import argparse
import json
from pathlib import Path

from src.analysis import build_analysis
from src.data_cleaning import clean_transactions, load_workbook
from src.download_data import WORKBOOK_PATH, download_source
from src.feature_engineering import build_dimensions_and_fact


ROOT = Path(__file__).resolve().parents[1]


def run(source: Path = WORKBOOK_PATH) -> dict:
    source = source if source.is_absolute() else ROOT / source
    if not source.exists():
        source = download_source()
    raw = load_workbook(source)
    clean, quality = clean_transactions(raw)

    processed = ROOT / "data/processed"
    reports = ROOT / "reports"
    processed.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    clean.to_csv(processed / "clean_transactions.csv", index=False)

    tables = build_dimensions_and_fact(clean)
    for name, table in tables.items():
        table.to_csv(processed / (name + ".csv"), index=False)

    summary = build_analysis(clean, processed, reports / "figures", reports / "analysis_summary.json")
    quality["eligible_revenue_lines"] = int(clean["revenue_eligible"].sum())
    quality["cancelled_invoices"] = int(clean.loc[clean["is_cancelled"], "invoice_no"].nunique())
    quality["non_cancellation_return_lines"] = int(clean["is_return"].sum())
    quality["rows_with_nonpositive_price"] = int((clean["unit_price_gbp"] <= 0).sum())
    quality["summary_metrics"] = summary
    (reports / "data_quality.json").write_text(json.dumps(quality, indent=2) + "\n", encoding="utf-8")
    return {"quality": quality, "summary": summary}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=WORKBOOK_PATH, help="Path to the UCI workbook")
    args = parser.parse_args()
    result = run(args.source)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
