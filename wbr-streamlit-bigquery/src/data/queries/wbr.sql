-- SQL query to retrieve data for WBR methodology
SELECT 
    DATE(`{{date_col}}`) AS date,
    `{{metric_col}}` AS metric_value
FROM 
    `your_project.your_dataset.your_table`
WHERE 
    DATE(`{{date_col}}`) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 6 WEEK) AND CURRENT_DATE()
ORDER BY 
    DATE(`{{date_col}}`);