# CODEX FIX REPORT — Topography Matrix Row Visibility and Evidence Links

Date: 2026-07-11

Repository: `cagdascagdas100/chat_gpt_clone_1`

Branch: `codex/aays-single-runner-v5-20260706`

Canonical runtime: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`

Existing task to continue after this fix: `aays1-159-topography-official-source-acceleration-bridge-20260711`

## Safety and execution constraints

- Do not create a new runner or a parallel runner.
- Use only the existing F portable single shared runner.
- Do not treat any C drive checkout as canonical.
- Keep `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.
- Do not create numeric elevation values without a real source response or raster sample, method, source URL/path, and reproducible evidence.
- Apply this visibility fix first, then continue the existing task 159 chain. Do not create a duplicate Topography task.

## User-visible defect

The Topography page at:

`http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`

shows three rows, but it does not provide a complete, current, row-by-row view of all operations and their evidence. It also does not clearly distinguish newly completed operations from previous rows. The page currently remains tied to task 154 while task 159 is the active continuation task.

## Verified current state

Current visible data file:

`england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json`

Current status file:

`england_map_web/data/program_layer_matrix/topography_visible_status_latest.json`

Observed state:

- `visible_rows_count=3`
- `latest_task_id=topography-154-copdem-odata-geocell-sampling-20260711`
- all three rows have `changed_in_latest_run=true`
- all numeric elevation and regional-difference fields are still null
- `local_source_path=not_available`
- the row `source_file_path` points to a queue contract rather than a downloaded/raw/processed source artifact
- the page summary reports `source_manifest_path`, `served_commit_sha`, and `artifact_sha` as unavailable
- the UI shows `Pending runner: not_available`
- the page does not show task 159 stage progress while the task is pending or running

## Root causes

### 1. The page consumes only a replace-in-place latest-row file

The page loads `topography_visible_rows_latest.json`. There is no append-only operation ledger. Every new run replaces the prior visible state, so the user cannot inspect all completed source checks, downloads, samples, calculations, browser checks, and blocked attempts as separate rows.

### 2. Current activity is published too late

Task 159 updates the visible row file only after the inherited 158 chain plus SRTM30, ASTER30, and consensus work. During long execution the site continues to show task 154. A start/stage heartbeat is not published to a site-facing operation feed after every stage.

### 3. Repository evidence paths are not browser links

In `TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`, `webRelative()` creates links only for paths beginning with `england_map_web/` or `data/`. Paths beginning with `docs/` and `outputs/` are rendered as plain `REPO PATH` text. The user therefore cannot open report, status, queue, source snapshot, fixture, or runner-output evidence from the page.

### 4. Source provenance is incomplete in the visible row contract

The visible row contract does not consistently expose:

- exact request URL
- exact dataset/product identifier
- raw response or raster path
- processed fixture path
- report path
- status path
- runner-output path
- local F path when a file was downloaded
- served browser URL for that artifact
- file SHA-256
- file size
- acquisition timestamp
- sampling/calculation method
- source-specific numeric value and unit

A generic catalogue URL and a queue file are not sufficient source evidence for a numeric result.

### 5. New-row semantics are not durable

All current rows contain `changed_in_latest_run=true`, but there is no reliable batch identity, previous-batch identity, first-seen timestamp, or latest-change commit comparison. Old rows can remain styled as new.

### 6. Summary fields are generic and do not match the Topography contract

The summary tries generic fields such as `source_csv`, `source_geojson`, and `source_manifest_path`. Current Topography data does not provide these top-level values, producing `not_available` even when report and queue paths exist on each row.

### 7. Browser acceptance does not verify evidence accessibility

Current browser checks verify row count, badge/column text, and console errors. They do not verify that every expected evidence link resolves with HTTP 200, that newly completed operations are visually distinct, or that the page shows the current task and stage count.

## Required implementation

### A. Add an append-only site-facing operation ledger

Create and maintain:

`england_map_web/data/program_layer_matrix/topography_operations_latest.json`

The file must contain one row per operation, not only one row per parcel. Minimum operation types:

- task pickup/start
- coordinate evidence read
- boundary lookup
- EU-DEM request/sample
- SRTM90 request/sample
- Copernicus catalogue request/readback
- EA LiDAR source check
- OS Terrain source check
- SRTM30 request/sample
- ASTER30 request/sample
- regional control sample
- regional average calculation
- parcel height-difference calculation
- multi-source consensus calculation
- site publication
- browser validation
- GitHub push/readback
- blocked/unavailable source attempt

Minimum top-level fields:

- `task_id`
- `batch_id`
- `previous_batch_id`
- `updated_at`
- `stage_completed_count`
- `stage_total_count`
- `operation_count`
- `new_operation_count`
- `current_stage`
- `runner_status`
- `rows`
- all safety flags set false as required

Minimum row fields:

- `operation_id`
- `stage_no`
- `operation_type`
- `task_id`
- `batch_id`
- `parcel_id`
- `parcel_ref`
- `status`
- `is_new_in_latest_batch`
- `started_at`
- `completed_at`
- `source_name`
- `source_url`
- `request_url`
- `dataset_id`
- `product_id`
- `method`
- `numeric_value`
- `unit`
- `accuracy_score_4`
- `confidence_percent`
- `repo_artifact_path`
- `served_artifact_url`
- `local_source_path`
- `artifact_sha256`
- `artifact_size_bytes`
- `report_path`
- `status_path`
- `runner_output_path`
- `blocker`
- `needs_manual_review`
- `final_ready=false`
- `fake_data=false`

