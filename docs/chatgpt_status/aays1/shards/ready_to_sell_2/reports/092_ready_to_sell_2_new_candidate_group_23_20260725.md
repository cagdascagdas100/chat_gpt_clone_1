# ready_to_sell_2 — New Candidate Group 23

- Workstream: `AAYS_21_SLOT_SAFE_PARALLEL_V1`
- Continuation key preserved: `da6954bff072c6a97aaa78097592fabc53311db34d81e0a89dfae0fb70104c29`
- First unverified canonical step remains `AUTOMATION_167_DOM_PROOF`
- Publication scope: staging branch and existing draft PR only
- Promotion: forbidden

## Results

- 20/20 current first-party Savills catalogue records accessible.
- 20/20 exact repository duplicate preflights completed; 0 matches.
- 40/40 source and duplicate checks completed.
- 160/160 source-supported fields verified.
- 142 source-supported enrichments recorded.
- Average verification confidence: 99.4/100.
- 16 semantic-warning rows and one first-party internal conflict retained fail-closed.
- Withdrawn Prior Lot 277 was excluded.

## Selected records

- Land at Romney Avenue: 0.89-acre freehold site with permission for eight houses; source states work has commenced.
- Land at Sandleford Parade: 0.33-acre mixed-use site with current rents of £33,600 p.a. and full permission for fourteen apartments.
- Units 1-3, 6, 8 and 10 Church Street: eight shops, seven flats, 7,072 sq ft, £69,330 p.a. plus 1,388 sq ft vacant storage.
- 48 Sackville Road: five-flat long-leasehold investment, £30,541.20 p.a. plus one vacant flat; headlease expiry 31 May 2132.
- 8/10 Newland Street: three retail units, 7,946 sq ft, £32,000 p.a.; one unit holding over and one unit vacant.
- 51 Market Place: source conflict preserved because the catalogue states both recently let at £12,000 p.a. and currently vacant.

## Guards

- Existing planning permission was stored separately from STC, STP and alternative-use potential.
- Current income was stored separately from historic, nearby or advertised rent.
- Holding-over occupation was not treated as a new lease.
- Vacant storage and vacant upper floors were not treated as income-producing accommodation.
- Source conflicts were retained as blockers rather than silently reconciled.
- No fake data, candidate promotion, database write, migration, force push or runner duplication occurred.

## Automation blocker

Automation 167 remains queued for the existing single F-host runner. The slot heartbeat remains unclaimed/stale; no second task or runner was created.
