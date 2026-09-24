-- KPI overview: net item revenue includes non-cancelled return lines as negatives.
SELECT
    SUM(line_revenue_gbp) AS net_revenue_gbp,
    COUNT(DISTINCT invoice_no) FILTER (WHERE quantity > 0 AND revenue_eligible) AS positive_quantity_orders,
    COUNT(DISTINCT customer_id) FILTER (
        WHERE customer_id IS NOT NULL AND quantity > 0 AND revenue_eligible
    ) AS identified_purchasing_customers,
    SUM(line_revenue_gbp) / NULLIF(
        COUNT(DISTINCT invoice_no) FILTER (WHERE quantity > 0 AND revenue_eligible), 0
    ) AS average_order_value_gbp
FROM retail_analytics.fact_sales_line
WHERE revenue_eligible;

-- Monthly sales with month-over-month comparison to the immediately preceding observed month.
WITH monthly AS (
    SELECT d.year, d.month, MIN(d.full_date) AS month_start,
           SUM(f.line_revenue_gbp) AS revenue_gbp,
           COUNT(DISTINCT f.invoice_no) FILTER (WHERE f.quantity > 0) AS order_count
    FROM retail_analytics.fact_sales_line f
    JOIN retail_analytics.dim_date d USING (date_key)
    WHERE f.revenue_eligible
    GROUP BY d.year, d.month
), trend AS (
    SELECT *, LAG(revenue_gbp) OVER (ORDER BY month_start) AS prior_month_revenue_gbp
    FROM monthly
)
SELECT *, revenue_gbp - prior_month_revenue_gbp AS revenue_change_gbp,
       (revenue_gbp - prior_month_revenue_gbp) / NULLIF(prior_month_revenue_gbp, 0) AS revenue_change_rate
FROM trend
ORDER BY month_start;

-- Top product codes and their share of net revenue.
WITH product_sales AS (
    SELECT p.product_code, p.product_description,
           SUM(f.line_revenue_gbp) AS revenue_gbp,
           SUM(f.quantity) AS net_quantity,
           COUNT(DISTINCT f.invoice_no) FILTER (WHERE f.quantity > 0) AS invoice_count
    FROM retail_analytics.fact_sales_line f
    JOIN retail_analytics.dim_product p USING (product_code)
    WHERE f.revenue_eligible
    GROUP BY p.product_code, p.product_description
), ranked AS (
    SELECT *, DENSE_RANK() OVER (ORDER BY revenue_gbp DESC) AS revenue_rank,
           revenue_gbp / NULLIF(SUM(revenue_gbp) OVER (), 0) AS revenue_share
    FROM product_sales
)
SELECT * FROM ranked WHERE revenue_rank <= 20 ORDER BY revenue_rank, product_code;

-- Repeat customer share. Customer frequency counts distinct invoices with positive sales.
WITH customer_orders AS (
    SELECT customer_id, COUNT(DISTINCT invoice_no) AS order_count,
           SUM(line_revenue_gbp) FILTER (WHERE quantity > 0) AS positive_sales_gbp
    FROM retail_analytics.fact_sales_line
    WHERE customer_id IS NOT NULL AND revenue_eligible AND quantity > 0
    GROUP BY customer_id
), classified AS (
    SELECT *, CASE WHEN order_count >= 2 THEN 'Repeat' ELSE 'One-time' END AS customer_type
    FROM customer_orders
)
SELECT customer_type, COUNT(*) AS customers, SUM(positive_sales_gbp) AS positive_sales_gbp,
       COUNT(*)::NUMERIC / NULLIF(SUM(COUNT(*)) OVER (), 0) AS customer_share
FROM classified
GROUP BY customer_type
ORDER BY customer_type;

-- Country analysis, using source country as customer geography.
SELECT country, SUM(line_revenue_gbp) AS revenue_gbp,
       COUNT(DISTINCT invoice_no) FILTER (WHERE quantity > 0) AS order_count,
       COUNT(DISTINCT customer_id) FILTER (WHERE customer_id IS NOT NULL AND quantity > 0)
           AS identified_purchasing_customers
FROM retail_analytics.fact_sales_line
WHERE revenue_eligible
GROUP BY country
ORDER BY revenue_gbp DESC;

-- Customers whose revenue is in the upper quartile, using a CTE and window function.
WITH customer_revenue AS (
    SELECT customer_id, SUM(line_revenue_gbp) AS revenue_gbp,
           COUNT(DISTINCT invoice_no) AS invoice_count
    FROM retail_analytics.fact_sales_line
    WHERE customer_id IS NOT NULL AND revenue_eligible AND quantity > 0
    GROUP BY customer_id
), scored AS (
    SELECT *, NTILE(4) OVER (ORDER BY revenue_gbp DESC) AS revenue_quartile
    FROM customer_revenue
)
SELECT customer_id, revenue_gbp, invoice_count
FROM scored
WHERE revenue_quartile = 1
ORDER BY revenue_gbp DESC;
