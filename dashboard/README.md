# Power BI dashboard specification

The Python pipeline creates CSV tables in `data/processed/`. Import `dim_date.csv`, `dim_product.csv`, `dim_customer.csv`, and `fact_sales_line.csv` as separate tables; connect date, product, and customer dimensions to the fact table using their keys. The CSVs are ignored by Git and are generated locally after downloading the source workbook.

## Page 1 — Executive overview

- **KPIs:** Net revenue GBP, positive-quantity orders, identified purchasing customers, average order value.
- **Visuals:** Monthly revenue line chart; revenue and order-count cards.
- **Slicers:** Year, quarter, country.
- **Question:** How did recorded net sales and order activity change over the observed period?

## Page 2 — Product and geography

- **Visuals:** Top stock codes by net revenue; stock-code quantity/invoice table; country revenue bar chart.
- **Slicers:** Date, country, product code.
- **Question:** Which product codes and customer countries account for the most recorded net sales?
- The top source code can be a postage/service line. There is no product-category or product-type field; do not describe stock-code rankings as merchandise-only or create category labels without an external, documented mapping.

## Page 3 — Customer behavior

- **KPIs:** Identified customers, repeat-customer share, purchase frequency.
- **Visuals:** RFM segment customer and monetary-value bars; customer revenue distribution.
- **Slicers:** Snapshot date, country, segment.
- **Question:** How does historical purchasing differ across descriptive RFM groups?

## Measure definitions

Use the same definitions as [`docs/methodology.md`](../docs/methodology.md). Net revenue excludes cancellation invoices and nonpositive-price lines while retaining eligible negative-quantity return lines. Average order value is net revenue divided by distinct positive-quantity invoices. The repeat-customer measure uses identified customers only. Do not interpret historical RFM groups as predictions.

A `.pbix` file is not included; no Power BI dashboard has been built or represented as a screenshot.
