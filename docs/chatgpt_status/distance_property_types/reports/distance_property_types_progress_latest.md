# Distance Property Types runner progress

page_key=distance_property_types
layer_name=Distance to Nearby Property Types
status=queued_waiting_single_runner
final_ready=false
product_final_ready=false
evidence_rows=0
verified_csv_rows=0
input_rows=0
completion_percent=35
remaining_percent=65
blockers=missing_real_evidence_rows;source_candidate_csv_is_header_only;site_integration_not_verified_with_real_features

## Queue

pending_task=docs/chatgpt_status/distance_property_types/queue/distance_property_types_real_evidence_rows_20260708.task.json
script_path=docs/chatgpt_status/distance_property_types/automation/distance_property_types_batch_runner.ps1
input_path=docs/chatgpt_status/distance_property_types/inputs/distance_property_types_source_candidates.csv

## Current site data

verified_csv=header_only
verified_geojson=empty_feature_collection

## Next action

Single runner should pick up the pending task. If the input CSV remains header-only, the result must stay blocked with missing_real_evidence_rows.
