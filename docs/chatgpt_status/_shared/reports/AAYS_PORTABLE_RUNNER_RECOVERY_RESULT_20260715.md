# AAYS Portable Runner Recovery Result

- Status: PASS_WITH_PHYSICAL_TEST_LIMITATIONS
- Tested at: 2026-07-15T00:17:04Z
- Branch: `codex/aays-single-runner-v5-20260706`
- Portable root: `F:\TerraYield_AAYS_Portable`
- Canonical repo: `F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`

## Root Cause

The local repository `.git/config` was 601 bytes of NUL data. Both `git config --local --list` and `git status --short --branch` failed with `fatal: bad config line 1 in file .git/config`, preventing the portable launcher and runner recovery flow from reaching normal startup.

## Changed Files

- `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.ps1`
- Backup: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.ps1.pre_git_recovery_20260715.bak`
- Versioned source: `docs/chatgpt_status/_shared/automation/RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.ps1`

No new runner, guardian, parallel worker, or business task was created.

## Self-Heal Flow

1. Detect missing, empty, NUL-containing, BOM-encoded, or Git-unparseable local config.
2. Fail closed while a fresh `.git/config.lock` exists; quarantine only a stale config lock.
3. Preserve the damaged config as `config.corrupt.<timestamp>.bak`.
4. Atomically write the minimum `core`, `origin`, and branch tracking config as UTF-8 without BOM.
5. Validate with both `git config --local --list` and `git status --short --branch`.
6. Continue through the existing live-PID lock check and existing guardian/daemon only after validation succeeds.
7. Write `logs/launcher_latest.log` and `logs/recovery_latest.json` with all safety flags false.

## Test Results

- PowerShell parser: PASS.
- Real corrupt config recovery: PASS; reason `config_contains_nul`.
- Corrupt config backup: PASS; 601-byte backup preserved.
- Git config parse after repair: PASS.
- Git status after repair: PASS.
- First launcher execution: PASS; `persistent_daemon_started`, PID `22928`.
- Second launcher execution: PASS; `already_running`, same PID `22928`, `second_launch_blocked=true`.
- Process count: PASS; exactly one stable daemon.
- Heartbeat: PASS; `runner_active=true`, state `worker_running`, site 8012 healthy.
- Startup guardian task: PASS; task exists and was running.
- Portable disk missing simulation: PASS; `waiting_for_portable_disk`.
- Network unavailable simulation: PASS; `waiting_for_network`, existing runner not duplicated.
- Resume simulation: PASS; `runner_healthy`, `resume_grace_owner_verified`.
- Safety: PASS; `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
- Launcher SHA-256: `BA7E318E49077BA4D78AAB445F0ACAFB3429963EC2A7103BD273B7A96B37B6CC`.

## Physical Test Limitations

Physical USB removal, full Windows reboot, forced sleep/wake, and real internet disconnection were not performed because they would interrupt the active user session. Their existing recovery branches were exercised through the guardian's built-in safe simulation switches. This limitation is not reported as a fake full end-to-end pass.

## Repository State

The F runner checkout is heavily dirty from existing runtime outputs and is `ahead 198, behind 1`. Those unrelated files were not reset, cleaned, staged, or included. The fixed launcher source and this report are published directly to the requested remote branch to avoid corrupting existing work.

## Remaining Blockers

- Physical hardware/reboot tests remain unperformed.
- Five page checkpoints show some local checkpoint files unavailable; this is business-task state, not a runner startup blocker.
- Product completion remains false and is outside this recovery task.
