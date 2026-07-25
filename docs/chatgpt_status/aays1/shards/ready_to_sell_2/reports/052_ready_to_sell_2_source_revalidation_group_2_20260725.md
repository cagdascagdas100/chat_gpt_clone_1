# ready_to_sell_2 — Wave 47 first-party source revalidation, group 2 (2026-07-25)

## Scope

Recovery-safe audit of 10 existing Wave 47 candidates from parts 3 and 4. No second queue task, runner, owner, or direct canonical push was created. Existing candidate business rows were not changed or promoted.

- Canonical queue continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Audit series key: `2c86067ed0f414c228c36304b87d872d3726c5488e22349502a7125444264cbc`
- Source head: `a118b47b5ebcccb149b01bc13eed186d6ba49231`
- First unverified step: `AUTOMATION_167_DOM_PROOF`
- Existing queue state: `queued_for_single_shared_runner`
- Owner state: `unclaimed`
- Runner blocker: `SAFE_F_HOST_SINGLE_RUNNER_NOT_CURRENTLY_HEARTBEATING`

## Result

- First-party source pages accessible: **10/10**
- Comparison checks completed: **20/20**
- Rows with confirmed corrections: **4**
- Confirmed field corrections: **6**
- Verified enrichments: **11**
- Rows without confirmed corrections: **6**
- Audited field accuracy before staged corrections: **64/70 = 91.43%**
- Audited field accuracy after staged corrections: **70/70 = 100.00%**
- Average verification confidence: **98.8/100**

## Confirmed corrections

1. `rts2_w47_34_bankside`: tenure `not_stated_in_selected_extract` → `freehold`.
2. `rts2_w47_flat4_66_city_road`: tenure `not_stated_on_first_party_page` → `leasehold`.
3. `rts2_w47_245_251_lord_street`: tenure `not_stated_on_first_party_page` → `leasehold`.
4. `rts2_w47_3_5_north_street`:
   - marketing status `upcoming_auction_active` → `upcoming_auction_mixed_occupation`;
   - current contracted annual rent added as **£10,000** for No. 5;
   - source semantics corrected to retain No. 3's **£8,000 estimated rental value** separately from No. 5's current passing rent.

## Verified enrichments

- Doncaster commercial/car-park lot: postcode `DN1 1QN`, car-park area `165 m²`, tenancy-at-will status.
- Birchfield: vacant-possession status.
- Sticker Lane land: vacant-possession status.
- 34 Bankside: vacant-possession status.
- Kiln Hill: source states no local-occupancy restriction.
- 245-251 Lord Street: postcode `PR8 1NY`, plans prepared for six two-bedroom apartments subject to consent.
- 3 & 5 North Street: postcode `DN21 2HP`, No. 3 estimated rental value `£8,000` retained as non-contracted estimate.

## Safety and publication state

All corrections remain staging-only. Candidate mutation is deferred until real Automation 167 port-8012 headless DOM acceptance succeeds. `promotion_allowed=false`, `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.

Row-level evidence:

- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725_wave2_latest.json`
- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725.html`
