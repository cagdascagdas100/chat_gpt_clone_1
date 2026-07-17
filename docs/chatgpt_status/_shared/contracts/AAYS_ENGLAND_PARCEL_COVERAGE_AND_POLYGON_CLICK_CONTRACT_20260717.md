# AAYS England Parcel Coverage and Polygon Click Contract

## Authority

- The legacy London point layer has 99,783 point records.
- The current verified program matrix has 92,283 canonical parcel records.
- Neither count is the complete England parcel universe.
- Complete England status requires a deduplicated row-level parcel registry built from the official regional parcel sources. A PMTiles coverage archive or authority count alone is not a row registry.

## Fixed operational row contract

- `canonical_target_row_count=92283`
- `canonical_unique_key=parcel_id`
- Gas emissions, security, height difference and parcel label outputs must each contain exactly the same 92,283 unique parcel IDs in the same deterministic order.
- Row coverage and verified-value coverage are separate. A 92,283-row file is not complete when values lack real source evidence.
- The 92,283 set is the current canonical AAYS program set. Do not describe it as complete England cadastral coverage until a verified national row registry replaces it.

## Required workflow

1. Reconcile the 99,783 legacy points with the 92,283 canonical rows using official parcel identifiers first (`hmlr_inspire_id`, national cadastral reference, HMLR row ID), then point-in-polygon containment.
2. Record matched, unmatched and duplicate counts. Do not silently discard rows.
3. Build or consume one authoritative England parcel registry. Every thematic output must use exactly one row per registry parcel ID.
4. Keep rows with unavailable thematic values and set `data_status=no_data`. Row coverage and verified-value coverage are separate metrics.
5. Never copy the nearest point to a neighbouring parcel merely to fill a value.
6. A polygon click must resolve a thematic record only when the thematic point is inside that polygon or an official parcel ID matches.
7. `completed`, `100%` and `final_ready=true` require a deduplicated England registry, equal row counts for all four outputs, real source provenance and browser proof.

## Join priority

1. Exact official ID: INSPIRE ID or national cadastral reference.
2. Exact HMLR row ID when its source version is verified.
3. Source point contained by the parcel polygon.
4. Source area/grid containing the parcel centroid or intersecting the parcel under a documented rule.

Do not use arbitrary nearest-point assignment. When multiple source records match, write a conflict record and keep the value pending until the documented tie-break is verified.

## Common output fields

`parcel_registry_id`, official parcel ID fields, longitude, latitude, authority, source, source_date, spatial_join_method, data_status, confidence, and the page-specific value fields.

## Page-specific spatial rules

- Gas emissions: assign an official area/grid value to parcels contained by that source geography; preserve source geography ID and resolution.
- Security: join official LSOA or equivalent public-safety geography by parcel centroid or polygon intersection; preserve geography ID and date.
- Height difference: sample the verified DEM at the parcel centroid or calculate documented polygon statistics; preserve DEM source and resolution.
- Parcel label: use official parcel/land-use identifiers or a verified polygon overlay. Do not infer a label from an unrelated nearest point.

## Safety

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false` until all acceptance evidence exists.
