# AAYS1 / Distance Property Types - Site Visibility Blocker Report

Date: 2026-07-10
Task id: 158_aays1_distance_property_types_site_visibility_blocker_fix_20260710
Status: BLOCKER_REPORT_FOR_CODEX_FIX
Branch: codex/aays-single-runner-v5-20260706
Canonical runner: F:\\TerraYield_AAYS_Portable\\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd
Final ready: false

## User-visible problem

The local Program Parcel Layer Matrix page is open at:

`http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`

The page currently shows the `Gas Emissions` layer with 3,533 records. The user cannot see the `Distance to Nearby Property Types` / `distance_property_types` candidates that ChatGPT prepared in batches 136 through 157.

The user needs the prepared candidates to be visible row-by-row on the same site, including:

- candidate/property label row
- selected category from the six-category contract
- source URL
- local/GitHub source path
- payload/task path
- accuracy score
- changed/new-run marker
- runner/completed status
- any manual-review reason

## Root problems detected

1. **Prepared candidates are not surfaced in the website table.**
   - Candidate payloads are written under `docs/chatgpt_status/aays1/inputs/`.
   - Queue tasks are written under `docs/chatgpt_status/aays1/queue/`.
   - They are not currently visible from the page's `data/program_layer_matrix` table.

2. **Runner is active but not processing the queued tasks.**
   - Latest heartbeat reports `runner_active=true`, `pid_alive=true`, and `lock_valid=true`.
   - It also reports `queue_detected_count=61` and `processed_task_count=0`.
   - Completed files for at least task 136 and 157 are missing/not found.

3. **The page appears to expose only the already-generated program layers.**
   - Screenshot shows panels for Safety/Security, Gas Emissions, Internet Access, and Topography.
   - There is no visible Distance Property Types current-changes panel.
   - The dropdown is currently on Gas Emissions. If the Distance Property Types option exists, it is not obvious from the user view; if it does not exist, it must be added.

4. **No pending-candidate view exists.**
   - Even before runner completion, the user needs to see prepared but unprocessed rows as `pending_runner` / `prepared_not_visible` rows.
   - The page must clearly distinguish:
     - `visible_program_layer_row`
     - `prepared_pending_runner_row`
     - `manual_review_required`
     - `new_in_latest_batch`

## Required fix

Codex/runner must implement a site-visible Distance Property Types status surface before new candidate expansion continues.

### A. Add or fix page integration

Update the local site so that the layer dropdown and table can show a `Distance Property Types` layer from the F portable data root.

Required display name:

`Distance to Nearby Property Types`

Required layer key:

`distance_property_types`

Required site source roots:

- `F:\\TerraYield_AAYS_Portable\\data\\program_layer_matrix\\distance_property_types.geojson`
- `F:\\TerraYield_AAYS_Portable\\data\\distance_property_types\\distance_property_types_verified.csv`
- `F:\\TerraYield_AAYS_Portable\\data\\distance_property_types\\distance_property_types_verified.geojson`
- `F:\\TerraYield_AAYS_Portable\\data\\distance_property_types\\evidence_manifest.json`
- `F:\\TerraYield_AAYS_Portable\\data\\distance_property_types_updates\\latest_changes.json`

If these files do not exist locally, the runner must create/update them from the existing candidate payloads without fake data.

### B. Add pending-candidate table fallback

Until completed output exists, the website must read prepared candidate payloads from:

- `docs/chatgpt_status/aays1/inputs/136_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/137_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/138_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/139_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/140_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/141_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/142_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/143_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/144_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/145_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/146_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/147_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/148_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/149_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/150_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/151_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/152_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/153_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/154_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/155_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/156_distance_property_types_append_payload_20260710.json`
- `docs/chatgpt_status/aays1/inputs/157_distance_property_types_append_payload_20260710.json`

The fallback must show these rows as `prepared_pending_runner=true` and **must not** count them as completed/visible production rows.

### C. Required columns for site table

The Distance Property Types view must include these columns when data is available:

- `batch_id`
- `task_id`
- `candidate_status`
- `parcel_id`
- `name`
- `selected_property_type`
- `selected_color_category`
- `accuracy_score_4`
- `accuracy_label_4`
- `confidence_percent`
- `source_url`
- `source_title`
- `source_date`
- `source_path`
- `payload_path`
- `queue_task_path`
- `official_source_evidence`
- `web_source_evidence`
- `map_source_evidence`
- `matching_method`
- `needs_manual_review`
- `manual_review_reason`
- `changed_in_latest_run`
- `change_reason`
- `geometry_status`

### D. Add current-changes panel

Add a new panel:

`Distance Property Types - Guncel Degisiklikler`

The panel must show:

- last prepared batch
- last completed batch, if any
- prepared pending candidate count
- visible program layer count
- new rows in latest batch
- blocker summary
- `fake_data=false`
- `final_ready=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`

Suggested JSON file:

`england_map_web/data/distance_property_types_updates/latest_changes.json`

### E. Highlight new rows

Newly prepared rows must be visibly marked with a distinct table marker, e.g.:

- `NEW_PREPARED`
- `PENDING_RUNNER`
- `SOURCE_UPGRADE_REQUIRED`
- `MANUAL_REVIEW_REQUIRED`

Do not use styling that implies completion unless a completed status file exists.

### F. Runner processing requirement

The runner must either:

1. process queued tasks 136 through 157 and write completed status files, or
2. write an explicit blocker output explaining why it cannot process them.

Minimum expected status paths:

- `docs/chatgpt_status/aays1/status/136_aays1_distance_property_types_append_14_20260710_completed.json`
- `docs/chatgpt_status/aays1/status/157_aays1_distance_property_types_real_source_candidates_20260710_completed.json`

If processed, update:

- `england_map_web/data/program_layer_matrix/distance_property_types.geojson`
- `england_map_web/data/distance_property_types/distance_property_types_verified.csv`
- `england_map_web/data/distance_property_types/distance_property_types_verified.geojson`
- `england_map_web/data/distance_property_types/evidence_manifest.json`
- `england_map_web/data/distance_property_types_updates/latest_changes.json`

## Acceptance criteria

- The website dropdown includes `Distance to Nearby Property Types`.
- The user can select the layer and see rows for all prepared candidates 136 through 157 at least as `prepared_pending_runner` rows.
- Each row displays source URL and source/payload/queue path.
- New rows are visibly marked.
- Completed rows and pending rows are not mixed without status labels.
- Site-visible completed row count is only increased when completed output exists.
- `fake_data=false` remains true in all outputs.
- `final_ready=false` remains true in all outputs.
- `db_write=false`, `migration=false`, and `production_deploy=false` remain true in all outputs.
- No new runner is started.
- Canonical runner remains `F:\\TerraYield_AAYS_Portable\\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`.

## Stop condition for ChatGPT candidate expansion

ChatGPT should pause further candidate generation until this blocker is fixed or a new runner output proves that the site can show the prepared rows.
