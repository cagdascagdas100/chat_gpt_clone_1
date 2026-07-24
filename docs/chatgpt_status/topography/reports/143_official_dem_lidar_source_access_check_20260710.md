# Topography 143 - Official DEM/LiDAR Source Access Check

Page key: topography
Layer: Topography / Height Difference
Branch: codex/aays-single-runner-v5-20260706
Final: false

## Purpose
Continue the Height Difference workflow after coordinate visibility was fixed for parcel_2757, parcel_2758 and parcel_2759.

## Internet source access checked

### 1. Defra / Environment Agency Data Services Platform
Status: reachable source portal identified.
Role: preferred England LiDAR DTM/DSM survey/download source where coverage exists.
Notes: The service exposes a Defra Survey Data Download area and links to Data Services Platform APIs. Actual elevation values still require the runner/local process to query the relevant tile/survey and sample raster values at the three centroids.

### 2. Copernicus DEM GLO-30
Status: official fallback source identified.
Role: global 30 m DSM fallback if England LiDAR DTM/DSM is unavailable or not sampled.
Notes: Copernicus DEM provides GLO-30 and GLO-90 instances; GLO-30 is a DSM. It is not a direct replacement for LiDAR DTM, and values must be sampled from source-backed raster/API data before being written.

## Candidate coordinates
- parcel_2757 / 52213412 / 51.6167362 / -0.1421556
- parcel_2758 / 52213916 / 51.6168592 / -0.1417993
- parcel_2759 / 52040420 / 51.6169525 / -0.1430858

## Data integrity decision
No numeric elevation, regional average, or height difference was written in this step.

Reason:
- Defra/EA and Copernicus source portals are identified.
- Actual raster/tile/API sampling proof is still missing.
- Regional-average method is still pending.

## Next action
The runner must perform source-backed DEM/LiDAR raster/tile sampling for the three candidate centroids and then write only sampled numeric values with source path/URL, source date, matching method and calculation explanation.

Safety flags:
- final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
