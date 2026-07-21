# Ready to Sell Shard 2 — Wave 20 Official Planning and Income Controls

- Slot: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Source snapshot: `2026-07-21`
- Final ready: `false`
- Product promotion: `0`

## Remote runner readback

The repaired `slots_21/aays_21` current-task contract remains internally consistent. Current task is still `idle`; heartbeat is `unclaimed` and stale; `automation_167_dom_proof_latest.json` remains absent. No new or parallel runner was created. The remaining runtime blocker is the existing shared runner not visibly polling, claiming or executing the pending task.

## Wave 20 research

Nine unique current official Auction House records were added after repository duplicate preflight:

1. Land Adjacent to The Gables — full permission `23/01637/FUL`; current active reoffer conflicts with an older Postponed record and decision date.
2. Roof Space at 41 Peckham Road — `20/AP/1951` and `23/AP/2644`; implemented claim and roof-space rights require legal-pack evidence.
3. Unit 2, 2 Elm Park Road — prior approval `26/01799/PMA`; advertised unit configuration and conditional freeholder consent require reconciliation.
4. Land and Garage on the North Side of Ruby Mews — full permission `24/01752/FUL`.
5. 153-155 Hamlet Court Road — prior approval `25/00261/PA64`; fire damage, VAT and vendor loan claim remain explicit risks.
6. 62A Osborne Road — outline permission `F/YR21/1448/O`, all matters reserved; current validity is not inferred.
7. Charnwood, King Edward Street — four July 2026 householder or prior-approval extension references, not additional-dwelling consent.
8. 6A Cable Street — periodic tenancy at GBP 21,000 per annum with notice served; notice is not vacant possession.
9. 18 Northgate — GBP 39,000 annual commercial rent with the second floor sold off on a long lease.

Nine direct-source upgrades were attached. Three records were excluded: 42 Mounts Road for unresolved current-versus-older planning scope, 6a Pembury Close for sold-versus-reoffer conflict, and 25-27 King Street Ramsgate because the current official commercial index marks it Postponed.

## Metrics

- Unique candidates: `88`
- New in wave 20: `9`
- High-source-confidence candidates: `88`
- Current/upcoming/available: `86`
- Latest batch average confidence: `98.78/100`
- Aggregate average confidence: `98.49/100`
- Source upgrades this wave: `9`
- Cumulative source-upgrade rows: `38`
- Cumulative duplicate removals: `7`
- Completed operations: `151/152` (`99.34%`, `+0.06` points)
- Overall evidence progress: `165/166` (`99.40%`, `+0.05` points)

## Remaining acceptance blocker

`AUTOMATION_167_DOM_PROOF` remains pending. A real canonical port-8012 headless-browser execution, HTTP 200 readback, DOM `data-load-state=ready`, visible/live row checks and remote truth artifact are required before the browser evidence batch can close. Canonical parcel geometry, official planning record-level readback and real vision-score rows remain separate product blockers.

Safety flags remain `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
