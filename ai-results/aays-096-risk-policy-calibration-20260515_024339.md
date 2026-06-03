# AAYS 096 Risk Policy Calibration
Generated: 2026-05-15T02:43:40
TaskId: aays-096-risk-policy-calibration-20260515
Mode: read-only calibration memo; no DB writes; no UI patch.

## Input finding
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

## Calibration finding
Current v1 policy is safe but over-conservative: every row becomes critical/manual_review because verified_polygon_geojson is missing or empty for all 120 rows.
This is acceptable for fail-closed production safety, but not useful for ranking manual review effort.

## Proposed v2 separation
Keep acceptance_status strict: no row with missing verified polygon should become verified/accepted.
Relax risk_label to rank review priority even when acceptance_status remains manual_review.

risk_label_v2 critical: missing polygon plus extreme area/price/ppm or contradictory fields.
risk_label_v2 high: derived_ai_visual without polygon, or derived_signal with area/price anomaly.
risk_label_v2 medium: derived_signal without additional anomaly.
risk_label_v2 low: derived_multi_signal without anomaly, still manual_review until source checks pass.

## Safe next implementation
AAYS 097 should generate risk_preview_v2 CSV with both strict acceptance_status and calibrated risk_label_v2.
No DB writes. No UI patch. Source CSV not overwritten.

wide_accuracy_program_percent: 82
AAYS_096_RISK_POLICY_CALIBRATION_DONE=true
