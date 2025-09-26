# Section 6: Setting Up Duck Lake with S3 and MotherDuck

## Step 1. Create an S3 Bucket
1. In the AWS console, search for **S3** and open the service.  
2. Click **Create bucket**.  
3. Fill out:  
   - **Bucket name**: Must be globally unique (e.g., `ducklake-andreas-001`)  
   - **AWS Region**: Pick the region you want (e.g., `us-east-1` or `eu-central-1`)  
   - **Block Public Access**: Keep all checkboxes enabled (recommended)  
4. Leave other defaults unless you have special needs (like encryption, versioning).  
5. Click **Create bucket**.  

---

## Step 2. Create the IAM User
1. Go to **IAM → Users → Add users**.  
2. Enter a username (e.g., `ducklake-user`).  
3. On the **Set permissions** screen, either:  
   - Attach **AmazonS3FullAccess** directly (for testing), or  
   - Create a custom policy scoped to your bucket (recommended).  

👉 At this point, the user exists, but has no access keys yet.  

### Step 2.1. Attach Permissions to the User
- In the IAM creation flow, choose **Attach policies directly**.  
- Start with **AmazonS3FullAccess** for testing.  
- Later, restrict access to just your Duck Lake bucket. Example custom policy:  

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": [
        "arn:aws:s3:::ducklake-andreas-001",
        "arn:aws:s3:::ducklake-andreas-001/*"
      ]
    }
  ]
}
```

Attach this policy to the user.  

---

## Step 3. Create Access Keys for the User
1. Go to **IAM → Users → ducklake-user**.  
2. Open the **Security credentials** tab.  
3. Scroll down to **Access keys** → Click **Create access key**.  
4. Select **Application running outside AWS**.  
5. AWS generates:  
   - **Access Key ID**  
   - **Secret Access Key** (shown only once — save securely).  

---

## Step 4. Collect Connection Info
You now have:  
- Access Key ID ✅  
- Secret Access Key ✅  
- Region (e.g., `us-east-1`) ✅  
- Endpoint (`https://s3.<region>.amazonaws.com`) ✅  

That’s all DuckDB/MotherDuck needs to talk to your bucket.  

---

## Step 5. Set Credentials
- Go to **MotherDuck → Secrets**  
- Set secret `ducklake` and test it.  

---

## Step 6. Create Database
```sql
CREATE DATABASE my_ducklake (
  TYPE DUCKLAKE,
  DATA_PATH 's3://ducklake-andreas-001/nyc/'
);
```

---

## Step 7. Copy Table into Duck Lake
```sql
CREATE TABLE my_ducklake.main.clean_requests AS
SELECT *
FROM course_demo.main.clean_requests;
```

---

## Step 8. Query Yearly Complaints
```sql
SELECT EXTRACT(YEAR FROM created_date) AS year, COUNT(*) AS complaints
FROM my_ducklake.main.clean_requests
GROUP BY 1
ORDER BY 1;
```

---

## Step 9. Insert a New Record
```sql
INSERT INTO my_ducklake.main.clean_requests (
  unique_key,
  created_date,
  closed_date,
  agency,
  agency_name,
  complaint_type,
  descriptor,
  location_type,
  incident_zip,
  incident_address,
  street_name,
  cross_street_1,
  cross_street_2,
  intersection_street_1,
  intersection_street_2,
  address_type,
  city,
  landmark,
  facility_type,
  status,
  due_date,
  resolution_description,
  resolution_action_updated_date,
  community_board,
  bbl,
  borough,
  x_coordinate_state_plane_,
  y_coordinate_state_plane_,
  open_data_channel_type,
  park_facility_name,
  park_borough,
  vehicle_type,
  taxi_company_borough,
  taxi_pick_up_location,
  bridge_highway_name,
  bridge_highway_direction,
  road_ramp,
  bridge_highway_segment,
  latitude,
  longitude,
  location,
  closed_in_days
)
VALUES (
  90000001,
  TIMESTAMP '2025-09-08 09:15:00',
  NULL,
  'HPD',
  'Department of Housing Preservation',
  'Elevator',
  'Elevator Stuck Between Floors',
  'Residential Building',
  '10001',
  '350 5TH AVE',
  '5TH AVE',
  '33RD ST',
  '34TH ST',
  NULL,
  NULL,
  'ADDRESS',
  'NEW YORK',
  'Empire State Building',
  'Residential',
  'Open',
  TIMESTAMP '2025-09-10 23:59:00',
  NULL,
  NULL,
  '05 MANHATTAN CB5',
  '1015560001',
  'MANHATTAN',
  985000,
  211000,
  'MOBILE',
  'Central Park',
  'MANHATTAN',
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  NULL,
  40.748817,
  -73.985428,
  '(40.748817, -73.985428)',
  NULL
);
```

---

## Step 10. Verify Insert
```sql
SELECT EXTRACT(YEAR FROM created_date) AS year, COUNT(*) AS complaints
FROM my_ducklake.main.clean_requests
GROUP BY 1
ORDER BY 1;
```

---

## Step 11. Clean Up
```sql
DROP TABLE my_ducklake.main.clean_requests;
```
