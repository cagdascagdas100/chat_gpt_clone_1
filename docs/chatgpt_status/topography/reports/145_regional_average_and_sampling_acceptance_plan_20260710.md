# Topography 145 - Regional Average and Sampling Acceptance Plan

Page key: topography
Layer: Topography / Height Difference
Program output: Elevation Difference from Sea Level, Elevation Difference from Regional Average
Final: false

## Purpose
Prepare the source-backed calculation method required before numeric height-difference values are allowed.

## Inputs
Starter candidate coordinates:

- parcel_2757 / 52213412 / 51.6167362 / -0.1421556
- parcel_2758 / 52213916 / 51.6168592 / -0.1417993
- parcel_2759 / 52040420 / 51.6169525 / -0.1430858

## Official source priority
1. Defra / Environment Agency Data Services Platform survey download: preferred England LiDAR DTM/DSM route where coverage exists.
2. Copernicus DEM GLO-30: official global 30 m DSM fallback if local LiDAR DTM/DSM cannot be sampled.

## Required numeric value gates
Do not write any numeric elevation or height-difference value unless all gates pass:

1. The raster/tile source is downloaded, queried, or accessed from an official source.
2. The exact source name, source path or URL, tile/geocell identifier, and source date/release are recorded.
3. The sampled coordinate is inside the raster/tile coverage.
4. The sampled elevation unit is meters.
5. The vertical datum or elevation reference is recorded when available.
6. The regional average method is recorded and reproducible.
7. The final field remains false until the whole layer meets final criteria.

## Regional average method
For starter rows, regional average should be computed only after source-backed elevation samples exist.

Preferred method:

- Use all verified parcels in the same local authority when enough verified samples exist.
- For the current starter batch, local authority is Barnet from the visible matrix evidence.
- If fewer than 5 verified same-authority samples exist, keep regional_average_elevation_m null and write blocker regional_average_sample_count_too_low.
- If a temporary starter-batch average is needed for QA, write it only as qa_batch_average_elevation_m, not as regional_average_elevation_m.

Formula after enough verified samples exist:

- regional_average_elevation_m = mean(source_backed_elevation_sea_level_m for verified parcels in same regional group)
- elevation_difference_regional_average_m = elevation_sea_level_m - regional_average_elevation_m

## Site visibility requirement
The site must show the current state row-by-row with:

- changed_in_latest_run: true
- display_badge: REGIONAL_AVERAGE_METHOD_READY
- source_file_path: this report
- elevation_sea_level_m: null until official sampling proof exists
- regional_average_elevation_m: null until enough verified samples exist
- elevation_difference_regional_average_m: null until both values exist
- final_ready: false
- fake_data: false

## Status
Regional-average method is ready. Numeric sampling is still pending.
