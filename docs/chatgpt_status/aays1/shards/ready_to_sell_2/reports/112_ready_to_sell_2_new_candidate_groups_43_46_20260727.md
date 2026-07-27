# ready_to_sell_2 — New Candidate Groups 43–46 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue.
- 40 active records staged from Lots 171–203.
- Lots 187–192 were excluded as Sold Prior; Lot 197 was excluded as Withdrawn.
- 40 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 40/40
- Duplicate preflights: 40/40; matches: 0
- Checks: 80/80
- Source-supported fields: 320/320
- Verified enrichments: 148
- Raw catalogue agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.45/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 177 — detached house arranged as two two-bedroom holiday lets, currently marketed through Airbnb and offered with vacant possession; booking and possession readback remains pending.
2. Lot 178A — 323 sq m / 3,484 sq ft freehold land; no planning permission inferred.
3. Lot 200 — twelve single-storey lock-up garages on approximately 6,100 sq ft; development potential only, subject to consents.
4. Lot 202 — 468 sq m / 5,040 sq ft freehold land; development potential only, subject to consents.
5. Lot 202A — vacant garage on approximately 54 sq m / 581 sq ft.
6. Lot 203 — beach land measuring approximately 3.89 acres / 15,750 sq m / 169,531 sq ft.
7. Lots 181, 193, 197A and 199 retain their tenancy/no-internal-viewing status and are not treated as vacant.

## Accuracy guards

- Unspecified occupancy is not treated as vacant possession.
- Periodic, student and other tenancies are not treated as vacant.
- Development or redevelopment potential is not treated as planning permission.
- Room counts and unspecified unit use are not converted into bedroom counts or residential use.
- Unusual catalogue tenure/classification fields are preserved and sent to legal-pack review.
- Approximate land and beach measurements remain approximate.
- Detail-link internal errors fall back to current catalogue evidence; no missing fields are invented.
- Sold Prior and Withdrawn lots are excluded from candidate publication.

## Cumulative staging

- Source rows: 680
- Checks: 1,360/1,360
- New unique candidates: 650
- Source upgrades: 650
- Verified enrichments: 3,201
- Audited agreement before normalization: 5,370/5,400 = 99.44%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.4/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so port-8012 headless DOM proof and canonical promotion remain blocked. No second runner or duplicate task was created.
