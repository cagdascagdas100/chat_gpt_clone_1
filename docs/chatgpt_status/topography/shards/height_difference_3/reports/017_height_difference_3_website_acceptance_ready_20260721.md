# height_difference_3 — website publication and port 8012 acceptance ready

## Scope

- Slot: `height_difference_3`
- Rows: `61523-92283` (`30,761` rows)
- Canonical source: `security.geojson`, `92,283` features, Git blob `8afd1d2bac414cf0f6b9484014e7878a4ceff877`
- Existing shared F runner only; no queue, lease, owner, heartbeat, new runner, or parallel runner was created.

## Work completed

1. Audited the measurement and publication schemas used by `009` and `010`.
2. Confirmed that pipeline outputs were written only to the runner output directory and that website example files retained a stale blocked contract.
3. Added `031_publish_verify_three_examples_port8012.py`.
4. Added `032_run_full_pipeline_and_website_acceptance.py` and routed the existing `012` task through it.
5. Updated the empty website JSON/GeoJSON contracts without inserting parcel values.
6. Added fail-closed validation for exactly rows `61523`, `61524`, and `61525`.
7. Required `HIGH` or `MEDIUM_HIGH` confidence, at least four EA cells, no nearest fill, and a maximum EA/OS difference of `8 m`.
8. Required SHA-256 evidence for every EA and Terrain 50 raster used.
9. Required exact JSON/GeoJSON identity and atomic website copies.
10. Required exact JSON, GeoJSON, and runtime readback through port `8012`.
11. Added six acceptance rows to the runtime only after successful HTTP readback.
12. Corrected the combined-runtime zero-count issue by normalizing counts only after full artefact validation; conflicting non-zero counts fail closed.
13. Passed `14/14` new tests; cumulative result is `169/169`.

## Official source refresh

- HM Land Registry INSPIRE polygons were published on `5 July 2026`; files are monthly local-authority GMLs, and a boundary polygon may appear in both authority files.
- Environment Agency LIDAR Composite DTM is approximately `99%` England coverage at `1 m`, EPSG:27700, metres ODN, with source-survey vertical accuracy of approximately `±15 cm RMSE`.
- OS Terrain 50 is a July-updated Great Britain DTM supplied as `10 km` tiles; ASCII grids contain `200 × 200` cells at `50 m`, and the national grid supply contains `2,858` tiles in `55` 100 km folders.

## Real result state

All real counters remain zero. No parcel ID, boundary, elevation, geometry, or example value was fabricated or promoted.

## Next required step

`RUN_032_FULL_PIPELINE_THEN_ATOMIC_WEBSITE_PUBLICATION_AND_PORT_8012_ACCEPTANCE_ON_EXISTING_F_RUNNER`

The existing F runner must execute the full chain and commit/push/read back the real outputs. `final_ready=false` remains mandatory.
