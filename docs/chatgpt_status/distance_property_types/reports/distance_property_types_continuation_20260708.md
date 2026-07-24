# Distance Property Types continuation

page_key=distance_property_types
layer_name=Distance to Nearby Property Types
checked_at=2026-07-07T23:47:13Z
status=blocked_waiting_real_evidence_rows
final_ready=false
product_final_ready=false

Applied in this continuation:

- Added validation runner script at docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1
- Queued task at docs/chatgpt_status/distance_property_types/queue/distance_property_types_real_evidence_rows_20260708.task.json

Current proof from the previous runner output:

- evidence_rows=0
- verified_csv_rows=0
- completion_percent=35
- remaining_percent=65
- blocker=missing_real_evidence_rows

Current site state:

- distance_property_types_verified.csv is header only.
- distance_property_types_verified.geojson has no features.

Next action:

The source candidate CSV must be populated with real parcel-level evidence before progress can increase. Wait for the stable shared runner to process the queued task.
