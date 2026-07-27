# ready_to_sell_2 — New Candidate Groups 77–79 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential and commercial auction catalogue, pages 18–21.
- 30 active records staged: Lots 174–176, 178, 179, 182, 184–189, 191, 193–199, 201, 202, 204–209, 211 and 212.
- Lots 177, 180, 181 and 183 were excluded as Withdrawn Prior; Lots 190 and 192 as Withdrawn; Lot 200 as Sold Prior.
- 30 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 180
- Raw catalogue agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.30/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 211 — vacant strategic West Drayton land of approximately 6.375 acres; guide £2,500,000.
2. Lot 206 — freehold Colliers Wood mixed investment with two commercial units and two one-bedroom duplex flats; current source-stated income £74,600 p.a.; guide £800,000.
3. Lot 202 — vacant freehold Wandsworth mixed-use building with retail and two flats; guide £590,000.
4. Lot 209 — vacant-possession freehold Reading office opportunity of approximately 5,465 sq ft; guide £390,000.
5. Lot 201 — vacant freehold Woking mixed-use building with takeaway and three-bedroom flat; guide £350,000.
6. Lot 212 — Barnsley retail investment let to Specsavers; source-stated income £45,000 p.a.; guide £325,000.

## Accuracy guards

- Sold Prior, Withdrawn and Withdrawn Prior records are excluded.
- Unstated occupancy is not treated as vacant.
- Ground-rent investments are not treated as vacant buildings or ownership of the individual flats.
- The Essex portfolio remains one research candidate and is not parcel-bound without title geometry.
- Future rent and tenant intention are not treated as current executed income.
- Development, redevelopment and residential-conversion potential is not planning permission.
- Garages, workshops, offices and strategic land are not treated as existing residential dwellings.
- Current lawful mixed-use configuration is not inferred from marketing wording.
- Lease, income, reversion and title-scope claims remain pending legal-pack review.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 980
- Checks: 1,960/1,960
- New unique candidates: 950
- Source upgrades: 950
- Verified enrichments: 4,930
- Audited agreement before normalization: 7,768/7,800 = 99.59%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
