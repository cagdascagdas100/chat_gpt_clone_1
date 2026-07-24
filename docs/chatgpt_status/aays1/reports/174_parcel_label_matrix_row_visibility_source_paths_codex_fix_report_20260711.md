# AAYS / TerraYield — Parcel Label Matrix Row Visibility and Source Paths — Codex Fix Report

## Scope

- Repo: `cagdascagdas100/chat_gpt_clone_1`
- Branch: `codex/aays-single-runner-v5-20260706`
- Page key: `aays1`
- Layer: `Parcel Label / Distance Property Types`
- Browser page: `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`
- Canonical runtime: the existing single shared F portable runner only

## User-visible failure

The website loads and shows 98 tracked rows, but it does not show the newer Parcel Label work prepared after batch 161. Rows created or enriched in batches 163–171 are absent. The user therefore cannot inspect the latest candidates row by row with source URL, payload, queue, report, evidence, downloaded/local source, and runner-output paths.

The page also reports misleading summary metadata:

- `Blocker: none` although the status artifact contains an active bulk blocker.
- `Görünür / izlenen satır: 98` combines two different concepts; only 6 rows are source-backed/visible pilot rows, while 98 are tracked rows.
- `Yeni / latest: 4` and `Batch: 161` are stale.
- `source_url`, `source_csv`, `source_geojson`, `served_commit_sha`, and `artifact_sha` show `not_available` even when row-level source URLs and repo artifacts exist.
- `docs/chatgpt_status/...` paths are displayed as non-clickable `REPO PATH`; only `england_map_web/...` paths become browser links.
- New rows and source/address-enriched rows are not visually distinguished from old pending rows.

## Confirmed data-state mismatch

Current served artifacts are stale:

- `england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json`
  - `updated_at`: `2026-07-11T01:10:56.760662+00:00`
  - `latest_batch_id`: `161`
  - `total_tracked_count`: `98`
  - `pending_runner_count`: `92`
- `distance_property_types_status_latest.json` repeats the same batch/count state.
- `distance_property_types_latest_changes.json` contains only the 4 rows from batch 161.
- `distance_property_types_source_manifest_latest.json` lists inputs only through batch 161.
- Task 169 runner output and browser/HTTP proof are absent from the remote branch.

Newer inputs and enrichment evidence exist under `docs/chatgpt_status/aays1/inputs`, `evidence`, `reports`, and `status`, but they are not consolidated into the web-served matrix artifacts.

## Confirmed frontend defects

File: `england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html`

1. `renderSummary()` computes blocker with:
   `s.blocker || d.bulk_blocker || d.blocker ...`
   It omits `s.bulk_blocker`, so the status-file blocker is hidden and the UI shows `none`.

2. The first metric uses `state.rows.length` while the label says `Görünür / izlenen satır`. Tracked and actually visible/source-backed counts must be separate metrics.

3. `webRelative()` only links paths beginning with `england_map_web/` or `data/`. Repo-relative `docs/chatgpt_status/...` paths must resolve to a browser URL such as `../docs/chatgpt_status/...`.

4. The distance table omits important audit columns:
   - `change_kind`
   - `change_reason`
   - `last_updated`
   - `downloaded_source_path`
   - `source_validation_ok`
   - `source_validation_http_status`
   - `source_validation_final_url`
   - `geometry_status`

5. Visual states only cover generic `latest`, `pending`, `manual`, and `blocked`. The page needs distinct badges/styles for:
   - `NEW ROW`
   - `SOURCE UPGRADED`
   - `ADDRESS / GEOMETRY ENRICHED`
   - `UPDATED THIS RUN`
   - `VISIBLE / SOURCE-BACKED`
   - `PENDING GEOMETRY`

6. The summary expects one top-level `source_url`, although this layer has many row-level source URLs. It should display counts and manifest links rather than `not_available`.

## Required Codex implementation

### A. Repair the consolidation pipeline

Create or repair a deterministic builder that:

1. Reads the current `distance_property_types_all_rows_latest.json`.
2. Reads every valid `docs/chatgpt_status/aays1/inputs/*distance_property_types*.json` payload.
3. Reads relevant enrichment/source-quality artifacts for the same parcel IDs.
4. Deduplicates by `parcel_id`.
5. Applies precedence in this order:
   - newest geometry/address enrichment
   - newest source-quality upgrade
   - newest candidate input
   - existing matrix row
