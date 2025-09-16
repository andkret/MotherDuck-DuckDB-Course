```
duckdb elt.duckdb
```

```sql
Show tables

describe service_requests;
```

```sql
SELECT 
      "Complaint Type",
      COUNT(*) AS complaint_count
  FROM service_requests
  GROUP BY "Complaint Type"
  ORDER BY complaint_count DESC;
```