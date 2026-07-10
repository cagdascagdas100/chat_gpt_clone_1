# AAYS1 Security site visibility and one-click runner recovery report

Date: 2026-07-10
Page key: aays1
Branch: codex/aays-single-runner-v5-20260706
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

## Scope

Fix both blocking problems before continuing Security/Public Safety source expansion:

1. The local Parcel Layer Matrix page does not show the verified Security/Public Safety rows in the main table.
2. The one-click runner flow can trust an old lock or PID, stop after stash, and fail to push fresh proof to GitHub.

## Current verified data state

- Verified Security/Public Safety rows: 150
- Accuracy 4/4 rows: 150
- Manual review rows: 0
- Source family: official/open data.police.uk evidence with verified spatial matching
- final_ready must remain false
- fake_data, db_write, migration, and production_deploy must remain false

## Site visibility defect

The local page can show Gas Emissions in the main selector and table while Security/Public Safety appears only in the upper status card. The user therefore cannot inspect the produced Security rows one by one.

### Required site behavior

1. Add Security/Public Safety as a normal main-table layer option.
2. When selected, render all 150 verified rows from:
   - england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json
   - england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json
   - england_map_web/data/security_public_safety/parcel_security_scores_verified.csv
   - england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson
   - outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json
3. Show row-level fields for parcel id/reference, security score/level, source name, source URL, local source file path, evidence or matching note, source date, accuracy, confidence, manual-review state, and changed-in-latest-run.
4. Mark newly produced or changed rows with a clearly visible badge, row style, or dedicated column.
5. Add a source-path panel showing exactly which local and repository files feed the table.
6. Make the upper status card and the main table read from the same F portable data paths.
7. Do not display a completed state merely because the files exist; require browser proof that the main table really renders the rows.

## Runner defect

The portable panel can show a new local PID while the launcher and GitHub proof still trust an old single_runner.lock PID. The recovery flow may also stop after git stash instead of continuing through pull, bootstrap, heartbeat, commit, and push.

### Required one-click runner behavior

When the user presses Tek Runner Baslat or executes the canonical launcher:

1. Inspect lock PID, live process, process command, process start time, launcher path, repository root, branch, and heartbeat freshness.
2. Treat the lock as stale when the PID is missing, unrelated, not the canonical runner command, or paired with a stale heartbeat.
3. Replace only a stale lock; never start a second runner when the canonical runner is genuinely active.
4. Recover interrupted git state and preserve local work with stash when required.
5. Continue after the stash step through fetch, pull, runner start, heartbeat write, commit, and push.
6. Ensure panel PID, lock PID, heartbeat PID, and bootstrap proof PID all match.
7. Produce a harmless small roundtrip sample file, commit it, push it to the target branch, and record the real commit SHA.
8. Store proof where the GitHub connector and ChatGPT can fetch it.

## Required proof files

- docs/chatgpt_status/aays1/runner_outputs/141_security_site_visibility_and_runner_recovery.json
- docs/chatgpt_status/aays1/runner_outputs/141_one_click_runner_roundtrip_sample.json
- docs/chatgpt_status/aays1/reports/141_security_browser_smoke.md
- docs/chatgpt_status/aays1/reports/141_security_site_visibility_and_runner_recovery_result.md
- docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json
- docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json
- docs/chatgpt_status/_shared/locks/single_runner.lock

## Acceptance criteria

The task passes only when all of the following are true:

- Exactly one canonical F portable runner is active.
- Panel PID equals lock PID equals heartbeat PID equals bootstrap proof PID.
- Heartbeat is fresh.
- Recovery continues after any stash step.
- A real GitHub commit and push are recorded for the small roundtrip sample.
- ChatGPT can fetch the roundtrip sample through the GitHub connector.
- Security/Public Safety is selectable in the main matrix table.
- The main table renders all 150 verified rows.
- Row-level source URL and local source-file path are visible.
- Newly changed rows are visually distinct.
- Browser smoke proof confirms the rendered rows and fields.
- final_ready remains false.
- fake_data=false, db_write=false, migration=false, production_deploy=false remain unchanged.

## Continuation rule

Do not continue to 151+ source expansion until both the site visibility proof and one-click runner roundtrip proof exist. After both pass, continue with only real official/open source-backed Security/Public Safety rows. Never create synthetic rows or increase metrics without repository proof.
