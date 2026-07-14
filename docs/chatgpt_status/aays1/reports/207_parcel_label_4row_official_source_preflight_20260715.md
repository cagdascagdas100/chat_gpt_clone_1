# Parcel Label Task 207 Preflight

- Baseline accepted task: `206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714`
- Baseline rows visible: `194`
- Existing source/classification upgrades: `53`
- Exact geometry rows: `0`
- New batch size: `4`
- Average classification score: `3.9375 / 4` (`98.44%` of scale)
- Queue state at this report: `NOT_YET_EXECUTED`
- Existing shared runner heartbeat: stale; no new or parallel runner created.

## Candidate rows

| Candidate | Classification | Score | Primary official source | Geometry |
|---|---|---:|---|---|
| Bullring Birmingham | Retail Property | 3.95 / 4 | `https://www.bullring.co.uk/` | NOT_BOUND |
| The Cube Birmingham | Mixed Building | 3.95 / 4 | `https://www.thecube.co.uk/` | NOT_BOUND |
| One Angel Square Manchester | Office Building | 3.90 / 4 | `https://noma-manchester.com/tenants/the-co-op/` | NOT_BOUND |
| MPS 187, Magna Park South Lutterworth | Industrial Unit | 3.95 / 4 | `https://eu.glp.com/property/magna-park-lutterworth/` | NOT_BOUND |

## Execution contract

The existing single shared runner must:

1. Compare exact candidate IDs against the latest remote `distance_property_types_all_rows_latest.json`.
2. Append only missing IDs; repeat execution must add zero duplicate rows.
3. Perform runtime GET validation of each official source URL.
4. Update all-rows, status, latest-changes, source-manifest and artifact-index files.
5. Copy those five artifacts only to the canonical served root when present.
6. Verify matrix-page HTTP 200 and prove all four IDs in the served JSON.
7. Publish report, evidence, output, gate and canonical checkpoint files.
8. Keep browser DOM proof, manual footprint review and exact geometry as explicit remaining gates.

## Remote-first continuation

New pages must read:

`docs/chatgpt_status/aays1/checkpoints/parcel_label_canonical_checkpoint.json`

ZIP or handoff file age must not block continuation. Completed tasks 174, 205 and 206 must not be regenerated.

`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
