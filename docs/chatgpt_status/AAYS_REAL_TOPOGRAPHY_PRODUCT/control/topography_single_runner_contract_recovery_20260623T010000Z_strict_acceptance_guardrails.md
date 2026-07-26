# Strict acceptance guardrails for AAYS real topography product

TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT
BRANCH=main
STATUS=ADDITIVE_ACCEPTANCE_GUARDRAILS_REGISTERED
PRODUCT_COMPLETENESS_IMPACT=NO_DIRECT_PERCENT_INCREMENT
READY_100_ALLOWED=false

These rules are additive acceptance gates for the existing single-runner task. They do not replace the active queue task and do not authorize any manual completion marker.

## Data-source constraints

1. Do not use paid, contact-required, invitation-only, or login-required data sources.
2. Use only:
   - repository files already present in this repo,
   - files already present on local D/F/C disks,
   - open and free internet sources.
3. Do not fabricate parcel geometry, parcel_id, point, or polygon.
4. If open data is not parcel-level, this must be explicitly reported using one of these layer states:
   - POSTCODE_LEVEL_ONLY
   - POINT_LEVEL_ONLY
   - OPEN_DATA_PROXY_READY
   - DATA_GATE_BLOCKED

## 100-ready constraints

A 100-ready product state may be written only when all of these are proven together by real evidence:

1. live map visibility,
2. non-empty feature set,
3. required popup or right-panel fields,
4. geometry accuracy.

If any item is missing, the runner must keep the product marked not-ready and must write a blocker report instead of a completion report.

## Runner contract

The existing single shared runner must continue using the active page-key queue. No separate PowerShell runner, no second runner, no forced push, no DB write, no migration, and no production deploy are authorized by this file.

The next valid runner-produced evidence remains:

docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/topography_single_runner_contract_recovery_20260623T010000Z_v6_terminal_bridge_report.txt
