# AAYS / TerraYield — Parcel Label Site Visibility + One-Click Runner Combined Fix Report

Date: 2026-07-10

Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Canonical runner: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
Portable site: `http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`

## 1. User-visible problem

The Program Parcel Layer Matrix still shows Gas Emissions instead of a usable Parcel Label / Distance to Nearby Property Types view. The existing real Parcel Label pilot data is not visible row-by-row with its evidence, source URL, source path, local evidence/report paths, accuracy, status, and latest-change marker.

The user must be able to open the site and inspect every Parcel Label row directly, including newly prepared rows and runner-completed rows, without opening GitHub manually.

## 2. Current verified data state

- Real source-backed pilot rows: `6`
- Prepared pending bulk rows: `88`
- Completed bulk rows proven by real runner output: `0`
- The 88 prepared rows must never be displayed as completed until real completed status/output and site synchronization exist.
- `final_ready=false`

Existing data source:

`england_map_web/data/distance_property_types/distance_property_types_verified.csv`

Required visibility artifacts:

- `england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json`
- `england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json`
- `england_map_web/data/distance_property_types_updates/latest_changes.json`
- `docs/chatgpt_status/distance_property_types/reports/141_distance_property_types_site_visibility_fix_report_20260710.md`

## 3. Required Parcel Label site behavior

### 3.1 Layer selection

Add and verify a dropdown option named:

`Distance to Nearby Property Types / Parcel Label`

Selecting it must load the Parcel Label dataset instead of leaving Gas Emissions active.

### 3.2 Row-by-row visibility

The page must show the 6 real pilot rows immediately. Each row or expandable row detail must expose:

- `parcel_id`
- `parcel_ref`
- `selected_property_type`
- `selected_color_category`
- `accuracy_score_4`
- `accuracy_label_4`
- `confidence_percent` when available
- `source_url`
- `source_title`
- `source_date`
- `source_path`
- `downloaded_source_path` or equivalent local evidence path when a source file was downloaded
- `report_path`
- `evidence_path`
- `payload_path`
- `queue_task_path`
- `official_source_evidence`
- `web_source_evidence`
- `map_source_evidence`
- `photo_ai_evidence`
- `photo_ai_image_path`
- `matching_method`
- `needs_manual_review`
- `manual_review_reason`
- `candidate_status`
- `changed_in_latest_run`
- `change_reason`
- `geometry_status`
- `batch_id`
- `task_id`

Long source/evidence fields may use an expandable detail drawer, but their values and paths must remain visible and copyable.

### 3.3 Source/path presentation

- Web URLs must be clickable.
- Repository paths must be shown as text and, where practical, linked to the local or GitHub view.
- Local downloaded source/evidence/report paths must be shown exactly as stored.
- Missing fields must display `not_available`; they must not be silently hidden.

### 3.4 New and pending row distinction

Use visibly distinct badges and row styling:

- `VISIBLE_PILOT_SOURCE_BACKED`
- `NEW_PREPARED`
- `PENDING_RUNNER`
- `COMPLETED_VISIBLE`
- `NEEDS_MANUAL_REVIEW`
- `BLOCKED`

Newly prepared rows must be visibly different from existing pilot rows. Runner-completed rows may become `COMPLETED_VISIBLE` only after real completed status/output, site artifact generation, GitHub push, and remote readback succeed.

### 3.5 Current changes panel

Add a panel titled:

`Distance Property Types / Parcel Label - Guncel Degisiklikler`

The panel must show:

- last update time
- latest task ID
- batch ID
- added row count
- updated row count
- completed-visible count
- pending-runner count
- manual-review count
- blocker
- output paths
- commit SHA
- remote readback status
- `final_ready`

## 4. One-click runner recovery integration

This report incorporates the requirements from task/report 162.

The existing `Tek Runner Baslat` button in the F portable control panel must execute one deterministic sequence and must never start a second runner.

Required sequence:

1. Verify portable root and canonical repo root.
2. Verify remote repository and branch.
3. Check git merge/rebase state and worktree status.
4. Safely stash dirty changes when necessary.
5. Verify lock file and lock PID.
6. Verify whether the lock PID is alive.
7. Remove a lock only after proving its PID is dead.
8. Reconcile panel PID, lock PID, and heartbeat PID.
9. Require heartbeat freshness of 60 seconds or less before PASS.
10. Pull/sync the target branch or write an explicit blocker.
11. Queue an immediate priority smoke-control task inside the same shared runner.
12. Have the real runner create a unique smoke artifact.
13. Commit and push the artifact to the target branch.
14. Fetch origin and read back the exact artifact.
15. Display stage-by-stage PASS/FAIL, artifact path, run ID, and commit SHA in the panel.

Required smoke paths:

- `docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_latest.json`
- `docs/chatgpt_status/_shared/smoke_tests/one_click_runner_smoke_push_proof_latest.json`
- `docs/chatgpt_status/_shared/blockers/one_click_runner_blocker_latest.json`

Required smoke content:

- unique `run_id`
- `generated_by_real_runner=true`
- payload `AAYS_ONE_CLICK_RUNNER_SMOKE_OK`
- canonical runner path
- panel PID
- lock PID
- heartbeat PID
- heartbeat timestamp and age
- artifact commit SHA
- push result
- remote readback result
- exact artifact path

## 5. Combined acceptance criteria

The fix is accepted only when all conditions below are proven:

1. Parcel Label appears in the matrix dropdown and is selectable.
2. The real 6 source-backed pilot rows are visible row-by-row.
3. Each row exposes source URL/path, evidence paths, accuracy, status, and change marker.
4. Newly prepared rows are clearly marked `NEW_PREPARED` and `PENDING_RUNNER`.
5. The 88 pending rows are not counted as completed.
6. The Parcel Label current-changes panel is visible.
7. The two visibility JSON files and latest-changes JSON exist on the target branch and F portable site root.
8. `Tek Runner Baslat` performs the complete recovery/smoke flow with one click.
9. Repeated clicks do not start a parallel runner.
10. Panel PID equals lock PID equals heartbeat PID.
11. Heartbeat is fresh and belongs to the canonical F portable runner.
12. The real runner generates the smoke artifact.
13. GitHub push succeeds and remote readback returns the same `run_id` and payload.
14. The panel displays artifact path and commit SHA.
15. Parcel Label candidate production resumes only after these checks pass.
16. Any failure produces an explicit blocker file and leaves progress unchanged.

## 6. Safety invariants

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

No fake completed marker, fake 100 percent, fake site row count, or fake GitHub proof is allowed.

## 7. Resume rule

Do not generate additional Parcel Label candidates until the combined site-visibility and one-click runner acceptance checks are proven through real GitHub artifacts. After proof exists, resume with a small batch of real internet-sourced candidates and expose them on the site as `NEW_PREPARED` / `PENDING_RUNNER` before completion.
