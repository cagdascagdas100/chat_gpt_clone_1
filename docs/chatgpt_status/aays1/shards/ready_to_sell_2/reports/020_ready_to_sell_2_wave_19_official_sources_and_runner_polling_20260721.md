# Ready to Sell 2 — Wave 19 Official Sources and Runner Polling Audit

- SLOT_ID: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Checkpoint target: `22`
- First unverified step: `AUTOMATION_167_DOM_PROOF`
- Product final ready: `false`

## Remote runner readback

The repaired `slots_21/aays_21` current-task paths, non-empty slot status, queue script path, read paths, exact write paths and safety flags remain internally consistent. The slot current task remains `idle`, heartbeat remains `unclaimed/stale`, and the Automation 167 truth artifact remains absent. Repository searches did not expose another slot-local queue-scanner repair target. The remaining blocker is the existing shared runner not visibly polling or claiming the pending task. No new or parallel runner was created.

## Wave 19 candidate evidence

Six repository-unique official-source candidates or controls were added:

1. Land to the Rear of 8 Langton Way — positive pre-application advice, but the direct page explicitly says no planning application has been submitted.
2. Flat 1, 33 Windsor Road — two studio flats, one regulated tenancy producing GBP 3,510 per annum and one vacant.
3. 5 Cornmarket — current retail investment index at GBP 80,000 guide and GBP 8,500 annual rent.
4. 97 Caledon Road — current guaranteed-rent value GBP 26,400 conflicts with an older official AST value of GBP 24,000; both are preserved.
5. Flat B, 1 Dartmouth Road — current periodic-tenancy income control at GBP 26,400 per annum.
6. Unit 17 Tait Road Industrial Estate — vacant approximately 4,000 square-foot industrial control with no development permission inferred.

Six source-upgrade rows were added. Three drawings-only or subject-to-consents records were excluded. No candidate was promoted because canonical parcel geometry and official record-level planning readback remain incomplete.

## Metrics

- Completed operations: `138 / 139`
- Batch progress: `99.28%` (`+0.06` points)
- Overall evidence progress: `99.35%` (`+0.05` points)
- Unique research candidates: `79`
- High-confidence candidates: `79`
- Current/upcoming/available: `77`
- Latest batch confidence: `98.33 / 100`
- Aggregate source confidence: `98.46 / 100`
- Cumulative duplicate removals: `7`
- Cumulative source upgrades: `29`
- Promoted rows: `0`

## Web evidence

`england_map_web/ready_to_sell_2_progress_wave_19.html` loads candidate waves through wave 19 and renders operations, blockers, duplicate corrections, excluded records, source upgrades and unique candidates row by row. Actual port-8012 browser execution remains unverified until the canonical shared runner produces the truth artifact.

## Safety

- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- `final_ready=false`
- terminal tasks `146`, `153`, `155`, `166` were not replayed.
