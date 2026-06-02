# Estate024 Lat/Lon Header Value Probe

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

source_file=C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\05_london_bbox_sample_parcels_with_air_quality.csv
source_exists=True
columns=parcel_id|parcel_ref|local_authority|lon|lat|area_m2|airQualityPercent|pollutionRiskPercent|confidencePercent|airQualityGrade|airQualityNearestName|airQualityNearestDistanceKm
sample_rows=20

Next:
- If lat/lon values are numeric, run exact-header bbox join.
- If lat/lon values are blank/non-numeric, true 100 remains blocked by missing coordinate values.
