# Estate025 Promote Geometry Parse Final

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false

join_candidate=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\estate022_geometry_parcel_group_join_candidate.csv
coverage_candidate=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\estate022_coverage_groups_candidate.csv
strict_join_rows=4
strict_coverage_rows=12
xlsx_status=present
missing_final_file_count=0
READONLY_FINAL_100=True
PRODUCTION_100=false
REAL_COMPLETION_PERCENT=100

final_file_status:
"file","exists","bytes"
"estate_agent_verified_final.csv","True","12472"
"estate_agent_evidence_sources_final.csv","True","10122"
"estate_agent_coverage_groups_final.csv","True","4458"
"terrayield_parcel_group_join_final.csv","True","1392"
"TerraYield_Emlakci_Parsel_Eslesme_FINAL.xlsx","True","55399"


remaining_for_production_100:
- explicit human acceptance
- explicit DB import approval
- explicit production deploy approval
