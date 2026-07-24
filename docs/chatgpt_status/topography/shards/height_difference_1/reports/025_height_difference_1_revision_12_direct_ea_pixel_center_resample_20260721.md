# Height Difference 1 revision 12 direct EA pixel-center resample

## Result

Revision 12 is prepared on the same logical task and idempotency key. Runtime execution on the canonical F portable shared runner has not occurred.

## New direct measurement path

- Run the existing official HMLR/geometry/datum upstream gate.
- Read each accepted official HMLR Polygon or MultiPolygon in EPSG:27700.
- Discover the current EA DTM 1 m WCS coverage through WCS 2.0.1 GetCapabilities.
- Hash GetCapabilities and DescribeCoverage responses.
- Request an EPSG:27700 GeoTIFF for each official polygon extent and hash the GeoTIFF.
- Apply `rasterio.mask(..., crop=True, all_touched=False, filled=False)`.
- Recalculate every selected pixel centre and require the official HMLR polygon to cover it.
- Record deterministic SHA-256 values for the selected-pixel mask and selected pixel-centre list.
- Calculate minimum, maximum, median, Q1, Q3, IQR and maximum-minus-minimum height difference.
- Re-run revision 10 HMLR/EA/OS evidence and conflict gates and revision 11 sampling-provenance gate.

## Fail-closed behaviour

- A direct EA WCS sampling error is not treated as valid `NO_DATA`.
- Any direct sampling error produces `BLOCKED_DIRECT_EA_PIXEL_CENTER_RESAMPLE` and a non-zero exit code.
- Centroid fallback is forbidden.
- Fewer than three valid pixels, wrong raster CRS, an outside selected pixel centre, malformed geometry, source hash failure or integrity mismatch blocks promotion.
- OS Terrain 50 remains an independent absolute-elevation and ODN crosscheck, not the parcel range source.
- EA/OS absolute difference above 8 m remains human-review-only.

## Validation

- Source-level and synthetic GeoTIFF assertions: `54/54`.
- Synthetic raster selected pixels: `16`.
- Synthetic expected height difference: `33.0 m`.
- Real network execution: `false`; canonical F portable single shared runner is required.

## Safety

- Same logical task: `height-difference-1-official-boundary-elevation-samples-20260720`.
- Same idempotency key: `height_difference_1-004-20260720`.
- New runner: `false`.
- Parallel runner: `false`.
- Shared control override: `false`.
- `final_ready=false`.
- `product_final_ready=false`.
- `fake_data=false`.
- `db_write=false`.
- `migration=false`.
- `production_deploy=false`.
