# height_difference_3 — Official source acquisition pipeline ready

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761`)
- Checkpoint target: `7`
- Real measured parcel rows: `0`
- Final ready: `false`

## Completed in this cycle

1. Re-read remote branch HEAD, sequence 6 checkpoint/status and runner state.
2. Confirmed no live lease for this shard. The sibling height-difference task is also unclaimed, so no additional queue or parallel runner was created.
3. Added HMLR monthly local-authority GML download, unique row-context matching, SHA256 provenance and safe archive extraction.
4. Added EA DTM 1m WCS GetCapabilities/DescribeCoverage/GetCoverage retrieval bounded by the matched HMLR polygon.
5. Added exact OS Terrain 50 10km ASCII tile extraction and 200x200 / 50m / southwest-origin validation.
6. Added a six-stage single-runner orchestrator from official-source preparation through website publication.
7. Passed 10/10 local non-production tests. Fixtures and values were not committed or promoted.
8. Published website operation rows 105-136.

## Official source facts refreshed

- HMLR INSPIRE publication: 5 July 2026; local-authority GML files; first-Sunday monthly update.
- EA DTM: approximately 99% England, 1m, 5km GeoTIFF, EPSG:27700, ODN and persistent WCS.
- OS Terrain 50: July 2026, Great Britain, ASCII Grid available; exact 10km tile validation retained.

## Remaining blocker

The canonical 8012 source-backed export for rows `61523-92283` is still absent, so no real candidate may be selected. OS Terrain 50's July 2026 ASCII source archive is also not present in the remote branch. HMLR and EA files can now be automatically prepared once real candidates exist.

Next step: `RUN_005_CANONICAL_DISCOVERY_ON_EXISTING_F_PORTABLE_RUNNER_THEN_RUN_015_AUTO_SOURCE_AND_MEASUREMENT_PIPELINE`.
