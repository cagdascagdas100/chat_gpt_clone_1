# ready_to_sell_2 — New Candidate Groups 74–76 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential auction catalogue, pages 14–18.
- 30 active records staged: Lots 134–140, 143–155, 162–165 and 167–173, excluding numbering gaps and inactive lots.
- Lots 141 and 157 were excluded as Sold Prior; Lots 142 and 161A as Withdrawn; Lots 158, 158A, 160 and 161 as Withdrawn Prior.
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
- Average verification confidence: 99.37/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 151 — freehold six-bedroom HMO-arranged Tooting property, vacant and ready for letting source claim; guide £1,050,000.
2. Lot 150 — vacant Tooting building arranged as a four-bedroom maisonette and one-bedroom garden flat; approximately 2,023 sq ft; guide £985,000.
3. Lot 169 — Maida Vale one-bedroom lower-ground flat with rear garden; guide £341,000; occupancy not stated.
4. Lot 172 — vacant Paddington one-bedroom second-floor flat in a purpose-built block with lift; guide £310,000.
5. Lot 147 — Hanwell three-bedroom first-floor investment flat on a periodic tenancy; source-stated annual income £22,800; guide £300,000.

## Accuracy guards

- Sold Prior, Withdrawn and Withdrawn Prior records are excluded.
- Shared ownership remains a source claim pending legal-pack review.
- Periodic tenancy and investment-let records are not treated as vacant possession.
- Planning permission is retained only as a source claim pending reference, conditions and implementation verification.
- Development and extension potential is not treated as planning permission.
- Lot 165's two-room wording is not converted to two bedrooms.
- Lot 151's HMO arrangement, licensing and readiness for letting are not independently verified.
- Mobile-home pitch and site terms are not inferred.
- Current lawful flat/HMO configuration is not inferred from marketing wording.
- Unstated occupancy is not treated as vacant.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 950
- Checks: 1,900/1,900
- New unique candidates: 920
- Source upgrades: 920
- Verified enrichments: 4,750
- Audited agreement before normalization: 7,528/7,560 = 99.58%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
