# Topography 145 - One Click Runner Recovery and GitHub Smoke Test

Branch: codex/aays-single-runner-v5-20260706
Portable root: F:\TerraYield_AAYS_Portable
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Final: false

## Confirmed PID state
The live process output shows only PID 15656 running the canonical legacy runner daemon. PID 10108 is not present in the live process query and must be treated as stale lock/heartbeat state.

## Required Codex fix
The Portable Control Panel button `Tek Runner Başlat` must perform one complete recovery and proof cycle without opening a second runner.

Required sequence:
1. Detect all runner daemon processes for the canonical F portable repo.
2. If exactly one valid daemon is alive, reuse it and never start a second one.
3. If the lock PID is absent, replace the stale lock with the real live PID.
4. Validate portable_root, repo_root, work_root and branch.
5. Abort stale rebase/merge only when present.
6. Stash local changes before pull when needed.
7. Pull/sync the target branch safely.
8. Refresh heartbeat with the real live PID and current UTC timestamp.
9. Run a minimal smoke-test task.
10. Create a small proof JSON file and push it to GitHub.
11. Verify the pushed file by reading it back from the target branch.
12. Show PASS or exact blocker in the Portable Control Panel.

## Required smoke-test output
Create a timestamped file under:
`docs/chatgpt_status/topography/runner_outputs/145_one_click_smoke_test_<timestamp>.json`

Required fields:
- test_id
- page_key: topography
- runner_pid
- portable_root
- repo_root
- branch
- created_at_utc
- heartbeat_at_utc
- queue_scan_ok
- file_write_ok
- git_commit_ok
- git_push_ok
- github_readback_ok
- proof_file_path
- commit_sha
- AAYS_ONE_CLICK_SMOKE_TEST_OK
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

## Required status output
Create/update:
`docs/chatgpt_status/topography/status/145_one_click_runner_recovery_and_smoke_test_latest.json`

The status must include the real PID, smoke-test path, commit SHA, push/readback result, exact blocker if failed, and processed task count.

## Panel requirement
After clicking `Tek Runner Başlat`, the panel must display:
- Runner ACTIVE / FAILED
- real PID
- heartbeat age
- queue count
- processed task count
- smoke-test PASS / FAIL
- GitHub proof path
- commit SHA
- exact blocker

## Integrity rules
- Do not open a parallel runner.
- Do not claim success without GitHub readback proof.
- Do not write fake Topography elevation.
- Keep final_ready=false.
- Keep fake_data=false, db_write=false, migration=false and production_deploy=false.
