# hybrid_workflow.py
import os
import duckdb
from dotenv import load_dotenv

# ---------- 1) Local: open elt.duckdb & find hotspot in Manhattan elevator requests ----------
local_con = duckdb.connect("elt.duckdb", read_only=True)

sql_hotspot = """
WITH base AS (
  SELECT
    CAST(latitude AS DOUBLE)  AS lat,
    CAST(longitude AS DOUBLE) AS lon
  FROM clean_requests
  WHERE UPPER(borough) = 'MANHATTAN'
    AND complaint_type = 'elevator'
    AND latitude IS NOT NULL AND longitude IS NOT NULL
),
bounds AS (
  SELECT
    quantile_cont(lat, 0.10) AS lat_p10,
    quantile_cont(lat, 0.90) AS lat_p90,
    quantile_cont(lon, 0.10) AS lon_p10,
    quantile_cont(lon, 0.90) AS lon_p90
  FROM base
),
clipped AS (
  SELECT b.lat, b.lon
  FROM base b, bounds t
  WHERE b.lat BETWEEN t.lat_p10 AND t.lat_p90
    AND b.lon BETWEEN t.lon_p10 AND t.lon_p90
),
-- choose densest ~0.002° bins (~220 m) in clipped area
clipped_bins AS (
  SELECT
    ROUND(lat, 3) AS lat_bin,
    ROUND(lon, 3) AS lon_bin,
    COUNT(*) AS cnt,
    AVG(lat) AS avg_lat,
    AVG(lon) AS avg_lon
  FROM clipped
  GROUP BY 1,2
  ORDER BY cnt DESC
  LIMIT 1
),
-- fallback to overall densest if clipped is empty (e.g., very small dataset)
overall_bins AS (
  SELECT
    ROUND(lat, 3) AS lat_bin,
    ROUND(lon, 3) AS lon_bin,
    COUNT(*) AS cnt,
    AVG(lat) AS avg_lat,
    AVG(lon) AS avg_lon
  FROM base
  GROUP BY 1,2
  ORDER BY cnt DESC
  LIMIT 1
)
SELECT
  COALESCE(c.avg_lat, o.avg_lat) AS avg_lat,
  COALESCE(c.avg_lon, o.avg_lon) AS avg_lon,
  COALESCE(c.cnt,     o.cnt)     AS bin_count
FROM clipped_bins c
FULL OUTER JOIN overall_bins o ON TRUE;
"""

hq_lat, hq_lon, hotspot_count = local_con.execute(sql_hotspot).fetchone()
print(f"Chosen HQ hotspot: lat={hq_lat:.6f}, lon={hq_lon:.6f}, complaints_in_bin={hotspot_count}")

maps_url = f"https://www.google.com/maps?q={hq_lat:.6f},{hq_lon:.6f}"
print("Google Maps link:", maps_url)

# ---------- 2) Cloud: connect to MotherDuck and query within 2 miles ----------
load_dotenv()
token = os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise RuntimeError("MotherDuck token not found in env var MOTHERDUCK_TOKEN.")

md_con = duckdb.connect(f"md:?motherduck_token={token}")

EARTH_MI = 3958.7613  # radius in miles

cloud_sql_yearly = f"""
WITH src AS (
  SELECT
    complaint_type,
    created_date,
    CAST(latitude  AS DOUBLE) AS lat,
    CAST(longitude AS DOUBLE) AS lon
  FROM sample_data.nyc.service_requests
  WHERE latitude IS NOT NULL AND longitude IS NOT NULL
),
dist AS (
  SELECT
    complaint_type,
    strftime('%Y', created_date) AS year,
    2 * {EARTH_MI} * ASIN(
      SQRT(
        POWER(SIN(RADIANS((lat - {hq_lat})/2)), 2)
        + COS(RADIANS({hq_lat})) * COS(RADIANS(lat)) *
          POWER(SIN(RADIANS((lon - {hq_lon})/2)), 2)
      )
    ) AS distance_miles
  FROM src
)
SELECT
  year,
  complaint_type,
  COUNT(*) AS requests_in_radius
FROM dist
WHERE distance_miles <= 2.0
GROUP BY year, complaint_type
ORDER BY year, complaint_type;
"""

df = md_con.execute(cloud_sql_yearly).fetchdf()  # pandas DataFrame directly
pivoted = df.pivot(index="complaint_type", columns="year", values="requests_in_radius").fillna(0).astype(int)

# Sort by 2022 column (descending) if it exists
if "2022" in pivoted.columns:
    pivoted = pivoted.sort_values(by="2022", ascending=False)

print("\nPivoted DataFrame (complaint_type x year, sorted by 2022):")
print(pivoted.head())