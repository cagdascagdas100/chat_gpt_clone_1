# ready_to_sell_2 — New Candidate Groups 71–73 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential auction catalogue, pages 11–14.
- 30 active records staged: Lots 101–111, 113, 115–117, 117A–124, 127, 129, 129A and 130–133.
- Lots 112, 125 and 126 were excluded as Withdrawn Prior; Lot 128 was excluded as Sold Prior.
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
- Average verification confidence: 99.40/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 116 — freehold four-flat Ealing building; source-stated annual income £64,300 plus one vacant flat; guide £1,600,000.
2. Lot 101 — freehold Hyde Park Estate two-bedroom mews house with source-stated positive pre-app and one garage leased for approximately seven years; guide £1,500,000.
3. Lot 127 — Grade II listed detached seven-bedroom Torquay house; source claims over 11,000 sq ft; guide £1,200,000; occupancy not stated.
4. Lot 117A — vacant Chigwell two-bedroom bungalow with source-stated planning permission for loft conversion and rear extension; guide £540,000.
5. Lot 121 — vacant Dulwich three-bedroom back-to-back semi-detached house; guide £425,000.
6. Lot 130 — Earl's Court investment studio with source-stated annual income £17,400 and approximately 108 years remaining; guide £200,000.

## Accuracy guards

- Withdrawn Prior and Sold Prior records are excluded.
- Lot 101's leased garage is not treated as vacant possession; positive pre-app is not planning permission.
- Lot 116's investment income plus one vacant flat is not treated as full vacant possession.
- Lot 117A's planning-permission statement is preserved as a source claim; reference, conditions and implementation remain pending.
- Lot 127's occupancy and tenure remain unstated and are not inferred.
- Lot 131's commenced works are not treated as completed units or verified lawful configuration.
- Development, extension and further potential is not treated as planning permission.
- New, long and short lease wording is preserved without legal normalization.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 920
- Checks: 1,840/1,840
- New unique candidates: 890
- Source upgrades: 890
- Verified enrichments: 4,570
- Audited agreement before normalization: 7,288/7,320 = 99.56%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
