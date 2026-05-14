# AAYS/TerraYield Contractor Pipeline Final Local Status

Plan completed: 95%
Plan remaining: 5%

Completed:
- PostgreSQL/PostGIS DB load completed.
- Loaded companies: 317
- Loaded procurement/projects: 421
- Loaded evidence rows: 4536
- Contractor normalized rows: 317
- Procurement event rows: 421
- Contractor score rows: 317
- Existing parcel match rows in export: 29
- App export rows: 317
- DO_NOT_CONTACT count: 54
- Critical provenance missing count: 0
- Fake data: not used
- Missing evidence remained null until mapped from official provenance evidence.
- DO_NOT_CONTACT gate preserved: legal_contact_score < 50 or do_not_contact=true.
- SQL + CSV transfer files present under E:\AAYS_DATA\legal\db_transfer

Current block:
- Fresh parcel matching failed closed.
- Block report: E:\AAYS_DATA\contractor\raw\status\blocked_by_missing_input_parcel_match.json
- Reason: parcel match input/table/config is missing or not visible to the runner.

Final status:
- DB load and app export are complete.
- Pipeline is operationally complete except fresh parcel match regeneration.
- Current completion: 95%.
