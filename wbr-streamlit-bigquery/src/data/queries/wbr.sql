-- SQL query to retrieve data for WBR methodology
SELECT 
    DATE(`{{date_col}}`) AS date,
    `{{metric_col}}` AS metric_value,
    {{shopping_col}} AS shopping
FROM 
    `your_project.your_dataset.your_table`
WHERE 
    -- Fetch from Jan 1 of last year up to today to support CY/PY comparisons and monthly series
    DATE(`{{date_col}}`) BETWEEN DATE_SUB(DATE_TRUNC(CURRENT_DATE(), YEAR), INTERVAL 1 YEAR) AND CURRENT_DATE()
ORDER BY 
    DATE(`{{date_col}}`);