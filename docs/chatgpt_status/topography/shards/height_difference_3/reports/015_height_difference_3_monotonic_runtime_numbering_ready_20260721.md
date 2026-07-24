# height_difference_3 — monotonic runtime numbering ready

- Slot: `height_difference_3`
- Parcel range: `61523-92283` (`30,761` rows)
- State: real existing-F-runner execution still pending
- Safety: no new runner, parallel runner, queue, lease, database write, migration or deployment

## Defect resolved

Website history already contained static operations `331-366`, while the existing task still instructed the real runtime to start at `331`. A real run would therefore have produced duplicate operation numbers.

`029_preflight_then_execute_resumable.py` now reads the committed slot operation history and allocates the preflight start as `max(operation_no)+1`. It rejects duplicate, stale, gapped, non-positive or cumulative-count-inconsistent histories. The `026` start is derived from the actual number and sequence of operations written by the preflight report instead of a hard-coded increment.

## Validation

- New tests: `15/15 PASS`
- Cumulative tests: `133/133 PASS`
- Bootstrap remote blob: `2c67aa7179f3fc8549200fb04a66f8363aeb2c24`
- Bootstrap SHA-256: `2066439c196e2a310c238d3e2d2545dbe6e7f6b60a96d93a97d7f23fca2f1eae`

## Official-source contract retained

The pipeline still requires current HMLR INSPIRE polygons, EA LIDAR Composite DTM 1m data in EPSG:27700 and exact OS Terrain 50 grid crosschecks. No measured value is published without all source and confidence gates.

## Real result state

- Canonical shard rows exported: `0/30,761`
- Real starter candidates: `0`
- HMLR matches: `0`
- EA DTM samples: `0`
- Terrain 50 samples: `0`
- Verified website examples: `0`

## Next unverified step

`RUN_029_MONOTONIC_PREFLIGHT_THEN_026_WITH_VALIDATOR_027_ON_EXISTING_F_RUNNER_THEN_VERIFY_PORT_8012`

`final_ready=false`
