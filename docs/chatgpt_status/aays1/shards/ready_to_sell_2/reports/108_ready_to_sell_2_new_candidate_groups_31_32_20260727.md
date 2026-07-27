# ready_to_sell_2 — New Candidate Groups 31–32 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue and accessible detail pages.
- 20 active records staged from Lots 72–90.
- Lots 75A, 77, 79A, 83, 84 and 85A were excluded because the current first-party catalogue marks them Sold Prior or Postponed.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party sources: 20/20
- Repository duplicate preflights: 20/20; matches: 0
- Checks: 40/40
- Source-supported fields: 160/160
- Verified enrichments: 75
- Average verification confidence: 99.35/100
- Validation: 10 PASS / 0 FAIL

## Group 31 highlights

1. The Plough, Catcliffe — three retail units and five flats sold on 999-year leases; £36,540 p.a.; 1,194 sq m plot and circa 12 parking spaces.
2. Unit 3 Hampstead Gate — freehold three-storey office, 176 sq m / 1,894 sq ft, vacant possession.
3. 18 Northgate — Holland & Barrett retail/ancillary unit producing £39,000 p.a.; second floor sold on a long lease.
4. 9A Battle Hill — leasehold restaurant producing £13,500 p.a.; source gross yield 15%.
5. 153–155 Hamlet Court Road — vacant corner commercial building with permission to convert upper floors into seven flats.

## Group 32 highlights

1. 2–4 Chapel Street — vacant former social club/restaurant with renewed permission for five commercial units and six flats.
2. 5 Cornmarket — leasehold retail unit producing £8,500 p.a.; source gross yield 10.6%.
3. 8 Red Street — Boots Opticians retail building producing £34,000 p.a.
4. 13 Vanguard Avenue — four-bedroom detached house with occupancy explicitly unknown; not treated as vacant.
5. 54 Albacore Crescent — six-bedroom semi-detached house offered with vacant possession.
6. Flat B and Flat D, 28 Hibernia Road — separate vacant one- and two-bedroom leasehold flats.

## Accuracy guards

- Catalogue-only rows are identified when individual detail-page readback was unavailable; no detail fields were invented.
- Unknown occupancy is retained as unknown and is not treated as vacant possession.
- Development potential subject to consent is not treated as planning permission.
- Planning permission remains subject to reference, conditions and expiry readback before promotion.
- Flats sold off on long leases are not counted as current rental income.
- Rent and tenancy payments remain pending legal-pack verification.

## Cumulative staging

- Source rows: 540
- Checks: 1,080/1,080
- New unique candidates: 510
- Source upgrades: 510
- Verified enrichments: 2,638
- Audited agreement before correction/fail-closed normalization: 4,258/4,280 = 99.49%
- Corrected or fail-closed assertions: 100.00%
- Weighted average verification confidence: 99.4/100

## Publication readback

- Candidate JSON commit: `6a9b81a7c66f53e79bba62e1421cfc915b694ffc`
- Row-by-row HTML commit: `97635974f66141bdf6acd792281b7f277eae78dc`
- Report commit: `e0e133e739dcce4cce9560bd0ece5c8fec41b71c`
- Validation commit: `3528f965cfab1501d33c33f2c6fa3cc8b8757b9e`
- Sealed report commit: `ac7249ab17aeefef2e2d3e2c51555b148336a0ae`
- Remote JSON, HTML and validation readback passed.

## Remaining blocker

Automation 167 remains queued for the existing single F-host runner. The canonical slot is unclaimed with a stale heartbeat, so port-8012 headless DOM proof and canonical candidate mutation remain blocked. No second runner or duplicate task was created.
