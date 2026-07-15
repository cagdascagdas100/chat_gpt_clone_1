# Task 165 — Official LiDAR / OS Terrain / HMLR boundary validation

- Task: `aays1-165-topography-official-lidar-boundary-validation-20260713`
- Batch: `topography-165-20260715154536775269`
- Stages: `14/14`
- Candidate parcels: `3`
- Official sources reachable: `3/4`
- EA LiDAR sample rows: `0`
- OS Terrain sample rows: `0`
- HMLR boundary matches: `0`
- Website operation rows: `38`
- Site HTTP validation: `PASS`
- Completion: `78%` (`+0`)
- Accuracy: `2.5/4 fallback`
- Blockers: `real_parcel_boundary_required; ea_lidar_or_os_terrain_numeric_validation_required; second_official_numeric_source_required_for_two_source_validation`
- `final_ready=false`
- `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`

All numeric and geometry promotion decisions are based on real local files acquired from or attributable to official public sources. Missing evidence remains a blocker and is not synthesized.
