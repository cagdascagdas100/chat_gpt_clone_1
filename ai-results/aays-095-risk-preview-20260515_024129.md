# AAYS 095 Risk Preview
Generated: 2026-05-15T02:41:29
TaskId: aays-095-risk-preview-20260515
SourceCsv: E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv
OutCsv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-095-risk-preview-20260515_024129.csv
Mode: read-only derived preview; source CSV is not overwritten.
source_rows: 120
preview_rows: 120

## risk_label distribution
critical: 120

## acceptance_status distribution
manual_review: 120

## policy_reason top distribution
no_verified_polygon;ai_visual_candidate;area_above_25000;price_above_3000000;ppm_above_5000: 39
no_verified_polygon;ai_visual_candidate;ppm_above_5000: 26
no_verified_polygon;ai_visual_candidate;area_above_25000;ppm_above_5000: 21
no_verified_polygon;signal_candidate;area_above_25000;ppm_above_5000: 13
no_verified_polygon;ai_visual_candidate;price_above_3000000;ppm_above_5000: 13
no_verified_polygon;signal_candidate;area_above_25000;price_above_3000000;ppm_above_5000: 4
no_verified_polygon;signal_candidate;ppm_above_5000: 2
no_verified_polygon;multi_signal_candidate;price_above_3000000;ppm_above_5000: 1
no_verified_polygon;multi_signal_candidate;area_above_25000;price_above_3000000;ppm_above_5000: 1

wide_accuracy_program_percent: 78
AAYS_095_RISK_PREVIEW_DONE=true