Do not fabricate unavailable paths or numbers. Use explicit values such as `not_downloaded`, `request_failed`, or `not_applicable`, with the corresponding blocker/error.

### B. Publish stage progress atomically

Task 159 and its inherited chain must update the operation ledger at task start and after every stage. Use atomic writes. The page must show current progress before the full batch completes.

Required visible progress fields:

- current task ID
- current stage name
- completed stages / total stages
- last successful source operation
- last blocked operation
- last update timestamp
- runner state

### C. Keep parcel result rows and operation rows separate

Retain `topography_visible_rows_latest.json` as the current parcel-result table.

Add a second page section or tab named:

`Yeni İşlemler / Kaynak Kanıtları`

It must render `topography_operations_latest.json`.

The page must provide:

1. `Yeni işlemler` — only rows where `is_new_in_latest_batch=true`
2. `Tüm işlemler` — complete ledger
3. `Parsel sonuçları` — current parcel-level result rows
4. `Blocker işlemleri` — blocked or unavailable operations

### D. Make all evidence paths clickable and verified

Update path resolution so these prefixes can become safe browser links:

- `england_map_web/`
- `data/`
- `docs/`
- `outputs/`

Do not use `file://` links.

Preferred behavior:

- map repository paths to a safe read-only served URL on port 8012, or
- add a safe allowlisted read-only artifact endpoint.

Only allow repository-relative paths under the approved prefixes. Reject traversal sequences.

For every rendered artifact link, display one of:

- `HTTP 200 / AVAILABLE`
- `MISSING`
- `NOT DOWNLOADED`
- `BLOCKED`

The browser test must open or request each required link and record the HTTP status.

### E. Expose complete source provenance

For every numeric elevation or calculated difference, the visible parcel row and operation ledger must identify:

- exact source URL/request URL
- raw response/raster evidence path
- processed rows/fixture path
- sampling method and interpolation
- source CRS and coordinate used
- numeric result and unit
- calculation explanation
- checksum when a local artifact exists
- report/status/runner-output paths

If a source was only checked for reachability, label it `source_check_only`; do not present it as sampled numeric evidence.

### F. Correct new-operation styling

Use a batch-based comparison:

- assign a unique `batch_id`
- retain `previous_batch_id`
- set `is_new_in_latest_batch=true` only for operations created or materially changed in the current batch
- reset prior rows to false

Visual requirements:

- new operations: strong green/blue `YENİ` badge and distinct background
- running operations: blue `RUNNING`
- completed source-backed operations: green `VERIFIED`
- blocked operations: red `BLOCKED`
- manual review: amber `MANUEL İNCELEME`
- source check without numeric sample: neutral `SOURCE CHECK ONLY`

### G. Improve table usability

The current table has too many narrow columns and heavily wrapped headers.

Required changes:

- sticky first columns: status, operation/task, parcel, source
- group source/evidence fields
- provide an expandable row-detail panel for long paths and provenance
- keep full text available without hiding data
- add copy buttons for repository path, local path, source URL, and checksum
- preserve filtering and search
- show row counts for new/all/blocked/result sections

### H. Topography-specific summary

Replace generic unavailable summary values with explicit Topography fields:

- current task
- current batch
- stage progress
- parcel result row count
- operation ledger row count
- new operation count
- numeric source-backed row count per dataset
- regional control count
- height-difference value count
- source snapshot path
- consensus evidence path
- latest report path
- latest status path
- latest runner-output path
- served commit SHA
- remote readback status
- final and safety flags

## Acceptance criteria

All conditions below must pass before continuing the numeric expansion stage of task 159:

1. The page shows the active task 159 ID, not task 154, once task 159 starts.
2. A task-start operation row appears within one runner scan/stage update.
3. Every completed or blocked stage appears as an individual operation row.
4. Three parcel result rows remain visible.
5. New operations are visually distinct from previous operations.
6. The page provides separate new/all/result/blocked views.
7. `docs/` and `outputs/` evidence paths are clickable through a safe read-only server mapping.
8. Required source/report/status/runner-output links return HTTP 200 when the artifact exists.
9. Missing or undownloaded files are explicitly labelled; no false available state is shown.
10. Numeric values have source URL, evidence path, method, coordinate, unit, and calculation proof.
11. Browser validation renders at least three parcel rows and the operation ledger.
12. Browser validation confirms zero severe console errors.
13. Browser validation confirms latest-operation styling and current stage progress.
14. Browser validation records link-integrity results.
15. GitHub push and remote readback proof are written.
16. `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.

## Required proof outputs

Create or update these outputs:

- `england_map_web/data/program_layer_matrix/topography_operations_latest.json`
- `england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json`
- `england_map_web/data/program_layer_matrix/topography_visible_status_latest.json`
- `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`
- `docs/chatgpt_status/topography/reports/topography_matrix_visibility_and_link_validation_20260711.json`
- `docs/chatgpt_status/topography/reports/topography_matrix_visibility_and_link_validation_20260711.md`
- `docs/chatgpt_status/topography/runner_outputs/topography_matrix_visibility_fix_latest.json`

## Continuation order

1. Implement and browser-validate this page visibility/evidence-link fix using the existing single shared runner environment.
2. Push and verify remote readback.
3. Continue the existing task 159 chain.
4. Publish every new source operation and numeric result to the page as it occurs.
5. Keep final readiness false until the primary CopDEM raster, real parcel boundaries, and official LiDAR/OS numeric validation criteria are genuinely satisfied.
