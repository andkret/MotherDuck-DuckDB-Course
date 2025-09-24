# Configure token

```
export MOTHERDUCK_TOKEN=your_token_here      # macOS / Linux
setx MOTHERDUCK_TOKEN "your_token_here"      # Windows PowerShell
```

# Test the connection

```
duckdb md:
```

# Attach the file share from MotherDuck
https://motherduck.com/docs/getting-started/sample-data-queries/datasets/


```sql
ATTACH 'md:_share/sample_data/23b0d623-1361-421d-ae77-62d701d471e6';
```

```sql
SHOW DATABASES;
```

# Query some data

```sql
SELECT 
    strftime('%Y', created_date) AS year,
    COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
GROUP BY year
ORDER BY year;
```

```sql
SELECT 
    strftime('%Y-%m', created_date) AS month,
    COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
WHERE strftime('%Y', created_date) = '2023'
  AND complaint_type ILIKE 'elevator'
  AND borough = 'MANHATTAN'
GROUP BY month
ORDER BY month;
```

```sql
SELECT 
    strftime('%Y', created_date) AS year,
    COUNT(*) AS complaints
FROM sample_data.nyc.service_requests
WHERE complaint_type ILIKE 'elevator'
  AND borough = 'MANHATTAN'
GROUP BY year
ORDER BY year;
```

```sql
SELECT 
    strftime('%Y', "Created Date") AS year,
    COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN'
GROUP BY year
ORDER BY year;
```

# Detach the DATABASE
```sql
DETACH sample_data;
```