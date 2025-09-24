# DuckDB UI

**Start the UI**
```sql
duckdb -ui
```

**Start the UI when in the CLI**
```sql
CALL start_ui();
```

# Create a View

```sql
CREATE VIEW elevator_requests AS
SELECT *
FROM read_csv_auto('311_Elevator_Service_Requests_.csv', HEADER=TRUE);
```

# Run a Query

```sql
SELECT 
    strftime('%Y-%m', "Created Date") AS month,
    COUNT(*) AS complaints
FROM elevator_requests
WHERE "Borough" = 'MANHATTAN'
GROUP BY month
ORDER BY month;
```