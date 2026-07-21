# Ready To Sell 2 — Wave 21 Official Planning, Income and Availability Audit

- SLOT_ID: `ready_to_sell_2`
- Parcel range: `30762-61522`
- Branch: `codex/aays-single-runner-v5-20260706`
- Checkpoint target: `24`
- Final ready: `false`

## Remote runner readback

Automation 167 truth is still absent. The slot current-task contract remains repaired and internally consistent, while the slot heartbeat remains `unclaimed` and `stale`. The existing shared runner has not visibly claimed the pending queue task. No new or parallel runner was created.

## Wave 21 output

Nine unique official-source research candidates were added after repository duplicate preflight:

1. Avenue Business Centre, Chatham — current income with `MC/22/1500` expressly lapsed on 30 June 2026.
2. 4 Bakers Lane, Colchester — current full permission `260014` for two detached five-bedroom houses.
3. 2-4 Chapel Street, Newhaven — current renewed-permission marketing, with the application reference still missing from the current index.
4. Land Off Short Lane, Ettington — unsold/make-offer land with lapsed outline permission `15/01035/OUT` and overage.
5. 300-302 Stratford Road, Sparkbrook — unsold/make-offer income control with a preserved rent-increase-year conflict.
6. 68 and 68A Three Shires Oak Road, Bearwood — vacant retail plus AST flat producing GBP 8,400 per annum.
7. 8 The Walk, Rochdale — vacant long leasehold commercial control with no approved development scheme stated.
8. 34 Tenby Street, Birmingham — unsold long leasehold office/retail control with service charge and VAT evidence.
9. 15-17 Coventry Street, Kidderminster — unsold vacant former bank with alternative uses only subject to planning.

Three records were excluded because current official sources show Sold or Sold Prior status: 165 New Road Rubery, Hollytree House land, and 12 Windsor Street Stratford-upon-Avon.

## Metrics

- Unique candidates: `97`
- New in wave: `9`
- High source confidence: `97`
- Current/upcoming/available: `95`
- Latest-wave source confidence: `98.56/100`
- Aggregate source confidence: `98.50/100`
- Latest source upgrades: `9`
- Cumulative source-upgrade rows: `47`
- Cumulative duplicates removed: `7`
- Promoted rows: `0`
- Completed operations: `165/166`
- Batch progress: `99.40%` (`+0.06` points)
- Overall evidence progress: `99.44%` (`+0.04` points)

## Remaining blocker

`EXISTING_SHARED_RUNNER_NOT_VISIBLY_POLLING_OR_CLAIMING_PENDING_QUEUE`

Automation 167 still requires the existing canonical shared runner to execute a real port-8012 headless-browser check and publish `automation_167_dom_proof_latest.json`. Product completion, percent 100 and `final_ready=true` remain forbidden without that artifact and the remaining geometry/planning/vision evidence.

## Safety

- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
