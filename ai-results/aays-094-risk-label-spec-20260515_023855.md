# AAYS 094 Risk Label Spec
Generated: 2026-05-15T02:38:55
TaskId: aays-094-risk-label-spec-20260515
Mode: read-only implementation spec; no DB writes; no UI patch.

## New derived fields
risk_label: low, medium, high, critical
acceptance_status: accept_candidate, manual_review, needs_source, reject
policy_reason: semicolon-separated deterministic reasons

## Deterministic rules v1
critical: verified_polygon_geojson is null or empty -> acceptance_status=manual_review
high: geometry_verdict == derived_ai_visual -> acceptance_status=manual_review
high: normalized_area_m2 < 100 -> acceptance_status=manual_review
high: normalized_area_m2 > 25000 -> acceptance_status=manual_review
high: ask_price > 3000000 -> acceptance_status=manual_review
high: price_per_m2 > 5000 -> acceptance_status=manual_review
medium: geometry_verdict == derived_signal -> acceptance_status=manual_review
low: geometry_verdict == derived_multi_signal and source/postcode/authority checks pass -> acceptance_status=accept_candidate

## Safe implementation sequence
1. Add read-only transformation that computes risk_label and acceptance_status into an output CSV.
2. Do not overwrite source CSV.
3. Compare distribution before/after.
4. Review the 26-row manual validation set before changing thresholds.
5. Only after labels exist, promote to DB schema or UI.

## Expected next task
AAYS 095 should generate a risk-labeled preview CSV from stg_land_sales_50step_db_ready.csv without DB writes.

wide_accuracy_program_percent: 72
AAYS_094_RISK_LABEL_SPEC_DONE=true
