# Topography 141 - DEM/LiDAR Source Discovery Report

Page key: topography
Layer: Topography / Height Difference
Branch: codex/aays-single-runner-v5-20260706
Final: false

## Input candidates

- parcel_2757 / parcel_ref 52213412 / centroid 51.6167362, -0.1421556
- parcel_2758 / parcel_ref 52213916 / centroid 51.6168592, -0.1417993
- parcel_2759 / parcel_ref 52040420 / centroid 51.6169525, -0.1430858

## Official source candidates checked

### Source 1 - Defra / Environment Agency Data Services Platform

Status: source portal confirmed; raster/tile extraction still required locally.

Evidence:
- Defra Data Services Platform survey download page is available at environment.data.gov.uk/survey.
- The platform exposes survey/data download and API entry points.
- Content is under Open Government Licence v3.0 unless otherwise stated.

Use for AAYS:
- First priority for England local terrain because Environment Agency/Defra LiDAR DTM is the preferred high-resolution terrain source where coverage exists.
- Runner must query/download the appropriate LiDAR DTM/DSM tile for each centroid and sample actual raster elevation.

### Source 2 - Copernicus DEM

Status: official fallback source confirmed; actual tile/API extraction still required locally.

Evidence:
- Copernicus Data Space describes Copernicus DEM as a DSM provided at 90m, 30m, and 10m instances.
- GLO-30 provides global 30m coverage.
- General public users can view and download GLO-30/GLO-90 instances.
- Copernicus DEM is accessible through Copernicus Browser or API.
- GLO-30/GLO-90 are available worldwide with a free license.
- Vertical unit is meters and vertical CRS is EGM2008.

Use for AAYS:
- Fallback when Environment Agency/Defra LiDAR DTM is unavailable or not accessible.
- Because Copernicus DEM is DSM, it must be labelled as surface-model fallback, not as bare-earth LiDAR DTM.

## Current result

No elevation value has been written.
No regional average has been written.
No height difference has been written.

Reason:
Actual raster/DEM sampling has not yet been completed. Source discovery is complete enough to start the runner extraction task, but writing numeric elevation without tile sampling would be fake.

## Required next runner action

For each parcel:
1. Query Defra/Environment Agency LiDAR DTM coverage for the centroid.
2. Download or access the matching raster/tile.
3. Sample elevation at centroid.
4. If local LiDAR DTM is unavailable, query Copernicus DEM GLO-30 as fallback.
5. Compute regional average only from a documented local buffer or comparison group.
6. Write per-row source URL/path, source date, sampling method, and accuracy.

## Integrity rules

- Do not invent elevation values.
- Do not invent regional averages.
- Do not invent height difference.
- Keep final_ready=false.
- Keep fake_data=false.
- Keep db_write=false, migration=false, production_deploy=false.

## Status

source_discovery_complete=true
verified_height_rows=0
height_difference_values_written=false
final_ready=false
fake_data=false
