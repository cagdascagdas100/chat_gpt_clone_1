# AAYS1 TerraYield Contractor Final State

Generated at: 2026-05-11T23:08:08
Status: completed
Plan completed: 38%
Plan remaining: 62%

## Key Counters
- Script files present: 6
- DB transfer files present: 0
- Procurement raw files present: 0
- Companies House raw present: False
- Compile exit code: 0
- Contractor score rows: 0
- App export rows: 0
- Parcel match rows: 0
- DB credentials present: False

## Next Action
DB credentials are not visible to this runner. Set DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD, then run DB load and parcel match.

## File Checks
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_companies_house.py exists=True bytes=14112
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_collect_procurement_ocds.py exists=True bytes=18162
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_normalize_and_score.py exists=True bytes=22555
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py exists=True bytes=9284
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py exists=True bytes=14684
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py exists=True bytes=4301
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\requirements_contractor.txt exists=True bytes=78
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\README_CONTRACTOR_PIPELINE.md exists=True bytes=3791
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\schema_apply.sql exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\load_order.csv exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\export_manifest.csv exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\runbook_windows_linux.txt exists=False bytes=0
- E:\AAYS_DATA\legal\raw\companies_house\company_profiles.jsonl exists=False bytes=0
- E:\AAYS_DATA\legal\raw\procurement\contracts_finder_ocds.jsonl exists=False bytes=0
- E:\AAYS_DATA\legal\raw\procurement\find_tender_ocds.jsonl exists=False bytes=0
- E:\AAYS_DATA\legal\processed\contractors_normalized.csv exists=False bytes=0
- E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv exists=False bytes=0
- E:\AAYS_DATA\legal\processed\contractor_scores.csv exists=False bytes=0
- E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv exists=False bytes=0
- E:\AAYS_DATA\legal\exports\contractor_app_export.csv exists=False bytes=0
- E:\AAYS_DATA\legal\exports\contractor_app_export.jsonl exists=False bytes=0
