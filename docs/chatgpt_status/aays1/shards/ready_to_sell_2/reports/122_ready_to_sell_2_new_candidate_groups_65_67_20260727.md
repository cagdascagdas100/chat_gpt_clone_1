# ready_to_sell_2 — New Candidate Groups 65–67 (2026-07-27)

## Scope

- First-party source: Savills 28–29 July 2026 residential auction catalogue, pages 4–7.
- 30 active records staged: Lots 32, 33, 34, 35, 37–56, 58, 59, 61, 62, 64 and 65.
- Lot 34A was excluded as Withdrawn, Lot 36 as Sold Prior, Lot 67 as Withdrawn and Lot 70 as Withdrawn Prior.
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

1. Lot 47 — two newly constructed freehold blocks with 28 flats; source-stated annual income £443,010; guide £6,000,000.
2. Lot 39 — freehold 16-flat block with nine units sold off on long leases, source-stated annual income £90,322 and vacant possession of two flats; guide £1,800,000.
3. Lot 61 — two private islands totalling approximately 2.9 acres with a five-bedroom detached house; guide £1,650,000.
4. Lot 62 — vacant four-bedroom Raynes Park semi-detached house; guide £550,000.
5. Lot 64 — four-bedroom first-floor investment flat, source-stated annual income £39,600; guide £370,000.

## Accuracy guards

- Withdrawn, Withdrawn Prior and Sold Prior records are excluded.
- Lot 32's two-bedroom end-terrace and two one-bedroom flat wording is preserved as a source-card conflict rather than reconciled.
- Development and extension potential is not treated as planning permission.
- Mixed income plus vacant flats is not treated as full vacant possession.
- Source income and tenancy claims remain subject to legal-pack review.
- A ground-floor flat sold off on lease is not treated as a vacant retained asset.
- New lease wording remains source-claimed and is not independently legally normalized.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 860
- Checks: 1,720/1,720
- New unique candidates: 830
- Source upgrades: 830
- Verified enrichments: 4,210
- Audited agreement before normalization: 6,808/6,840 = 99.53%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.