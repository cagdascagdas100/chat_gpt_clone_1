# Height Difference 1 — revision 6 API/evidence reconciliation

- Slot: `height_difference_1`
- Parcel partition: `1-30761`
- Logical task ID unchanged: `height-difference-1-official-boundary-elevation-samples-20260720`
- Payload revision: `6`
- Active shared-control task was not replaced.
- New or parallel runner: `false`

## Newly resolved execution risks

1. OS Downloads API now supports both documented response modes: HTTP `307` redirect and HTTP `200` JSON download list.
2. The JSON response `url`, `fileName`, `size`, and official `md5` fields are retained; MD5 is verified when supplied and SHA-256 is always calculated.
3. HMLR monthly GML and WFS matches are reconciled. Different non-empty INSPIRE IDs or disjoint bounding boxes produce `HUMAN_REVIEW_SOURCE_CONFLICT` and cannot be promoted.
4. WCS coverage discovery prefers actual `CoverageId` nodes instead of generic service names.
5. HMLR, Environment Agency, and Ordnance Survey source-family jobs can run concurrently with a hard maximum of three workers.
6. Large binaries remain temporary, while a persistent small source-snapshot manifest retains final URLs, byte counts, checksums, selected archive members, geometry and numeric evidence.

## Validation

- Syntax compile: passed
- Self-tests: `12/12`
- Network execution: not performed in this page; existing canonical F portable single shared runner remains required.
- Measured parcel rows written: `0`
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

## Official contracts revalidated

- HMLR INSPIRE monthly files: publication `2026-07-05`; Barnet and Enfield available as GML.
- Environment Agency: persistent WCS `2.0.1` endpoints for 1 m, 2 m and 10 m DTM.
- OS Terrain 50: July 2026, national grid ZIP approximately 157 MB, 10 km tiles, 200 × 200 ASCII cells at 50 m spacing and 0.1 m height precision.

## Remaining blocker

The active shared-control alias remains assigned to `height_difference_2`, which is still pending runner claim. `height_difference_1` therefore remains sequentially queued; its heartbeat and revision 6 official result are not yet present.
