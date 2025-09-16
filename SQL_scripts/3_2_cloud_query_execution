```sql
EXPLAIN
SELECT 
    strftime('%Y', created_date) AS year,
    COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
GROUP BY year
ORDER BY year;
```

```sql
EXPLAIN ANALYZE
SELECT 
    strftime('%Y', created_date) AS year,
    COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
GROUP BY year
ORDER BY year;
```

```sql
EXPLAIN ANALYZE
SELECT
  EXTRACT(YEAR FROM created_date) AS year,
  COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
GROUP BY year
ORDER BY year;
```