# height_difference_1 — Buffered official execution upgrade

- SLOT_ID: `height_difference_1`
- Parcel partition: `1-30761`
- Task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Payload revision: `2`
- Queue state read before upgrade: `pending`
- Slot current task read before upgrade: `idle`

## Completed in this continuation

1. Preserved the existing single-coordinator queue task; no new or parallel runner was created.
2. Added HMLR WFS 1.1.0 BBOX retrieval to obtain actual cadastral polygon coordinates.
3. Added point-in-polygon validation at each existing candidate coordinate.
4. Added a 3 × 3 HMLR WMS GetFeatureInfo grid spanning ±15 metres to cover the transformation tolerance documented by HMLR.
5. Added EA LiDAR DTM 1 m and 2 m WCS capabilities discovery and multi-axis GetCoverage attempts.
6. Added the current OS Downloads API endpoint for OS Terrain 50 ASCII Grid.
7. Bound the three candidates to OS Terrain 50 10 km tile `TQ29` and added direct ASCII-grid sampling.
8. Kept acceptance gated on real HMLR geometry plus EA numeric elevation plus independent OS Terrain 50 numeric evidence.

## Candidate scope

- `parcel_2759` / `52040420`
- `parcel_2758` / `52213916`
- `parcel_2757` / `52213412`

## Current evidence state

- Real HMLR boundary matches accepted: `0`
- EA LiDAR official numeric rows accepted: `0`
- Independent OS Terrain 50 numeric rows accepted: `0`
- Two-source measured rows accepted: `0`
- Current accuracy: `2.5/4 fallback`
- Output semantics: `NO_DATA_NOT_INFERRED`

The payload is executable only by the existing F portable single coordinator. Remote source metadata and query contracts are prepared, but the remote queue remains pending and no coordinator-produced result has been read back yet.

## Next verified step

`OBSERVE_SINGLE_COORDINATOR_PAYLOAD_REVISION_2_RESULT_THEN_ACCEPT_ONLY_REAL_HMLR_PLUS_EA_PLUS_OS_ROWS`

## Safety

- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
