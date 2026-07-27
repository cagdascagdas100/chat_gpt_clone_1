# ready_to_sell_2 — New Candidate Groups 36–38 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue.
- 30 active records staged from Lots 107–130A.
- Lot 129 was excluded because the current first-party catalogue marks it Sold Prior.
- 30 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 110
- Raw cross-snapshot agreement: 99.17%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.6/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Lot 116A — 241 sq m / 2,597 sq ft freehold land; no planning permission inferred.
2. Lot 120A — two vacant terraced buildings arranged as seventeen flats; unit mix and legality remain unverified.
3. Lot 121 — vacant three-bedroom detached house on 1,208 sq m / 12,998 sq ft with outline planning source claim for four dwellings.
4. Lot 124 — 700 sq m / 7,534 sq ft land with permission-in-principle source claim for nine flats.
5. Lot 113 — two-bedroom flat producing £16,800 p.a.; source notice-served wording is preserved but legal validity remains pending.
6. Lot 125 — two-bedroom flat producing £17,232 p.a.; no internal viewing.

## Accuracy guards

- Lot 118 guide price changed from an earlier official £110,000+ snapshot to the current £100,000–£160,000 catalogue range.
- Lot 121 guide price changed from an earlier official £60,000+ snapshot to the current £60,000–£110,000 catalogue range.
- Current catalogue values control; earlier official values are retained as change evidence, not combined.
- Outline permission and permission in principle are not treated as full detailed planning permission.
- Development potential is not treated as planning permission.
- Periodic tenancy, notice-served and no-internal-viewing records are not treated as vacant.
- Detail-link internal errors fall back to current catalogue evidence; no missing fields are invented.

## Cumulative staging

- Source rows: 600
- Checks: 1,200/1,200
- New unique candidates: 570
- Source upgrades: 570
- Verified enrichments: 2,885
- Audited agreement before normalization: 4,733/4,760 = 99.43%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.4/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so port-8012 headless DOM proof and canonical promotion remain blocked. No second runner or duplicate task was created.
