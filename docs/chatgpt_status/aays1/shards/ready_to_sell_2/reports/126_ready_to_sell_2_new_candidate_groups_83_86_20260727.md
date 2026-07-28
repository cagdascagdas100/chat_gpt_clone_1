# ready_to_sell_2 — New Candidate Groups 83–86 (status-refreshed 2026-07-28)

## Scope

- First-party source: Auction House East Anglia 29 July 2026 current auction listing.
- 40 source rows remain visible and auditable.
- Current active candidates: 38.
- Lot 17 is Sold Prior; Lot 25 is Withdrawn; Lot 27 is Postponed; Lot 39 is Sold STC.
- Lot 25 and Lot 27 were detected during a current-source refresh and corrected through an overlay without rewriting the original snapshot.
- 40 exact-address repository duplicate preflights returned zero matches.
- Source scope is the first-party event listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 40/40
- Active candidate rows: 38
- Corrected prior rows: 2
- Duplicate preflights: 40/40; matches: 0
- Checks: 80/80
- Source-supported fields: 280/280
- Verified enrichments: 200
- Current-source agreement after correction: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.00/100
- Validation: 12 PASS / 0 FAIL

## High-value source rows

1. Lot 16 — The Old Maltings block of apartments; guide £1,000,000–£1,200,000.
2. Lot 19 — Wood Farm five-bedroom farmhouse; guide £550,000.
3. Lot 18 — Grove Cottage five-bedroom detached house; guide £475,000.
4. Lot 31 — Holly Farm House three-bedroom farmhouse; guide £400,000–£450,000.
5. Lot 13 — 49 Norwich Road source-listed as a ten-bedroom detached house; guide £375,000.
6. Lot 22 — Thailand Restaurant source-listed as a three-bed restaurant; guide £375,000.

## Accuracy guards

- Status refreshes are applied as an auditable overlay; original source snapshots remain preserved.
- Withdrawn, Postponed, Sold Prior and Sold STC rows are not active candidates.
- A listing snapshot is not an individual lot detail page.
- Tenure and occupancy are not stated and are not inferred.
- Guide price is not sale price.
- Source property-type and bedroom labels are preserved without legal or physical normalization.
- Land, plot and commercial-development labels are not existing dwellings or planning permission.
- Restaurant bedroom wording is not lawful residential-use verification.
- Block-of-apartments unit count is not inferred.
- Legal pack and individual lot detail review remain pending.

## Corrected cumulative staging

- Source rows: 1,050
- Checks: 2,100/2,100
- New unique candidates: 1,018
- Source upgrades: 1,018
- Verified enrichments: 5,310
- Audited agreement before normalization: 8,288/8,320 = 99.62%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.37/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
