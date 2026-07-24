# Ready to Sell 2 — Wave 48 leasehold and vacancy expansion

- Slot: `ready_to_sell_2`
- Continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Preserved first unverified step: `AUTOMATION_167_DOM_PROOF`
- Publication branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- Source snapshot: `2026-07-24`

## Result

- New first-party candidate rows: **20**
- Aggregate child candidate rows: **125**
- New line-level operations: **100**
- Aggregate child operations: **614 / 614 — 100%**
- New-batch source confidence: **99.10%**
- Aggregate source confidence: **99.46%**
- Accepted as repository-unique: **0**
- Promoted to canonical: **0**
- Canonical progress preserved: **869 / 870 — 99.89%**
- Canonical progress delta: **0.00 percentage points**
- Canonical candidate/source-upgrade counts preserved: **514 / 477**

## Accuracy controls

- Direct lease terms were retained only where the official first-party page stated them.
- Vacant, tenanted-without-published-rent, occupation-unknown and marketing rental-potential states remain distinct.
- Guide-price and schedule evidence from catalogue snapshots was not expanded into tenure, income or planning claims.
- Basement access, vacant land extent and development rights remain legal-pack dependent.
- Repository duplicate search again returned no result for the known Wave 47 control, so all new rows remain `HELD`.
- Canonical parcel geometry and real port-8012 Automation 167 DOM acceptance remain absent.

## Blocker

The Windows F-host single shared scanner is not polling. Manual action remains `OPEN`; do not create or start a second runner.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `canonical_progress_advanced=false`, `final_ready=false`.