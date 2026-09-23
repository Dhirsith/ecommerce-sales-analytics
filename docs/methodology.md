# Data and metric methodology

## Source and grain

The source is UCI's *Online Retail* workbook. A source row is an invoice line for one stock code; there is no source line identifier. The pipeline removes exact duplicate source rows and assigns a deterministic `sale_line_id` after that step. The same stock code can appear on multiple lines and those rows are retained unless every source field is identical.

## Cleaning rules

- Normalize column names, trim identifiers and country/description text, uppercase stock codes, preserve common country acronyms, and parse invoice timestamps.
- Exclude rows missing invoice number, stock code, quantity, invoice timestamp, unit price, or country. Customer ID and description may be missing.
- Fill a missing product description from the modal nonmissing description for the same stock code; otherwise retain `Unknown description`.
- Keep cancellation lines (invoice numbers prefixed by `C`), zero-price lines, negative-price adjustment rows, and negative quantities in the fact table with flags. They remain visible for quality review.
- `revenue_eligible` is true only for non-cancellation lines with nonzero quantity and positive unit price. `line_revenue_gbp` is quantity multiplied by unit price for those lines and zero otherwise. Negative quantities on eligible non-cancellation rows reduce net sales as returns.
- The source is GBP-denominated. No costs are present, so the project reports sales revenue, never profit or margin.
- Product performance groups by source stock code and description. The source includes postage and other service/adjustment codes, so a stock-code ranking is not a merchandise-only ranking.

## Customer metrics

Customer counts exclude missing customer IDs. A purchasing invoice is a distinct non-cancellation invoice with a positive quantity and positive unit price. Repeat means a known customer has at least two such invoices. RFM frequency counts distinct purchasing invoices, monetary value sums positive-quantity item revenue, and recency is days since the last positive purchase relative to one day after the final observed invoice date. Cancellations, returns, and nonpositive prices do not contribute to RFM monetary value. Quartile scores use average percentile ranks so equal values share a score. Segment labels are descriptive, retrospective groupings, not a production score or future-value prediction.

## Scope limits

This is one historical UK-based retailer with a single year of records. Missing customer IDs prevent customer attribution for some lines. Product categories, cost, discounts as a structured field, marketing exposure, and delivery outcomes are not supplied. Month-to-month patterns are descriptive and do not establish seasonality or causation. Country is the source's customer-country field, not shipping or store geography.
