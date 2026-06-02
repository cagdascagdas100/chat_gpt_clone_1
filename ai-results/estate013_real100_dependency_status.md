# Estate 013 Real 100 Dependency Status

Gerçek %100 için bağımlı zincir:
1. Review-priority candidate rows must be manually/source verified.
2. Verified rows create estate_agent_verified_final.csv.
3. Evidence rows create estate_agent_evidence_sources_final.csv.
4. Coverage mapping creates estate_agent_coverage_groups_final.csv.
5. Real parcel master creates terrayield_parcel_group_join_final.csv.
6. Only after 1-5, final Excel can be generated.

Bağımsız paralel işler:
- review candidate inspection
- parcel schema scan
- dependency report

DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false
