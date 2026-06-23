# Planned Buildings Guardrails - Latest

PAGE_KEY=planned-buildings-codex-20260622
BRANCH=feature/terrayield-aays-integration
STATUS=ACTIVE_GUARDRAIL

## Source rules

- Do not use paid data sources.
- Do not use sources that require contacting a vendor/person.
- Do not use invitation-only data sources.
- Do not use login-required data sources.
- Allowed sources only:
  - files already present in the repository,
  - files already present on local C/D/F disks,
  - open and free internet sources.

## Geometry rules

- Do not create fake parcel geometry.
- Do not create fake parcel_id values.
- Do not create fake points.
- Do not create fake polygons.
- If an open source is not parcel-level, report the layer status explicitly as one of:
  - POSTCODE_LEVEL_ONLY
  - POINT_LEVEL_ONLY
  - OPEN_DATA_PROXY_READY
  - DATA_GATE_BLOCKED

## Final readiness rules

FINAL_READY or 100 percent may only be reported when all are proven:

- live map visibility,
- non-empty feature set,
- popup or right panel required fields,
- geometry correctness.

## Required evidence before 100 percent

- Product report must exist: docs/chatgpt_status/planned-buildings-codex-20260622/reports/planned_buildings_contract_detector_latest.txt
- Poller/runner contract report must exist if runner still does not consume: docs/chatgpt_status/planned-buildings-codex-20260622/reports/poller_contract_probe_latest.txt
- No fake data and no fake final marker are allowed.
