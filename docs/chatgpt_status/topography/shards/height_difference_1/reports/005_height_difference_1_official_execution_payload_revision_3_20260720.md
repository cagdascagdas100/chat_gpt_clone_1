# height_difference_1 — Official execution payload revision 3

- SLOT_ID: `height_difference_1`
- Parcel partition: `1-30761`
- Task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Queue state observed before update: `pending`
- Slot state observed before update: `idle`
- Payload revision: `3`
- Generated: `2026-07-20T20:06:05Z`

## Official source checks added

1. HM Land Registry July 2026 INSPIRE release discovery from the official local-authority download page.
2. HM Land Registry WFS 1.1.0 50 metre BBOX retrieval and actual point-in-polygon testing.
3. GML response SHA-256, ring count and point-in-polygon match count persistence.
4. Environment Agency WCS capabilities parsing and coverage-ID discovery.
5. Environment Agency DTM sampling at 1 m, 2 m and 10 m using multiple WCS axis-name variants.
6. Environment Agency 5 km GeoTIFF delivery contract retained as an official archive fallback.
7. Ordnance Survey Terrain 50 direct download with a 120 MB safety budget, `TQ29` ASCII-grid selection and numeric cell sampling.

## Acceptance guard

A measured parcel row is accepted only when all of the following are present:

- a real HM Land Registry polygon containing the candidate point;
- a numeric Environment Agency 1 m DTM value;
- an independent numeric OS Terrain 50 value.

EA 2 m and 10 m values are same-provider resolution checks and are not counted as an independent second source.

## Current evidence state

- Candidate rows: `3`
- Real boundary matches accepted now: `0`
- Official numeric rows accepted now: `0`
- Two-source measured rows accepted now: `0`
- Accuracy remains: `2.5/4 fallback`
- Product completion remains: `78%`
- Output policy: `NO_DATA_NOT_INFERRED`

## Safety

- New runner: `false`
- Parallel runner: `false`
- Existing single coordinator only: `true`
- fake_data: `false`
- db_write: `false`
- migration: `false`
- production_deploy: `false`
- final_ready: `false`
