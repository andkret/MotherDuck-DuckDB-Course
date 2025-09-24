
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