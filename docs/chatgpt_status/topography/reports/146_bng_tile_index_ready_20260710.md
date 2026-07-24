# Topography 146 - BNG Tile Index Ready

Page key: topography
Layer: Topography / Height Difference
Final: false

## Purpose
Prepare the three coordinate-ready starter parcels for official DEM/LiDAR raster sampling without writing any invented numeric elevation values.

## Source context
Coordinates are from the visible matrix HMLR latitude/longitude evidence already recorded in report 140.
Official terrain source priority remains:
1. Defra / Environment Agency Data Services Platform LiDAR DTM/DSM where coverage exists.
2. Copernicus DEM GLO-30 fallback if LiDAR sampling is unavailable.

## Coordinate transformation
WGS84 latitude/longitude was transformed to British National Grid EPSG:27700 to identify the likely 1 km raster tile area needed by the runner/local sampling process.

## Candidate tile indexes

| parcel_id | parcel_ref | lat | lon | bng_easting_m | bng_northing_m | bng_1km_easting_floor | bng_1km_northing_floor | likely_100km_square | likely_1km_tile |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| parcel_2757 | 52213412 | 51.6167362 | -0.1421556 | 528723.664 | 192513.392 | 528000 | 192000 | TQ | TQ2892 |
| parcel_2758 | 52213916 | 51.6168592 | -0.1417993 | 528747.982 | 192527.698 | 528000 | 192000 | TQ | TQ2892 |
| parcel_2759 | 52040420 | 51.6169525 | -0.1430858 | 528658.656 | 192535.809 | 528000 | 192000 | TQ | TQ2892 |

## Sampling implication
All three starter parcels fall in the same likely 1 km BNG tile area: TQ2892.
The runner/local sampling process should first query or download the official LiDAR/DEM raster tile covering BNG 528000-529000 / 192000-193000.

## Data integrity rules
- Numeric elevation remains null until an official raster/tile sample is actually read.
- Regional average remains null until enough verified same-authority samples are available.
- final_ready=false.
- fake_data=false.
