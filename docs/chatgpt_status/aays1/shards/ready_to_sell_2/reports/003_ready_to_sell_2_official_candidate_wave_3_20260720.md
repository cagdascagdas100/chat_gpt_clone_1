# ReadyToSell Shard 2 — Official Candidate Wave 3

- Slot: `ready_to_sell_2`
- Parcel range: `30762-61522`
- Snapshot date: `2026-07-20`
- Result: `CANDIDATE_WAVE_3_PUBLISHED_AUTOMATION_167_STILL_QUEUED`
- New candidates: `4`
- Existing candidate source-upgraded: `1`
- Total research candidates: `12`
- High-source-confidence candidates: `12`
- Latest-wave average source confidence: `98.75/100`
- Overall average source confidence: `97.50/100`
- Promoted parcel/product rows: `0`

## Newly verified candidates

1. **Land and buildings north side of St Andrew's Road, Plaistow**
   - Upcoming Savills auction: 29 July 2026
   - Guide: GBP 180,000
   - Planning reference: `24/02474/FUL`
   - Evidence: two two-bedroom dwellings and re-provision of three garages; leaseholder consent remains required.
   - Source: https://auctions.savills.co.uk/auctions/28-july-2026-227/land-and-buildings-on-the-north-side-of-st-andrews-road-plaistow-london-e13-8qd-23609

2. **375 High Road, Ilford**
   - Upcoming Savills auction: 29 July 2026
   - Guide: GBP 575,000
   - Planning reference: `1456/23/02`
   - Evidence: reconfiguration to a shop and six studio flats.
   - Source: https://auctions.savills.co.uk/auctions/28--29-july-2026-227/375-high-road-ilford-london-ig1-1tf-23706

3. **Land adjoining 208 Columbia Road, Bournemouth**
   - Upcoming Savills auction: 28 July 2026
   - Guide: TBA
   - Planning reference: `7-2023-28535-B`
   - Evidence: one-bedroom detached bungalow with access, parking, bin and cycle storage.
   - Source: https://auctions.savills.co.uk/auctions/28-july-2026-227/land-adjoining-208-columbia-road-ensbury-park-bournemouth-bh10-4ds-23726

4. **2 Church Street, Esher**
   - Reoffered in the 29 July 2026 catalogue
   - Guide: GBP 750,000
   - Planning reference: `2025/1384`
   - Evidence: upper-floor conversion to three flats, rear extension, roof terraces and mansard reconstruction.
   - Sources:
     - https://auctions.savills.co.uk/auctions/23-june-2026-225/2-4-church-street-esher-surrey-kt10-8qs-23040
     - https://auctions.savills.co.uk/auctions/28-july-2026-227/page-22

## Source upgrade

- **Land at Sandleford Parade** now records West Berkshire reference `24/01905/FULMAJ` for 14 flats.
- The conflicting price signals remain preserved: GBP 1.2m on the property page versus GBP 980k in the current auction catalogue.
- No promotion is allowed while the price conflict and canonical parcel geometry match remain unresolved.

## Website evidence

- Page: `england_map_web/ready_to_sell_2_progress.html`
- Candidate JSON: `england_map_web/data/aays_21_slots/ready_to_sell_2/candidate_examples_latest.json`
- Progress JSON: `england_map_web/data/aays_21_slots/ready_to_sell_2/progress_latest.json`
- Latest-batch and source-upgraded records are visibly labelled row by row.

## Remaining blockers

- `EXISTING_SHARED_RUNNER_REMOTE_HEARTBEAT_STALE_2026-07-16T13:45:53Z`
- `AUTOMATION_167_CANONICAL_PORT_8012_HEADLESS_DOM_EXECUTION_PENDING`
- `CANDIDATE_CANONICAL_PARCEL_GEOMETRY_MATCH_PENDING`
- `OFFICIAL_PLANNING_PORTAL_RECORD_LEVEL_READBACK_PARTIAL`
- `REAL_VISION_SCORE_ROWS_ZERO`

No new or parallel runner was created. Terminal tasks `146`, `153`, `155`, and `166` were not replayed. `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false` remain unchanged.
