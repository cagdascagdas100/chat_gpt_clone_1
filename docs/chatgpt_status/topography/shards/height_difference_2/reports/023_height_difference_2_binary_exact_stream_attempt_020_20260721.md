# height_difference_2 — Binary Exact-Target Stream / Attempt 020

## Result

The same task and idempotency key remain active. No new task, runner architecture, worktree, database write, migration or deployment was created.

The exact candidate extractor was upgraded from a text `JSONDecoder` buffer plus a second SHA256 pass to `binary-feature-object-stream-v2`:

- full GeoJSON document loading is forbidden;
- SHA256 is calculated during the same full-file pass;
- every feature is scanned through the feature-array end;
- duplicate target rows occurring after the first matches are still detected;
- escaped strings, nested objects and chunk boundaries are handled explicitly;
- only rows `30762`, `46142` and `61522` may be accepted;
- nearest-row substitution remains forbidden;
- point elevation values remain non-promotable.

## Validation

Deterministic fixtures passed `18/18` across chunk sizes `4096`, `8192` and `65536` bytes:

- positive exact-target set: 3/3 pass;
- missing target: 3/3 fail closed;
- invalid target: 3/3 fail closed;
- duplicate target row: 3/3 fail closed;
- duplicate HMLR INSPIRE ID: 3/3 fail closed;
- nearest-only rows: 3/3 fail closed.

The validation is fixture/static-contract evidence only. It produced no product row.

## Pickup alignment

Attempt `height-difference-2-20260721-020` was retained. The following now bind the new extractor blob `a7e220421523d3f77012440d9303658b0142a715`, carrier blob `8c39a083043af7fd20edeea682578e5f70117be5`, queue commit `b14a99481e20e61936a55a52c3e033d95f7579ba`, and a 365-row web floor:

- canonical schema-v5 queue;
- queue refresh control;
- reboot/recovery request;
- portable `ai-tasks/current-task.json`;
- legacy queue/current text views.

## Current evidence

- real canonical candidate rows: 0;
- exact HMLR polygons: 0;
- EA DTM 1m polygon samples: 0;
- OS Terrain 50 crosschecks: 0;
- port 8012 acceptance rows: 0;
- measured parcel rows: 0;
- parcel measurement accuracy: `0/4_not_produced`;
- source/contract accuracy: `4.0/4`;
- automation validation: `332/332 PASS` after adding the 18 binary-stream fixtures;
- website operation rows: 365;
- overall completion: 78%;
- `final_ready=false`.

## Remaining blocker

The guarded operator recovery has not been executed on the existing F host. The committed daemon heartbeat remains dated 16 July 2026 and the slot remains unclaimed. Therefore no restart, claim, candidate, polygon or numeric measurement is inferred.

Next verified step:

`APPLY_GUARDED_OPERATOR_RECOVERY_ON_EXISTING_F_HOST_THEN_FRESH_DAEMON_HEARTBEAT_CLAIM_ATTEMPT_020_AND_RUN_BINARY_EXACT_TARGET_STREAM`
