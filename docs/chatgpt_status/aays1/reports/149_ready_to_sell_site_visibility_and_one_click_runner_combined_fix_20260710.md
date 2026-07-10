# AAYS1 Ready To Sell — Site Visibility + One-Click Runner Combined Fix

Date: 2026-07-10
Page key: aays1
Branch: codex/aays-single-runner-v5-20260706
Canonical launcher: F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Canonical portable root: F:\TerraYield_AAYS_Portable
Canonical repo root: F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707

## Purpose

This report combines two blockers that must be fixed before normal Ready To Sell / Geometry Review verification continues:

1. The local Geometry Review page does not show the latest evidence row by row with source and artifact paths.
2. The one-click runner panel can report an active runner from PID existence even when heartbeat and queue pickup are stale.

The task is accepted only after both the runner smoke test and the browser visibility test pass with real GitHub proof.

---

## A. Current site visibility problem

The local page at:

`http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html?refresh=codexfix`

has shown stale or incomplete data and broken Turkish text. The user must be able to see every completed result directly on this page.

### Required data files

The page must load and display the actual paths and fetch state of:

- `england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson`
- `england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json`
- `england_map_web/data/aays1/aays1_product_status_latest.json`
- latest relevant status JSON under `docs/chatgpt_status/aays1/status/`
- latest relevant report MD under `docs/chatgpt_status/aays1/reports/`

Do not silently load an older copy from another directory.

### Required top diagnostics panel

The browser page must show:

- loaded geometry path
- loaded AI evidence path
- loaded product status path
- HTTP/fetch result for every file
- file updated timestamp when available
- AI status
- product status
- rows_total
- rows_reviewed
- rows_with_live_source_verified
- rows_pending_vision_download
- site_visible_progress_percent
- product completion percent
- active task id
- latest status path
- latest report path
- `final_ready`
- `fake_data`, `db_write`, `migration`, `production_deploy`

Every JSON and GeoJSON fetch must use cache-busting based on the page refresh token or a timestamp.

### Required row-level fields

For every row, show clearly:

- row_id
- listing_url as a clickable source link
- parcel_ref
- matched Inspire id when available
- source_verification_status
- source_verification_result
- source_listing_type_verified
- source_photo_count_verified
- source_area_verified
- source_planning_ref_verified
- source_page_title_verified
- confidence_before
- confidence_after
- visual_match_score
- photo_shape_type
- photo_boundary_visible
- geometry_mismatch_flag
- source HTML/JSON local path when saved
- downloaded photo local path when saved
- polygon render local path when saved
- vision comparison output path when saved
- status JSON path
- report MD path
- task id / run id
- changed_in_latest_run or equivalent run marker

When an artifact does not exist, display an explicit value such as:

- `not downloaded`
- `not generated`
- `vision pending`
- `not available`

Do not leave these fields silently blank.

### Required latest-run visual markers

Rows added or changed in the latest run must be visually different from older rows. Use clear badges or row styling:

- `NEW IN LATEST RUN`
- `LIVE SOURCE VERIFIED`
- `PHOTO DOWNLOADED`
- `POLYGON RENDERED`
- `VISION COMPARED`
- `VISION PENDING`
- `NOT 3.5 PLUS`
- `MANUAL REVIEW REQUIRED`

The page should also provide a filter for latest-run rows.

### UTF-8 requirements

- Keep `<meta charset="utf-8">`.
- Save HTML, JSON and generated text files as UTF-8.
- Ensure the local HTTP server sends UTF-8 content type for text assets.
- Turkish labels must render correctly in both the page header and row data.

### Stale data protection

The page must show `STALE LOCAL DATA` when:

- the loaded JSON timestamp is older than the latest known product/status timestamp,
- the browser loaded row counts differ from the latest status file,
- the loaded paths are not the required site data paths,
- a fetch falls back to an empty result.

A failed AI JSON fetch must not silently become `{results:[]}` without an on-screen error.

---

## B. One-click runner recovery and GitHub smoke proof

The `Tek Runner Başlat` button in the portable panel must perform a complete single-runner preflight, recovery, queue pickup test and GitHub proof cycle.

A local `Runner: AKTİF` label is not sufficient.

### Mandatory one-click flow

