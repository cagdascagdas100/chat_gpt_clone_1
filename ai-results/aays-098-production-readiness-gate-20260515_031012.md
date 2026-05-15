# AAYS 098 Production Readiness Gate
Generated: 2026-05-15T03:10:12
TaskId: aays-098-production-readiness-gate-20260515
Mode: read-only readiness gate; no DB writes; no UI patch.

## Risk preview v2 carried forward
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

## Review sample carried forward
# AAYS 092 Supplemental Sample
Generated: 2026-05-15T02:29:49
TaskId: aays-092-supplemental-sample-20260515
Mode: read-only supplemental sample; no DB writes; no UI patch.
source_rows: 120
base_label_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-091-validation-label-template-20260515_021151.csv
base_rows: 22
supplemental_rows: 4
combined_review_rows: 26
supplemental_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-092-supplemental-sample-20260515_022949.csv

## Purpose
Adds extra non-duplicate rows so the review set reaches at least 25 rows.

## Preview

supplemental_case_id verification_id       listing_id   geometry_verdict  geometry_evidence_type                 geomet
                                                                                                                 ry_unc
                                                                                                                 ertain
                                                                                                                 ty_m  
-------------------- ---------------       ----------   ----------------  ----------------------                 ------
SUP-001              L4-00012-OTM-10935976 OTM-10935976 derived_signal    signal_based_non_rectangular_candidate 24.0  
SUP-002              L4-00014-OTM-10973719 OTM-10973719 derived_signal    signal_based_non_rectangular_candidate 24.0  
SUP-003              L4-00555-OTM-16460389 OTM-16460389 derived_ai_visual visual_hint_assisted_candidate         28.0  
SUP-004              L4-01217-OTM-17888180 OTM-17888180 derived_ai_visual visual_hint_assisted_candidate         28.0  




wide_accuracy_program_percent: 65
AAYS_092_SUPPLEMENTAL_SAMPLE_DONE=true

## Gate decision
production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT
reason: acceptance_status_strict remains manual_review for all 120 rows because verified polygons are missing.
safe_output_gate: READY_FOR_MANUAL_REVIEW_QUEUE
reason: risk_label_v2 now separates review priority and source CSV was not overwritten.

## What is safe to use now
1. Use 26-row review set for manual labeling.
2. Use risk_preview_v2 as manual review prioritization only.
3. Keep all rows out of auto-verified/auto-accepted status until polygon/source checks pass.

## Hard blockers before production auto-accept
1. verified_polygon_geojson must be present and georeferenced.
2. source_urls_json/listing evidence must be checked for the reviewed rows.
3. reviewer labels must be filled for at least 25 rows.
4. threshold changes must wait until reviewed label outcomes exist.

## Next task
AAYS 099 should create a final handoff summary with all output paths, gates, blockers, and next manual steps.

wide_accuracy_program_percent: 90
AAYS_098_PRODUCTION_READINESS_GATE_DONE=true
