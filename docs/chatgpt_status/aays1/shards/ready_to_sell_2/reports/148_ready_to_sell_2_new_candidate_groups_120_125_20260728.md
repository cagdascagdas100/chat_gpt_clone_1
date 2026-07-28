# ready_to_sell_2 — New Candidate Groups 120–125 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current-auction listing.
- 60 active records staged: Lots 112–128 and 130–167, excluding inactive records.
- Lots 129 and 151 were excluded as Sold Prior.
- 60 exact-address repository duplicate preflights returned zero matches.
- Two related-interest checks retained distinct interests: Lots 123/155 are separate leasehold flats in the same building; Lots 134/135 are a house and adjacent land.
- Source scope is the first-party current-auction listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 60/60
- Duplicate preflights: 60/60; matches: 0
- Related-interest checks: 2/2
- Checks: 122/122
- Source-supported fields: 420/420
- Matched before fail-closed normalization: 418/420 = 99.52%
- Verified enrichments: 360
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 98.98/100
- Validation: 15 PASS / 0 FAIL

## High-value and semantics-sensitive rows

1. Lot 120A — 16–17 Larkstone Terrace, pair of vacant buildings described as providing seventeen flats; guide £20,000–£60,000. Lawful unit configuration is not independently verified.
2. Lot 142 — 23 & 25 Corby Road, pair of vacant semi-detached houses; guide £180,000–£260,000.
3. Lot 121 — 62A Osborne Road, vacant three-bedroom house on approximately 1,208 sq m with outline permission for four dwellings; source category conflicts with its description.
4. Lot 124 — land adjacent to Esso, approximately 700 sq m with source-stated permission in principle for nine flats; guide £260,000+.
5. Lot 150 — 36 Summerhill, four-bedroom house subject to individual tenancies; source income £21,519.84 p.a.
6. Lot 113 — 88C London Road, periodic tenancy producing £16,800 p.a.; notice served is not vacant possession.

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before auction.
- Vacant wording is used only where the source explicitly states it.
- Periodic, individual, regulated and notice-served tenancies are not vacant possession.
- Notice served is not vacant possession.
- Occupancy is not inferred when not stated.
- Commercial, land, ground-rent, former-use and nonstandard rows are not standard vacant dwellings.
- Room count, former use and source bedroom ranges are not normalized to current bedroom count.
- Source category/description conflicts remain explicit.
- Submitted, awaiting-decision, outline and permission-in-principle planning claims are not completed detailed approval.
- Development potential is not planning permission.
- Approximate measurements remain approximate.
- Income, tenancy, lease, title, unit configuration, planning status and lawful use require legal-pack review.

## Cumulative staging

- Source rows: 1,381
- Checks: 2,770/2,770
- Active unique candidates: 1,349
- Source upgrades: 1,349
- Verified enrichments: 7,245
- Audited agreement before normalization: 10,598/10,635 = 99.65%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.29/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.