# AAYS 105 Evidence Collection Plan
Generated: 2026-05-15T15:03:24
TaskId: aays-105-evidence-collection-plan-20260515
Mode: read-only evidence plan; no DB writes; no UI patch; no scoring changes.

## Threshold re-audit carried forward
# AAYS 104 Threshold Re-audit
Generated: 2026-05-15T14:01:27
TaskId: aays-104-threshold-reaudit-20260515
Mode: read-only re-audit; no DB writes; no UI patch; no scoring changes.
completed_label_file: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-103-completed_labels_auto_conservative-20260515_133839.csv
rows: 26
reviewer_label_filled: 26
accept: 0
downgrade: 0
reject: 0
needs_source: 16
ambiguous: 10
evidence_checked_yes: 0

## threshold decision
threshold_gate: DO_NOT_RELAX_THRESHOLDS
reason: no accepted rows and no checked evidence in completed label file
recommended_policy: keep all rows manual_review / needs_source until evidence is checked
next_allowed_task: evidence_collection_plan
production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT
wide_accuracy_program_percent: 98
AAYS_104_THRESHOLD_REAUDIT_DONE=true

## Label outcome carried forward
# AAYS 103 Label Outcome Audit
Generated: 2026-05-15T13:40:08
TaskId: aays-103-label-outcome-audit-20260515
Mode: read-only audit; no DB writes; no UI patch; no scoring changes.
completed_label_file: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-103-completed_labels_auto_conservative-20260515_133839.csv
rows: 26
reviewer_label_filled: 26

## reviewer_label distribution
needs_source: 16
ambiguous: 10

## reviewer_confidence distribution
low: 26

## evidence_checked distribution
no: 26

## issue_type distribution
geometry_unsupported: 14
ambiguous_candidate: 10
missing_source: 2

manual_review_gate: LABEL_OUTCOME_AUDITED
next_allowed_task: threshold_reaudit
production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT
wide_accuracy_program_percent: 97
AAYS_103_LABEL_OUTCOME_AUDIT_DONE=true

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

## Evidence collection objective
Collect enough source and polygon evidence to convert selected rows from needs_source/ambiguous into either reject, downgrade, or accept_candidate. Do not auto-accept without evidence_checked=yes.

## Priority order
P1: all derived_multi_signal rows, because there are only 2 and they are closest to accept_candidate after source checks.
P2: all ambiguous derived_signal rows from the 26-row review set.
P3: high-value or extreme-area critical rows from risk_preview_v2.
P4: derived_ai_visual rows only after georeferenced polygon evidence exists.

## Required evidence fields per row
verification_id, listing_id, canonical_source_url, source_url_status, postcode_check, local_authority_check, polygon_source, polygon_georeferenced, evidence_checked, evidence_notes

## Evidence decisions
If source URL missing or inaccessible: reviewer_label=needs_source.
If postcode/authority conflict: reviewer_label=reject or ambiguous.
If polygon not georeferenced: reviewer_label=needs_source; acceptance_status remains manual_review.
If polygon/source/postcode/authority all pass: reviewer_label may become accept_candidate subject to human review.

## Output files to use
completed_labels_auto_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-103-completed_labels_auto_conservative-20260515_133839.csv
risk_preview_v2_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-097-risk-preview-v2-20260515_025249.csv

## Next safe task
AAYS 106 should create an evidence tracking CSV template from completed_labels_auto and risk_preview_v2. It must remain read-only and must not modify DB/UI/scoring.

wide_accuracy_program_percent: 99
production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT
safe_output_gate: READY_FOR_EVIDENCE_COLLECTION
AAYS_105_EVIDENCE_COLLECTION_PLAN_DONE=true
