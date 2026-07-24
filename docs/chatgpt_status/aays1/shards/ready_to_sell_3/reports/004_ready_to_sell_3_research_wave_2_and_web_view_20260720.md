# ready_to_sell_3 — research wave 2 and line-by-line web view

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283`
- Task: `aays1-ready-to-sell-3-automation-167-dom-proof-20260720`
- Remote queue status at readback: `pending`
- Remote current task: `idle`
- Live lease: absent
- Final ready: `false`

## Completed in this continuation

1. Re-read remote queue, current-task and ownership state.
2. Preserved single-runner and no-terminal-replay constraints.
3. Researched eight additional current London development candidates from live listing or official agent sources.
4. Published candidate-only source records to:
   `england_map_web/data/aays_21_slots/ready_to_sell_3/research_preload_wave_2_20260720.json`
5. Published a line-by-line web view to:
   `england_map_web/data/aays_21_slots/ready_to_sell_3/index.html`
6. Kept all candidates unpromoted because HTTP SHA256, canonical parcel matching and geometry proof have not run.

## Progress accounting

- Completed operations: `7`
- Total defined operations after scope expansion: `10`
- Overall progress: `70%`
- Previous progress: `50%`
- Increase: `+20 percentage points`
- Planned research targets: `13` (`5` existing runner targets + `8` additional web-preverified candidates)
- Rows visible immediately in slot web view: `8`
- Manually preverified source-confidence >=90: `6`
- Runner-scored high-confidence: `0`
- Promoted rows: `0`
- Source hashes: `0`
- Canonical parcel matches: `0`
- Geometry matches: `0`

## Additional candidate set

- Ashbourne Way, NW11 — direct listing, GBP 1.5m, 10,458 sq ft site, redevelopment subject to consent.
- 1 Mount Place & 6-8 Crown Street, W3 — direct listing, GBP 1,999,950, advertised planning ref `240717FUL` for nine flats plus Class E space.
- 1, 2 and 6 Ossington Close, W2 — official Knight Frank release, full planning reported March 2026, approximately 4,973 sq ft.
- 1 and 3 Metcalfe Avenue, Carshalton — official Knight Frank release, GBP 4.25m, 2.47 acres, 19,814 sq ft existing GIA.
- 392A Camden Road and 1 Hillmarton Road, N7 — direct listing record, implemented mixed-use consent reported.
- State Parade / State Mansions, IG6 — direct listing, airspace development potential subject to planning.
- 2 Marsh Lane, E10 — current search-index candidate; direct particulars still required.
- 25 Buckingham Gate, SW1E — current search-index candidate; direct Savills particulars and consent reference still required.

## Blocker

`WAITING_CANONICAL_SINGLE_COORDINATOR_PICKUP; CURRENT_TASK_IDLE; QUEUE_PENDING; HTTP_SHA256_AND_DOM_PROOF_NOT_YET_EXECUTED`

## Next verified step

The existing canonical single coordinator must claim the pending task, execute live HTTP/SHA256 checks and Automation 167 headless-browser DOM acceptance, publish the declared shard outputs through the single publisher, and prove remote readback.

## Safety

- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- `new_runner=false`
- `parallel_runner=false`
- terminal tasks `146`, `153`, `155`, `166` not replayed
