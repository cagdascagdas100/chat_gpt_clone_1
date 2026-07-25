# Ready to Sell 2 — Wave 48 first-party preflight expansion

- Slot: `ready_to_sell_2`
- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Continuation key: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Preserved first unverified step: `AUTOMATION_167_DOM_PROOF`
- Child branch: `agent/ready-to-sell-2-wave48-preflight-20260724`
- Source snapshot: `2026-07-24`

## Result

- First-party candidate rows prepared: **20**
- Row-level preflight operations: **89 / 89**
- Average first-party source confidence: **99.90%**
- Dual-endpoint Savills price integrity checks: **9**
- Rows accepted as repository-unique: **0**
- Rows promoted to canonical product data: **0**
- Canonical candidate count preserved: **514**
- Canonical source-upgrade rows preserved: **477**
- Canonical progress preserved: **869 / 870 — 99.89%**
- Canonical progress increase: **0.00 percentage points**

## Accuracy controls

1. Guide prices remain guide prices and are not treated as achieved sale prices.
2. Current contractual income, historic income, ERV/future rent, vacant/no-income and occupation-unknown states remain distinct.
3. Existing planning permission, subject-to-planning potential, subject-to-consent wording and marketing-only potential remain distinct.
4. Legal tenure is not replaced by marketing phrases such as “virtual freehold”.
5. Additional rooms are not silently reclassified as bedrooms.
6. Candidate promotion remains blocked until repository-wide duplicate proof, canonical parcel geometry matching and real Automation 167 DOM acceptance exist.
7. Nine Savills rows were checked against both the auction catalogue and lot-detail presentation. Catalogue prices were preserved where the detail header presented TBA.

## Website evidence

- Candidate set 1: `england_map_web/data/aays_21_slots/ready_to_sell_2/candidate_wave_48_preflight_latest.json`
- Candidate set 2: `england_map_web/data/aays_21_slots/ready_to_sell_2/candidate_wave_48_preflight_part_2_latest.json`
- Operation set 1: `england_map_web/data/aays_21_slots/ready_to_sell_2/progress_wave_48_preflight_latest.json`
- Operation set 2: `england_map_web/data/aays_21_slots/ready_to_sell_2/progress_wave_48_preflight_part_2_latest.json`
- Row-by-row web page: `england_map_web/data/aays_21_slots/ready_to_sell_2/ready_to_sell_2_progress_wave_48_preflight.html`

## Blocker and safety

The external Windows F-host single shared scanner is not currently polling, and real port-8012 Automation 167 DOM acceptance is absent. The existing manual action remains OPEN. No second runner, parallel runner, second business task, database write, migration, deployment, fake data, force push or canonical direct push was created.

`final_ready=false`
