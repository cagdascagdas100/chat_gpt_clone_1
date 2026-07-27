# ready_to_sell_2 — New Candidate Groups 56–58 (2026-07-27)

## Scope

- First-party source: iamsold active national, latest-property, homepage and buying-guide listing snapshots.
- 30 active records staged: 7 `Live now` and 23 `Pre-auction Marketing`.
- 30 exact-address/title repository duplicate preflights returned zero matches.
- No sold/withdrawn record, canonical business-row mutation, parcel promotion, second task, or second runner.

## Validation totals

- First-party source rows: 30/30
- Duplicate preflights: 30/30; matches: 0
- Checks: 60/60
- Source-supported fields: 240/240
- Verified enrichments: 180
- Raw listing agreement: 100.00%
- Fail-closed normalized assertions: 100.00%
- Average verification confidence: 99.03/100
- Validation: 10 PASS / 0 FAIL

## Accuracy guards

- Starting bids are not sale prices or valuations.
- Status counters are preserved as raw labels; their unit is not inferred.
- Occupancy, planning, floor area, rent and condition are not inferred from listing cards.
- Generic source type `property` remains generic.
- Detail pages were not read; every row is explicitly marked `listing_snapshot_only`.
- Rotating listing pages may show different records later; the 2026-07-27 snapshot is preserved in repository data.

## Cumulative staging

- Source rows: 770
- Checks: 1,540/1,540
- New unique candidates: 740
- Source upgrades: 740
- Verified enrichments: 3,670
- Audited agreement before normalization: 6,088/6,120 = 99.48%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.38/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.
