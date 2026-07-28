# ready_to_sell_2 — New Candidate Groups 87–91 (2026-07-28)

## Scope

- First-party source: Auction House East Anglia 29 July 2026 current auction listing.
- 50 active records staged: Lots 40–51, 53, 53a, 54–60, 60A, 61–71, 73–75, 77, 79–83 and 86–93.
- Lot 52 and Lot 85 were excluded as Sold Prior; Lots 72, 76 and 84 were excluded as Postponed/Withdrawn.
- 50 exact-address repository duplicate preflights returned zero matches.
- Source scope is the first-party event listing snapshot, not individual lot detail pages.
- Wave 47 current-status corrections remain applied: its active-candidate contribution is 38, not 40.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 50/50
- Duplicate preflights: 50/50; matches: 0
- Checks: 100/100
- Source-supported fields: 350/350
- Verified enrichments: 250
- Current-source agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.00/100
- Validation: 12 PASS / 0 FAIL

## High-value source rows

1. Lot 62 — 286 London Road residential-development listing; guide £750,000–£850,000.
2. Lot 58 — 23 Cobham Road source-listed as a 13-bed commercial property; guide £650,000.
3. Lot 51 — Riverside Cottages four-bedroom detached-house listing; guide £400,000.
4. Lot 86 — 18 and 18A Beatrice Avenue six-bedroom detached-house listing; guide £395,000.
5. Lot 66 — 127/127a Albany Road source-listed as two-bed mixed use; guide £375,000.

## Accuracy guards

- Listing snapshot is not an individual lot detail page.
- Tenure and occupancy are not stated and are not inferred.
- Guide price is not sale price.
- Source property-type and bedroom labels are preserved without legal or physical normalization.
- Land, plot and residential-development labels are not existing dwellings or planning permission.
- Commercial, shop, retail and mixed-use labels are not lawful residential-use verification.
- Missing bedroom count is not inferred.
- Sold Prior, Postponed and Withdrawn records are not active candidates.
- Legal pack and individual lot detail review remain pending.

## Cumulative staging

- Source rows: 1,100
- Checks: 2,200/2,200
- New unique candidates: 1,068
- Source upgrades: 1,068
- Verified enrichments: 5,560
- Audited agreement before normalization: 8,638/8,670 = 99.63%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.35/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
