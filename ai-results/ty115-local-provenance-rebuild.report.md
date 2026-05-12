# TY115 Local Provenance Rebuild

Plan completed: 88%
Plan remaining: 12%
DB credentials present: False
Critical provenance missing count: 4

## Actions
- rebuilt contractor_app_export.csv/jsonl from provenance-bearing contractors + scores
- filled parcel match provenance from matching contractor_id rows only

## Checks
- E:\AAYS_DATA\legal\processed\contractors_normalized.csv rows=317 has_provenance=True missing_rows=317
- E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv rows=421 has_provenance=True missing_rows=0
- E:\AAYS_DATA\legal\processed\contractor_scores.csv rows=317 has_provenance=True missing_rows=317
- E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv rows=29 has_provenance=True missing_rows=29
- E:\AAYS_DATA\legal\exports\contractor_app_export.csv rows=317 has_provenance=True missing_rows=317