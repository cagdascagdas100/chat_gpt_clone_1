# AAYS1 Security/Public Safety — Site Row Visibility and Provenance Fix Request

Date: 2026-07-11
Repo: `cagdascagdas100/chat_gpt_clone_1`
Branch: `codex/aays-single-runner-v5-20260706`
Canonical runner: `F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd`
Target page: `http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`

## Mandatory operating constraints

- Do not create a new runner or a parallel runner.
- Use the existing persistent single shared runner only.
- Do not treat `C:\` as canonical.
- Keep `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.
- Do not increase any row, accuracy, source, or completion metric without real output, browser proof, Git push, and remote readback.
- Preserve the existing 150 verified baseline rows.
- Continue the existing `142` visibility task and then the existing `137 -> 146` expansion chain; do not duplicate these tasks.

## User-visible problem

The Security/Public Safety matrix shows 150 rows, but it does not expose complete row-level provenance for the work being performed. The user must be able to inspect every result and every newly completed operation directly on the site, with working source, downloaded artifact, evidence, manifest, report, checksum, and runner-output links.

Observed page state:

- Visible rows: `150`
- GeoJSON features: `150`
- New/latest: `0`
- Pending runner: `not_available`
- Batch: `security_baseline_150_verified`
- Blocker shown by page: `none`
- `served_commit_sha`: `not_available`
- `artifact_sha`: `not_available`
- Page displays `MISSING / NOT DOWNLOADED` in the summary while other artifacts are shown as browser links.

This state is internally inconsistent: the page claims no blocker and ready visible rows, while required provenance and execution metadata are absent.

## Confirmed defects

### 1. The per-row report target does not exist

Every visible row currently points to:

`docs/chatgpt_status/aays1/reports/142_security_site_row_evidence_visibility_fix_completion_20260711.md`

The file is absent from the branch. Therefore the row report reference is not verifiable and cannot satisfy an HTTP-200 acceptance gate.

### 2. Report and runner paths are not browser-safe

The matrix renderer only turns paths beginning with `england_map_web/` or `data/` into browser links. Paths under `docs/chatgpt_status/...` are displayed only as repository text. The user cannot open the report or runner output from the local site.

Required fix: mirror user-facing reports and runner summaries under a browser-served path such as:

`england_map_web/data/security_public_safety/reports/`

The canonical repository path may remain in a separate field, but the site must also expose an HTTP-200 browser path.

### 3. Provenance is shared-artifact-level, not row-level

All visible rows reuse the same generic CSV, GeoJSON, manifest, and report paths. A row does not currently identify:

- exact official endpoint used,
- official source month,
- query parameters or request method,
- HTTP status,
- response SHA-256,
- downloaded/raw response path,
- source-pool SHA-256,
- row/feature selector inside the shared CSV or GeoJSON,
- row-specific evidence JSON,
- publishing commit SHA,
- artifact SHA-256,
- runner task/output that produced or last verified the row.

A generic `https://data.police.uk/` link is not sufficient row-level provenance.

### 4. Existing manifest is stale and contradicts the current site

`security_evidence_manifest.json` still describes an older task/status and older blockers. It does not contain the current publishing commit, artifact checksums, row-evidence inventory, official API response inventory, or current browser-proof result.

### 5. New work is not separately observable

The page can color genuine latest rows through `is_new_in_latest_batch`, `new_this_run`, or `changed_in_latest_run`, but there is currently no user-visible operation/run log showing work stages such as:

- queue pickup,
- candidate selection,
- official latest-month fetch,
- per-LSOA validation,
- checksum generation,
- browser validation,
- atomic publish/restore,
- Git push,
- remote readback.

Even when a task runs without publishing a new row, the user must be able to see the real operation status and its report/output path. Do not mark baseline rows as new merely to provide visual activity.

### 6. Summary fields are incomplete or misleading

`pending_runner=not_available`, `served_commit_sha=not_available`, and `artifact_sha=not_available` must be populated from real status/output evidence. `Blocker: none` must not be shown when required provenance, report files, or runner outputs are missing.

## Required row schema

Add or populate these fields for every visible Security row. Use `MISSING` only when the artifact genuinely does not exist; never create a fake link.

- `parcel_id`
- `batch_id`
- `task_id`
- `runner_output_path`
- `runner_output_browser_path`
- `candidate_status`
- `is_new_in_latest_batch`
- `changed_in_latest_run`
- `first_seen_at`
- `last_verified_at`
- `security_score_percent`
- `security_level`
- `accuracy_score_4`
- `confidence_score`
- `needs_manual_review`
- `lsoa_code`
- `lsoa_name`
- `matching_method`
- `spatial_score`
- `source_url`
- `official_source_endpoint`
- `official_source_month`
- `official_source_query`
- `official_source_http_status`
- `official_source_response_sha256`
- `official_source_response_path`
- `official_source_response_browser_path`
- `source_pool_path`
- `source_pool_sha256`
- `source_csv_path`
- `source_csv_browser_path`
- `source_csv_row_selector`
- `source_geojson_path`
- `source_geojson_browser_path`
- `source_geojson_feature_selector`
- `row_evidence_path`
- `row_evidence_browser_path`
- `source_manifest_path`
- `source_manifest_browser_path`
- `report_path`
- `report_browser_path`
- `served_commit_sha`
- `artifact_sha256`

