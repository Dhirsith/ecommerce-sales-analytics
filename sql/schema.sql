-- PostgreSQL star schema for the UCI Online Retail transaction line data.
CREATE SCHEMA IF NOT EXISTS retail_analytics;

CREATE TABLE IF NOT EXISTS retail_analytics.dim_date (
    date_key       INTEGER PRIMARY KEY,
    full_date      DATE NOT NULL UNIQUE,
    year           SMALLINT NOT NULL,
    quarter        SMALLINT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month          SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name     TEXT NOT NULL,
    day_of_week    SMALLINT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    day_name       TEXT NOT NULL,
    is_weekend     BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_analytics.dim_product (
    product_code        TEXT PRIMARY KEY,
    product_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retail_analytics.dim_customer (
    customer_id BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS retail_analytics.fact_sales_line (
    sale_line_id       BIGINT PRIMARY KEY,
    invoice_no         TEXT NOT NULL,
    product_code       TEXT NOT NULL REFERENCES retail_analytics.dim_product(product_code),
    customer_id        BIGINT REFERENCES retail_analytics.dim_customer(customer_id),
    date_key           INTEGER NOT NULL REFERENCES retail_analytics.dim_date(date_key),
    invoice_at         TIMESTAMP NOT NULL,
    country            TEXT NOT NULL,
    quantity           INTEGER NOT NULL,
    unit_price_gbp     NUMERIC(18, 4) NOT NULL,
    line_revenue_gbp   NUMERIC(18, 4) NOT NULL,
    is_cancelled       BOOLEAN NOT NULL,
    is_return          BOOLEAN NOT NULL,
    revenue_eligible   BOOLEAN NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_invoice
    ON retail_analytics.fact_sales_line(invoice_no);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_date
    ON retail_analytics.fact_sales_line(customer_id, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_date
    ON retail_analytics.fact_sales_line(product_code, date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_country_date
    ON retail_analytics.fact_sales_line(country, date_key);
