# ready_to_sell_2 — Wave 48 Auction House expansion

- Slot: `ready_to_sell_2`
- Continuation: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- Source snapshot: `2026-07-24`
- Existing first unverified step preserved: `AUTOMATION_167_DOM_PROOF`
- Publication branch: `agent/ready-to-sell-2-wave48-preflight-20260724`

## This expansion

Ten additional current first-party Auction House rows were transcribed from auctions closing on 4, 18 and 25 August 2026:

1. 109 Cleveland Street, Birkenhead — guide £61,000; freehold.
2. 76 Mallard Avenue, Nuneaton — guide £115,000+; tenure held pending legal-pack readback.
3. 45 The Chase, Grays — guide £180,000; vacant leasehold with 155 years from 1 November 2014.
4. 2 South View, Easington Lane — guide £46,000; freehold; occupation not explicitly stated.
5. Apartment 906 Marco Island, Nottingham — guide £59,000; leasehold; no current tenancy or rent inferred.
6. Gorphwysfa, Village Road, Llanfairfechan — guide £200,000–£250,000; freehold; Grade II reference 5845; title CYM668892.
7. 10 Summersfield Road, Minchinhampton — guide £150,000; internal configuration unconfirmed because the auctioneer could not enter.
8. Ground Floor Flat, 24 Greenbank Avenue, Plymouth — guide £55,000; vacant leasehold.
9. Carvean, 12 Sunnyside, Perranporth — guide £190,000; freehold; occupation not explicitly stated.
10. Apartment 31, Broadwater Boulevard Flats, Worthing — guide £147,000; current first-party catalogue row only; direct detail page unavailable.

## Accuracy and taxonomy

- New rows: 10.
- New line-level operations: 50/50 complete.
- New-batch first-party source confidence: 99.6/100.
- Aggregate Wave 48 child rows: 30 candidates and 139/139 operations.
- Aggregate child source confidence: 99.8/100.
- Current income, future rental potential, vacancy and unknown occupation remain separate.
- Existing permission, listed status, necessary-consent wording and marketing potential remain separate.
- Guide prices remain guide prices, not sale prices.
- The known Wave 47 control query `97 Mandeville Court` returned zero repository search results, proving the code-search duplicate gate has a false-negative condition in this execution context. All ten rows remain held.

## Canonical state preserved

- Canonical candidates: 514.
- Canonical source upgrades: 477.
- Canonical operations: 869/870 = 99.89%.
- Canonical delta: +0.00 percentage points.
- Unique accepted rows: 0.
- Promoted rows: 0.

## Runtime blocker

The single Windows F-host scanner is not currently polling, and real port-8012 Automation 167 DOM evidence remains absent. Manual action remains OPEN. No second runner, second task, database write, migration or deployment was created.

## Web visibility

`england_map_web/data/aays_21_slots/ready_to_sell_2/ready_to_sell_2_progress_wave_48_preflight.html` now loads all three candidate and progress parts, rendering 30 candidate rows and 139 operation rows line by line.

`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
