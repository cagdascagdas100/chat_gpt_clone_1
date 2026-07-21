# ReadyToSell 2 — Wave 15 path and duplicate repair

- Slot: `ready_to_sell_2`
- Parcel range: `30762-61522`
- Final ready: `false`
- Single runner only: `true`

## Direct blocker repair

The slot-local `current_task_latest.json` incorrectly referenced `_shared/slots_18` and `aays_18_slots`. Sibling slots `ready_to_sell_1` and `ready_to_sell_3` use `_shared/slots_21` and `aays_21_slots`. Only the `ready_to_sell_2` allowed paths were corrected. The task remains idle and no runner or duplicate task was created.

## Duplicate correction

Wave 14 incorrectly counted three records already present in `candidate_examples_latest.json`:

- 2 Church Street — planning reference `2025/1384`
- St Andrew's Road, Plaistow — planning reference `24/02474/FUL`
- Romney Avenue, Folkestone — planning reference `Y19/0925/FH`

The three rows were removed from new-candidate counts and converted to source upgrades on the existing canonical candidate rows. Corrected pre-wave-15 unique count: `55`.

## Wave 15

Six unique official-auction candidates were added:

1. The Old Woodyard, Fordwich — planning/certificate reference conflict preserved.
2. Higher Grange Cottage land, Pelynt — full dwelling permission stated.
3. Land adjacent to Aucuba, Kelly Bray — outline permission, all matters reserved, contamination warning.
4. Rear of 51 High Street, Cosham — three-flat permission with implementation/CIL claims pending independent readback.
5. Land rear of 30 Rock Close, Coventry — unsold/make-offer with implemented/extant claim pending council evidence.
6. Land at 18 Hurst Road, Coventry — previous approval recorded but current validity not inferred.

## Canonical metrics

- Unique researched candidates: `61`
- New unique candidates: `6`
- Duplicate candidates removed this turn: `3`
- Latest source upgrades: `2`
- Cumulative source-upgrade rows: `11`
- High-source-confidence candidates: `61`
- Current/upcoming/available: `59`
- Promoted rows: `0`
- Latest-batch confidence: `98.33/100`
- Aggregate confidence: `98.47/100`
- Completed operations: `92/93`
- Batch progress: `98.92%` (`+0.17` points)
- Overall evidence progress: `99.07%` (`+0.13` points)

## Remaining blocker

`AUTOMATION_167_DOM_PROOF` remains unverified. The existing canonical shared runner must pick up the same task and produce real port-8012 headless-browser DOM, commit, push and remote readback evidence. `final_ready=false` remains unchanged.
