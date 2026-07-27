# ready_to_sell_2 — New Candidate Groups 47–49 (2026-07-27)

## Scope

- First-party sources: Auction House London current 29–30 July 2026 catalogue and official timed-auction summary.
- 30 active records staged: 25 livestream Lots 204–223 plus 5 timed-auction records.
- Current-auction Lots 224–242 were excluded because the official catalogue marks all 19 Sold Prior.
- 30 exact-address/title repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 114
- Raw source agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.57/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 207 — approximately 3.68 acres / 14,892 sq m / 160,296 sq ft of land and roadways.
2. Lot 208 — approximately 5.45 acres / 22,055 sq m / 237,398 sq ft of land and roadways.
3. Lot 215 — six garages on 2,070 sq ft; two let producing £1,560 p.a.; development potential only subject to consents.
4. Lot 222 — approximately 2,139 sq m / 23,021 sq ft of freehold land.
5. Timed T1 — approximately 930 sq m / 10,010 sq ft Solihull land, guide and starting price £45,000.
6. Timed T3 — eleven freehold plots and roadways; individual addresses and areas are absent from the summary and remain unbound.
7. Timed T5 — approximately 1,520 sq m / 16,366 sq ft at Plot B2 Top Farm.

## Accuracy guards

- No Reserve is not converted into a guide price.
- Starting price and guide price remain separate fields.
- Unspecified occupancy is not treated as vacant.
- Sold-off flats and ground-rent investments are not treated as physical vacant possession.
- Development potential is not treated as planning permission.
- Approximate measurements remain approximate.
- Timed-auction tenure missing from the summary is not inferred.
- Detail-link internal errors fall back to first-party summary evidence; no missing fields are invented.
- Current-auction Lots 224–242 are excluded as Sold Prior.

## Cumulative staging

- Source rows: 710
- Checks: 1,420/1,420
- New unique candidates: 680
- Source upgrades: 680
- Verified enrichments: 3,315
- Audited agreement before normalization: 5,610/5,640 = 99.47%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.41/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
