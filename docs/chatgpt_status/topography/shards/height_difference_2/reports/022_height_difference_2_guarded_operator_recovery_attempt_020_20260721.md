# height_difference_2 — guarded operator recovery / attempt 020

- SLOT_ID: `height_difference_2`
- Parcel range: `30762-61522`
- Task: `aays1-height-difference-2-canonical-export-official-sampling-20260720`
- Attempt: `height-difference-2-20260721-020`
- Final ready: `false`

## New diagnosis

The queue-refresh and reboot-request JSON files are audit/control records. The shared launcher starts the persistent daemon only when the launcher or a guarded F-side entry is actually invoked. A GitHub commit alone cannot start a Windows process on the canonical F host.

## Recovery repair

The restart helper previously still wrote an attempt `019` receipt. It is now bound to attempt `020` and records the immutable rows `30762`, `46142`, `61522` with nearest-row fallback disabled.

A guarded operator recovery entry was added:

`docs/chatgpt_status/topography/shards/height_difference_2/automation/030_apply_attempt_020_existing_f_runner_recovery.ps1`

It:

1. Uses only the canonical F checkout and exact codex branch.
2. Blocks a dirty repo before any reset.
3. Fetches the exact branch and reads back `origin/<branch>`.
4. Resets only a clean checkout whose local HEAD differs from the remote HEAD.
5. Requires local HEAD to equal the remote HEAD after synchronization.
6. Verifies the corrected restart-helper Git blob.
7. Invokes only the guarded helper; it contains no direct `Start-Process` call.
8. Preserves the existing single-runner architecture and writes a deterministic preflight receipt.

## Validation

`018_operator_recovery_contract_validation_20260721.json` records `25/25 PASS` using GitHub remote blob readback and static contract inspection.

- Corrected helper blob: `b3a18bcdb1b7158d18aab33b42d5797342d23cd1`
- Operator entry blob: `1632d6d7467c21d0ba0bfdd880a137afb2f905f3`
- Verifier blob: `9f76200f602f73bb60ffa72102a384c7ae08fb5d`
- Operator execution observed: `false`
- Runner restart observed: `false`
- Product rows promoted: `0`

Cumulative deterministic/static validation: `314/314 PASS`.

## Progress

- Planned operations: `361`
- Completed operations: `321`
- Blocked operations: `6`
- Pending operations: `14`
- Batch progress: `88.92%`
- Batch increase: `0.36 percentage points`
- Overall completion: `78%`
- Overall increase: `0%`
- Website operation rows: `345`
- Candidate target / actual: `3 / 0`
- Exact HMLR polygons: `0`
- EA DTM1m polygon samples: `0`
- OS Terrain50 crosschecks: `0`

## First unverified step

`APPLY_GUARDED_OPERATOR_RECOVERY_ON_EXISTING_F_HOST_THEN_FRESH_DAEMON_HEARTBEAT_CLAIM_ATTEMPT_020_AND_PROVE_EXACT_ROWS`

## Blocker

`GUARDED_OPERATOR_RECOVERY_NOT_EXECUTED_ON_F_HOST;PERSISTENT_CANONICAL_F_DAEMON_RESTART_NOT_OBSERVED;SLOT_CLAIM_NOT_OBSERVED;THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_PENDING;THREE_EXACT_HMLR_POLYGONS_PENDING;THREE_EA_DTM1M_POLYGON_SAMPLES_PENDING;THREE_OS_TERRAIN50_CROSSCHECKS_PENDING;PORT_8012_HTTP_READBACK_PENDING`

Safety flags remain false for fake data, database writes, migrations and production deployment.
