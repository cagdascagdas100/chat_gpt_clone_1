# ready_to_sell_2 — Wave 47 first-party source revalidation (2026-07-25)

## Scope

This is a recovery-safe audit of 10 existing Wave 47 candidates. It does not create a second queue task, does not modify candidate business rows, does not promote any parcel, and does not claim Automation 167 DOM completion.

- Continuation key: `2c86067ed0f414c228c36304b87d872d3726c5488e22349502a7125444264cbc`
- Source head: `5092c4e0835182b281b9bead0d0b5e5f4b9ec77c`
- First unverified step: `AUTOMATION_167_DOM_PROOF`
- Checked at: `2026-07-25T02:21:18Z`
- Existing queue state: `queued_for_single_shared_runner`
- Owner state: `unclaimed`
- Runner blocker: `SAFE_F_HOST_SINGLE_RUNNER_NOT_CURRENTLY_HEARTBEATING`

## Result

- First-party source pages accessible: **10/10**
- Comparison checks completed: **20/20**
- Rows with confirmed corrections: **7**
- Confirmed field corrections: **8**
- Verified enrichments: **3**
- Rows without confirmed corrections: **3**
- Audited field accuracy before staged corrections: **52/60 = 86.67%**
- Audited field accuracy after staged corrections: **60/60 = 100.00%**
- Average verification confidence: **99/100**

## Confirmed corrections

1. `rts2_w47_97_mandeville_court`: tenure `not_stated_on_first_party_page` → `leasehold`.
2. `rts2_w47_flat3_fordbrook_chambers`: tenure → `leasehold_subject_to_tenancy`.
3. `rts2_w47_flat3_oriel_chambers`: tenure → `leasehold_subject_to_tenancy`.
4. `rts2_w47_flat4_witley_house`: tenure → `leasehold`.
5. `rts2_w47_1_6_sun_terrace`: tenure → `freehold`.
6. `rts2_w47_37_41_knifesmithgate`: annual rent `£65,706` → `£66,106`.
7. `rts2_w47_abbey_house_greenfield`: tenure → `freehold`; planning reference `exact_reference_not_stated` → `054277`.

## Verified enrichments

- `104A Halifax Road`: postcode `BD21 5ET`.
- `1-6 Sun Terrace`: postcode `LL21 9HS`.
- `Abbey House`: Grade II listed status confirmed.

## Safety and publication state

Candidate mutations remain deferred until the real Automation 167 port-8012 headless DOM gate completes. `promotion_allowed=false`, `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, and `production_deploy=false`.

The row-level staged evidence is stored in:

- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725_latest.json`
- `england_map_web/data/aays_21_slots/ready_to_sell_2/source_revalidation_20260725.html`
