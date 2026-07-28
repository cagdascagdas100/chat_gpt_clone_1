# ready_to_sell_2 — New Candidate Groups 97–101 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current auction listing.
- 50 active records staged: Lots 1–27 excluding inactive Lot 19A, then Lots 29, 30, 30A and 30B.
- Lot 19A was excluded as Sold Prior; Lot 28 was excluded as Withdrawn.
- 50 exact-address repository duplicate preflights returned zero matches.
- Source scope is the first-party current-auction listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 50/50
- Duplicate preflights: 50/50; matches: 0
- Checks: 100/100
- Source-supported fields: 350/350
- Matched before fail-closed normalization: 349/350 = 99.71%
- Verified enrichments: 300
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.06/100
- Validation: 13 PASS / 0 FAIL

## High-value and conflict-sensitive rows

1. Lot 15 — 58 Vauxhall Grove, vacant seven-room end-terrace house; guide £900,000+. Seven rooms are not inferred as seven bedrooms.
2. Lot 1 — 31 Lansdowne Road, vacant four-bedroom semi-detached house; guide £490,000+. Additional-house plans remain subject to consents.
3. Lot 14 — 12–14 Frederick Street, vacant commercial development site; guide £450,000+. Permission for five houses is source-stated, while the separate seventeen-bedroom HMO is plans-drawn only.
4. Lot 16 — Flat 8 Fraser House, guide £450,000+, subject to an unknown tenancy and not treated as vacant possession.
5. Lot 10B — source heading says terraced while description says semi-detached; the conflict is preserved.

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before the auction.
- Vacant wording is used only where the source explicitly states it.
- Unknown, periodic and assured tenancies are not vacant possession.
- A sold-off ground-floor flat plus a let upper flat does not make the whole freehold vacant.
- Plans drawn, potential, positive pre-application and submitted applications are not permission.
- Lapsed planning permission is not current approval.
- Permission for an extension is not permission for an additional dwelling.
- Land, garage, development site and commercial units are not existing dwellings.
- Room count is not bedroom count.
- The Lot 10B property-type conflict remains explicit and unnormalised.
- Approximate areas remain approximate.
- Legal-pack review remains pending.

## Cumulative staging

- Source rows: 1,201
- Checks: 2,406/2,406
- Active unique candidates: 1,169
- Source upgrades: 1,169
- Verified enrichments: 6,165
- Audited agreement before normalization: 9,341/9,375 = 99.64%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.32/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
