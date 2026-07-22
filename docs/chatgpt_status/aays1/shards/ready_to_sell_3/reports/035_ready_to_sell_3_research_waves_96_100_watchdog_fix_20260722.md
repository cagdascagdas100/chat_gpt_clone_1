# ReadyToSell 3 — Waves 96–100 and stall-watchdog fix

- Slot: `ready_to_sell_3`
- Parcel partition: `61523–92283`
- New source-level candidates: **30**
- High-source-confidence candidates: **30/30**
- Average confidence: **98.60/100** (range 97–99)
- Exact title/postcode indexed duplicates: **0/30**
- Existing use or explicit permission: **23**
- STPP, no-current-consent or configuration uncertainty: **7**
- Integrity warnings retained: **30**
- Promoted product/parcel rows: **0**
- Visible research rows after publication: **665**
- Visible operations: **579/581 (99.66%)**, delta **+0.03**

## Candidate groups

- Wave 96: Norwich/Gorleston leasehold, marine, refurbishment and coastal-erosion records.
- Wave 97: amenity land, country house, short lease, incomplete extract and dual-kitchen configuration records.
- Wave 98: long lease, permissioned building plot, former hotel conversion and refurbishment records.
- Wave 99: modernisation, two-flat tenancy income, former campsite and Grade II listed commercial records.
- Wave 100: residential extracts, STPP land and former care-facility conversion potential.

## Stall diagnosis and fix

The expected canonical DOM proof file is absent (`404`). No runner heartbeat, lease or ownership proof supports treating the task as actively running. The state is therefore classified as `external_blocked_not_running_pending`; no DOM pass was fabricated and no shared-runner ownership was claimed.

The web page had an independent reliability defect: required `Promise.all` loading caused a full-page failure when any preload/progress file was temporarily unavailable. The page is changed to settled partial loading, failed-file reporting and a bounded 15-second watchdog. Research publication can continue while the canonical DOM, SHA256, parcel and geometry gates remain closed.

## Remaining blocker

`CANONICAL_RUNNER_EXTERNAL_BLOCKED_DOM_PROOF_ABSENT`

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false` remain preserved.
