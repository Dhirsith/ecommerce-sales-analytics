# E-Commerce Sales & Customer Analytics

An end-to-end analytics portfolio project built from UCI's public Online Retail transaction data. It turns invoice-line records into audited sales/customer tables, answers business questions with Python and PostgreSQL SQL, and prepares Power BI import tables. The project is deliberately limited to what the source fields can support.

## Business questions

- How did recorded net sales and positive-quantity order counts change by month?
- Which product codes contribute the most net sales and item volume?
- Which customer countries account for the most recorded sales?
- What are average order value and the identified repeat-customer share under the documented definitions?
- How do customers group under a retrospective RFM-style description?
- What cancellations, returns, missing customer IDs, duplicate lines, and invalid prices need to be considered before interpreting results?

The source has no product category, cost, marketing, or delivery fields. The project therefore makes no category, profit, campaign, or fulfillment claims.

## Dataset

- **Name:** Online Retail
- **Source:** [UCI Machine Learning Repository, dataset 352](https://archive.ics.uci.edu/dataset/352/online+retail), DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33)
- **Attribution:** Chen, D. (2012). *Online Retail* [Dataset]. UCI Machine Learning Repository.
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0); attribute UCI and the dataset author when redistributing or adapting the data. The raw workbook is downloaded locally and is not committed here.
- **Source scale:** 541,909 rows and eight fields, covering a UK-based online retailer's transactions from 2010-12-01 through 2011-12-09. The source workbook is about 22.6 MB.
- **Why selected:** It supplies transaction dates, products, quantities, GBP unit prices, customer IDs, and country, enabling sales, product, customer, time, and geographic analysis without fabricating fields.

| Source field | Type used | Meaning |
|---|---|---|
| `InvoiceNo` | text | Invoice identifier; values prefixed with `C` indicate cancellation records. |
| `StockCode` | text | Product/item identifier; leading zeros are preserved. |
| `Description` | text | Product description; some rows are blank. |
| `Quantity` | integer | Units on the invoice line; negative values can represent returns. |
| `InvoiceDate` | timestamp | Date and time of the transaction. |
| `UnitPrice` | decimal | Price per unit in GBP. |
| `CustomerID` | nullable integer | Customer identifier; absent on some rows. |
| `Country` | text | Customer country as provided by the source. |

## Method and metric definitions

The pipeline removes exact duplicate source rows, cleans whitespace and identifiers, parses timestamps and numeric fields, and drops rows missing required invoice/product/quantity/date/price/country values. Missing customer IDs remain available for product and country totals. A missing description is filled from the most common description for that stock code, or marked `Unknown description` when no value exists.

Cancellation rows, returns, and nonpositive prices stay in the fact table with explicit flags. Net sales revenue is the sum of `quantity × unit price` on non-cancellation rows with nonzero quantity and positive unit price; negative quantities on those eligible lines reduce revenue. This is sales revenue, not profit. Average order value divides that net revenue by distinct invoices with positive quantity and positive unit price. Customer metrics use identified customers only; a repeat customer has at least two distinct positive-quantity invoices.

RFM is retrospective: recency is measured against one day after the last observed transaction, frequency is distinct positive-purchase invoices, and monetary value is positive-quantity sales. Tied values receive the same percentile-based quartile score. Segment names are descriptive groups, not a production scoring system or prediction.

## Architecture

```text
UCI workbook (downloaded locally)
  → Python cleaning and audit
  → date/product/customer dimensions + invoice-line fact table (CSV)
  → PostgreSQL schema and analytical SQL
  → Python aggregates, charts, customer RFM, and Power BI-ready CSVs
```

The raw workbook and generated processed tables are excluded from Git. Source code, SQL, notebooks, tests, methodology, and reproducible summary outputs are tracked.

## Technologies

- Python 3.9+
- pandas and NumPy for cleaning, feature engineering, aggregation, and customer analysis
- Matplotlib and Seaborn for four question-driven visualizations
- PostgreSQL for the relational star schema and analytical queries
- JupyterLab for exploration and business-analysis notebooks
- pytest for data logic tests; `pglast` parses PostgreSQL scripts during testing

## Project structure

```text
data/                   ignored raw workbook and generated CSV tables
dashboard/README.md     Power BI page, KPI, visual, and filter specification
docs/methodology.md     cleaning policy, metric definitions, limitations
notebooks/              exploration and business-analysis notebooks
reports/                generated quality/analysis summaries and local figures
sql/                    PostgreSQL schema, quality checks, analytical queries
src/                    download, cleaning, feature, analysis, pipeline, DB loader
tests/                  cleaning, schema, RFM, and PostgreSQL parse tests
```

## Run locally

