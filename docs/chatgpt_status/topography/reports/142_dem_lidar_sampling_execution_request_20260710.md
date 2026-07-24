# Topography 142 - DEM/LiDAR Sampling Execution Request

Page key: topography
Layer: Topography / Height Difference
Final: false

## Purpose
Continue from coordinate visibility fix and source discovery. The three starter parcels now have visible coordinates, but no numeric height or height-difference values may be written until actual DEM/LiDAR raster or tile sampling is performed.

## Input candidates

| parcel_id | parcel_ref | centroid_lat | centroid_lon |
|---|---:|---:|---:|
| parcel_2757 | 52213412 | 51.6167362 | -0.1421556 |
| parcel_2758 | 52213916 | 51.6168592 | -0.1417993 |
| parcel_2759 | 52040420 | 51.6169525 | -0.1430858 |

## Required source priority

1. Defra / Environment Agency Data Services Platform LiDAR DTM or DSM where coverage exists.
2. Copernicus DEM GLO-30 fallback if LiDAR sampling is unavailable.
3. Do not use unofficial or unverifiable elevation values for product rows.

## Required runner work

1. Query the official DEM/LiDAR tile or raster source for each centroid.
2. Record the exact tile/product name, dataset name, acquisition/product date if available, and source path or URL.
3. Sample elevation at each centroid.
4. Compute a regional average only after a reproducible method is defined, for example a fixed local buffer or matrix-region candidate set.
5. Write height-difference only after both sampled elevation and regional average are available.
6. Update site-visible latest_changes.json row by row.

## Strict data rules

- Do not invent elevation.
- Do not invent regional average.
- Do not invent height difference.
- Keep final_ready=false.
- Keep fake_data=false.
- Keep db_write=false.
- Keep migration=false.
- Keep production_deploy=false.

## Current result

Sampling request prepared and site rows marked as DEM/LiDAR tile sampling queued. Numeric height fields remain null.
