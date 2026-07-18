# AAYS 18 Slot + Internet Portable Integration Result

Status: `PASS_WITH_DECLARED_SCOPE_LIMITATIONS`
Workstream: `AAYS_18_SLOT_SAFE_PARALLEL_V1`

## Implemented

- One coordinator, one publisher and 18 isolated logical slots.
- Added `internet_access_1`, `internet_access_2`, `internet_access_3`.
- Existing 15-slot tasks remain accepted for non-Internet slots during transition.
- Canonical remote state is `docs/chatgpt_status/_shared/slots_18/`.
- Portable aliases start the same coordinator; they do not create another runner.
- The control panel shows all 18 slots, active/max workers, scheduling pause and truthful data scope.
- Internet rows target the existing 92,283-row London matrix: 33,785 matched/verified proxy rows and 58,498 pending or `NO_DATA` rows. Missing scores are not fabricated.

## Tests

- Python compile: PASS
- PowerShell parser: PASS
- JSON parse: PASS
- Portable preflight: PASS, 18/18 worktrees self-contained
- 18-light-slot fixture: PASS
- Wrong-slot rejection: PASS
- Duplicate-task rejection: PASS
- Path-overlap rejection: PASS
- Alternate drive-letter simulation: PASS
- Physical second-PC/reboot test: NOT RUN on a second physical host

## Capacity

- Under 10 GB RAM: maximum 5 concurrent child tasks.
- 10-24 GB RAM: maximum 15 concurrent child tasks.
- 24 GB or more: maximum 18 concurrent child tasks.
- Git publish, runtime sync, shared publish and heavy disk operations remain serialized.

## Scope Blocker

The existing 92,283 records are the London canonical matrix, not a proven all-England parcel inventory. National map PMTiles are available, but `NATIONAL_ENGLAND_CANONICAL_PARCEL_INVENTORY_NOT_ESTABLISHED` remains a real blocker. Therefore whole-England data completion is not claimed.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