Python 3.9 or newer is required. PostgreSQL is optional for the Python pipeline and required only to load/query the relational tables.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.download_data
python -m src.pipeline
pytest
```

The pipeline writes `data/processed/` exports and `reports/data_quality.json`, `reports/analysis_summary.json`, and four PNG charts under `reports/figures/`. Generated data files are ignored by Git. Explore the outputs with `jupyter lab` and open the notebooks.

To load the CSVs into a **dedicated** PostgreSQL database, set `DATABASE_URL` and run `python -m src.load_postgres`. The loader rebuilds tables in the `retail_analytics` schema, so use a database reserved for this project. Then run the scripts in `sql/` with `psql` or a PostgreSQL client.

## PostgreSQL model and SQL

The star schema contains `fact_sales_line` at source invoice-line grain, with `dim_product`, `dim_customer`, and `dim_date`. Country remains on the fact rows because it is a transaction attribute in the source. Foreign keys connect the fact to dimensions; indexes cover invoice, customer/date, product/date, and country/date access patterns.

The SQL examples use joins, filtered aggregates, `CASE`, CTEs, `LAG`, `DENSE_RANK`, `NTILE`, and window aggregates to analyze monthly change, product contribution, customer repeat behavior, geography, and high-revenue customers. `data_quality.sql` checks revenue flags/calculations and dimension relationships.

## Python analysis and customer analytics

The analysis creates monthly KPIs, product and country performance, customer segments, and four charts: monthly net revenue, top product codes, top countries, and customer counts by RFM segment. `customer_rfm.csv` includes recency, frequency, monetary value, score, segment, and snapshot date. A geography field exists, so country analysis is included; product category analysis is not.

## Power BI dashboard design

See [`dashboard/README.md`](dashboard/README.md) for three proposed pages: Executive Overview, Product & Geography, and Customer Behavior. It specifies KPIs, charts, slicers, relationships, and definitions using the prepared CSV tables. **No `.pbix` file or Power BI screenshots are included.**

## Data quality and actual findings

The full pipeline was run against the downloaded UCI workbook. It read **541,909 rows** and retained **536,641** after removing **5,268 exact duplicate rows**; no rows were dropped for missing required invoice/product/quantity/date/price/country fields. In the raw workbook, **135,080 rows lack CustomerID** and **1,454 lack Description**. Descriptions were filled from the same stock code when possible; customer IDs remain missing. The source has **9,288 cancellation rows** across **3,836 cancellation invoice IDs**, **10,624 negative-quantity rows**, and **2,517 zero/negative-price rows** before exact duplicate removal. After deduplication, **1,336 non-cancellation negative-quantity rows** remain and **2,512 lines have nonpositive prices**.

### Findings from the implemented metric definitions

- Eligible net sales revenue is **£10,642,110.80** over **19,960** positive-quantity invoices. Mean net AOV is **£533.17** and median invoice net revenue is **£303.30**; the difference shows that the mean is sensitive to high-value orders in this wholesale-including dataset.
- Among **4,338 identified purchasing customers**, **2,845** meet the repeat definition (at least two distinct positive-quantity invoices), a repeat share of **65.58%**. Customers without IDs are not included in that denominator.
- The United Kingdom has **£9,001,744.09**, or **84.59%**, of eligible net sales revenue.
- The highest-revenue stock code is **DOT / DOTCOM POSTAGE** at **£206,248.77**. This is a postage charge, not merchandise; stock-code rankings include service/adjustment codes because the source does not provide a reviewed product-type mapping. The next code by revenue is **22423 / REGENCY CAKESTAND 3 TIER** at **£174,156.54**.
- **November 2011** is the highest-revenue month (**£1,503,866.78**) and **February 2011** the lowest (**£522,545.56**) in the observed data. The range is descriptive only; the dataset spans about one year and starts/ends with partial December periods, so these values do not establish seasonality.

These outputs are generated in `reports/analysis_summary.json`, `reports/data_quality.json`, and the ignored CSVs in `data/processed/`. Regenerate them with `python -m src.pipeline`. Interpretation must account for cancellations/returns, missing customer IDs, a single historical retailer, wholesaler customers, and absent cost/category fields.

## Limitations and future work

- This is one historical, UK-based retailer, not a representative current e-commerce market sample.
- Customer IDs are missing on some lines, which limits customer attribution.
- Invoice lines include cancellations, negative quantities, zero-price records, and adjustment rows; the project flags and documents how these affect the metrics.
- The data spans about one year. Monthly variation is descriptive; it is not evidence of a recurring seasonal pattern or cause.
- Product categories and product costs are absent, so category revenue, profit, and margin cannot be calculated without a separately sourced mapping or cost dataset.
- The UCI source contains service/adjustment stock codes such as postage; raw stock-code rankings should not be described as merchandise-only product rankings.
- Future work: add a held-out period for repeat-purchase analysis, define tests against a real PostgreSQL instance, and document a reviewed external product taxonomy if category analysis is desired.

## Code and dataset licenses

Project code is licensed under MIT (see [`LICENSE`](LICENSE)). The UCI dataset has its own CC BY 4.0 license and attribution requirements; this code license does not replace or alter that dataset license.
