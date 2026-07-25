# ReadyToSell 3 — Research Waves 367–378

- Continuation key preserved: `6f2f2e66567b0e654a32a3bb26684504438ff4a7085d0170335bdbfe452a687a`
- New task / runner / owner: `false / false / false`
- Research candidates: **72**
- High-confidence candidates: **72/72**
- Average source confidence: **98.42/100**
- Source mix: **66 official specific future-auction rows + 6 official National aggregate rows**
- Visible research rows: **2261 → 2333**
- Promotion / parcel / geometry: **0 / 0 / 0**
- Operations before final readback: **2008 / 2011**

## Source and integrity controls

- Official Auction House National pages were used for 28 July, 11 August, 18 August, 25 August and 22 September 2026, plus six unused current aggregate rows.
- Eight rows explicitly marked Withdrawn, Postponed or Sold Prior on the 28 July page were excluded.
- `5 Sandylands Park`, `60 Wood Street` and `72 Middle Street` were excluded because official historical bid/result evidence created relist ambiguity.
- Guide prices remain guide prices; no achieved-sale inference was made.
- Lot number and auction date were retained only where exposed. Unsupported tenure/title/lawful-use/parcel/geometry fields remain `not_exposed` or unverified.
- Duplicate checking was bounded to recent waves and the current batch; it is not a full historical title/UPRN scan.

## Publication

- Wave files: `367` through `378`
- Progress feed: `ready_to_sell_3_progress_events_wave_367_378_20260724.json`
- Dedicated web view: `ready_to_sell_3_waves_367_378_live_progress.html`
- Main index remains lightweight and loads only the latest twelve waves; previous groups remain archive links.

## Remaining blocker

`CANONICAL_RUNNER_EXTERNAL_BLOCKED_DOM_PROOF_ABSENT`

Research may continue, but canonical promotion and final acceptance remain blocked until the existing single runner and port-8012 service produce `automation_167_dom_proof_latest.json`.
