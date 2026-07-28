# ready_to_sell_2 — New Candidate Groups 114–119 (2026-07-28)

## Scope

- First-party source: Auction House London 29–30 July 2026 current-auction listing.
- 60 active records staged from Lots 70–111, excluding inactive records.
- Lots 75A, 79A and 85A were excluded as Sold Prior; Lots 77, 83 and 84 were excluded as Postponed.
- 60 exact-address repository duplicate preflights returned zero matches.
- Two same-building related-interest pairs were reviewed and retained as distinct leasehold candidates: Lots 76/107 and Lots 85/109.
- Source scope is the first-party current-auction listing snapshot, not individual lot detail pages.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 60/60
- Duplicate preflights: 60/60; matches: 0
- Related-interest checks: 2/2; distinct pairs retained: 2
- Checks: 122/122
- Source-supported fields: 420/420
- Matched before fail-closed normalization: 419/420 = 99.76%
- Verified enrichments: 360
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.00/100
- Validation: 15 PASS / 0 FAIL

## High-value and semantics-sensitive rows

1. Lot 73 — Unit 3 Hampstead Gate; vacant commercial office; guide £950,000+; approximately 176 sq m.
2. Lot 90A — 4 Bakers Lane development site; guide £875,000+; source-stated permission for two five-bedroom detached houses.
3. Lot 94 — 77 Discovery Walk; guide £650,000+. The heading says terraced while the description says end-of-terrace; the conflict is preserved.
4. Lot 87A — 54 Albacore Crescent; vacant six-bedroom semi-detached house; guide £600,000+.
5. Lot 81 — 153–155 Hamlet Court Road; vacant commercial building; guide £475,000+; source-stated permission for seven flats.
6. Lot 102 — Foelas Residential Home; fully let care home; source income £50,000 p.a.; not treated as vacant standard housing.

## Related-interest safeguards

- Lots 76 and 107 share 9A Battle Hill but represent a restaurant and a second-floor residential flat under separate leasehold interests.
- Lots 85 and 109 share 5 Cornmarket but represent the ground/lower retail unit and the first/second-floor flat under separate leasehold interests.
- These pairs are related records, not repository duplicates.

## Accuracy guards

- Current-auction listing snapshot is not an individual detail page.
- Guide price is not sale price and may change before auction.
- Vacant wording is used only where explicitly stated.
- Periodic, unknown, fully-let, part-let and commercial tenancies are not vacant possession.
- Commercial, mixed-use, office, industrial, retail, care-home, ground-rent and land records are not standard vacant residential dwellings.
- Room count is not bedroom count; planned bedrooms are not existing bedrooms.
- Plans drawn, permitted-development wording, potential and unimplemented planning claims are not completed dwellings.
- Planning claims remain subject to reference, conditions, commencement and implementation review.
- Source-internal property-type conflicts remain explicit and unnormalised.
- Approximate measurements remain approximate.
- Income, yield, tenancy, lease, title and unit configuration require legal-pack review.

## Cumulative staging

- Source rows: 1,321
- Checks: 2,648/2,648
- Active unique candidates: 1,289
- Source upgrades: 1,289
- Verified enrichments: 6,885
- Audited agreement before normalization: 10,180/10,215 = 99.66%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.30/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.