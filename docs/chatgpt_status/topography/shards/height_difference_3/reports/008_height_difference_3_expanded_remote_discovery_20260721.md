# Height Difference 3 — Expanded Remote Discovery

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761` rows)
- Checkpoint target: `8`
- Final ready: `false`

## Completed

1. Re-read remote branch HEAD and checkpoint sequence 7.
2. Confirmed GitHub code search indexing is disabled for the repository; previous empty search results were not treated as proof that files do not exist.
3. Added read-only GitHub REST commit-tree and blob discovery for CSV, JSON, JSONL, NDJSON and GeoJSON sources.
4. Added strict canonical validation: explicit row numbers, complete unique shard range, parcel IDs, authority/data status, and source-backed coordinates/geometry/UPRN.
5. Added manifest-path traversal and blob-SHA provenance.
6. Added OS Terrain 50 browser HAR/direct download URL capture and validation.
7. Added HTTPS/host, maximum size, HTML rejection, ZIP signature, safe-path and ASCII-grid gates.
8. Added expanded existing-runner orchestrator linking remote discovery to the previously published official measurement pipeline.
9. Passed 11 of 11 compile, positive and fail-closed tests. Test fixtures were not committed or promoted.

## Official source refresh

OS Terrain 50 remains a free OpenData product with a July 2026 version. Official documentation states that gridded ASCII/GML supply covers Great Britain as 2,858 10 km tiles arranged in 55 100 km folders; the full compressed grid supply is approximately 157 MB. The Data Hub download UI is JavaScript-driven, so the real generated HTTPS download URL or a browser HAR is required for deterministic unattended retrieval.

## Current evidence

- Official/public source candidates: `5`
- High-confidence source candidates: `4`
- Source contracts: `9`
- Automation scripts ready: `15`
- Single-runner contracts: `5`
- Self-tests: `31/31`
- Canonical shard rows exported: `0`
- Real parcel candidates: `0`
- Official numeric sample rows: `0`
- Verified website examples: `0`

## Blockers

- `CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED`
- `REAL_SHARD_PARCEL_CANDIDATES_REQUIRED`
- `OS_TERRAIN50_LIVE_DOWNLOAD_URL_OR_ARCHIVE_REQUIRED`
- `OFFICIAL_CROSSCHECKED_REAL_ROWS_REQUIRED`

## Next step

Run local/8012 discovery and the new GitHub-tree fallback on the existing F portable runner. Capture the official Terrain 50 download request as HAR or direct HTTPS URL, validate the archive, then continue through the existing source acquisition and measurement pipeline.

Safety flags remain false: fake data, database write, migration and production deployment.
