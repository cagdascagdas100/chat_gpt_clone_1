# Security / Public Safety Shard 1 — HTTP, Hash, DOM, Console and Browser Acceptance

- SLOT_ID: `security_public_safety_1`
- Task: `aays1-security-public-safety-1-hydrate-300-http-hash-dom-console-browser-acceptance-20260720`
- Parcel partition: `1-30761`
- Status: `BLOCKED`
- Hydrated rows: `300`
- Data semantics: `AREA_LEVEL_PROXY`
- Parcel measurement: `false`
- Display disclaimer: `LSOA/area-level proxy; not a parcel measurement`

## Acceptance

- Shard probe checks: `{"browser_exit_zero": true, "console_zero": false, "dom_area_level_proxy": true, "dom_hash_present": true, "dom_not_parcel_measurement": true, "dom_row_count_300": true, "http_200": true, "http_hash_present": true, "json_http_200": true, "semantic_contract_true": true}`
- Product matrix checks: `{"area_level_proxy_visible": false, "browser_exit_zero": true, "console_zero": true, "dom_hash_present": true, "http_200": true, "visible_rows_300": false}`
- Blockers: `SHARD_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FAILED; PRODUCT_MATRIX_AREA_LEVEL_PROXY_DOM_ACCEPTANCE_FAILED`

## Safety

`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
