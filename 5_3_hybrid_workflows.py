# hybrid_heatmap_and_yearly.py
# Requires: duckdb, numpy, matplotlib, pandas, python-dotenv
import os
import math
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

# ----------------------------
# Config
# ----------------------------
DB_PATH = "elt.duckdb"
RADIUS_MILES = 1.0
BINS_X = 120    # heat map resolution (longitude bins)
BINS_Y = 160    # heat map resolution (latitude bins)
SORT_YEAR = "2022"  # pivot sort column

# ----------------------------
# 1) Local data: load points (MANHATTAN, elevator) + robust HQ
# ----------------------------
con = duckdb.connect(DB_PATH, read_only=True)

points_sql = """
SELECT
  CAST(latitude AS DOUBLE)  AS lat,
  CAST(longitude AS DOUBLE) AS lon
FROM clean_requests
WHERE UPPER(borough) = 'MANHATTAN'
  AND complaint_type = 'elevator'
  AND latitude IS NOT NULL AND longitude IS NOT NULL;
"""
pts = con.execute(points_sql).fetchall()
if not pts:
    raise RuntimeError("No elevator points for MANHATTAN in clean_requests.")

lats = np.array([p[0] for p in pts], dtype=float)
lons = np.array([p[1] for p in pts], dtype=float)

hotspot_sql = """
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
hq_lat, hq_lon, hotspot_count = con.execute(hotspot_sql).fetchone()
print(f"HQ candidate (robust): lat={hq_lat:.6f}, lon={hq_lon:.6f}, complaints_in_bin={hotspot_count}")
print("Google Maps:", f"https://www.google.com/maps?q={hq_lat:.6f},{hq_lon:.6f}")

# ----------------------------
# 2) Heat map (local)
# ----------------------------
# Pad plot bounds slightly
pad_lat = (np.percentile(lats, 99) - np.percentile(lats, 1)) * 0.05
pad_lon = (np.percentile(lons, 99) - np.percentile(lons, 1)) * 0.05
lat_min, lat_max = lats.min() - pad_lat, lats.max() + pad_lat
lon_min, lon_max = lons.min() - pad_lon, lons.max() + pad_lon

H, xedges, yedges = np.histogram2d(
    lons, lats, bins=[BINS_X, BINS_Y], range=[[lon_min, lon_max], [lat_min, lat_max]]
)

fig, ax = plt.subplots(figsize=(7, 9))  # single chart, no subplots
extent = [lon_min, lon_max, lat_min, lat_max]
ax.imshow(H.T, origin="lower", extent=extent, aspect="equal")
ax.plot([hq_lon], [hq_lat], marker="o", markersize=6)

# 2-mile radius circle (approx, using degrees per mile)
lat_per_mile = 1.0 / 69.0
lon_per_mile = 1.0 / (69.0 * math.cos(math.radians(hq_lat)))
theta = np.linspace(0, 2*np.pi, 360)
circle_lats = hq_lat + RADIUS_MILES * lat_per_mile * np.sin(theta)
circle_lons = hq_lon + RADIUS_MILES * lon_per_mile * np.cos(theta)
ax.plot(circle_lons, circle_lats, linewidth=1.5)

ax.set_title("Manhattan Elevator Requests — Density Heat Map (Local)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.tight_layout()
fig.savefig("manhattan_elevator_heatmap.png", dpi=200)
print("Saved heat map to manhattan_elevator_heatmap.png")

# ----------------------------
# 3) Cloud: yearly counts in 2-mile radius -> pivoted pandas DataFrame
# ----------------------------
load_dotenv()
token = os.getenv("MOTHERDUCK_TOKEN")
if not token:
    raise RuntimeError("MotherDuck token not found in .env (MOTHERDUCK_TOKEN).")

md_con = duckdb.connect(f"md:?motherduck_token={token}")

EARTH_MI = 3958.7613
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
WHERE distance_miles <= {RADIUS_MILES}
GROUP BY year, complaint_type
ORDER BY year, complaint_type;
"""

df = md_con.execute(cloud_sql_yearly).fetchdf()  # -> pandas DataFrame
pivoted = (
    df.pivot(index="complaint_type", columns="year", values="requests_in_radius")
      .fillna(0)
      .astype(int)
)

# Sort by a specific year (e.g., 2022) if present
if SORT_YEAR in pivoted.columns:
    pivoted = pivoted.sort_values(by=SORT_YEAR, ascending=False)

print("\nPivoted DataFrame (complaint_type x year, sorted by", SORT_YEAR, "):")
print(pivoted.head(20))  # preview

# Optional: save artifacts 
# 
# pivoted.to_csv("radius_requests_by_year.csv")
# try:
#     pivoted.to_parquet("radius_requests_by_year.parquet", index=True)
# except Exception as e:
#     print("Parquet save skipped (install pyarrow or fastparquet to enable).", e)
# print("Saved pivot to radius_requests_by_year.csv (and parquet if available).")
# 