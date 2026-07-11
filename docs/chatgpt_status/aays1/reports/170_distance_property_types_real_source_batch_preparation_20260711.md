# Batch 170 — Distance Property Types real-source preparation

- Batch rows: 12
- Categories: 2 Retail, 2 Mixed, 2 Detached, 2 Apartment, 2 Office, 2 Industrial
- Initial average accuracy: 3.642 / 4
- Primary source web-verified rows: 4
- Primary-domain/owner rows requiring canonical-runner remote readback: 8
- Geometry: NOT_BOUND for all rows
- Candidate state: pending, not completed
- Existing executable orchestrator: Task 169
- Expected tracked-row target after Task 169 deduplication: up to 182

The batch deliberately does not assert coordinates, parcel polygons, completed status, browser proof, or final readiness. The canonical F portable single runner must probe URLs, deduplicate parcel IDs, bind or reject geometry, merge rows into the website all-rows artifact, and write HTTP/browser evidence.

Safety: `single_runner_only=true`, `new_runner=false`, `parallel_runner=false`, `fake_data=false`, `final_ready=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
