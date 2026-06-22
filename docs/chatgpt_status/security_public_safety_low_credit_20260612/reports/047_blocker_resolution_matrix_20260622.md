# 047 Blocker Resolution Matrix

generated_at: 2026-06-22T15:25:00Z
page_key: security_public_safety_low_credit_20260612
script_path: docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/vrun.ps1

## Blocker 1: runner execution pending

Resolution: the existing shared runner must read current-task or queue and execute the script path already written in this page-key.
Expected proof: runner_outputs/047_runner_output_<timestamp>.log

## Blocker 2: parcel polygon carrier not verified

Resolution: the runner must prove that the active parcel output has Polygon or MultiPolygon geometry. Point-only output remains rejected.
Expected proof: reports/047_field_contract_<timestamp>.json with polygon_feature_count greater than zero.

## Blocker 3: canonical field contract not verified

Resolution: the runner must prove at least one live feature has all canonical fields.
Required fields: parcel_id, security_score, security_level, security_level_label, security_color_category, security_color_hex, source_name, source_url, source_date, evidence, matching_method, calculation_explanation, confidence_score, accuracy_rating.
Expected proof: reports/047_field_contract_<timestamp>.json with contract_fields_complete true.

## Safe parallelization

The queued task separates work into non-conflicting probes: local file contract scan, GeoJSON contract probe, HTTP smoke probe, and frontend static check. It does not run competing writers against app.js, GeoJSON, DB, or runner state.

## Acceptance rule

100 is allowed only when status/latest.json is written by the runner with final_ready true and completion_percent 100. Otherwise the task remains blocked with exact blockers in reports/047_blockers_<timestamp>.md.
