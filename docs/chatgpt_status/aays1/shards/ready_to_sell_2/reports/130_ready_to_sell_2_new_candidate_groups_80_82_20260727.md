# ready_to_sell_2 — New Candidate Groups 80–82 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential and commercial auction catalogue, pages 22–25.
- 30 active records staged: Lots 213, 216–222, 224–228, 230, 231, 233, 234, 243, 244, 247, 248, 250–254, 259, 260, 262 and 263.
- Lot 215 was excluded as Sold Prior; Lot 245 was excluded as Withdrawn Prior.
- 30 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 180
- Raw catalogue agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.23/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 219 — vacant Grade II listed Mayfair mixed-use building; guide £5,750,000.
2. Lot 222 — vacant Queen Anne Street mixed-use building marketed as virtual freehold; guide £5,400,000.
3. Lot 216 — Kings Road mixed-use former furniture store and four-bedroom apartment, vacant on completion; guide £2,700,000.
4. Lot 233 — ten-unit Bradford industrial estate; source-stated annual income £191,179; guide £1,950,000.
5. Lot 213 — seven-unit Cardiff industrial estate with six tenants, one vacant unit and source-stated annual income £173,361; guide £1,750,000.
6. Lot 225 — Stafford medical centre investment with source-stated annual income £88,165 and 41 parking spaces; guide £1,200,000.

## Accuracy guards

- Sold Prior and Withdrawn Prior records are excluded.
- Mixed and part occupancy is not treated as full vacant possession.
- A 12-month rent guarantee is not treated as current tenant income.
- “Virtual freehold” marketing wording is not normalized to freehold.
- Future rent, outstanding rent review and tenant intention are not treated as current executed income.
- Planning, development, conversion and change-of-use potential is not planning permission.
- Future houses, apartments, studios and other proposed units are not treated as existing units.
- Sold-off long-lease garages are not treated as vacant retained assets.
- Currently trading and vacant on completion remain temporally distinct.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 1,010
- Checks: 2,020/2,020
- New unique candidates: 980
- Source upgrades: 980
- Verified enrichments: 5,110
- Audited agreement before normalization: 8,008/8,040 = 99.60%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
