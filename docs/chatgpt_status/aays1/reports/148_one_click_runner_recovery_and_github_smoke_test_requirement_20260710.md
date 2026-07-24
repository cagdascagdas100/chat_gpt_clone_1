# AAYS One-Click Runner Recovery and GitHub Smoke Test Requirement

Date: 2026-07-10
Page key: aays1
Branch: codex/aays-single-runner-v5-20260706
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Canonical portable root: F:\TerraYield_AAYS_Portable
Canonical repo root: F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707

## Goal

The `Tek Runner Baslat` button in the portable control panel must perform a complete single-runner recovery, health verification, queue pickup verification, and GitHub smoke test in one click.

This task is not accepted based only on a local `Runner: AKTIF` label. Success requires a fresh GitHub heartbeat and a small runner-generated proof file pushed to the repository so ChatGPT can read it.

## Mandatory one-click flow

When the user clicks `Tek Runner Baslat`, the program must execute these steps in order:

1. Validate the canonical portable root, repo root, work root, and target branch.
2. Abort stale rebase or merge state when present.
3. Inspect `git status --porcelain`.
4. Preserve real local changes safely with an automatic named stash when required.
5. Run fetch/pull for `codex/aays-single-runner-v5-20260706` and report the exact result.
6. Inspect the single-runner lock and recorded PID.
7. Test whether the locked PID is really alive and is the expected runner process.
8. Check heartbeat freshness, not only PID existence.
9. Treat a heartbeat older than the configured freshness window as stale even when the PID exists.
10. If the old runner is stale or non-responsive, terminate only that stale canonical runner process, remove only the stale lock, and start exactly one canonical runner.
11. Never start a second or parallel runner when a healthy canonical runner is already active.
12. Wait for a fresh local heartbeat from the new/current runner.
13. Perform a real queue pickup smoke test.
14. Generate a small proof file from inside the runner process.
15. Commit and push the proof file and fresh heartbeat to the target GitHub branch.
16. Verify that the pushed proof file is retrievable from GitHub.
17. Update the control panel with pass/fail state for every step.

## Required GitHub smoke-test artifact

The runner must generate and push this file:

`docs/chatgpt_status/_shared/smoke/one_click_runner_smoke_latest.json`

Required fields:

- `test_name`: `one_click_runner_smoke`
- `status`: `passed` or `failed`
- `generated_by_runner`: true
- `generated_at`
- `portable_root`
- `repo_root`
- `work_root`
- `branch`
- `pid`
- `lock_valid`
- `heartbeat_fresh`
- `heartbeat_at`
- `queue_pickup_tested`
- `queue_pickup_passed`
- `test_task_id`
- `test_payload`: a small deterministic value such as `AAYS_SMOKE_OK_20260710`
- `git_commit_sha`
- `git_push_status`
- `github_fetch_verified`
- `final_ready`: false
- `fake_data`: false
- `db_write`: false
- `migration`: false
- `production_deploy`: false

Also write a human-readable companion file:

`docs/chatgpt_status/_shared/smoke/one_click_runner_smoke_latest.txt`

It must contain the timestamp, PID, branch, queue pickup result, commit SHA, and `AAYS_SMOKE_OK` marker.

## Queue pickup proof

The smoke test must not merely create the proof file from the launcher script. It must prove that the runner itself picked up and executed a tiny test task.

Use a dedicated test task such as:

`docs/chatgpt_status/_shared/queue/one_click_runner_smoke.task.json`

The runner must:

- detect the task,
- execute it,
- write the smoke output,
- mark the task processed,
- push the output to GitHub.

A local-only file is not sufficient.

## Control panel requirements

The portable panel must show these fields after one click:

- App health
- Canonical runner PID
- Lock state
- Heartbeat age
- Branch
- Git pull result
- Local dirty/stash result
- Queue pickup test result
- Smoke file local path
- Smoke file GitHub path
- Commit SHA
- Push result
- GitHub fetch verification result
- Final overall state: `HEALTHY`, `STALE`, or `FAILED`

Do not show `Runner: AKTIF` based only on a live PID. A live PID with stale heartbeat or zero task pickup must be shown as `STALE`.

## Failure handling

On failure, the panel and output must state the exact blocker, for example:

- `stale_heartbeat`
- `pid_alive_but_runner_not_processing`
- `lock_pid_mismatch`
- `git_pull_failed`
- `stash_failed`
- `queue_pickup_failed`
- `github_push_failed`
- `github_fetch_verification_failed`

Do not write fake success, fake completion, fake 100 percent, or fake final readiness.

## Acceptance criteria

The fix is accepted only when all conditions below are true:

1. A single click performs all preflight and recovery checks.
2. Exactly one canonical runner remains active.
3. A fresh heartbeat is written after the click.
4. The runner picks up and executes the dedicated smoke task.
5. `one_click_runner_smoke_latest.json` is created by the runner.
6. The proof file is committed and pushed to `codex/aays-single-runner-v5-20260706`.
7. The proof file can be fetched from GitHub by ChatGPT.
8. The panel displays the real commit SHA and GitHub verification result.
9. `processed_task_count` or equivalent proof increases for the smoke task.
10. No second runner is started.
11. `final_ready=false` remains unchanged.
12. `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.

## Current observed defect

The current launcher preserves PID 10108 because the PID appears alive, but GitHub heartbeat remains stale and `processed_task_count` remains zero. Therefore PID existence alone is currently producing a false healthy state. The new implementation must use heartbeat freshness and queue pickup as mandatory health signals.
