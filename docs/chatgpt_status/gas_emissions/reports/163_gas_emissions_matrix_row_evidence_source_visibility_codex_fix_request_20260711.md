# Gas Emissions — Matrix row evidence, source materialization and latest-row visibility fix request for Codex

Date: 2026-07-11  
Repo: `cagdascagdas100/chat_gpt_clone_1`  
Branch: `codex/aays-single-runner-v5-20260706`  
Page key: `gas_emissions`  
Canonical portable root: `F:\TerraYield_AAYS_Portable`  
Canonical served repo: `F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707`  
Matrix URL: `http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable`  
Status: `BLOCKED_UI_EVIDENCE_VISIBILITY_AND_SOURCE_MATERIALIZATION`

## User requirement

The user must be able to see every verified Gas Emissions result row in the 8012 matrix, together with:

- official internet source URL;
- exact official source line / record evidence;
- downloaded local raw source path when a real local download exists;
- source manifest path and raw-file SHA256/size;
- generated visible artifact path;
- status path;
- report path;
- batch / task / pipeline stage;
- accuracy and confidence;
- parcel-binding state;
- a visually distinct marker for newly added rows.

Queued candidates and completed verified rows must not be mixed. Unverified candidates may be shown only in a separate `ADAY / KUYRUKTA` area and must never be represented as completed or visible source-backed rows.

## Current user-visible state from the 2026-07-11 screenshot

The Gas Emissions matrix currently shows:

- visible / tracked rows: `28`;
- GeoJSON feature count: `3533`;
- latest rows: `4`;
- pending runner: `not_available`;
- manual review: `28`;
- batch: `gas_emissions_28_browser_smoke_20260711_01`;
- blocker: `none`;
- `final_ready=false`;
- `fake_data=false`;
- `source_csv: NOT_DOWNLOADED`;
- `source_geojson: not_available`;
- `source_manifest_path: not_available`.

The first displayed row is an old 2005 Transport row. The four latest rows are appended later in the dataset and are not promoted to the first screen. A user opening the Gas Emissions layer therefore does not immediately see what was newly completed.

## Confirmed implementation defects

### 1. Latest rows are not sorted to the top

`renderRows()` renders `state.filtered` in source order. The dataset places the newest rows later, so the latest four rows can be hidden on the second page. The presence of a `YENİ / LATEST` badge is insufficient when the new rows are not visible on initial load.

Required fix:

- default Gas Emissions ordering: latest rows first, then newest batch/year/source-line order;
- keep `Tüm durumlar` available, but show the latest four rows at the top;
- add a visible `Yeni 4 satırı göster` shortcut / tab;
- keep all 28 verified rows accessible and paginatable.

### 2. Raw official source is not materialized locally

Every current row has `source_local_raw_path: NOT_DOWNLOADED`. The summary also shows `source_csv: NOT_DOWNLOADED`, while `source_manifest_path` is absent.

Required fix:

- download the official DESNZ CSV into a non-Git local source cache under the canonical portable root, for example:
  `F:\TerraYield_AAYS_Portable\sources\gas_emissions\2005-23-uk-local-authority-ghg-emissions-CSV-dataset.csv`;
- do not commit the large raw CSV to Git;
- create a small committed manifest:
  `england_map_web/data/program_layer_matrix/gas_emissions_source_manifest_latest.json`;
- manifest fields must include official URL, local raw path, file size, SHA256, downloaded_at, source publication date, authority/year selector and downloader task ID;
- if download fails, display the real error and retain `NOT_DOWNLOADED`; never fabricate a local path.

### 3. Report and status paths are not browser-openable

The matrix helper `webRelative()` only turns paths beginning with `england_map_web/` or `data/` into links. Paths under `docs/chatgpt_status/...` are rendered as plain `REPO PATH`, so the user cannot open batch reports or status files from the page.

Required fix — choose one safe implementation:

- map repository paths beginning with `docs/` to a safe relative browser URL such as `../docs/...` when the 8012 server root is the repository root; or
- mirror only approved Gas Emissions reports/status artifacts into a served evidence directory under `england_map_web/data/program_layer_matrix/evidence/gas_emissions/`.

Do not expose arbitrary filesystem paths. Add a copy button for every repo path and local path.

### 4. Row-level source evidence is incomplete

The table shows `source_lines`, but it does not show the actual official source row values as a compact evidence excerpt, a raw-source hash, or a row-specific evidence artifact.

Required fix:

Create:

- `england_map_web/data/program_layer_matrix/evidence/gas_emissions_row_evidence_latest.json`;
- optionally a matching CSV for easy inspection.

Each verified row must include:

- `row_id`;
- authority and authority code;
- calendar year;
- sector, subsector and gas;
- territorial and scope values;
- official source line / record identifier;
- exact source values or a normalized source excerpt;
- official source URL;
- local raw path;
- raw SHA256;
- batch ID;
- task ID;
- report path;
- status path;
- verification timestamp;
- confidence and accuracy;
- `is_new_in_latest_batch`;
- parcel-binding status.

