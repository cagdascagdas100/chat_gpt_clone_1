# height_difference_2 — actual hotfix and persistent daemon — attempt 019

## Result

The canonical root command was traced through its real active path:

`RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd` → `RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd` → `devam.ps1` → shared launcher → one persistent daemon → stable queue scanner.

The active hotfix previously bypassed the persistent daemon and ran an infinite `MaxTasks 8` polling loop. It now validates the canonical F branch and delegates once to `devam.ps1`. The existing single-runner architecture is preserved and each scan is constrained to one task.

## Contract changes

- Same task ID and idempotency key retained.
- Attempt advanced to `height-difference-2-20260721-019`.
- Queue remains schema version 5, priority 1 and FIFO by `created_at`.
- Restart success now requires exactly one persistent daemon.
- Ambiguous transient processes or multiple daemons fail closed.
- Carrier and numeric gate use a web acceptance floor of 305 manifest-driven rows.
- No new runner, worktree, queue task or parallel process architecture was created.

## Validation

- Actual runner-chain static validation: **24/24 PASS**.
- Cumulative automation validation: **271/271 PASS**.
- Official source contract accuracy: **4.0/4**.
- Parcel measurement accuracy: **0/4 — no official numeric parcel measurement produced**.

## Official source readback

- HMLR INSPIRE local-authority GML publication: 5 July 2026.
- Environment Agency LiDAR Composite DTM 1 m: EPSG:27700 and ±15 cm RMSE metadata; WCS 2.0.1 contract retained.
- OS Terrain 50: July 2026, Great Britain coverage, secondary crosscheck only.

## Current metrics

- Planned operations: 321.
- Completed operations: 283.
- Batch progress: 88.16%.
- Overall completion: 78%.
- Website operation rows: 305.
- Candidate target / actual: 3 / 0.
- Exact HMLR polygons: 0.
- EA DTM 1 m polygon samples: 0.
- OS Terrain 50 crosschecks: 0.

## Blocker

The repaired F launcher and persistent daemon execution have not been observed remotely. The daemon heartbeat remains dated 16 July 2026 and the slot remains unclaimed. No candidate, polygon or official numeric row is promoted without the real runner outputs.

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
