# AAYS 100 Reviewer Work Order
Generated: 2026-05-15T03:22:18
TaskId: aays-100-reviewer-work-order-20260515
Mode: read-only reviewer work order; no DB writes; no UI patch.

## Inputs to open
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-091-validation-label-template-20260515_021151.csv
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-092-supplemental-sample-20260515_022949.csv
C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-097-risk-preview-v2-20260515_025249.csv

## Reviewer fields to fill
reviewer_label: accept | downgrade | reject | needs_source | ambiguous
reviewer_confidence: high | medium | low
evidence_checked: yes | no
issue_type: none | missing_source | postcode_mismatch | authority_mismatch | geometry_unsupported | area_outlier | price_outlier | ambiguous_candidate | other
corrected_verdict: only if downgrade or reject

## Minimum completion rule
Fill at least 25 rows before threshold or scoring changes.

## Production rule
Do not auto-accept any row until verified polygon and evidence checks pass.

## After reviewer labels are filled
1. Save completed label CSV in ai-results with suffix completed_labels.
2. Run label outcome audit.
3. Re-run threshold audit.
4. Only then patch scoring/UI.

wide_accuracy_program_percent: 96
AAYS_100_REVIEWER_WORK_ORDER_DONE=true
