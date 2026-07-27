# ready_to_sell_2 — New Candidate Groups 33–35 (2026-07-27)

## Scope

- First-party source: Auction House London current 29–30 July 2026 catalogue and accessible detail pages.
- 30 active records staged from Lots 90A–106.
- 30 exact-address repository duplicate preflights returned zero matches.
- No canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 137
- Raw source agreement: 98.75%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.37/100
- Validation: 10 PASS / 0 FAIL

## High-value detail readbacks

1. Lot 90B — 383 sq m land; planning ref 24/0256/FUL granted 27 March 2024 for a three-bedroom, two-bathroom single-storey dwelling.
2. Lot 93 — 216 sq m land; planning ref 25/01937/FL granted 6 May 2026; six-week completion and vendor planning-cost addendum identified.
3. Lot 97 — nine flats sold on 125-year leases; £2,925 p.a. ground rent; planning refs 23/AP/2644 and 20/AP/1951; implementation claimed by source.
4. Lot 102 — 15-bedroom care home, 432 sq m / 4,650 sq ft, ten-year lease from 22 January 2026, £50,000 p.a.

## Fail-closed source differences

1. Lot 90A guide price: current catalogue £875,000+; earlier official page £950,000+.
2. Lot 93 guide price: current catalogue £30,000+; detail page £20,000+.
3. Lot 105 description: current open catalogue says third-floor studio; earlier official crawl says second-floor two-bedroom flat.
4. Lot 101 unit-mix wording is semantically redundant (`2 x One Bedroom, 1 x One Bedroom`) and is preserved verbatim rather than normalized.

## Cumulative staging

- Source rows: 570
- Checks: 1140/1140
- New unique candidates: 540
- Source upgrades: 540
- Verified enrichments: 2775
- Audited agreement before normalization: 4495/4520 = 99.45%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.4/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so port-8012 headless DOM proof and canonical promotion remain blocked. No second runner or duplicate task was created.
