# AAYS 097 Risk Preview V2
Generated: 2026-05-15T02:52:49
TaskId: aays-097-risk-preview-v2-20260515
SourceCsv: E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv
OutCsv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-097-risk-preview-v2-20260515_025249.csv
Mode: read-only calibrated preview; source CSV is not overwritten.
source_rows: 120
preview_rows: 120

## risk_label_v2 distribution
critical: 99
high: 21

## acceptance_status_strict distribution
manual_review: 120

## policy_reason_v2 top distribution
no_verified_polygon;area_above_25000;price_above_3000000;ppm_above_5000;ai_visual_candidate: 39
no_verified_polygon;ppm_above_5000;ai_visual_candidate: 26
no_verified_polygon;area_above_25000;ppm_above_5000;ai_visual_candidate: 21
no_verified_polygon;area_above_25000;ppm_above_5000;signal_candidate: 13
no_verified_polygon;price_above_3000000;ppm_above_5000;ai_visual_candidate: 13
no_verified_polygon;area_above_25000;price_above_3000000;ppm_above_5000;signal_candidate: 4
no_verified_polygon;ppm_above_5000;signal_candidate: 2
no_verified_polygon;price_above_3000000;ppm_above_5000;multi_signal_candidate: 1
no_verified_polygon;area_above_25000;price_above_3000000;ppm_above_5000;multi_signal_candidate: 1

wide_accuracy_program_percent: 86
AAYS_097_RISK_PREVIEW_V2_DONE=true
