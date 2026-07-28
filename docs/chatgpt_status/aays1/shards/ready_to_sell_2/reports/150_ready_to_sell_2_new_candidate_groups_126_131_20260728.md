# ready_to_sell_2 — New Candidate Groups 126–131 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current-auction listing.
- 60 active records staged: first 60 active records after Lot 167, ending at Lot 217.
- Lot 182 and Lot 197 were excluded as Withdrawn; Lots 187–192 were excluded as Sold Prior.
- 60 exact-address repository duplicate preflights returned zero matches.
- One adjacent-interest review confirmed Lots 185 and 186 are separate addresses and separate research interests.
- Source scope is the first-party current-auction listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 60/60
- Duplicate preflights: 60/60; matches: 0
- Related-interest checks: 1/1
- Checks: 121/121
- Source-supported fields: 420/420
- Matched before fail-closed normalization: 420/420 = 100.00%
- Verified enrichments: 360
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 98.90/100
- Validation: 15 PASS / 0 FAIL

## High-value and semantics-sensitive rows

1. Lot 176A — 126 Uppingham Avenue, vacant three-bedroom semi-detached house; guide £500,000+.
2. Lot 177 — Tig Bhan, two two-bedroom holiday lets currently let via Airbnb and offered with vacant possession; guide £350,000+. Both states are preserved.
3. Lot 170 — Flat 2, 69 Cowley Road, one-bedroom ground-floor flat; guide £345,000+. Occupancy is not stated and not inferred.
4. Lot 172 — 6 Aviary Close, four-bedroom end-terrace house; guide £320,000+. Occupancy is not stated and not inferred.
5. Lot 213 — 9 Whippendell Road ground-rent investment; current £150 p.a., rising to £200 p.a. in 2048. Future rent is not current income.
6. Lot 215 — six garages at Cricketers Way; two are let producing £1,560 p.a.; development potential is not permission.

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before auction.
- Vacant wording is used only where the source explicitly states it.
- Occupancy is not inferred where unstated.
- Periodic tenancy, student tenancy, part-let garages, ground-rent investment and current holiday letting are not ordinary vacant possession.
- “Currently let via Airbnb” and “offered with vacant possession” are both preserved for Lot 177.
- Retirement restrictions, lease terms, income, title and reversion scope require legal-pack review.
- Room count is not bedroom count; a generic “unit” label does not establish lawful residential use.
- Former church, former Salvation Army, land, garages, parking, beach and roadways are not existing standard dwellings.
- Development potential is not planning permission.
- Flats sold off on long leases do not make the freehold building vacant.
- Future ground rent is not current income.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 1,441
- Checks: 2,891/2,891
- Active unique candidates: 1,409
- Source upgrades: 1,409
- Verified enrichments: 7,605
- Audited agreement before normalization: 11,018/11,055 = 99.67%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.27/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
