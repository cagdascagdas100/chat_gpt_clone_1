# ready_to_sell_2 — New Candidate Groups 50–52 (2026-07-27)

## Scope

- First-party sources: SDL Property Auctions live-stream event pages and Auction House active online-auction pages.
- 30 active records staged: 5 SDL and 25 Auction House records.
- 30 exact-address repository duplicate preflights returned zero matches.
- No sold/withdrawn record, canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 175
- Raw cross-source agreement: 99.17%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.17/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. SDL-51128 — Skegness guest house with source-claimed planning for eight self-contained holiday units; two rooms still operate through Airbnb and vacant possession is only promised on completion.
2. SDL-51256 — Swanwick plot with source-claimed full detailed planning reference AVA/2026/0146 for a three-bedroom detached bungalow and garage.
3. AH-86435903 — Darlington three-bedroom semi-detached house plus adjoining land with source-claimed planning permission for another three-bedroom dwelling.
4. AH-189436 — Coventry HMO arranged as five bedsits and one studio; £32,000 p.a. is potential income, not current income.
5. AH-189061 — Eastwood plot with lapsed former permission; restoration application is not approval.
6. AH-8f8ec225 — fully vacant freehold mixed-use former takeaway and two-bedroom flat measuring approximately 114 sq m / 1,227 sq ft.
7. SDL-51352 and SDL-51320 — tenanted investments producing £12,000 p.a. each.

## Accuracy guards

- 5 James Court has first-floor and second-floor source wording; no single floor is asserted.
- Lemare Lodge says fifth-floor flat but also describes a building over ground and first floors; the conflict is preserved.
- Pre-planning advice, potential income, lapsed permission and restoration applications are not treated as current approval or current rent.
- The Minchinhampton bungalow bedroom count is retained as a source claim because the auctioneer could not access the interior.
- “Effective freehold” remains a marketing phrase; 5 Evesham Street is recorded as leasehold.
- Immediate availability and no onward chain are not treated as formal vacant possession.
- Missing tenure, occupancy, bedroom and service-charge fields are not inferred.

## Cumulative staging

- Source rows: 740
- Checks: 1,480/1,480
- New unique candidates: 710
- Source upgrades: 710
- Verified enrichments: 3,490
- Audited agreement before normalization: 5,848/5,880 = 99.46%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.40/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
