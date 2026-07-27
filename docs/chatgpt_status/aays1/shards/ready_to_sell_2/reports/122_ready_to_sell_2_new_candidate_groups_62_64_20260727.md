# ready_to_sell_2 — New Candidate Groups 62–64 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential auction catalogue.
- 30 active records staged: Lots 1–17, 19–29 and 31.
- Lots 18 and 30 were excluded because the catalogue marks them Sold Prior.
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
- Average verification confidence: 99.60/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 20 — 192 Victoria Road, vacant four-bedroom mid-terrace house, approximately 2,271 sq ft, guide £1,000,000.
2. Lot 9 — 25 Norman Grove, vacant three-bedroom Bow terraced house, guide £785,000.
3. Lot 2 — ten one-bedroom self-contained flats plus office accommodation in Birmingham, vacant, guide £650,000.
4. Lot 4 — Dulwich three-bedroom maisonette with source-claimed 40 years unexpired, guide £500,000.
5. Lot 25 — freehold four-bedroom Upper Norwood house, approximately 137.68 sq m / 1,500 sq ft, guide £450,000.
6. Lot 6 — Streatham three-bedroom flat on a periodic tenancy producing £24,000 per annum.
7. Lot 12 — previous rent of £2,200 per month is historical and is not treated as current income.

## Accuracy guards

- Lots 18 and 30 are excluded as Sold Prior.
- Development, extension, loft or holiday-let potential is not treated as planning permission.
- Previous rent is not treated as current rent.
- Four-room wording is not converted to four bedrooms.
- Unspecified occupancy is not treated as vacant.
- Periodic tenancy is not treated as vacant possession.
- New, long or dual lease/freehold wording is preserved without legal normalization.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 830
- Checks: 1,660/1,660
- New unique candidates: 800
- Source upgrades: 800
- Verified enrichments: 4,030
- Audited agreement before normalization: 6,568/6,600 = 99.52%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
