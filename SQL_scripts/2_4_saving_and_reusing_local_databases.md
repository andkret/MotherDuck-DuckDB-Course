# Create the DB file and import the CSV

```
duckdb elevator_data.duckdb
```

```sql

-- create a persistent table from your CSV
CREATE TABLE elevator_requests AS
SELECT *
FROM read_csv_auto('311_Elevator_Service_Requests_.csv', HEADER=true, AUTO_DETECT=true);

-- quick sanity checks
SELECT COUNT(*) FROM elevator_requests;
SELECT COUNT(*) FROM read_csv_auto('311_Elevator_Service_Requests_.csv', HEADER=true, AUTO_DETECT=true);
```

```sql
DESCRIBE elevator_requests;   -- see columns & types
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

# Quit the CLI
```
.quit
```

# Reopen DB & Query
```
duckdb elevator_data.duckdb
```

```sql
SHOW TABLES;                               -- should list elevator_requests
SELECT * FROM elevator_requests LIMIT 5;   -- sample rows
```
