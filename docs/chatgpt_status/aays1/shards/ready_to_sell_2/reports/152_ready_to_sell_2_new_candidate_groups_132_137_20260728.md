# ready_to_sell_2 — New Candidate Groups 132–137 (2026-07-28)

## Scope

- First-party sources: Auction House London 29–30 July 2026 current-auction tail and 12 August 2026 future-auction listing.
- 56 active records staged: current Lots 218, 218A, 219, 219A, 220, 220A, 221, 222 and 223; future-auction Lots 1–36 and 38–45 including A/B sublots.
- Current Lots 224–242 were excluded as Sold Prior; future Lot 37 was excluded as Sold Prior.
- 56 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 56/56
- Duplicate preflights: 56/56; matches: 0
- Checks: 112/112
- Source-supported fields: 392/392
- Matched before fail-closed normalization: 392/392 = 100.00%
- Verified enrichments: 336
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.01/100
- Validation: 14 PASS / 0 FAIL

## High-value and semantics-sensitive rows

1. Future Lot 12 — 38 & 38A Rectory Road; fully let eight-bedroom HMO; guide £600,000+; source income £96,000 p.a.
2. Future Lot 16 — 50 Hodder Drive; fully let six-bedroom HMO; guide £570,000+; source income £75,000 p.a.
3. Future Lot 17 — 5 Perimeade Road; part-let six-bedroom HMO; guide £550,000+; source income £72,000 p.a.
4. Future Lot 22 — 396 Forest Road; source-stated permission for a one-bedroom ground-floor conversion and separate two-bedroom potential remain distinct.
5. Future Lot 25 — Former School, Lea Road; source-stated permission for 28 flats and works commenced; implementation and lawful commencement remain subject to legal verification.
6. Current Lots 218–223 — land, garage, parking and roadway interests; none is treated as an existing residential dwelling.

## Accuracy guards

- Listing snapshots are not individual lot detail pages.
- Guide price is not sale price and may change.
- Vacant wording is used only where explicitly stated.
- Occupancy is not inferred when unstated.
- Fully let, part-let, periodic-tenancy and commercial-let records are not vacant possession.
- Sold-off leasehold interests do not make the whole freehold vacant.
- Room count is not bedroom count.
- Freehold-flat source labels remain unnormalised pending title review.
- Land, roadway, garage, parking, commercial, former-school and mixed-use records are not existing standard dwellings.
- Plans, potential and applications are not planning permission.
- Source-stated planning permission still requires conditions, implementation and legal-pack review.
- Planned units are not existing units.
- Retirement restrictions, HMO licensing, leases, titles, tenancies and income require legal-pack review.
- Approximate measurements remain approximate.

## Cumulative staging

- Source rows: 1,497
- Checks: 3,003/3,003
- Active unique candidates: 1,465
- Source upgrades: 1,465
- Verified enrichments: 7,941
- Audited agreement before normalization: 11,410/11,447 = 99.68%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.26/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
