# DuckDB UI

**Start the UI**
```sql
duckdb -ui
```

**Start the UI when in the CLI**
```sql
CALL start_ui();
```


**Set Environment Variable**
```
export MOTHERDUCK_TOKEN=your_token_here      # macOS / Linux
setx MOTHERDUCK_TOKEN "your_token_here"      # Windows PowerShell
```

**Test the Connection**
```
duckdb md:
SHOW DATABASES;
```