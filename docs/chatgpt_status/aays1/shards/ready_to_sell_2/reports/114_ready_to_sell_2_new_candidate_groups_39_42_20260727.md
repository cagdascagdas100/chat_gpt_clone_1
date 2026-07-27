# ready_to_sell_2 — New Candidate Groups 39–42 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue and accessible detail pages.
- 40 active records staged from Lots 131–170.
- Lot 151 was excluded because the current first-party catalogue marks it Sold Prior.
- 40 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 40/40
- Duplicate preflights: 40/40; matches: 0
- Checks: 80/80
- Source-supported fields: 320/320
- Verified enrichments: 168
- Raw cross-source agreement: 99.06%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.53/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 135 — 3,746 sq ft land; plans drawn for two three-bedroom semi-detached houses; no planning application submitted.
2. Lot 140 — 355 sq m / 3,821 sq ft land; plans drawn for two three-bedroom semi-detached houses; no planning application submitted.
3. Lot 142 — pair of vacant semi-detached houses, five-bed and two-bed; three storeys, refurbishment required, garage and large gardens.
4. Lot 150 — four-bedroom end-terrace house producing £21,519.84 p.a.; individual tenancies and no internal viewing.
5. Lot 160 — 212 sq m / 2,281 sq ft land; development potential only, subject to consents.
6. Lot 166 — vacant former fourteen-bedroom hotel; lawful use and licensing remain unverified.

## Accuracy guards

- Lot 134 guide price differs between earlier official snapshot (£40,000+) and current catalogue (£50,000+); current catalogue controls.
- Lot 135 area differs between earlier official snapshot (3,678 sq ft) and current detail (3,746 sq ft); current detail controls and remains approximate.
- Lot 142 current catalogue gives £180,000–£260,000 while current detail page gives £180,000+; no combined value is asserted.
- Unspecified occupancy for Lots 131, 132, 153 and 170 is not treated as vacant.
- Regulated, periodic and individual tenancies are not treated as vacant possession.
- Plans drawn and development potential are not treated as planning permission.
- Room counts are not silently converted into bedroom counts.
- Lot 151 Sold Prior is excluded.

## Cumulative staging

- Source rows: 640
- Checks: 1,280/1,280
- New unique candidates: 610
- Source upgrades: 610
- Verified enrichments: 3,053
- Audited agreement before normalization: 5,050/5,080 = 99.41%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.4/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so port-8012 headless DOM proof and canonical promotion remain blocked. No second runner or duplicate task was created.
