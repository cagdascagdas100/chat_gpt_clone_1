# ReadyToSell 2 — Wave 46 stale-pending recovery and current candidates

- Slot: `ready_to_sell_2`
- Parcel range: `30762-61522`
- Snapshot: `2026-07-22`
- Status: candidate research published; Automation 167 queue recovered to `ready_for_claim`; actual DOM truth still pending.
- Screened/new: `20 / 20`
- Duplicate matches: `0`
- Latest source upgrades: `20`
- Latest integrity repairs: `2`
- Latest average source confidence: `99.65/100`
- Product promotions: `0`

## Pending/block recovery

1. The existing Automation 167 queue was still marked `pending` and preserved obsolete Wave 27 baselines.
2. The previous browser acceptance page loaded only legacy ReadyToSell candidate waves and did not represent the current shard candidate stream.
3. A current acceptance page was published at `england_map_web/ready_to_sell_2_automation_167_acceptance.html`.
4. Recovery worker v2 was published at `docs/chatgpt_status/aays1/automation/ready_to_sell_2_automation_167_dom_worker_v2.ps1`.
5. The existing queue item was updated to `ready_for_claim`; no new runner, parallel runner or new task was created.
6. The acceptance page now combines Wave 45 and Wave 46 candidates, current progress and the full Wave 46 operation file.
7. Actual port-8012 browser truth is not claimed until the existing canonical shared runner picks up the queue.

## Candidate summary

1. 16C Bury Street — periodic tenancy producing GBP 19,200 pa.
2. Flat 31A Hanover Gate Mansions — vacant one-bedroom flat.
3. 30 Ancton Way — vacant three-bedroom detached bungalow.
4. 16 Purley Court — vacant two-bedroom flat.
5. 28 West Street — vacant two-bedroom house.
6. 40 Coronation Road — vacant three-bedroom house; loft extension STC.
7. 2 Kimble Crescent — vacant three-bedroom semi-detached house.
8. 18 Sherborne Road — vacant three-bedroom house; side/rear extension STC.
9. 19 Stradbroke Place — vacant three-bedroom house; side/rear extension STC.
10. 198 Weston Lane — substantial vacant four-bedroom house; redevelopment STC.
11. 82 Sussex Way — building arranged as three flats; lawful-use evidence pending.
12. 2 Lotus Mews — vacant three/four-bedroom house; exact room count retained as ambiguous.
13. Flat 1 Hamlet Court — vacant one-bedroom flat.
14. Flat 21 Emerald House — vacant two-bedroom flat.
15. 82 Holly Hill Road — vacant three-room flat; no bedroom count inferred.
16. 18 Malvern Road — vacant four-bedroom semi-detached house.
17. Flat 13 Campden Hill Towers — vacant two-bedroom flat.
18. 24 Benville Road — vacant two-bedroom house.
19. Land Adjacent to The Gables — approximately 1.32 acres with an eight-house permission signal; exact reference and conditions pending.
20. 325A London Road — vacant three-bedroom flat.

## Progress

- Completed operations: `804/805`
- Overall progress: `99.88%`
- Increase: `+0.01`
- Aggregate candidates: `484`
- Current/open candidates: `481`
- Cumulative source upgrades: `447`
- Cumulative integrity repairs: `14`
- Full line evidence: `england_map_web/data/aays_21_slots/ready_to_sell_2/progress_wave_46_latest.json`

## Remaining blocker

`EXISTING_SHARED_RUNNER_FAMILY_NOT_YET_CLAIMING_READY_FOR_CLAIM_QUEUE`

`AUTOMATION_167_CANONICAL_PORT_8012_HEADLESS_DOM_EXECUTION_PENDING`

`final_ready=false`, `product_final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
