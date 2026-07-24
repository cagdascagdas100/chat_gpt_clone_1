# AAYS one-click runner recovery acceptance task

Date: 2026-07-10
Page key: aays1
Branch: codex/aays-single-runner-v5-20260706
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

## Objective

Make the portable control panel button perform a complete one-click recovery and proof flow for the single shared runner.

## Current defect

The panel can show a new local PID while the launcher still trusts an old `single_runner.lock` PID and refuses bootstrap. GitHub heartbeat/proof can therefore remain stale even though the panel says the runner is active.

## Required behavior

When the user clicks `Tek Runner Baslat` or runs the canonical launcher:

1. Inspect the current lock, recorded PID, live process, process start time, launcher path, repository root, branch, and heartbeat freshness.
2. Treat the lock as stale when the PID is missing, belongs to an unrelated process, does not match the canonical runner command, or the heartbeat is outside the allowed freshness window.
3. Safely replace only a stale lock. Never start a second runner while the canonical runner is genuinely active.
4. Recover interrupted git state, preserve local work with a stash when required, fetch and pull the target branch, and continue after the stash step instead of stopping there.
5. Start exactly one runner from the F portable launcher.
6. Write a fresh heartbeat and bootstrap proof containing the actual live PID and current timestamps.
7. Run a small roundtrip acceptance test that creates a harmless text or JSON proof file inside the repository, commits it, pushes it to the target branch, and records the commit SHA.
8. Store the acceptance file where GitHub and ChatGPT can read it.
9. Update the control panel status from the same live proof source so the panel PID, lock PID, and GitHub proof PID agree.

## Required acceptance artifact

Create a small file such as:

`docs/chatgpt_status/aays1/runner_outputs/140_one_click_runner_roundtrip_sample.json`

It must contain at least:

- task_id
- runner_active
- pid
- lock_pid
- pid_match
- launcher_path
- portable_root
- repo_root
- branch
- heartbeat_at
- git_pull_status
- git_push_status
- pushed_commit_sha
- sample_file_path
- sample_file_sha
- single_runner_only
- new_runner
- parallel_runner
- final_ready
- fake_data
- db_write
- migration
- production_deploy

The sample file may contain only a timestamp, task id, and a fixed test message. It must not contain production or personal data.

## Proof paths

- `docs/chatgpt_status/aays1/runner_outputs/140_one_click_runner_recovery_acceptance.json`
- `docs/chatgpt_status/aays1/runner_outputs/140_one_click_runner_roundtrip_sample.json`
- `docs/chatgpt_status/aays1/reports/140_one_click_runner_recovery_acceptance.md`
- `docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json`
- `docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json`
- `docs/chatgpt_status/_shared/locks/single_runner.lock`

## Pass criteria

The task passes only when all of these are true:

- One canonical runner only.
- Panel PID equals lock PID equals heartbeat PID equals bootstrap proof PID.
- Heartbeat timestamp is fresh.
- The launcher completes after any stash step.
- The sample proof file exists on GitHub on the target branch.
- `git_push_status` is `pushed` and a real commit SHA is recorded.
- ChatGPT can fetch the sample file through the GitHub connector.
- `final_ready=false` remains unchanged.
- `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.

Do not report completed status unless the GitHub roundtrip file and commit proof are present.