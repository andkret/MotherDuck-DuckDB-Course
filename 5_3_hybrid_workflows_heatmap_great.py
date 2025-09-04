# heatmap_local_requests.py
# Requires: duckdb, numpy, matplotlib
import duckdb
import numpy as np
import matplotlib.pyplot as plt
import math

DB_PATH = "elt.duckdb"

# --- 1) Load local Manhattan elevator points ---
con = duckdb.connect(DB_PATH, read_only=True)

# Pull all elevator points in MANHATTAN
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
    raise RuntimeError("No elevator points found for MANHATTAN in clean_requests.")

lats = np.array([p[0] for p in pts], dtype=float)
lons = np.array([p[1] for p in pts], dtype=float)

# --- 2) Choose HQ (robust densest bin in clipped bounds to avoid extreme uptown/downtown) ---
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
hq_lat, hq_lon, _ = con.execute(hotspot_sql).fetchone()

print(f"HQ candidate: lat={hq_lat:.6f}, lon={hq_lon:.6f}")
print("Google Maps:", f"https://www.google.com/maps?q={hq_lat:.6f},{hq_lon:.6f}")

# --- 3) Build a 2D density heat map ---
# Set bounds to data extent with a small padding
pad_lat = (np.percentile(lats, 99) - np.percentile(lats, 1)) * 0.05
pad_lon = (np.percentile(lons, 99) - np.percentile(lons, 1)) * 0.05
lat_min, lat_max = lats.min() - pad_lat, lats.max() + pad_lat
lon_min, lon_max = lons.min() - pad_lon, lons.max() + pad_lon

# Grid resolution (increase bins for finer detail)
bins_x = 120  # longitude bins
bins_y = 160  # latitude bins

H, xedges, yedges = np.histogram2d(lons, lats, bins=[bins_x, bins_y],
                                   range=[[lon_min, lon_max], [lat_min, lat_max]])

# --- 4) Plot heat map, HQ point, and 2-mile radius circle ---
fig, ax = plt.subplots(figsize=(7, 9))  # single chart; no subplots

# imshow expects [x,y] -> [lon,lat] order
extent = [lon_min, lon_max, lat_min, lat_max]
# NOTE: We do not set any specific colors or styles.
im = ax.imshow(H.T, origin="lower", extent=extent, aspect="equal")

# Overlay HQ
ax.plot([hq_lon], [hq_lat], marker="o", markersize=6)

# Draw 2-mile radius circle (approx):
# 1 degree latitude ≈ 69 miles; 1 degree longitude ≈ 69*cos(lat) miles
lat_per_mile = 1.0 / 69.0
lon_per_mile = 1.0 / (69.0 * math.cos(math.radians(hq_lat)))
radius_miles = 2.0
theta = np.linspace(0, 2*np.pi, 360)
circle_lats = hq_lat + radius_miles * lat_per_mile * np.sin(theta)
circle_lons = hq_lon + radius_miles * lon_per_mile * np.cos(theta)
ax.plot(circle_lons, circle_lats, linewidth=1.5)

ax.set_title("Manhattan Elevator Requests — Density Heat Map (Local)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

plt.tight_layout()
plt.show()

# Optionally save image
fig.savefig("manhattan_elevator_heatmap.png", dpi=200)
print("Saved heat map to manhattan_elevator_heatmap.png")
