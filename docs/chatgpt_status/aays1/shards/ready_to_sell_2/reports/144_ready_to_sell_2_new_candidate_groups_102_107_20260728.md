# ready_to_sell_2 — New Candidate Groups 102–107 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current-auction listing.
- 60 active records staged: Lots 31–38B, 40–54, 55A, 56A–69, excluding inactive records.
- Lot 39 was excluded as Sold Prior; Lots 55 and 56 were excluded as Withdrawn.
- 60 exact-address repository duplicate preflights returned zero matches.
- Source scope is the first-party current-auction listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 60/60
- Duplicate preflights: 60/60; matches: 0
- Current-source refresh corrections: 3/3
- Checks: 123/123
- Source-supported fields: 420/420
- Matched after current-source refresh and before fail-closed normalization: 420/420 = 100.00%
- Verified enrichments: 360
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.10/100
- Validation: 15 PASS / 0 FAIL

## Current-source corrections

1. Prior Wave 50 Lot 4 — guide refreshed from £230,000+ to £250,000+.
2. Wave 51 Lot 34A — guide corrected from an unsupported £90,000–£160,000 range to £90,000+.
3. Wave 51 Lot 69 — guide corrected from £600,000+ to £650,000+.

The original values remain available in Git history; current row rendering now uses the verified current-source values.

## High-value and semantics-sensitive rows

1. Lot 31A — 24 Great North Road, five-flat fully let building; guide £1,500,000+; source income £121,800 p.a.
2. Lot 38A — 82 Sussex Way, three-flat building offered with vacant possession; guide £1,300,000+.
3. Lot 43 — land at Great Leighs, approximately 1.32 acres with source-stated permission for eight detached homes; guide £1,250,000+.
4. Lot 63B — 245 Royal College Street, three flats fully let; guide £1,100,000+; source income £91,392 p.a.
5. Lot 63A — 33 Fairbridge Road, two flats fully let; guide £1,000,000+; source income £87,600 p.a.
6. Lot 66 — 1 Wood Lane, shop plus four letting rooms fully let; guide £850,000+; source income £89,900 p.a.

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before auction.
- Vacant wording is used only where the source explicitly states it.
- Periodic, guaranteed-rent, fully-let and part-let records are not vacant possession.
- Notice served is not vacant possession.
- Commercial, mixed-use, office, industrial, retail and land records are not existing residential dwellings.
- Room count is not bedroom count; bedroom ranges remain ranges.
- Unit mix and letting-room wording do not independently establish lawful configuration.
- Plans drawn, potential, permitted-development wording and prior permission are not current implemented approval.
- Planning claims remain subject to reference, conditions, commencement and implementation review.
- Approximate measurements remain approximate.
- Income, ERV, yield, tenancy, lease, title and unit configuration require legal-pack review.

## Cumulative staging

- Source rows: 1,261
- Checks: 2,529/2,529
- Active unique candidates: 1,229
- Source upgrades: 1,229
- Verified enrichments: 6,525
- Audited agreement before normalization: 9,761/9,795 = 99.65%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.31/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.