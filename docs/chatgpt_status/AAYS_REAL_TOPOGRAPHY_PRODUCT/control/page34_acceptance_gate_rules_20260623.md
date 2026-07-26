# Page34 Acceptance Gate Rules

PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
LAYER=Distance to Nearby Property Types

## Source policy

Allowed sources only:
- Existing repository files.
- Existing local files on C, D, or F disk.
- Open and free internet sources.

Disallowed sources:
- Paid sources.
- Contact-required sources.
- Invitation-only sources.
- Login-required sources.

## Data integrity policy

Do not create fake parcel geometry.
Do not create fake parcel_id.
Do not create fake points.
Do not create fake polygons.

If open data is not parcel-level, report the layer using one of these states:
- POSTCODE_LEVEL_ONLY
- POINT_LEVEL_ONLY
- OPEN_DATA_PROXY_READY
- DATA_GATE_BLOCKED

## Final acceptance gate

FINAL_READY_CONFIRMED and PRODUCT_PROGRESS_ESTIMATE=100 are allowed only when all evidence exists in GitHub reports:
- live map visibility confirmed
- non-empty feature set confirmed
- popup or right-panel required fields confirmed
- geometry accuracy confirmed

Until all four are confirmed, keep:
FINAL_STATUS=BLOCKED_RUNTIME_ACCEPTANCE_NOT_CONFIRMED
PRODUCTION_COMPLETE=false
