# NYC 311 Elevator Complaints – Data Exploration & Analysis with DuckDB

We’ll use NYC Open Data to analyze elevator service requests.  
Dataset: [311 Service Requests from 2010 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/explore)

👉 Pre-filtered dataset link (only Elevator complaints in 2024):  
[Filtered Query Link](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9/explore/query/SELECT%0A%20%20%60unique_key%60%2C%0A%20%20%60created_date%60%2C%0A%20%20%60closed_date%60%2C%0A%20%20%60agency%60%2C%0A%20%20%60agency_name%60%2C%0A%20%20%60complaint_type%60%2C%0A%20%20%60descriptor%60%2C%0A%20%20%60location_type%60%2C%0A%20%20%60incident_zip%60%2C%0A%20%20%60incident_address%60%2C%0A%20%20%60street_name%60%2C%0A%20%20%60cross_street_1%60%2C%0A%20%20%60cross_street_2%60%2C%0A%20%20%60intersection_street_1%60%2C%0A%20%20%60intersection_street_2%60%2C%0A%20%20%60address_type%60%2C%0A%20%20%60city%60%2C%0A%20%20%60landmark%60%2C%0A%20%20%60facility_type%60%2C%0A%20%20%60status%60%2C%0A%20%20%60due_date%60%2C%0A%20%20%60resolution_description%60%2C%0A%20%20%60resolution_action_updated_date%60%2C%0A%20%20%60community_board%60%2C%0A%20%20%60bbl%60%2C%0A%20%20%60borough%60%2C%0A%20%20%60x_coordinate_state_plane%60%2C%0A%20%20%60y_coordinate_state_plane%60%2C%0A%20%20%60open_data_channel_type%60%2C%0A%20%20%60park_facility_name%60%2C%0A%20%20%60park_borough%60%2C%0A%20%20%60vehicle_type%60%2C%0A%20%20%60taxi_company_borough%60%2C%0A%20%20%60taxi_pick_up_location%60%2C%0A%20%20%60bridge_highway_name%60%2C%0A%20%20%60bridge_highway_direction%60%2C%0A%20%20%60road_ramp%60%2C%0A%20%20%60bridge_highway_segment%60%2C%0A%20%20%60latitude%60%2C%0A%20%20%60longitude%60%2C%0A%20%20%60location%60%0AWHERE%0A%20%20%60created_date%60%0A%20%20%20%20BETWEEN%20%222024-01-01T09%3A42%3A31%22%20%3A%3A%20floating_timestamp%0A%20%20%20%20AND%20%222024-12-31T09%3A42%3A31%22%20%3A%3A%20floating_timestamp%0A%20%20AND%20caseless_one_of%28%60complaint_type%60%2C%20%22Elevator%22%29%0AORDER%20BY%20%60created_date%60%20DESC%20NULL%20FIRST/page/filter)

Download this dataset as CSV (name it `311_Elevator_Service_Requests_.csv`) and use the following queries in DuckDB.

---

## 1. Peek at the Data

```sql
.mode csv

SELECT * 
FROM read_csv_auto('311_Elevator_Service_Requests_.csv') 
LIMIT 5;

.mode duckbox
.maxrows 500
```

---

## 2. Time Breakdown of Elevator Complaints (Monthly)

```sql
SELECT strftime('%Y-%m', "Created Date") AS month,
       COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
GROUP BY month
ORDER BY month;
```

_This shows us how many elevator complaints happen each month._

---

## 3. Geographic Breakdown (by Borough)

```sql
SELECT "Borough", COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
GROUP BY "Borough"
ORDER BY complaints DESC;
```

---

## 4. Focus on Manhattan Complaints Over Time

```sql
SELECT 
    strftime('%Y-%m', "Created Date") AS month,
    COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN'
GROUP BY month
ORDER BY month;
```

---

## 5. Elevator Complaints per ZIP (Manhattan Only)

```sql
SELECT "Incident Zip",
       COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN'
GROUP BY "Incident Zip"
ORDER BY complaints DESC;
```

---

## 6. Elevator Complaints by Street Name (Top 20 in Manhattan)

```sql
SELECT "Street Name",
       COUNT(*) AS complaints
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN'
GROUP BY "Street Name"
ORDER BY complaints DESC
LIMIT 20;
```

---

# Finding the Optimal HQ Location

We’ll now use geographic coordinates (latitude/longitude) to estimate good headquarters locations.

---

## 7. Simple Centroid Approach

```sql
SELECT 
    AVG("Latitude") AS hq_lat,
    AVG("Longitude") AS hq_lon
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN';
```

👉 This gives the geographic “center of mass” for complaints.

---

## 8. Weighted Centroid (Better)

```sql
WITH street_points AS (
  SELECT 
      "Street Name",
      AVG("Latitude") AS lat,
      AVG("Longitude") AS lon,
      COUNT(*) AS complaints
  FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
  WHERE "Borough" = 'MANHATTAN'
  GROUP BY "Street Name"
)
SELECT 
    SUM(lat * complaints) / SUM(complaints) AS hq_lat,
    SUM(lon * complaints) / SUM(complaints) AS hq_lon
FROM street_points;
```

👉 This biases the HQ location toward high-complaint hotspots.

---

## 9. Median Point (Robust to Outliers)

```sql
SELECT 
    percentile_cont(0.5) WITHIN GROUP (ORDER BY "Latitude") AS median_lat,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY "Longitude") AS median_lon
FROM read_csv_auto('311_Elevator_Service_Requests_.csv')
WHERE "Borough" = 'MANHATTAN';
```

👉 This gives the median latitude/longitude, often closer to the densest cluster.