## Required site changes

### A. Security results table

Keep the current row table, but add visible columns or expandable details for:

1. exact official endpoint and month,
2. LSOA code/name and matching method,
3. HTTP status and response checksum,
4. raw/downloaded source path,
5. row-specific evidence path,
6. CSV row selector,
7. GeoJSON feature selector,
8. task ID and runner output,
9. report path,
10. publishing commit and artifact SHA-256.

Every browser path must return HTTP 200. Repository-only paths may be displayed in addition to, not instead of, browser paths.

### B. Latest/new styling

- Apply a clearly visible `YENI BATCH` badge and distinct row styling only when the row is genuinely part of the latest published batch.
- Preserve all 150 baseline rows with no latest badge.
- When the 150-row expansion is actually published, show exactly 150 latest rows and 300 total rows.
- Provide a working `Yalnız yeni / latest` filter.

### C. Operations/run log

Add a second table or panel sourced from a browser-served JSON file, for example:

`england_map_web/data/security_public_safety/security_operations_latest.json`

Each real operation entry must contain:

- `task_id`
- `stage`
- `status`
- `started_at`
- `completed_at`
- `rows_before`
- `rows_after`
- `rows_added`
- `source_count`
- `validated_lsoa_count`
- `http_200_count`
- `failure_count`
- `output_path`
- `output_browser_path`
- `report_path`
- `report_browser_path`
- `commit_sha`
- `remote_readback_status`
- `blocker`

Pending or failed work must remain visible as pending/blocked and must not be counted as completed.

### D. Summary correction

The summary must show real values for:

- total visible rows,
- verified CSV rows,
- verified GeoJSON features,
- latest rows,
- pending runner operations,
- manual review count,
- current batch,
- real blocker,
- served commit SHA,
- manifest SHA-256,
- CSV SHA-256,
- GeoJSON SHA-256,
- report link,
- runner output link,
- last successful browser validation time.

Do not display `Blocker: none` while a required report/output is absent.

## Required files to update or create

- `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`
- `england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json`
- `england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json`
- `england_map_web/data/security_public_safety/security_evidence_manifest.json`
- `england_map_web/data/security_public_safety/security_operations_latest.json`
- `england_map_web/data/security_public_safety/row_evidence/*.json`
- `england_map_web/data/security_public_safety/reports/*.md` or browser-renderable equivalents
- `england_map_web/data/security_public_safety/runner_outputs/*.json`
- `docs/chatgpt_status/aays1/automation/142_security_site_row_evidence_visibility_fix.ps1`
- `docs/chatgpt_status/aays1/automation/145_security_official_api_lsoa_validation.ps1`
- `docs/chatgpt_status/aays1/automation/146_security_strict_multiwork_orchestrator.ps1`
- `docs/chatgpt_status/aays1/automation/147_security_300_browser_validation.ps1`

## Acceptance criteria

1. Existing 150 baseline rows remain unchanged and none is marked latest.
2. Every row exposes working official-source, CSV, GeoJSON, row-evidence, manifest, report, and runner-output links, or an explicit `MISSING` label without a fake link.
3. Every browser link checked by the validation script returns HTTP 200.
4. The missing 142 completion report is created and mirrored to a browser-served path.
5. `served_commit_sha` and all required artifact SHA-256 values are populated from real Git/GitHub and file evidence.
6. The Security manifest reflects the current task, current batch, exact official-source evidence, file checksums, browser proof, and remote readback.
7. The operations table shows real stages and statuses without counting pending work as completed.
8. Chrome/Selenium confirms baseline total `150`, latest `0`, GeoJSON `150`, working links, and zero severe console errors before expansion.
9. After strict expansion gates pass, Chrome/Selenium confirms total `300`, latest `150`, GeoJSON `300`, working links, and zero severe console errors.
10. Git push and remote readback pass for all published site artifacts.
11. `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.

## Execution order

1. Fix browser-safe report/output/evidence visibility for the current 150-row baseline.
2. Produce and push the real 142 output, completion report, browser proof, checksums, and remote readback.
3. Confirm the corrected page to the user.
4. Only then continue the existing `137 -> 146` strict 150-to-300 expansion.
5. If any gate fails, restore expanded site files and publish only truthful blocker evidence.

## Current release gate

`BLOCKED_SITE_PROVENANCE_VISIBILITY`

The Security expansion must not be presented as complete, and no new rows may be claimed, until the defects above are fixed and the browser proof passes.
