-- SQL query to retrieve data for WBR methodology
SELECT 
    date,
    metric_value
FROM 
    `your_project.your_dataset.your_table`
WHERE 
    date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 6 WEEK) AND CURRENT_DATE()
ORDER BY 
    date;