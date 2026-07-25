# ready_to_sell_2 — Wave 47 first-party source revalidation, group 3 (2026-07-25)

## Scope

Recovery-safe audit of 10 existing Wave 47 candidates from parts 5 and 6. No second queue task, runner, owner, or direct canonical push was created. Existing candidate business rows were not changed or promoted.

- Canonical queue continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Audit series key: `2c86067ed0f414c228c36304b87d872d3726c5488e22349502a7125444264cbc`
- First unverified step: `AUTOMATION_167_DOM_PROOF`
- Existing queue state: `queued_for_single_shared_runner`
- Owner state: `unclaimed`
- Runner blocker: `SAFE_F_HOST_SINGLE_RUNNER_NOT_CURRENTLY_HEARTBEATING`

## Result

- First-party source pages accessible: **10/10**
- Comparison checks completed: **20/20**
- Rows with confirmed corrections: **4**
- Confirmed field corrections: **5**
- Verified enrichments: **8**
- Rows without confirmed corrections: **6**
- Audited field accuracy before staged corrections: **65/70 = 92.86%**
- Audited field accuracy after staged corrections: **70/70 = 100.00%**
- Average verification confidence: **99.0/100**

## Confirmed corrections

1. `rts2_w47_10_fairmount_avenue`: tenure → `leasehold`; marketing status → `upcoming_auction_vacant`.
2. `rts2_w47_land_north_drysgol_road`: tenure → `freehold`.
3. `rts2_w47_flat7_flagg_lodge`: tenure → `leasehold`.
4. `rts2_w47_44_winter_knoll`: tenure → `freehold`.

## Verified enrichments

- Cornmill Yard: vacant possession and direct Skipton Road access.
- Upper Luton Road rear land: vacant possession.
- Flagg Lodge: EPC rating C.
- 82 Colne Lane: EPC rating D.
- Winter Knoll: driveway capacity for two to three vehicles.
- Brookside Stables: mains water and three grazing paddocks.

## Safety and publication state

All corrections remain staging-only. Candidate mutation is deferred until real Automation 167 port-8012 headless DOM acceptance succeeds. `promotion_allowed=false`, `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.

Row-level evidence:

- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725_wave3_latest.json`
- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725.html`
