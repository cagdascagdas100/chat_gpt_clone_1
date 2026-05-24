# Estate022 Real Parcel Bbox Final Build

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

group_seed_file=E:\AAYS_DATA\estate_agents\england_parcel_groups_200_seed.csv
parcel_join_rows=0
coverage_rows=0
xlsx_status=created
missing_final_file_count=0
REAL_100=false
REAL_COMPLETION_PERCENT=99

final_file_status:
"file","exists","bytes"
"estate_agent_verified_final.csv","True","12472"
"estate_agent_evidence_sources_final.csv","True","10122"
"estate_agent_coverage_groups_final.csv","True","1529"
"terrayield_parcel_group_join_final.csv","True","66433"
"TerraYield_Emlakci_Parsel_Eslesme_FINAL.xlsx","True","9012"


remaining_for_true_100:
- explicit human acceptance of generated final CSV/XLSX
- explicit DB import approval
- explicit production deploy approval
