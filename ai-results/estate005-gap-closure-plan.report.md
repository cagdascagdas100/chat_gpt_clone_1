# Estate Agent Missing Work Closure Plan 005

Generated: 2026-05-23T22:49:59

## Current truth
Technical runner finalization is complete, but the user-requested estate-agent parcel product is not complete.
DB write: false
Production deploy: false
Fake data: false

## Existing file checks
- parcel_groups: False :: E:\AAYS_DATA\estate_agents\england_parcel_groups_200_seed.csv
- agent_schema: False :: E:\AAYS_DATA\estate_agents\estate_agent_directory_seed_schema.csv
- source_plan: False :: E:\AAYS_DATA\estate_agents\estate_agent_source_acquisition_plan_002.json
- scoring_rules: False :: E:\AAYS_DATA\estate_agents\estate_agent_coverage_scoring_rules_002.md
- artifact_inventory: False :: E:\AAYS_DATA\estate_agents\estate_existing_artifact_inventory_002.csv
- candidates: True :: E:\AAYS_DATA\estate_agents\estate_agent_candidates_from_local_artifacts_003.csv
- excel_seed: False :: E:\AAYS_DATA\estate_agents\TerraYield_Emlakci_Parsel_Eslesme_Plan.xlsx

## Missing work to continue
1. Build verified estate-agent rows from legal/open/user-provided sources.
2. Verify every contact field and attach source_url/evidence_summary.
3. Score every fact on 0-4 truth scale.
4. Score each agent on 0-10 trust scale.
5. Map each branch to one or more ENG-PG-001..ENG-PG-200 parcel groups.
6. Find the real TerraYield parcel table/export and map parcel_id to parcel_group_id.
7. Add application lookup: clicked parcel -> parcel_group -> matching agents only -> sorted by score.
8. Generate final Excel/CSV from verified rows only.

## Next Codex tasks
- Implement dry-run import models and API/service skeleton.
- Produce missing-data report if verified agent source data is absent.
- Do not insert DB records until user approves.

PLAN_PROGRESS_PERCENT=40
TASK_COMPLETION=100/100
TERRAYIELD_TASK_DONE