### 5. Summary blocker is misleading

The page shows `Blocker: none` even though:

- raw source is not downloaded;
- source manifest is missing;
- browser smoke is not proven in the canonical status;
- parcel binding is pending;
- pending runner status is unavailable.

`renderSummary()` only displays an explicit blocker field and does not derive warnings from failed gates or missing evidence.

Required fix:

Show separate fields:

- `Pipeline durumu`;
- `Kanıt uyarıları`;
- `Browser smoke`;
- `Raw source`;
- `Parcel binding`;
- `Final blocker`.

At minimum, the current state must report:

- `raw_source_not_downloaded`;
- `source_manifest_missing`;
- `browser_smoke_pending` when false;
- `parcel_binding_pending`.

These are not permission to set final ready. `final_ready=false` must remain.

### 6. Pending pipeline stages are invisible

The user cannot see the prepared sequential pipeline:

- 28 publish/browser proof;
- 37 rows;
- 66 rows;
- 100 rows;
- 151 rows;
- 233 rows;
- 316 rows.

Required fix:

Create a small served pipeline artifact, for example:

`england_map_web/data/program_layer_matrix/gas_emissions_pipeline_status_latest.json`

For each stage show:

- stage target row count;
- task ID;
- state: queued / running / blocked / passed;
- started/completed timestamps;
- report and status paths;
- current real blocker;
- expected new row count;
- whether browser proof passed.

Render this in a separate `İşlem / Batch Geçmişi` section. Queued rows must not be included in the verified-row count.

### 7. GeoJSON count label is misleading

The page displays `GeoJSON feature: 3533`, while `parcel_binding_gate_passed=false`. This can be interpreted as 3533 Gas Emissions-linked parcels even though no such parcel allocation is proven.

Required fix:

Rename the metric to:

`Temel parsel GeoJSON feature (Gas Emissions bağlantısı yok)`

or hide it from the Gas Emissions summary until parcel binding exists.

### 8. Wide-table usability prevents evidence inspection

The table requires extreme horizontal scrolling. Important path and source columns are difficult to inspect together.

Required fix:

- keep `Durum`, `Satır`, `Yıl`, `Sektör`, `Gaz`, `Doğruluk` sticky;
- add a row-level `Detay / Kanıt` expander;
- move long paths, SHA values and calculation explanation into the detail panel;
- preserve search and filters;
- add copy/open controls beside every source/report/status path.

## Required visual states

Use distinct, combinable markers:

- `YENİ / LATEST` — green highlight;
- `KAYNAKLI / DOĞRULANMIŞ` — normal verified row;
- `MANUEL İNCELEME` — amber marker;
- `ADAY / KUYRUKTA` — blue marker in a separate candidate section;
- `BLOCKED` — red marker with exact blocker;
- `PARSEL BAĞLANTISI YOK` — explicit neutral warning.

A new row may simultaneously show `YENİ / LATEST`, `MANUEL İNCELEME` and `PARSEL BAĞLANTISI YOK`.

## Acceptance criteria

1. On first Gas Emissions load, the four latest rows appear at the top and are visibly distinct:
   - `GHG-HPL-2005-waste-other-n2o`;
   - `GHG-HPL-2006-agriculture-gas-ch4`;
   - `GHG-HPL-2006-agriculture-gas-n2o`;
   - `GHG-HPL-2006-commercial-electricity-n2o`.
2. The page still reports exactly 28 verified visible rows and exactly four latest rows.
3. All 28 verified rows can be inspected row by row.
4. Every row exposes official URL, source record/line, normalized source evidence, confidence, accuracy, calculation explanation, parcel-binding state, visible artifact, status and report paths.
5. A real local raw CSV path, file size and SHA256 are shown only after a successful real download.
6. `gas_emissions_source_manifest_latest.json` exists and is browser-openable.
7. Report and status links open from the 8012 page, or approved mirrored evidence links open.
8. A separate pipeline section shows the seven real stages and their real states without counting queued candidates as completed rows.
9. `Pending runner` is no longer `not_available`; it is populated from the canonical pipeline status.
10. The GeoJSON metric cannot be mistaken for parcel-bound Gas Emissions results.
11. Real Chrome/Selenium proof validates:
    - 28 unique verified rows;
    - four latest rows at the top;
    - latest/manual markers combined correctly;
    - source manifest link;
    - report/status links;
    - pipeline section;
    - zero severe console errors.
12. GitHub remote readback proves the report/status/browser artifacts were pushed.
13. Keep all safety flags unchanged:
    - `final_ready=false`;
    - `product_final_ready=false`;
    - `fake_data=false`;
    - `db_write=false`;
    - `migration=false`;
    - `production_deploy=false`.

## Work gate

Pause the 37 → 316 data expansion chain until this UI/source-evidence acceptance test passes. After proof is pushed and read back from GitHub, requeue the existing single-runner dispatcher and continue from the first unmet stage. Do not create a new runner and do not run stages in parallel.
