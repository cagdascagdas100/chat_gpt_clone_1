# Parcel Label Recovery and Candidate Preparation — 2026-07-15

## Remote recovery

- Expired shared claim task: `aays1-ready-to-sell-eight-wave-continuation-20260713`
- Queue state changed to: `failed_recoverable`
- Shared active claim changed to: `failed_recoverable`
- Release reason: `STALE_CLAIM_REMOTE_HEARTBEAT_EXPIRED`
- Queue recovery commit: `d08dae9474225c95cb126c27fe57e4e993aceefb`
- Claim recovery commit: `851ac6ffdf3a95a27502f50dfd7042fc5c30c928`

A newer queue-refresh signal from the Gas Emissions page was detected and preserved instead of overwritten. That signal already records the expired AAYS1 claim and instructs the existing single runner to revalidate and release it.

## Parcel Label evidence retained

- Task 174 browser visibility proof: 194 rendered rows; do not repeat.
- Task 205: 53-row source classification publish, `done`, `PUSH_SYNC_OK=true`.
- Task 206: 53-row runtime visibility recovery, `done`, `PUSH_SYNC_OK=true`.
- Global Parcel Label completion remains `NOT_PROVEN`.
- `final_ready=false`.

## Prepared official-source examples

Artifact: `docs/chatgpt_status/aays1/inputs/parcel_label_official_source_candidate_examples_20260715.json`

| Candidate | Proposed class | Classification score | Geometry | Publication |
|---|---:|---:|---|---|
| Westfield London | Retail Property | 3.95 / 4 | NOT_BOUND | PREPARED_NOT_PUBLISHED |
| The News Building | Office Building | 3.85 / 4 | NOT_BOUND | PREPARED_NOT_PUBLISHED |
| The Shard | Mixed Building | 3.95 / 4 | NOT_BOUND | PREPARED_NOT_PUBLISHED |

Average classification score: `3.9167 / 4` (`97.92%` of the scoring scale). This is classification confidence only; it is not parcel-bound geometry accuracy.

Official sources checked:

- Westfield London operator page and published Ariel Way address.
- News UK official 1 London Bridge Street address.
- The Shard official mixed-use description and Shard Quarter identity for The News Building.
- HM Land Registry INSPIRE Index Polygons guidance for indicative freehold-property extent.

## Current blockers

1. Fresh heartbeat from the existing F portable shared runner has not yet been published.
2. A new current-task checkpoint after queue refresh has not yet been published.
3. The three prepared candidates still require exact footprint/parcel binding and manual geometry review.
4. HTTP and browser visibility have not been proved for this new candidate batch.

## Safety

- `single_runner_only=true`
- `new_runner=false`
- `parallel_runner=false`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
