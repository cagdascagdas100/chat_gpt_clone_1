# TerraYield Contractor DB Export Preflight

Status: completed_preflight
Generated at: 

Plan completed: 52%
Plan remaining: 48%

Database credentials present: False

## Command Checks
- COMPILE_LOAD_MATCH_EXPORT: exit=0
- APP_EXPORT_SMOKE: exit=1

## File Checks
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\schema_apply.sql exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\load_order.csv exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\db_transfer\export_manifest.csv exists=False bytes=0
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_load_to_postgres.py exists=True bytes=9284
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_match_to_parcels.py exists=True bytes=14684
- C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts\contractor_export_for_app.py exists=True bytes=4301
- E:\AAYS_DATA\legal\processed\contractors_normalized.csv exists=False bytes=0
- E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv exists=False bytes=0
- E:\AAYS_DATA\legal\processed\contractor_scores.csv exists=False bytes=0
- E:\AAYS_DATA\legal\exports\contractor_app_export.csv exists=False bytes=0
- E:\AAYS_DATA\legal\exports\contractor_app_export.jsonl exists=False bytes=0
- E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv exists=False bytes=0
- E:\AAYS_DATA\legal\reports\blocked_by_missing_credential_postgres.json exists=False bytes=0

## Recommended Next Step
