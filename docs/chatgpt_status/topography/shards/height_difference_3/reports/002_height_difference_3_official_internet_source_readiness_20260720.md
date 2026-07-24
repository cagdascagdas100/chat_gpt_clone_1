# height_difference_3 — Official Internet Source Readiness

- SLOT_ID: `height_difference_3`
- Parcel partition: `61523-92283`
- Remote HEAD read before this cycle: `362036a030bf304e4426498f809edf3816863dfc`
- Checked at: `2026-07-20T16:22:25Z`
- Result: `SOURCE_ENDPOINTS_VERIFIED; PARCEL SAMPLING BLOCKED BY SHARD COORDINATE/GEOMETRY INVENTORY`

## Verified source candidates

1. **HM Land Registry INSPIRE Index Polygons**
   - Official monthly local-authority GML download page is available.
   - The July 2026 publication is visible.
   - Intended role: real parcel boundary candidate.
   - Source confidence: `99/100`.
   - Not yet promoted: no shard parcel-to-local-authority mapping or downloaded GML file.

2. **Environment Agency LiDAR Time Stamped Point Cloud**
   - Official dataset and area-download workflow are available.
   - Data is supplied in 5 km LAZ tiles in EPSG:27700 where surveyed.
   - Published vertical accuracy: `+/-15 cm RMSE`.
   - Intended role: primary official numeric elevation.
   - Source confidence: `99/100`.
   - Not yet sampled: shard coordinates or polygons are not exposed.

3. **OS Terrain 50**
   - Official OpenData download page is available.
   - Version date observed: July 2026.
   - Great Britain coverage, 50 m ASCII/GML grid, British National Grid.
   - Intended role: official national numeric elevation source or EA LiDAR coverage fallback.
   - Source confidence: `98/100`.
   - Not yet sampled: required 10 km tiles cannot be selected without shard coordinates.

4. **Copernicus DEM GLO-30**
   - Official Copernicus Data Space access documentation is available.
   - Global 30 m DSM where public GLO-30 is available; GLO-90 may fill gaps.
   - Intended role: secondary crosscheck only, not sole UK bare-earth validation.
   - Source confidence: `92/100`.

## Progress rows published to the website

Web artifact:

`england_map_web/data/aays_18_slots/height_difference_3/official_source_progress_latest.json`

Published operation rows:

1. remote HEAD read — PASS
2. slot checkpoint read — PASS
3. HMLR boundary source discovery — PASS
4. EA LiDAR source discovery — PASS
5. OS Terrain 50 source discovery — PASS
6. Copernicus secondary-source discovery — PASS
7. shard coordinate inventory — BLOCKED
8. measured-value publication — NOT RUN

## Evidence gate

No numeric parcel value was produced. The existing public CopDEM examples belong to `parcel_2757` through `parcel_2759`; they are outside this shard and were not reused for parcel IDs `61523-92283`.

- measured parcel rows: `0`
- real geometry rows: `0`
- official numeric samples: `0`
- inferred values: `0`

## Current blocker

`CANONICAL_SHARD_61523_92283_COORDINATES_OR_POLYGONS_NOT_EXPOSED; HMLR_LOCAL_AUTHORITY_GML_NOT_DOWNLOADED; EA_LIDAR_OR_OS_TERRAIN50_TILE_NOT_DOWNLOADED; SECOND_OFFICIAL_NUMERIC_CROSSCHECK_NOT_SAMPLED`

## Next step

`RESOLVE_CANONICAL_SHARD_COORDINATES_AND_LOCAL_AUTHORITIES_THEN_DOWNLOAD_HMLR_GML_AND_EA_LIDAR_OR_OS_TERRAIN50_TILES`

This next operation must remain on the existing single shared runner. Source acquisition lanes may be grouped inside one task, but no second runner or competing shard claim is permitted.

## Metrics

- official candidates verified: `4`
- high-confidence sources (>=95): `3`
- operation rows completed or gated: `8/8`
- historical product completion: `78%`
- product percentage increase: `0` because no new parcel-bound measurement passed the evidence gate
- source-readiness percentage: `100%` for the four targeted source endpoints

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
