# ready_to_sell_2 — New Candidate Groups 102–107 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current-auction listing.
- 60 active records staged from the Lot 31–69 range.
- Lot 39 was excluded as Sold Prior; Lots 55 and 56 were excluded as Withdrawn.
- 60 exact-address repository duplicate preflights returned zero matches.
- Source scope is the first-party listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 60/60
- Duplicate preflights: 60/60; matches: 0
- Checks: 120/120
- Source-supported fields: 420/420
- Matched before fail-closed normalization: 419/420 = 99.76%
- Verified enrichments: 360
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.04/100
- Validation target: 14 PASS / 0 FAIL

## Source-semantics distribution

- Explicit vacant residential rows: 34
- Tenanted or income-bearing investment rows: 10
- Commercial or mixed-use rows: 11
- Land, planning or special-semantics rows: 5

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before auction.
- Vacant wording is used only where explicitly stated.
- Assured, periodic, regulated, commercial and unknown tenancies are not vacant possession.
- Income figures remain source claims pending legal-pack review.
- Room count is not bedroom count.
- Commercial, mixed-use, office, shop and garage rows are not assumed residential dwellings.
- Plans drawn, potential, pre-application, submitted applications and lapsed permissions are not current planning permission.
- Permission for an extension is not permission for an additional dwelling.
- Approximate areas remain approximate.
- Missing tenure, lawful use, unit count and title extent are not inferred.

## Cumulative staging

- Source rows: 1,261
- Checks: 2,526/2,526
- Active unique candidates: 1,229
- Source upgrades: 1,229
- Verified enrichments: 6,525
- Audited fields: 9,795
- Matched fields before normalization: 9,760/9,795 = 99.64%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.31/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
