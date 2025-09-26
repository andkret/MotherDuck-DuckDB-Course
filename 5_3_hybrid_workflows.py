import os
import math
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv

DB_PATH = "elt.duckdb"
RADIUS_MILES = 1.0
SORT_YEAR = "2022"

# ----------------------------
# 1) Get Manhattan elevator points
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
    raise RuntimeError("No elevator points found in Manhattan.")

lats = np.array([p[0] for p in pts])
lons = np.array([p[1] for p in pts])

# ----------------------------
# 2) HQ candidate: densest bin (hotspot)
# ----------------------------
hq_sql = """
SELECT
  ROUND(lat, 3) AS lat_bin,
  ROUND(lon, 3) AS lon_bin,
  COUNT(*) AS complaints_in_bin,
  AVG(lat) AS avg_lat,
  AVG(lon) AS avg_lon
FROM (
  SELECT
    CAST(latitude AS DOUBLE) AS lat,
    CAST(longitude AS DOUBLE) AS lon
  FROM clean_requests
  WHERE UPPER(borough) = 'MANHATTAN'
    AND complaint_type = 'elevator'
    AND latitude IS NOT NULL AND longitude IS NOT NULL
)
GROUP BY 1,2
ORDER BY complaints_in_bin DESC
LIMIT 1;
"""
_, _, complaints_in_bin, hq_lat, hq_lon = con.execute(hq_sql).fetchone()

print(f"HQ candidate (hotspot): lat={hq_lat:.6f}, lon={hq_lon:.6f}, complaints_in_bin={complaints_in_bin}")
print("Google Maps:", f"https://www.google.com/maps?q={hq_lat:.6f},{hq_lon:.6f}")

# ----------------------------
# 3) Local heat map (aligned with SQL bins)
# ----------------------------
# Snap complaints into the same 0.001° bins (100x100 meters) as SQL
lat_bins = np.round(lats, 3)
lon_bins = np.round(lons, 3)

# Count per bin
df_bins = pd.DataFrame({"lat_bin": lat_bins, "lon_bin": lon_bins})
counts = df_bins.value_counts().reset_index(name="count")

# Pivot to 2D grid
pivot = counts.pivot(index="lat_bin", columns="lon_bin", values="count").fillna(0)

# Prepare mesh for plotting
lon_coords = pivot.columns.values
lat_coords = pivot.index.values
X, Y = np.meshgrid(lon_coords, lat_coords)

fig, ax = plt.subplots(figsize=(7, 9))
mesh = ax.pcolormesh(X, Y, pivot.values, cmap="hot", shading="auto")

# HQ marker
ax.plot([hq_lon], [hq_lat], marker="o", markersize=6, color="red")

# Add radius circle
lat_per_mile = 1.0 / 69.0
lon_per_mile = 1.0 / (69.0 * math.cos(math.radians(hq_lat)))
theta = np.linspace(0, 2*np.pi, 360)
ax.plot(
    hq_lon + RADIUS_MILES * lon_per_mile * np.cos(theta),
    hq_lat + RADIUS_MILES * lat_per_mile * np.sin(theta),
    linewidth=1.5,
    color="blue"
)

# Colorbar below chart
cbar = fig.colorbar(mesh, ax=ax, orientation="horizontal", fraction=0.05, pad=0.1)
cbar.set_label("Complaints per 0.001° bin")

ax.set_title("Manhattan Elevator Requests — Heat Map (SQL Bin HQ)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
plt.tight_layout()
fig.savefig("manhattan_elevator_heatmap.png", dpi=200)
print("Saved heat map to manhattan_elevator_heatmap.png")

# ----------------------------
# 4) Cloud: yearly counts in 2-mile radius -> pivoted pandas DataFrame
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

df = md_con.execute(cloud_sql_yearly).fetchdf()
pivoted = (
    df.pivot(index="complaint_type", columns="year", values="requests_in_radius")
      .fillna(0)
      .astype(int)
)

if SORT_YEAR in pivoted.columns:
    pivoted = pivoted.sort_values(by=SORT_YEAR, ascending=False)

print("\nPivoted DataFrame (complaint_type x year, sorted by", SORT_YEAR, "):")
print(pivoted.head(25))
