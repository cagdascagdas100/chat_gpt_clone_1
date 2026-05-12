# TY109 Provenance Gate and Final Preflight

Plan completed: 86%
Plan remaining: 14%
DB credentials present: False
Contractor rows: 317
Score rows: 317
Event rows: 421
App rows: 317
Parcel match rows: 29
Critical provenance missing count: 4

## Provenance Checks
- contractors_normalized.csv rows=317 has_cols=False missing_rows=317
- procurement_events_normalized.csv rows=421 has_cols=False missing_rows=0
- contractor_scores.csv rows=317 has_cols=False missing_rows=317
- contractor_app_export.csv rows=317 has_cols=False missing_rows=317
- contractor_parcel_matches.csv rows=29 has_cols=False missing_rows=29

## Copies
- contractors_normalized.csv copied=False source= reason=no candidate with all provenance columns found
- contractor_scores.csv copied=False source= reason=no candidate with all provenance columns found
- contractor_app_export.csv copied=False source= reason=no candidate with all provenance columns found
- contractor_parcel_matches.csv copied=False source= reason=no candidate with all provenance columns found

## Files
- E:\AAYS_DATA\legal\processed\contractors_normalized.csv exists=True bytes=33856
- E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv exists=True bytes=160217
- E:\AAYS_DATA\legal\processed\contractor_scores.csv exists=True bytes=21859
- E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv exists=True bytes=5688
- E:\AAYS_DATA\legal\exports\contractor_app_export.csv exists=True bytes=63729
- E:\AAYS_DATA\legal\exports\contractor_app_export.jsonl exists=True bytes=280330
- E:\AAYS_DATA\legal\reports\blocked_critical_provenance_missing.json exists=True bytes=3737
- E:\AAYS_DATA\legal\reports\blocked_by_missing_credential_postgres.json exists=True bytes=89
- E:\AAYS_DATA\legal\db_transfer\schema_apply.sql exists=True bytes=85
- E:\AAYS_DATA\legal\db_transfer\load_order.csv exists=True bytes=341
- E:\AAYS_DATA\legal\db_transfer\export_manifest.csv exists=True bytes=160

## Next Action
Find official-source CSV/JSONL with provenance; do not fabricate missing provenance.