6. Never invents coordinates or polygons. Unbound rows remain `geometry_status=NOT_BOUND` and pending.
7. Preserves all source and audit paths per row.
8. Produces:
   - `england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json`
   - `distance_property_types_status_latest.json`
   - `distance_property_types_latest_changes.json`
   - `distance_property_types_source_manifest_latest.json`
   - `distance_property_types_row_artifact_index_latest.json`
9. Adds top-level metadata:
   - `served_commit_sha`
   - `artifact_sha`
   - `generated_at`
   - `source_url_count`
   - `source_snapshot_count`
   - `latest_operation_id`
   - `latest_operation_row_count`
10. Computes counts from the actual unique-row union; do not hard-code 98, 182, or another target.

### B. Make all audit paths visible and usable

Each row must expose, when available:

- `source_url`
- `source_path`
- `downloaded_source_path`
- `local_source_path`
- `payload_path`
- `queue_task_path`
- `report_path`
- `evidence_path`
- `runner_output_path`
- `source_manifest_path`

Repo-relative paths under both `england_map_web/...` and `docs/...` must be clickable in the browser. External/local disk paths must remain plain text with an explicit `LOCAL PATH — BROWSER OPEN NOT AVAILABLE` label; do not create fake browser links.

### C. Fix summary semantics

Show separate metrics:

- `İzlenen toplam`
- `Kaynaklı görünür`
- `Pending runner`
- `Geometri bağlı`
- `Geometri bekliyor`
- `Yeni satır`
- `Güncellenen satır`
- `Kaynağı indirilen`
- `Manuel inceleme`
- `Aktif blocker`
- `Served commit`
- `Artifact SHA`

Read blocker precedence from both status and data artifacts, including `s.bulk_blocker`.

### D. Distinguish new work visually

Add row fields and badges:

- `change_kind=NEW_ROW`
- `change_kind=SOURCE_UPGRADED`
- `change_kind=ADDRESS_GEOMETRY_ENRICHED`
- `change_kind=UNCHANGED`

Provide filters for new rows and updated rows. Use a visibly different row background/border for new and enriched rows without changing truth status.

### E. Freshness and served-sync behavior

- Display artifact `generated_at` and age.
- Show `STALE` when the served artifact predates the latest accepted input/report.
- Do not show `Blocker: none` while consolidation, geometry, runner output, or browser proof is pending.
- Cache-busting must remain enabled.

## Acceptance tests

Codex must provide all of the following before marking this fix complete:

1. Unique row count in the browser equals the unique `parcel_id` count in the consolidated JSON.
2. Every valid current candidate input through batch 171 is either represented or listed in an explicit rejection report with reason.
3. Newly added and enriched rows are visibly distinguishable and filterable.
4. At least one row demonstrates each working browser-link type:
   - `england_map_web/...`
   - `docs/chatgpt_status/...`
   - external `https://...`
5. Missing/local-only paths are clearly labelled and not represented as downloadable.
6. Header blocker matches the status artifact.
7. Header shows non-empty `served_commit_sha` and `artifact_sha`.
8. Browser console errors: `0`.
9. HTTP 200 for the page and all generated web artifacts.
10. Browser proof records exact displayed totals, latest/new counts, and at least 5 newly surfaced row IDs.
11. GitHub remote readback verifies every changed artifact.
12. `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.

## Required proof outputs

- `docs/chatgpt_status/aays1/runner_outputs/174_aays1_parcel_label_matrix_visibility_source_paths_fix_output.json`
- `docs/chatgpt_status/aays1/runner_outputs/174_aays1_parcel_label_matrix_visibility_source_paths_browser_proof.json`
- `docs/chatgpt_status/aays1/status/174_aays1_parcel_label_matrix_visibility_source_paths_fix_status.json`
- `docs/chatgpt_status/aays1/reports/174_aays1_parcel_label_matrix_visibility_source_paths_fix_completion_report.md`

## Safety

- Keep the existing single shared runner.
- Do not open a new or parallel runner.
- No fake data.
- No database write.
- No migration.
- No production deployment.
- No completed claim without runner output, browser proof, and GitHub remote readback.
- `final_ready=false`.