1. Validate portable root, repo root, work root and target branch.
2. Abort stale rebase/merge state when present.
3. Inspect `git status --porcelain`.
4. Safely create a named stash when real local changes require preservation.
5. Fetch/pull `codex/aays-single-runner-v5-20260706` and show the exact result.
6. Inspect the single-runner lock and recorded PID.
7. Confirm the PID belongs to the expected canonical runner process.
8. Check heartbeat freshness, not only PID existence.
9. Treat stale heartbeat or zero queue pickup as `STALE` even when the PID is alive.
10. If stale, terminate only the stale canonical runner process and remove only its stale lock.
11. Start exactly one canonical runner.
12. Wait for a fresh local heartbeat.
13. Queue a dedicated tiny smoke task.
14. Prove that the runner itself picks up and executes the smoke task.
15. Generate the smoke output inside the runner process.
16. Commit and push the smoke output and fresh heartbeat.
17. Verify the pushed output by fetching it back from GitHub.
18. Show pass/fail for each step in the portable panel.

Never start a second or parallel runner when a healthy canonical runner already exists.

### Required smoke task and artifacts

Smoke task:

`docs/chatgpt_status/_shared/queue/one_click_runner_smoke.task.json`

Required runner-generated output:

`docs/chatgpt_status/_shared/smoke/one_click_runner_smoke_latest.json`

Required human-readable output:

`docs/chatgpt_status/_shared/smoke/one_click_runner_smoke_latest.txt`

Required JSON fields:

- test_name: `one_click_runner_smoke`
- status: `passed` or `failed`
- generated_by_runner: true
- generated_at
- portable_root
- repo_root
- work_root
- branch
- pid
- lock_valid
- heartbeat_fresh
- heartbeat_at
- heartbeat_age_seconds
- queue_pickup_tested
- queue_pickup_passed
- test_task_id
- test_payload: deterministic `AAYS_SMOKE_OK` marker
- processed_task_count_before
- processed_task_count_after
- git_commit_sha
- git_push_status
- github_fetch_verified
- blocker when failed
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

The launcher itself must not fabricate this output. The runner must pick up the test task and create it.

### Required panel fields

After one click, the portable panel must show:

- App health
- canonical runner PID
- process command/path verification
- lock state
- heartbeat timestamp and age
- branch
- git fetch/pull result
- local dirty/stash result
- queue pickup test result
- processed task count before/after
- smoke file local path
- smoke file GitHub path
- commit SHA
- push result
- GitHub fetch verification result
- final health state: `HEALTHY`, `STALE`, or `FAILED`
- exact blocker when not healthy

### Runner failure states

Use explicit blockers such as:

- stale_heartbeat
- pid_alive_but_runner_not_processing
- lock_pid_mismatch
- unexpected_process_for_lock_pid
- git_pull_failed
- stash_failed
- queue_pickup_failed
- smoke_output_not_created_by_runner
- github_push_failed
- github_fetch_verification_failed

Do not show `HEALTHY` if heartbeat is stale or queue pickup has not passed.

---

## C. End-to-end acceptance test

The combined fix is accepted only when all conditions below pass in one real run:

1. User clicks `Tek Runner Başlat` once.
2. Exactly one canonical runner remains active.
3. A fresh heartbeat appears locally and is pushed to GitHub.
4. The runner picks up and executes the smoke task.
5. Both smoke files are generated by the runner and pushed.
6. ChatGPT can fetch the smoke JSON from GitHub.
7. The panel shows the real commit SHA and successful GitHub verification.
8. The Geometry Review page opens with clean Turkish UTF-8.
9. The page displays the actual loaded data paths and fetch status.
10. The page displays the latest verified rows and all source/artifact/status/report paths row by row.
11. Latest-run rows are visually distinguished.
12. Missing artifacts are explicitly marked.
13. A small real verification batch can run after the smoke test.
14. The resulting changed rows become visible on the page without manual file copying or browser-cache ambiguity.
15. No confidence is upgraded to 3.5+ without real photo download, polygon render and vision compare proof.
16. `final_ready=false` remains unchanged.
17. `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` remain unchanged.

---

## D. Required continuation after both fixes pass

Only after the runner smoke proof and browser visibility proof pass:

1. Resume the existing aays1 Ready To Sell / Geometry Review task from the next unprocessed rows.
2. Process only a small first batch.
3. Use real internet source pages.
4. Download real candidate photos when permitted and technically available.
5. Render the real existing parcel polygon.
6. Produce an explicit vision comparison artifact.
7. Write source, photo, polygon, comparison, status and report paths into the row data.
8. Mark changed rows as latest-run rows.
9. Push all real outputs to GitHub.
10. Confirm the browser page shows those rows and paths.

Do not increase progress, verified-row counts, confidence or completion percent without real pushed output proof.

## Existing reports included by reference

This combined report supersedes and incorporates:

- `docs/chatgpt_status/aays1/reports/147_ready_to_sell_geometry_review_local_visibility_blocker_20260710.md`
- `docs/chatgpt_status/aays1/reports/148_one_click_runner_recovery_and_github_smoke_test_requirement_20260710.md`
