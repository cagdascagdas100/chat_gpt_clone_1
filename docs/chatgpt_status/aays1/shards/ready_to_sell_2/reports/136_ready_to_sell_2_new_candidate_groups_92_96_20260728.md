# ready_to_sell_2 — New Candidate Groups 92–96 (2026-07-28)

## Scope

- First-party source: Auction House East Anglia 29 July 2026 current auction listing plus individual lot detail status checks.
- 50 new active records staged: Lots 94, 95, 95a, 97, 97a, 98, 98A, 99–101, 103, 103a, 104–116, 118–140.
- Lot 96 was excluded as Sold Prior, Lot 102 as Postponed and Lot 117 as Withdrawn on the individual detail page.
- Wave 48 current-status correction adds Lot 84 as one current active row; Lot 85 remains Sold Prior.
- 51 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 51/51
- Duplicate preflights: 51/51; matches: 0
- Checks: 106/106
- Source-supported fields: 355/355
- Matched before fail-closed normalization: 354/355 = 99.72%
- Verified enrichments: 305
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 98.91/100
- Validation: 13 PASS / 0 FAIL

## High-value and conflict-sensitive rows

1. Lot 94 — Eight Elms; guide £700,000. The source header says four bedrooms while the body says six; the conflict is preserved.
2. Lot 113 — Autumn Leaves five-bedroom detached-house listing; guide £450,000–£500,000.
3. Lot 101 — 63 Hay Street three-bedroom detached-house listing; guide £445,000.
4. Lot 132 — White Lodge header says six-bedroom detached house while the body describes four self-contained flats; lawful configuration is not inferred.
5. Lot 121 — 1 & 2 Westerfield House Farm Cottages; guide £325,000–£375,000.
6. Lot 84 — 18 Postmill Close returned to active status; guide £92,000; leasehold.

## Accuracy guards

- Individual lot detail status controls when the event listing conflicts.
- Source-internal bedroom and configuration conflicts remain explicit.
- Tenure and occupancy are not inferred when not stated.
- Tenant in situ and investment-let records are not vacant possession.
- Vacant commercial property is not a vacant residential dwelling.
- Land, barn, office, shop and place-of-worship rows are not existing residential dwellings.
- Planning or alternative-use potential is not permission.
- Block/apartment labels and bedroom counts do not establish lawful unit count.
- Guide price is not sale price.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 1,151
- Checks: 2,306/2,306
- Active unique candidates: 1,119
- Source upgrades: 1,119
- Verified enrichments: 5,865
- Audited agreement before normalization: 8,992/9,025 = 99.63%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.33/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
