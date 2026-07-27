# ready_to_sell_2 — New Candidate Groups 68–70 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential auction catalogue, pages 8–11.
- 30 active records staged: Lots 71–82, 84, 85, 85A and 86–100.
- Lot 83 was excluded because the current catalogue marks it Withdrawn Prior.
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
- Average verification confidence: 99.50/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 85A — three-bedroom Mortlake period cottage on a generous plot; current first-party guide £775,000; development potential remains subject to consents.
2. Lot 71 — Clerkenwell three-bedroom second-floor flat with allocated parking and source-claimed new 150-year lease; guide £700,000.
3. Lot 86 — vacant five-bedroom Wembley end-terrace house with extension/conversion potential subject to consents; guide £495,000.
4. Lot 92 — Manchester two-bedroom investment flat; source-stated annual income £36,000; guide £400,000.
5. Lot 93 — vacant Stratford live/work unit with source-stated planning permission to split into a self-contained flat and office; guide £375,000.
6. Lot 98 — Ruislip two-bedroom ground-floor maisonette with source-claimed approximately 12 years unexpired; guide £100,000.

## Accuracy guards

- Lot 83 is excluded as Withdrawn Prior.
- Lot 72 remains `understood_vacant_but_not_guaranteed`; it is not promoted to vacant possession.
- Lot 74 is part vacant only; two flats sold on long leases are not treated as vacant retained assets.
- Development, extension, conversion and parking potential is not treated as planning permission.
- Lot 80's three-room wording is not converted to three bedrooms.
- Lot 93's planning-permission statement is preserved as a source claim; reference, conditions and implementation status remain pending.
- Lot 94's loft conversion is not treated as independently lawful.
- New, long and very short lease wording is preserved without legal normalization.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 890
- Checks: 1,780/1,780
- New unique candidates: 860
- Source upgrades: 860
- Verified enrichments: 4,390
- Audited agreement before normalization: 7,048/7,080 = 99.55%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
