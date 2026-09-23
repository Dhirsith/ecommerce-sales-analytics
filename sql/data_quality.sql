-- Run after loading the prepared tables into PostgreSQL.
SELECT 'fact_rows' AS check_name, COUNT(*)::BIGINT AS issue_count
FROM retail_analytics.fact_sales_line
UNION ALL
SELECT 'null_invoice_or_product', COUNT(*)
FROM retail_analytics.fact_sales_line
WHERE invoice_no IS NULL OR product_code IS NULL
UNION ALL
SELECT 'revenue_flag_mismatch', COUNT(*)
FROM retail_analytics.fact_sales_line
WHERE revenue_eligible <> (NOT is_cancelled AND quantity <> 0 AND unit_price_gbp > 0)
UNION ALL
SELECT 'line_revenue_mismatch', COUNT(*)
FROM retail_analytics.fact_sales_line
WHERE line_revenue_gbp <> CASE
    WHEN revenue_eligible THEN quantity * unit_price_gbp
    ELSE 0
END
UNION ALL
SELECT 'cancellation_flag_mismatch', COUNT(*)
FROM retail_analytics.fact_sales_line
WHERE is_cancelled <> (UPPER(invoice_no) LIKE 'C%')
UNION ALL
SELECT 'return_flag_mismatch', COUNT(*)
FROM retail_analytics.fact_sales_line
WHERE is_return <> (quantity < 0 AND NOT is_cancelled)
UNION ALL
SELECT 'orphan_product_dimension', COUNT(*)
FROM retail_analytics.fact_sales_line f
LEFT JOIN retail_analytics.dim_product p USING (product_code)
WHERE p.product_code IS NULL
UNION ALL
SELECT 'orphan_date_dimension', COUNT(*)
FROM retail_analytics.fact_sales_line f
LEFT JOIN retail_analytics.dim_date d USING (date_key)
WHERE d.date_key IS NULL;
