# Ready To Sell 2 — Wave 26 Official Web Reconciliation

- SLOT_ID: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Source snapshot: `2026-07-21`
- Final ready: `false`

## Revalidated official rows

- Four Clive Emson planning rows revalidated directly: Old Woodyard, Higher Grange Cottage, Aucuba and Portland.
- Four primary Acuitus rows revalidated directly: Pizza Express, Little Turnstile, Sports Direct and Rossmore Business Village.
- Four secondary Acuitus rows revalidated directly: Davy Court, Asda, B&M and Dulux.
- Three final Acuitus rows revalidated directly: High Newham Court, Union Street and Silver Court.

## Corrected discrepancy

The earlier Barn Whites Cottages `Postponed` override was not supported by the current direct official lot page. The authoritative override now restores:

- current 23 July 2026 auction status,
- guide price GBP 65,000+,
- planning reference `25/0370/FUL`.

Silver Court remains correctly classified as Sold for GBP 1,895,000.

## Corrected aggregate

- Unique candidates: `164`
- High-confidence candidates: `164`
- Current/upcoming/available candidates: `161`
- New wave-26 candidates: `14`
- Latest source upgrades and repairs: `19`
- Cumulative source upgrades: `121`
- Valid corrected prior rows: `3`
- Unique integrity repairs: `4`
- Cumulative duplicate removals: `7`
- Product rows promoted: `0`
- Latest-batch source confidence: `98.93/100`
- Aggregate source confidence: `98.61/100`

## Progress

- Completed operations: `262/263`
- Batch progress: `99.62%`
- Batch increase from checkpoint 28 baseline: `+0.05` percentage points
- Overall evidence progress: `276/277` = `99.64%`
- Overall increase: `+0.05` percentage points
- Remaining pending event: canonical port-8012 actual headless-browser DOM execution and remote truth readback.

## Runner classification

- ready_to_sell_2 heartbeat: unclaimed/stale
- ready_to_sell_1 heartbeat: unclaimed/stale
- ready_to_sell_3 heartbeat: unclaimed/stale
- current task: idle
- visible blocker: existing shared-runner family is not visibly polling or claiming pending queues
- new runner: `false`
- parallel runner: `false`

## Safety

- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- Terminal tasks `146`, `153`, `155`, and `166` were not replayed.
