# ready_to_sell_2 — New Candidate Group 25

- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Continuation key preserved: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- First unverified canonical step remains `AUTOMATION_167_DOM_PROOF`
- Publication scope: staging branch and existing draft PR only
- Promotion: forbidden

## Results

- 20/20 current first-party Acuitus detail records accessible and marked Available.
- 20/20 exact repository duplicate preflights completed; 0 matches.
- 40/40 source and duplicate checks completed.
- 160/160 source-supported fields verified.
- 141 source-supported enrichments recorded.
- Average verification confidence: 99.3/100.
- 17 semantic-warning rows and 2 source-internal conflict rows retained fail-closed.
- TG Jones, 3a & 4 Market Place was Sold Post and excluded.
- 157a Kew Road was Withdrawn Post and excluded.

## Selected records

- Ye Olde Rose & Crown: 10,017 sq ft freehold pub investment, £96,000 p.a., new 25-year no-break lease and three-bedroom upper flat.
- Asda Carlisle: 35,807 sq ft concurrent-leasehold superstore, current gross income £771,722 p.a., fixed future increases and a source yield-arithmetic conflict retained fail-closed.
- Broad Lane House: 47-unit student accommodation investment producing £264,894 p.a.
- 28/32 Market Place & 1/3 Shoemarket: two let units, vacant second floor and permission for three flats.
- Stena ET2 and ET3: long-dated heritable ground-rent investments to 2136 with outstanding 2021 rent reviews.
- High Newham Court: twelve retail units, residential ground rents, 33,115 sq ft and £46,334 p.a.
- Seymour House: three let units, 18,555 sq ft, 25 parking spaces and £112,200 p.a.

## Guards

- Current, fixed-future, previous and seller-top-up income values were stored separately.
- Advertised yields were not silently reconciled where source arithmetic differed.
- Planning permissions were separated from asset-management or conversion potential.
- Tenant not-in-occupation status was not treated as vacant possession.
- Old listing labels were overridden only by the current first-party detail page.
- No fake data, candidate promotion, database write, migration, force push or runner duplication occurred.

## Automation blocker

Automation 167 remains queued for the existing single F-host runner. The slot heartbeat remains unclaimed/stale; no second task or runner was created.
