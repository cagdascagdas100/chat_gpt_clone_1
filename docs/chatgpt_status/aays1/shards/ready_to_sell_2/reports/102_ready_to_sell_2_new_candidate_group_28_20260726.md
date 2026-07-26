# ready_to_sell_2 — New Candidate Group 28 (2026-07-26)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue and detail pages.
- 30 active records staged in three 10-row evidence files.
- Lot 39 excluded as Sold Prior; Lots 55 and 56 excluded as Withdrawn.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party sources: 30/30
- Repository duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 130
- Average verification confidence: 99.5/100
- Validation: 10 PASS / 0 FAIL

## Semantic guards

- Detail-page cache misses fall back only to the accessible first-party current catalogue.
- Sold Prior and Withdrawn states are excluded.
- Periodic tenancy, notice served and guaranteed-rent agreements are not treated as vacant-possession proof.
- Planning permission is distinct from development potential subject to consents.
- Three/four-bedroom wording remains ambiguous rather than guessed.
- Lease terms and rent payment remain pending where not stated or independently verified.

## Highlights

1. 198 Weston Lane — four-bedroom detached refurbishment/redevelopment opportunity; redevelopment remains subject to consents.
2. 82 Sussex Way — freehold block of three flats, offered with vacant possession.
3. Land Adjacent to The Gables — 1.32-acre site with permission for eight detached homes.
4. Flat 1, 33 Windsor Road — two studio flats, one let and one vacant, £3,510 p.a.; approximately 122 years unexpired.
5. 6A Cable Street — one-bedroom flat producing £21,000 p.a.; notice served, but not treated as vacant.
6. 97 Caledon Road — four-bedroom house with £26,400 p.a. guaranteed-rent agreement; agreement is not occupancy proof.
7. 162 Crockhamwell Road — two-bedroom maisonette on periodic tenancy producing £12,300 p.a.
8. Flat 83 Peverel House — fifteenth-floor one-bedroom flat producing £16,200 p.a.
9. 303 Wightman Road — five-bedroom semi-detached house with vacant possession.
10. Flat 3, 393 Archway Road — first-floor three/four-bedroom flat; bedroom count retained as ambiguous.

## Cumulative staging

- Source rows: 500
- Checks: 1,000/1,000
- New unique candidates: 470
- Source upgrades: 470
- Verified enrichments: 2,413
- Audited agreement before staged corrections: 3,941/3,960 = 99.52%
- Audited agreement after staged corrections: 3,960/3,960 = 100.00%
- Weighted average verification confidence: 99.4/100
- Web loader target: 51 evidence files / 500 rows

## Remaining blocker

Automation 167 remains queued for the existing single F-host runner. The canonical slot is unclaimed with a stale heartbeat, so port-8012 headless DOM proof and canonical candidate mutation remain blocked. No second runner or duplicate task was created.
