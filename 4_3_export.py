import duckdb
from pathlib import Path

con = duckdb.connect("elt.duckdb")

csv_path = Path("clean_requests.csv")
con.execute(f"""
    COPY clean_requests TO '{csv_path}' (HEADER, DELIMITER ',');
""")
print(f"Exported clean_requests to {csv_path.resolve()}")


parquet_path = Path("clean_requests.parquet")
con.execute(f"""
    COPY clean_requests TO '{parquet_path}' (FORMAT PARQUET);
""")
print(f"Exported clean_requests to {parquet_path.resolve()}")


df = con.execute("""
    SELECT complaint_type, COUNT(*) AS issues
    FROM read_parquet('clean_requests.parquet')
    GROUP BY complaint_type
    ORDER BY issues DESC
    LIMIT 10;
""").fetchdf()


print("\nTop complaint types from Parquet:")
print(df)
