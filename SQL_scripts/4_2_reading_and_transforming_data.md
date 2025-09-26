```
duckdb elevator_data.duckdb
```

```sql
Show tables

describe elevator_requests;
```

```sql
SELECT 
      "Complaint Type",
      COUNT(*) AS complaint_count
  FROM elevator_requests
  GROUP BY "Complaint Type"
  ORDER BY complaint_count DESC;
```

```
duckdb elt.duckdb
```

```sql
SELECT 
      complaint_type,
      COUNT(*) AS complaint_count
  FROM clean_requests
  GROUP BY complaint_type
  ORDER BY complaint_count DESC;
```

# If you run into the _ctypes error
**Install linux packages**
```
sudo apt update
sudo apt install -y build-essential libffi-dev libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    liblzma-dev
```

**cleanup pyenv**
```
pyenv uninstall motherduck
pyenv uninstall 3.11.6
pyenv install 3.11.6
```

**re-create the environment**
```
pyenv virtualenv 3.11.6 motherduck
pyenv activate motherduck
python -m pip install --upgrade pip
pip install duckdb pandas
```