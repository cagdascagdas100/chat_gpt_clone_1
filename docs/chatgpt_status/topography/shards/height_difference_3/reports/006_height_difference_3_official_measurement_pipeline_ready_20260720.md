# height_difference_3 — official measurement pipeline readiness

- Slot: `height_difference_3`
- Parcel range: `61523-92283`
- Canonical rows expected: `30,761`
- Date: `2026-07-20`
- Final ready: `false`

## Completed in this checkpoint

1. Added an HMLR INSPIRE matcher that keeps calculations in EPSG:27700.
2. Exact official identifier equality is preferred; unique point-in-polygon is the only fallback.
3. Ambiguous matches and nearest-polygon assignment fail closed.
4. Added an EA DTM 1m polygon sampler that records minimum, maximum, median, quartiles, IQR and Q05/Q95.
5. Defined parcel height difference as the robust EA DTM polygon `Q95 - Q05` range.
6. Added a minimum four valid EA-cell publication gate.
7. Added an OS Terrain 50 independent centroid-cell crosscheck.
8. Added an 8 m maximum cross-source publication threshold and a stricter 4 m HIGH-confidence threshold.
9. Added a website JSON/GeoJSON publisher that accepts only HIGH or MEDIUM_HIGH rows.
10. Added a single-runner orchestrator for boundary match, sampling and website publication.
11. Published an official technical source contract and immutable self-test evidence.

## Self-test evidence

Ten tests passed:

- all four scripts compiled;
- three-candidate HMLR positive path;
- ambiguous HMLR polygon fail-closed path;
- three-candidate EA and OS sampling positive path;
- positive cross-source threshold path;
- deliberately mismatched OS crosscheck fail-closed path;
- positive website JSON/GeoJSON publication path;
- empty website publication fail-closed path;
- positive single-runner orchestration path;
- boundary failure stops later orchestration stages.

All fixtures were local non-production fixtures. No fixture, identifier, coordinate, elevation or polygon was promoted to product data.

## Official-source method

- Geometry: HM Land Registry INSPIRE Index Polygons, current monthly GML, EPSG:27700.
- Primary numeric source: Environment Agency LIDAR Composite DTM 1 m.
- Independent numeric check: OS Terrain 50, 50 m grid supplied as 200 by 200 cells in 10 km tiles.
- Coordinate fallback: OS Open UPRN only when an exact canonical UPRN exists.
- Diagnostic only: Copernicus GLO-30.

## Current real blocker

The remote branch and accessible website artifacts still do not expose the canonical rows `61523-92283`, their real parcel identifiers, or source-backed coordinates/UPRNs. Therefore:

- canonical shard rows exported: `0`
- real parcel candidates: `0`
- current HMLR polygon matches: `0`
- EA DTM official samples: `0`
- OS Terrain 50 crosschecks: `0`
- verified website examples: `0`

No measured value is claimed.

## Next verified step

Run `005_discover_export_and_prepare_three.py` on the existing F portable runner. After it emits three real rows, run `011_execute_three_real_parcel_measurements.py` with current HMLR GML, EA DTM 1 m and OS Terrain 50 files.

## Safety state

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
