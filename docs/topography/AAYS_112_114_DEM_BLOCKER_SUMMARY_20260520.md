# AAYS 112-114 DEM Blocker Summary

Generated: 2026-05-20

## Completed tasks

- AAYS 112 parcel elevation evidence export ran successfully at runner level.
- AAYS 112 produced JSON, XLSX, CSV and report outputs.
- AAYS 112 did not sample real elevation because no usable DEM/DTM raster was available under the scanned local data paths.
- AAYS 113 broad raster inventory completed and found raster files, but the visible candidates were projection/geoid/grid-shift files, not terrain DEM/DTM rasters.
- AAYS 114 DEM candidate classifier completed with status `completed_no_true_dem_found` and `possible_dem_count=0`.

## Final blocker

A real terrain DEM/DTM raster is not currently available to the local runner. Elevation values must not be fabricated.

## Required next input

Place or mount an official terrain raster under one of these local folders:

- `E:\AAYS_DATA\elevation`
- `E:\AAYS_DATA\terrain`
- `E:\AAYS_DATA\dem`

Recommended raster formats:

- GeoTIFF `.tif` or `.tiff`
- ASCII grid `.asc`
- VRT `.vrt` only if all referenced raster tiles are accessible

## After DEM is available

Rerun:

`aays_112_parcel_elevation_evidence_export_20260519.ps1`

Expected success indicators:

- `elevation_sampled=true`
- `rows_written > 0`
- populated `elevation_centroid_m_asl`
- updated XLSX, CSV, JSON and report outputs

## Safety

- No DB writes were required.
- No production deploy was required.
- No fake elevation values were produced.
