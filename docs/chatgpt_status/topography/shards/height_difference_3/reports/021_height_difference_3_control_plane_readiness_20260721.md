# height_difference_3 — Sequence 21 control-plane readiness

## Result

The existing shared-runner control plane contained one stale path: `current_task_latest.json` allowed `_shared/slots_18/height_difference_3` although the active slot root is `_shared/slots_21/height_difference_3`.

The allowed path was corrected without creating or assigning a task, owner, claim, queue item, lease, heartbeat, runner, or parallel runner. `state=idle`, `task_id=null`, `owner_page_session_id=null`, and `final_ready=false` remain unchanged.

## Added audit

`automation/036_audit_existing_runner_control_plane.py` validates:

- exact slot and parcel partition identity;
- exact `slots_21`, shard, and web allowed paths;
- idle/unassigned current-task state;
- unclaimed and stale heartbeat state;
- checkpoint/status sequence and first-step agreement;
- existing-shared-runner-only task policy;
- no queue, lease, new runner, or parallel runner;
- approved full-pipeline command;
- NOT_STARTED runtime with zero real counts and no fabricated operations;
- all safety flags remaining false.

Positive and negative fixtures passed `15/15`; cumulative self-tests are `268/268`.

## Official sources refreshed

- HM Land Registry INSPIRE Index Polygons: publication dated 5 July 2026.
- Environment Agency / Defra LIDAR Composite DTM 1m WCS: EPSG:27700.
- Ordnance Survey Terrain 50: version date July 2026.

## Real-data counters

- canonical shard rows exported: 0 / 30,761
- real candidates: 0
- HMLR matches: 0
- EA DTM samples: 0
- Terrain 50 crosschecks: 0
- verified website examples: 0

## Remaining blocker

The existing F shared runner is still unclaimed and has not executed the committed `032 + 035` full chain. The next real step remains execution of the existing task followed by three official crosschecked examples and transactional port 8012 readback.

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` are preserved.
