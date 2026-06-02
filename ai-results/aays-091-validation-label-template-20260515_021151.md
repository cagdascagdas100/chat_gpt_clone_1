# AAYS 091 Validation Label Template
Generated: 2026-05-15T02:11:51
TaskId: aays-091-validation-label-template-20260515
SourceCsv: E:\AAYS_DATA\land_sales\final_outputs\stg_land_sales_50step_db_ready.csv
Mode: read-only label template generation; no DB writes; no UI patch.
source_rows: 120
template_rows: 22
label_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-091-validation-label-template-20260515_021151.csv

## Allowed reviewer_label values
accept, downgrade, reject, needs_source, ambiguous

## Allowed issue_type values
none, missing_source, postcode_mismatch, authority_mismatch, geometry_unsupported, area_outlier, price_outlier, ambiguous_candidate, other

## Review instructions
1. Fill reviewer_label for every row.
2. Fill reviewer_confidence as high, medium, or low.
3. Fill evidence_checked with yes/no.
4. Use corrected_verdict only when label is downgrade or reject.
5. Do not change thresholds until all 25 rows are labeled.

## Template preview

validation_case_id verification_id       listing_id   geometry_verdict     geometry_evidence_type                 geome
                                                                                                                  try_u
                                                                                                                  ncert
                                                                                                                  ainty
                                                                                                                  _m   
------------------ ---------------       ----------   ----------------     ----------------------                 -----
VS-001             L4-00001-OTM-16748769 OTM-16748769 derived_multi_signal multi_signal_non_rectangular_candidate 18.0 
VS-002             L4-00002-OTM-17945851 OTM-17945851 derived_multi_signal multi_signal_non_rectangular_candidate 18.0 
VS-003             L4-00003-OTM-10225397 OTM-10225397 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-004             L4-00005-OTM-10371311 OTM-10371311 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-005             L4-00006-OTM-10541029 OTM-10541029 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-006             L4-00007-OTM-10693127 OTM-10693127 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-007             L4-00008-OTM-10849824 OTM-10849824 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-008             L4-00009-OTM-10854933 OTM-10854933 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-009             L4-00010-OTM-10866038 OTM-10866038 derived_signal       signal_based_non_rectangular_candidate 24.0 
VS-010             L4-00011-OTM-10905789 OTM-10905789 derived_signal       signal_based_non_rectangular_candidate 24.0 




wide_accuracy_program_percent: 60
AAYS_091_VALIDATION_LABEL_TEMPLATE_DONE=true
