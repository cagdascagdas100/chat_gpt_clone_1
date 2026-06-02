# Estate021 Real Final Join Build

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

group_seed_file=E:\AAYS_DATA\estate_agents\england_parcel_groups_200_seed.csv
agent_group_join_rows=0
parcel_group_join_rows=0
readonly_final_files_created=False
REAL_100=false
REAL_COMPLETION_PERCENT=99

remaining_for_true_100:
- explicit DB import approval
- explicit production deploy approval
- final human acceptance of read-only generated CSVs

created_if_ready:
- estate_agent_verified_final_READONLY.csv
- estate_agent_evidence_sources_final_READONLY.csv
- estate_agent_coverage_groups_final_READONLY.csv
- terrayield_parcel_group_join_final_READONLY.csv
