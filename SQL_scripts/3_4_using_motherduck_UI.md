```
duckdb elevator_data.duckdb
```

```
CALL start_ui();
```

```sql
SELECT 
    strftime('%Y', created_date) AS month,
    COUNT(*) AS complaints
FROM nyc.service_requests
WHERE "Borough" = 'MANHATTAN'
GROUP BY month
ORDER BY month;
```