# simple_hq_hotspot.py
import os
import math
import numpy as np
import duckdb
import matplotlib.pyplot as plt
from dotenv import load_dotenv

DB_PATH = "elt.duckdb"
RADIUS_MILES = 1.0
BINS_X, BINS_Y = 60, 80
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
# 3) Local heat map with HQ marker
# ----------------------------
pad_lat = (np.percentile(lats, 99) - np.percentile(lats, 1)) * 0.05
pad_lon = (np.percentile(lons, 99) - np.percentile(lons, 1)) * 0.05
lat_min, lat_max = lats.min() - pad_lat, lats.max() + pad_lat
lon_min, lon_max = lons.min() - pad_lon, lons.max() + pad_lon

H, xedges, yedges = np.histogram2d(
    lons, lats, bins=[BINS_X, BINS_Y], range=[[lon_min, lon_max], [lat_min, lat_max]]
)

fig, ax = plt.subplots(figsize=(7, 9))
ax.imshow(H.T, origin="lower", extent=[lon_min, lon_max, lat_min, lat_max], aspect="equal")

cbar = plt.colorbar(ax.images[0], ax=ax)
cbar.set_label("Complaints per bin")

for x in xedges:
    ax.axvline(x, color="white", linewidth=0.3, alpha=0.5)
for y in yedges:
    ax.axhline(y, color="white", linewidth=0.3, alpha=0.5)

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

ax.set_title("Manhattan Elevator Requests — Heat Map (Hotspot HQ)")
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

# Sort by a specific year (e.g., 2022) if present
if SORT_YEAR in pivoted.columns:
    pivoted = pivoted.sort_values(by=SORT_YEAR, ascending=False)

print("\nPivoted DataFrame (complaint_type x year, sorted by", SORT_YEAR, "):")
print(pivoted.head(25))