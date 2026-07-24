# height_difference_3 — Streaming Canonical Extraction and Official OS API Readiness

## Scope

- Slot: `height_difference_3`
- Parcel rows: `61523-92283`
- Expected shard count: `30,761`
- Canonical registry: `92,283`
- New runner created: `false`
- Parallel task created: `false`
- Queue submitted: `false`

## Progress

The committed `security.geojson` remains the resolved canonical carrier. The previous full-memory extractor has been supplemented with a streaming parser that validates the complete explicit registry while retaining only the target shard. Feature order is never used as parcel identity.

The OS Terrain 50 input blocker was reduced from a browser HAR/manual URL requirement to the official OS Downloads API endpoint for product `Terrain50`, area `GB`, format `ASCII Grid and GML (Grid)`. The downloader records the resolved URL, response metadata, byte size and SHA-256, and validates safe ZIP paths, national ASCII inventory and sample `200 x 200 / 50 m` headers.

A one-command orchestrator now connects:

1. streaming canonical extraction,
2. first-three explicit candidate preparation,
3. official Terrain 50 API acquisition,
4. current HMLR + EA DTM + Terrain 50 measurement and verified web publication.

Every later stage stops after the first failed gate.

## Validation

- Streaming extractor: `5/5` tests passed.
- Official Terrain 50 API acquisition: `7/7` tests passed.
- Full orchestrator: `5/5` tests passed.
- Total new tests: `17/17` passed.
- Cumulative tests: `56/56` passed.
- Test fixtures committed: `false`.
- Test values promoted: `false`.

## Real data state

- Resolved canonical sources: `1`
- Canonical source features: `92,283`
- Real shard rows exported: `0`
- Real candidates selected: `0`
- HMLR boundary matches: `0`
- EA DTM numeric rows: `0`
- OS Terrain 50 numeric rows: `0`
- Verified website examples: `0`

No real row count or measurement metric was increased because the existing F runner has not yet executed the new orchestrator against the committed 61 MB canonical source.

## First unverified step

`RUN_022_STREAM_EXTRACT_OFFICIAL_OS_API_DOWNLOAD_THEN_HMLR_EA_OS_MEASURE_AND_PUBLISH`

## Blockers

1. Existing F runner must execute `022_execute_canonical_api_measurement_pipeline.py` against the committed `security.geojson`.
2. Official OS, HMLR and Environment Agency network calls must complete on that runner.
3. Boundary, EA DTM and Terrain 50 evidence must all pass before any parcel value is published.

## Safety

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
