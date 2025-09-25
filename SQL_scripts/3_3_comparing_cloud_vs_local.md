```sql
EXPLAIN ANALYZE
WITH local_counts AS (
  SELECT
    EXTRACT(YEAR FROM "Created Date") AS year,
    COUNT(*) AS complaints,
    'local' AS source
  FROM elevator_requests
  GROUP BY year
),
md_counts AS (
  SELECT
    EXTRACT(YEAR FROM created_date) AS year,
    COUNT(*) AS complaints,
    'sample_data' AS source
  FROM sample_data.nyc.service_requests
  GROUP BY year
)
SELECT *
FROM local_counts
UNION ALL
SELECT *
FROM md_counts
ORDER BY year, source;
```

```sql
EXPLAIN ANALYZE
WITH local_counts AS (
  SELECT
    EXTRACT(YEAR FROM "Created Date") AS year,
    COUNT(*) AS complaints,
    'local' AS source
  FROM elevator_requests
  GROUP BY year
),
md_counts AS (
  SELECT
    EXTRACT(YEAR FROM created_date) AS year,
    COUNT(*) AS complaints,
    'sample_data' AS source
  FROM sample_data.nyc.service_requests
  WHERE complaint_type ILIKE '%elevator%'   -- filter only elevator issues
  GROUP BY year
)
SELECT *
FROM local_counts
UNION ALL
SELECT *
FROM md_counts
ORDER BY year, source;
```

