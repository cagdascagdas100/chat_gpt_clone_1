# Gas Emissions Site Visibility and One-Click Runner Combined Fix

Task ID: gas-emissions-147-site-visibility-runner-combined-fix-20260710
Branch: codex/aays-single-runner-v5-20260706
Canonical runner: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Final ready: false

## User requirement

The user must be able to see every source-backed Gas Emissions result on the local 8012 site, row by row, with source names and source/file paths. Newly added rows must be visually distinct. The same portable panel must also provide a reliable one-click single-runner recovery and GitHub self-test proof.

New internet-sourced Gas Emissions expansion remains paused until both parts below pass.

## Part A - Local site row visibility

Current problem:

- The local page still treats `gas_emissions_updates/latest_changes.json` as the main visible card.
- The latest source-backed rows are not rendered row by row with source paths.
- `gas_emissions_status_latest.json` still points to an older 4-row marker.
- `gas_emissions_visible_rows_latest.json` currently reports 24 visible rows, not the previously claimed 120.
- `gas_emissions.geojson` could not be validated as non-empty through GitHub fetch.
- The earlier 142 visibility report path was not available.

Required UI fix:

1. Add or repair a dedicated `Gas Emissions - Kaynakli Son Satirlar` panel on the 8012 parcel-layer page.
2. Read the current Gas Emissions marker and visible-rows proof; do not treat stale `latest_changes.json` as final evidence.
3. Render rows one by one with at least:
   - row id
   - parcel id/ref when available
   - year or period
   - sector and subsector
   - greenhouse gas
   - emissions value and unit
   - source title
   - source URL
   - local/downloaded source path when available
   - report/proof path
   - matching method
   - confidence percent
   - accuracy score out of 4
   - manual-review flag
   - changed-in-latest-run flag
4. Mark new rows with a visible `Yeni` or `Latest` badge and a distinct row style.
5. Show a source/proof summary above the rows with the current marker path, visible rows path, verified rows path, report path and GeoJSON/proof path.
6. Make the row count internally consistent. If 120 rows are visible, the proof file must report and contain/reference 120. Otherwise show the real count.
7. Repoint `gas_emissions_status_latest.json` to the current visible-rows proof or add a `visible_rows_path` field.
8. Ensure the program-layer GeoJSON or a separate feature-count proof demonstrates the real feature count used by the page.
9. Run browser smoke on the 8012 page and write a proof file that records the rendered row count, newest-row count and proof paths.

Required browser proof path:

`docs/chatgpt_status/gas_emissions/browser_proof/gas_emissions_site_rows_latest.json`

## Part B - One-click single runner recovery and self-test

The portable-panel button `Tek Runner Baslat` must perform all checks in one click and remain idempotent.

Required behavior:

1. Use only the existing F portable shared runner.
2. Detect a live PID and valid lock; reuse it and never start a second runner.
3. If stale, validate PID, process existence, lock ownership and heartbeat before clearing only the stale lock.
4. Check repo path, branch, git status, merge/rebase state, remote reachability and write permission.
5. Stash dirty worktree changes before pull and record the result.
6. Pull `codex/aays-single-runner-v5-20260706`; on failure, write a blocker instead of success.
7. Wait for a fresh heartbeat and verify the panel PID matches the runner PID, or record an explicit parent/child PID mapping.
8. Produce a new UTF-8 JSON self-test file with a unique timestamp and random nonce.
9. Commit and push the self-test file to GitHub.
10. Update a stable proof path that ChatGPT can fetch.
11. Display runner PID, heartbeat, branch, pull status, self-test status, commit SHA, push status and proof path in the portable panel.

Required self-test paths:

- Timestamped: `docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_<YYYYMMDD_HHMMSS>.json`
- Stable latest: `docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_latest.json`
- Failure proof: `docs/chatgpt_status/_shared/runner_outputs/one_click_runner_self_test_blocker_latest.json`

## Combined acceptance criteria

The combined fix passes only when all are true:

1. One click reuses or recovers exactly one runner; no second or parallel runner exists.
2. A fresh runner self-test JSON is committed and pushed.
3. ChatGPT can fetch the stable latest self-test path and see nonce, PID, heartbeat, commit SHA and push status.
4. The 8012 Gas Emissions page shows current source-backed rows row by row.
5. Each visible row shows source URL and proof/source path when available.
6. New rows are clearly marked and visually distinct.
7. Browser smoke proof records the rendered row count and newest-row count.
8. `latest_changes.json` is not treated as final evidence when stale.
9. No fake completed, fake 100 percent or `final_ready=true` claim is allowed.

## Safety flags

- single_runner_only: true
- new_parallel_runner: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false
- final_ready: false
- product_final_ready: false

## Resume condition

Resume real internet-sourced Gas Emissions row expansion only after both the one-click runner self-test proof and the 8012 row-visibility browser proof are present on GitHub and internally consistent.