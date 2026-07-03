# TerraYield 046 Runner Sync Recovery Then Accuracy Expansion

page_key=security_public_safety
task_id=terrayield-046-runner-sync-recovery-then-accuracy-expansion
layer=Safety / Security
program_output=Security Level percent
status=QUEUED_FOR_SHARED_RUNNER
created_at=2026-07-03T14:20:00+03:00
final_ready=false
fake_data=false
db_write=false
ddl=false
migration_apply=false
prod_deploy=false
individual_person_data=false

## Source handoff accepted in this page

The uploaded handoff states that task `terrayield-046-runner-sync-recovery-then-accuracy-expansion` should perform runner/Git sync recovery, preflight checks, endpoint health probe, project red-flag quickscan, and 044 comprehensive accuracy expansion child launch. Initial scores from the handoff were:

- Source Accuracy Score: 45/100
- Parcel Matching Accuracy Score: 27/100
- Operational Health Score: 0/100
- Overall Confidence Score: 32/100

## What was done from this ChatGPT page

- `docs/chatgpt_status/security_public_safety/current-task.json` was written.
- `docs/chatgpt_status/security_public_safety/queue/terrayield-046-runner-sync-recovery-then-accuracy-expansion.task.json` was written.
- This report was written for the repo.
- No synthetic parcel scores were produced.
- `final_ready=false` is preserved.

## Runner execution contract

The single shared runner on the F bridge should pick up the queue task and perform these read-only checks:

1. Synchronize local F repo with GitHub `main` and record commit evidence.
2. Check shared runner state, current task, pending queue, lock files, and heartbeat without starting another runner.
3. Probe the local program endpoint and matrix page endpoint.
4. Run Security/Public Safety consistency checks.
5. Queue or block the 044 accuracy-expansion child with an explicit reason.
6. Update `outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json` with real runner results.

## Current blockers

- This ChatGPT connector can write GitHub files, but it cannot directly run the Windows F repo / F bridge runner.
- No real runner result has been returned yet for this 046 task.
- No browser smoke evidence exists yet for the matrix page.
- Verified parcel outputs are still required before any final state:
  - `england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson`
  - `england_map_web/data/security_public_safety/parcel_security_scores_verified.csv`
  - `england_map_web/data/security_public_safety/security_evidence_manifest.json`

## Required final gate

Do not set `final_ready=true` until there is real evidence for parcel layer rendering, popup/right-panel fields, latest_changes panel rendering, official/open aggregate source evidence, and browser smoke verification.
