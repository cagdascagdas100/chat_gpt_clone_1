# ready_to_sell_2 — New Candidate Group 30 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue and accessible detail pages.
- 10 active records staged for Lots 63B–71.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party sources: 10/10
- Repository duplicate preflights: 10/10; matches: 0
- Checks: 20/20
- Source-supported fields: 80/80
- Verified enrichments: 96
- Average verification confidence: 97.9/100
- Validation: 10 PASS / 0 FAIL

## Fail-closed source conflicts

1. Lot 65 tenure: current catalogue says freehold; detail page says leasehold. Tenure retained as source conflict.
2. Lot 68 guide price: current catalogue says £220,000+; detail page says £250,000+. Price retained as source conflict.
3. Lot 69 guide/planning: current catalogue says £600,000+ and planning permission; detail page says £650,000+ and positive pre-application advice/subject-to-planning. Both fields retained as source conflicts.

## Highlights

1. 245 Royal College Street — three flats, £91,392 p.a.; planning ref 2010/6105/P is explicitly lapsed.
2. 54 Hendon Lane — offices plus two flats, fully let at £61,500 p.a.
3. Units 1–7, 14A Andre Street — seven offices, current rent £63,444.84 p.a., ERV about £73,500; tenure conflict unresolved.
4. 1 Wood Lane — shop plus four rooms, £89,900 p.a.; enforcement notice/appeal requires legal-pack review.
5. Unit 17 Tait Road — vacant 4,000 sq ft industrial unit with seven parking spaces and EPC C.
6. 61 High Street — vacant 1,830 sq ft multi-floor retail unit, EPC C; guide-price conflict unresolved.
7. 10–18 Jackson Road — five shops plus offices/warehouse, £20,400 p.a.; price and planning status conflict unresolved.
8. 18 Victoria Square — vacant commercial building; conversion/HMO items remain plans, not permission.
9. 35 Biggin Street — shop let at £15,000 p.a., vacant uppers, 15-year FRI lease, EPC B.
10. 1 Holtspur Parade — leasehold coffee-shop unit producing £10,000 p.a.; detail-page internal error preserved as catalogue fallback.

## Cumulative staging

- Source rows: 520
- Checks: 1,040/1,040
- New unique candidates: 490
- Source upgrades: 490
- Verified enrichments: 2,563
- Audited agreement before normalization: 4,098/4,120 = 99.47%
- Fail-closed normalized assertions: 100.00%
- Weighted average verification confidence: 99.4/100

## Readback

- Candidate JSON blob SHA: `0fe86edef9263fc6c16fe5aa592e7f33a936150a`
- Summary JSON blob SHA: `516613dbf5aeb90598bc428c893f8d18a918f3f3`
- Row HTML blob SHA: `1193838628bcae979ac96d8d4c23338288aa8dec`
- Validation blob SHA: `e485fe497175ffa8b8270fb3847b6db459ab50b0`
- Sealed report blob SHA: `df85a775717601d3fac1c627806feeda33ab5d87`

## Remaining blocker

Automation 167 remains queued for the existing single F-host runner. The canonical slot is unclaimed with a stale heartbeat, so port-8012 headless DOM proof and canonical candidate mutation remain blocked. No second runner or duplicate task was created.
