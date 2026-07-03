# Distance Property Types - Applied Handoff

This repo path records the ChatGPT handoff package for the `Distance to Nearby Property Types` layer.

## Applied contract

- page_key: `distance_property_types`
- layer name: `Distance to Nearby Property Types`
- allowed primary property categories:
  - Industrial Unit
  - Detached Home
  - Retail Property
  - Apartment Building
  - Office Building
  - Mixed Building
- fallback for no evidence: `Unknown` with manual review and score below target
- target score: `accuracy_score_4 >= 3.0`
- latest-change filter: `changed_in_latest_run=true`

## Evidence order

1. Official/planning/registry/address-use source
2. Reliable web/business/listing/map record
3. Map/POI/building-label/location match
4. Photo/visual AI observation
5. Manual review note

## Safety state

No fake data, DB write, DDL, migration, or production deploy is authorized. If evidence is missing or conflicting, the row must remain in manual review.

## Current repo bootstrap

Created/queued:

- `docs/chatgpt_status/distance_property_types/queue/distance_property_types_bootstrap_20260703.task.json`
- `docs/chatgpt_status/distance_property_types/reports/distance_property_types_progress_latest.md`
- `docs/chatgpt_status/distance_property_types/reports/distance_property_types_manual_review_latest.csv`
- `england_map_web/data/distance_property_types/distance_property_types_verified.geojson`
- `england_map_web/data/distance_property_types/distance_property_types_verified.csv`
- `england_map_web/data/distance_property_types/distance_property_types_evidence_manifest.json`
- `docs/chatgpt_status/distance_property_types/site_integration/distance_property_types_site_requirements.md`
- `docs/chatgpt_status/distance_property_types/reports/distance_property_types_runner_notes.md`
- `docs/chatgpt_status/distance_property_types/handoff/01_DATA_CONTRACT_TR.md`
- `docs/chatgpt_status/distance_property_types/handoff/02_ACCURACY_SCALE_TR.md`
- `docs/chatgpt_status/distance_property_types/handoff/03_RUNNER_WORKFLOW_TR.md`
- `docs/chatgpt_status/distance_property_types/handoff/04_SITE_FILTER_REQUIREMENTS_TR.md`
- `docs/chatgpt_status/distance_property_types/handoff/05_MANUAL_REVIEW_RULES_TR.md`

Known blocked write from this ChatGPT environment:

- `docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1`

Reason: executable runner file creation through this ChatGPT GitHub write path was blocked. All non-executable bootstrap files were committed. The real runner file must be placed in the local F repo or created by Codex/runner before the single shared runner can execute the batch.
