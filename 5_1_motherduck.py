import duckdb
import os
# do "pip install dotenv" first
from dotenv import load_dotenv



# Load environment variables from .env
load_dotenv()

token = os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise RuntimeError("MotherDuck token not found. Did you set it in .env?")

con = duckdb.connect(f"md:_share/sample_data/23b0d623-1361-421d-ae77-62d701d471e6?motherduck_token={token}")

df = con.execute("""
    SELECT strftime('%Y', created_date) AS year, COUNT(*) AS complaints
    FROM sample_data.nyc.service_requests
    GROUP BY year
    ORDER BY year
    LIMIT 5
""").fetchdf()

print(df)