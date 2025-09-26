import duckdb
import re


con = duckdb.connect("elt.duckdb")

# Step 1: Local load (L)
con.execute("""
  CREATE OR REPLACE TABLE service_requests AS
  SELECT * FROM read_csv_auto('311_Elevator_Service_Requests_.csv', header=True);
""")

# Step 2: Local transform (L)
con.execute("""
  CREATE OR REPLACE TABLE clean_requests AS
  SELECT
    * REPLACE (LOWER("Complaint Type") AS "Complaint Type")
  FROM service_requests;
""")

# Step 3: Fix column names in clean_requests
cols = con.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'clean_requests'
    ORDER BY ordinal_position;
""").fetchall()

def normalize_colname(name: str) -> str:
    s = name.strip().lower().replace(" ", "_")
    s = re.sub(r'[^a-z0-9_]', '_', s)
    s = re.sub(r'_+', '_', s)
    return s

for (col,) in cols:
    new = normalize_colname(col)
    if new != col:  # only rename if changed
        sql = f'ALTER TABLE clean_requests RENAME COLUMN "{col}" TO {new};'
        print("Executing:", sql)
        con.execute(sql)

# Step 4: Verify
df = con.execute("PRAGMA table_info('clean_requests');").fetchdf()
print(df)

# Step 5: Add closed_in_days column to the dimension table
con.execute("""
  ALTER TABLE clean_requests
  ADD COLUMN closed_in_days INTEGER
""")

# Step 6: Populate it
con.execute("""
  UPDATE clean_requests
  SET closed_in_days = DATEDIFF('day', created_date, closed_date)
""")

# Step 7:Verify
print(con.execute("""
    SELECT created_date, closed_date, closed_in_days
    FROM clean_requests
    WHERE closed_date IS NOT NULL
    LIMIT 10;
""").fetchdf())