-- SQL query to retrieve data for WBR methodology
-- This query works with both BigQuery and PostgreSQL with client-side adaptations
SELECT 
    {{date_cast}} AS date,
    {{metric_col}} AS metric_value,
    {{shopping_col}} AS shopping
FROM 
    {{table_reference}}
WHERE 
    -- Fetch from Jan 1 of last year up to today to support CY/PY comparisons and monthly series
    {{date_filter}}
ORDER BY 
    date;