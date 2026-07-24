# Gas Emissions — 8012 stale publish and new-row visibility bug report for Codex

Date: 2026-07-11  
Branch: `codex/aays-single-runner-v5-20260706`  
Page key: `gas_emissions`  
Status: `BLOCKED_LOCAL_8012_STALE_PUBLISH_AND_ROW_PRESENTATION`

## User-visible problem

The user-provided screenshot of the local Parcel Layer Matrix shows:

- URL: `http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`
- selected layer: `Gas Emissions`
- visible row count: `24`
- GeoJSON feature count: `3533`
- `final_ready=false`
- `fake_data=false`
- first visible rows still reference report `147_gas_emissions_site_visibility_and_one_click_runner_combined_fix_20260710.md`
- old rows still show `changed_in_latest_run=true`
- the visible source material path says `source_csv: not_available`

The branch currently contains a canonical 28-row visible artifact and a status marker with `visible_rows_count: 28`. Therefore the local 8012 page is serving an older published/static copy and does not show the four newly added official rows.

## Confirmed repository state

Canonical data artifact:

- `england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json`
- status: `OFFICIAL_VISIBLE_SAMPLE_ROWS_EXPANDED_28`
- previous rows: `24`
- new rows: `4`
- current rows: `28`
- source accuracy: `3.4/4`

Canonical status marker:

- `england_map_web/data/program_layer_matrix/gas_emissions_status_latest.json`
- `visible_rows_count: 28`
- browser smoke for 28 rows is still pending

The existing 28-row smoke task is still queued:

- `docs/chatgpt_status/gas_emissions/queue/gas_emissions_28_browser_smoke_20260711_01.task.json`

## Root causes / UI defects

### 1. 8012 serves a stale publish root

The browser page uses cache-busting query parameters and `cache: no-store`, so the 24-row result is not explained by normal browser caching. The static server is serving a local file tree that has not been synchronized to the current branch content.

Required fix:

- identify the exact filesystem root served by port 8012;
- ensure it is the canonical active worktree or atomically publish the latest branch files into that served root;
- after publish, verify the served JSON itself contains `visible_row_count: 28` and 28 row objects;
- expose the served commit SHA and visible-row artifact SHA in the UI or `/health` output so stale publishes are immediately detectable.

### 2. New-row styling is hidden by manual-review precedence

The matrix page currently evaluates `needs_manual_review` before `changed_in_latest_run` in both `rowClass()` and `statusBadge()`. All official rows require manual review, so newly added rows are displayed only as `MANUEL İNCELEME`, not as new rows.

Required fix:

- show both states simultaneously, for example `YENİ / LATEST` plus `MANUEL İNCELEME`;
- give `changed_in_latest_run=true` rows a distinct background/border even when manual review is also true;
- ensure only the latest four rows are marked as changed after the 28-row publish.

### 3. Source-path presentation is incomplete/misleading

The page displays:

- online source URL;
- `source_csv: not_available`;
- a `source_path` that points to the visible JSON artifact, not to a downloaded raw source CSV.

Required fix:

- distinguish these fields explicitly:
  - `source_url`: official online source;
  - `source_local_raw_path`: downloaded/raw local source file, or `NOT_DOWNLOADED`;
  - `visible_rows_artifact_path`: generated canonical JSON;
  - `report_path`: batch report;
  - `status_path`: status marker;
- never label the generated visible JSON as the raw source CSV;
- make file paths copyable and, where the local application supports it safely, clickable/openable.

### 4. Important row evidence is not visible in the matrix

The canonical rows contain `calculation_explanation` and `parcel_binding_status`, but the Gas Emissions table does not display them.

Required fix:

Add visible columns for:

- calculation explanation;
- parcel-binding status;
- source-local raw path/materialization status;
- visible artifact path;
- status path;
- report path;
- changed-in-latest-run.

## Required acceptance criteria

1. The 8012 Parcel Layer Matrix shows `Görünür satır: 28` for Gas Emissions.
2. Page information shows exactly `28 satır` and all 28 row objects are rendered/paginatable.
3. The four new rows are visibly distinct and include a `YENİ / LATEST` indicator even though manual review remains true:
   - `GHG-HPL-2005-waste-other-n2o`
   - `GHG-HPL-2006-agriculture-gas-ch4`
   - `GHG-HPL-2006-agriculture-gas-n2o`
   - `GHG-HPL-2006-commercial-electricity-n2o`
4. The previous 24 rows have `changed_in_latest_run=false`.
5. Each row visibly exposes official source URL, source line, matching method, calculation explanation, confidence, accuracy, parcel-binding status, visible artifact path and report path.
6. Raw local source path is shown only when a real downloaded source artifact exists; otherwise show `NOT_DOWNLOADED`.
7. UI or health output shows the served Git commit and artifact SHA/count.
8. Real Chrome/Selenium evidence confirms 28/28 rows, the four new-row markers, source/report paths and zero console errors.
9. Runner output and GitHub remote readback are pushed before marking browser smoke passed.
10. Keep `final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.

## Work pause rule

Do not add another Gas Emissions data batch until the 28-row state is visible on port 8012 and the acceptance test above passes. This prevents branch data from advancing while the user-facing site remains stale.
