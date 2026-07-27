# ready_to_sell_2 — New Candidate Groups 59–61 (2026-07-27)

## Scope

- First-party sources: iamsold national pages 1–2, iamsold Northern Ireland buying page and William H Brown/iamiamsold partner page.
- 30 active records staged: 6 `Live now`, 21 `Pre-auction Marketing` and 3 `Online Auction`.
- The duplicate Skinner Street card exposed on national pages 1 and 2 was included only once.
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
- Average verification confidence: 99.00/100
- Validation: 10 PASS / 0 FAIL

## High-value source rows

1. Darenth Hill — freehold nine-bedroom detached listing; starting bid £1,650,000.
2. Sudeley Street — freehold three-bedroom terraced listing; starting bid £1,550,000.
3. Skinner Street — freehold 18-bedroom block-of-apartments listing; starting bid £1,450,000.
4. Bath Road — source card says seven-bedroom development land; planning permission is not inferred.
5. Killygullan — source wording says Development Site X6 Houses; planning status, parcel boundaries and approvals remain unverified.
6. Chelsea Harbour and Portland Square remain leasehold as stated by their source cards.
7. Dagdale preserves the source tenure `Unregistered (freehold)` rather than normalising it to registered freehold.

## Accuracy guards

- Starting bids are not sale prices, valuations or expected proceeds.
- Status counters are preserved as raw labels; their unit and countdown semantics are not inferred.
- Occupancy, rent, planning, condition, floor area and legal-pack attributes are not inferred from listing cards.
- Generic source type `property` remains generic.
- `Tenure To Be Confirmed` remains unresolved and is not converted to freehold or leasehold.
- Development wording is not treated as planning permission.
- Every row is marked `listing_snapshot_only`; dynamic pages may rotate later, while the 2026-07-27 snapshot is preserved in repository data.

## Cumulative staging

- Source rows: 800
- Checks: 1,600/1,600
- New unique candidates: 770
- Source upgrades: 770
- Verified enrichments: 3,850
- Audited agreement before normalization: 6,328/6,360 = 99.50%
- Fail-closed normalized assertions: 100.00%
- Weighted average confidence: 99.37/100

## Remaining blocker

Automation 167 remains queued for the existing single shared runner. Canonical heartbeat is unclaimed/stale and current task is idle, so real port-8012 headless DOM proof and canonical promotion remain blocked. The existing manual action remains OPEN. No second runner or duplicate task was created.