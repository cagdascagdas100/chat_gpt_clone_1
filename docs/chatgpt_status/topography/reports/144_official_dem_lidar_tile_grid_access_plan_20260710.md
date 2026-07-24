# Topography 144 - Official DEM/LiDAR Tile Grid Access Plan

Page key: topography
Layer: Topography / Height Difference
Final: false

## Purpose
Continue Height Difference work without inventing numeric elevation. This step records the next source-backed sampling route for parcel_2757, parcel_2758 and parcel_2759.

## Candidate coordinates
- parcel_2757 / 52213412 / lat 51.6167362 / lon -0.1421556
- parcel_2758 / 52213916 / lat 51.6168592 / lon -0.1417993
- parcel_2759 / 52040420 / lat 51.6169525 / lon -0.1430858

## Official source route
1. Preferred source: Defra / Environment Agency Data Services Platform Survey Data Download.
   - Role: discover and download England LiDAR DTM/DSM coverage/tile for the candidate coordinates where coverage exists.
   - Required next operation: query/download the relevant LiDAR tile, then raster sample the centroid.
2. Fallback source: Copernicus DEM GLO-30.
   - Role: global 30 m DSM fallback where LiDAR tile sampling is not available.
   - Required next operation: resolve the 1 degree geocell/product package and sample the raster cell for the centroid.

## Data integrity rules
- Do not write numeric elevation until actual raster/tile sampling proof exists.
- Do not write regional average until a reproducible local/regional averaging window is defined and sampled.
- Do not write height difference until both elevation_sea_level_m and regional_average_elevation_m are source-backed.
- Keep final_ready=false.
- Keep fake_data=false, db_write=false, migration=false, production_deploy=false.

## Site update requirement
Write current visible rows as TILE_GRID_ACCESS_PLAN_READY, with null height fields and source references to this report.

## Acceptance for next step
The next successful step must produce at least one sampled numeric elevation value with:
- source name
- source access path or URL
- tile/product identifier
- sampling method
- sampled elevation value in metres
- source date or product release
- accuracy_score_4 not lower than 3/4 if the source is official and reproducible
