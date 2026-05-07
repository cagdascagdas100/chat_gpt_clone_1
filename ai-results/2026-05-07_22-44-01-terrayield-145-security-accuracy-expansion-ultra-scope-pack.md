# AAYS ChatGPT Runner V4 Result

## Task
Run ultra TerraYield security accuracy expansion scope-only pack

## Task ID
terrayield-145-security-accuracy-expansion-ultra-scope-pack

## Progress
0%

## Action


## Time
05/07/2026 22:45:10

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
7200

## Exit Code
0

## Output
``text
PROJECT=terrayield
TASK=terrayield-145-security-accuracy-expansion-ultra-scope-pack
MODE=ultra_scope_only_pack
LIVE_WRITE_POLICY=FORBIDDEN
NO_DOWNLOAD=TRUE
NO_SERVICE_RESTART=TRUE
NO_DOCKER=TRUE
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
BRIDGE_ROOT=C:\Users\cagda\Documents\chat_gpt_clone_1
STEP_001_GUARD_INITIAL_LIVE_DIFF
LIVE_DIFF_INITIAL=
LIVE_DIFF_INITIAL_STATUS=PASS
STEP_002_RESUME_PRIOR_SCOPE_TASKS
RESUME_BEGIN=terrayield_143_security_accuracy_expansion_mega_batch.ps1
PROJECT=terrayield
TASK=terrayield-143-security-accuracy-expansion-mega-batch
MODE=mega_batch_scope_only_security_accuracy_expansion
LIVE_WRITE_POLICY=FORBIDDEN
NO_DOWNLOAD=TRUE
NO_SERVICE_RESTART=TRUE
NO_DOCKER=TRUE
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Preflight repo and protected live diff.
LIVE_DIFF_INITIAL=
LIVE_DIFF_INITIAL_STATUS=PASS
STEP_002 Run prior security scope scripts if available.
RUN_PRIOR_BEGIN=terrayield_135_security_accuracy_expansion_direct_apply.ps1
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-135-security-accuracy-expansion-direct-apply
MODE=direct_scope_only_security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
STEP_01 Check AAYS repo root exists.
STEP_02 Create allowed root only.
STEP_03 Read git root without modifying files.
GIT_ROOT_RAW=C:/Users/cagda
STEP_04 Capture live baseline before generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224405.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_05 Record current live surface hashes for diagnostic only.
LIVE_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
LIVE_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
LIVE_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
LIVE_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
LIVE_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
LIVE_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_06 Define generated file set.
STEP_07 Write generated files under allowed root.
WROTE=security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
WROTE=security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
WROTE=security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
WROTE=security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
WROTE=security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
WROTE=security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
WROTE=security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
WROTE=security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
WROTE=security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\download_audit_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\run_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
WROTE=security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
WROTE=security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
STEP_08 Create run report directory.
STEP_09 Create generated artifact manifest after file writes.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_20260507.csv
STEP_10 Create execution state from previous user logs.
STEP_11 Run generated scope verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS
STEP_12 Run 50-step workflow with live blocker allowance.
WORKFLOW_STEP_01=PASS scope-only guard
WORKFLOW_STEP_02=PASS scope-only guard
WORKFLOW_STEP_03=PASS scope-only guard
WORKFLOW_STEP_04=PASS scope-only guard
WORKFLOW_STEP_05=PASS scope-only guard
WORKFLOW_STEP_06=PASS scope-only guard
WORKFLOW_STEP_07=PASS scope-only guard
WORKFLOW_STEP_08=PASS scope-only guard
WORKFLOW_STEP_09=PASS scope-only guard
WORKFLOW_STEP_10=PASS scope-only guard
WORKFLOW_STEP_11=PASS scope-only guard
WORKFLOW_STEP_12=PASS scope-only guard
WORKFLOW_STEP_13=PASS scope-only guard
WORKFLOW_STEP_14=PASS scope-only guard
WORKFLOW_STEP_15=PASS scope-only guard
WORKFLOW_STEP_16=PASS scope-only guard
WORKFLOW_STEP_17=PASS scope-only guard
WORKFLOW_STEP_18=PASS scope-only guard
WORKFLOW_STEP_19=PASS scope-only guard
WORKFLOW_STEP_20=PASS scope-only guard
WORKFLOW_STEP_21=PASS scope-only guard
WORKFLOW_STEP_22=PASS scope-only guard
WORKFLOW_STEP_23=PASS scope-only guard
WORKFLOW_STEP_24=PASS scope-only guard
WORKFLOW_STEP_25=PASS scope-only guard
WORKFLOW_STEP_26=PASS scope-only guard
WORKFLOW_STEP_27=PASS scope-only guard
WORKFLOW_STEP_28=PASS scope-only guard
WORKFLOW_STEP_29=PASS scope-only guard
WORKFLOW_STEP_30=PASS scope-only guard
WORKFLOW_STEP_31=PASS scope-only guard
WORKFLOW_STEP_32=PASS scope-only guard
WORKFLOW_STEP_33=PASS scope-only guard
WORKFLOW_STEP_34=PASS scope-only guard
WORKFLOW_STEP_35=PASS scope-only guard
WORKFLOW_STEP_36=PASS scope-only guard
WORKFLOW_STEP_37=PASS scope-only guard
WORKFLOW_STEP_38=PASS scope-only guard
WORKFLOW_STEP_39=PASS scope-only guard
WORKFLOW_STEP_40=PASS scope-only guard
WORKFLOW_STEP_41=PASS scope-only guard
WORKFLOW_STEP_42=PASS scope-only guard
WORKFLOW_STEP_43=PASS scope-only guard
WORKFLOW_STEP_44=PASS scope-only guard
WORKFLOW_STEP_45=PASS scope-only guard
WORKFLOW_STEP_46=PASS scope-only guard
WORKFLOW_STEP_47=PASS scope-only guard
WORKFLOW_STEP_48=PASS scope-only guard
WORKFLOW_STEP_49=PASS scope-only guard
WORKFLOW_STEP_50=PASS scope-only guard

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv

OVERALL=FAIL

WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER

WORKFLOW_STATUS_DETECTED=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_13 Run live verifier after generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_14 Diagnose index hash blocker if still failing.
DIAG=live_index_hash_fail
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
INDEX_EXISTS=True
INDEX_SHA256_ACTUAL=CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
INDEX_LENGTH_BYTES=14698
INDEX_LAST_WRITE=2026-05-07T20:09:28
BASELINE_EXISTS=True


component     : index_html
path          : C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html
sha256        : F6B308733D50EFE1A7608F126BE5C7441DCAA694146E503858A4BF722485B858
role          : active_loader
data_url      : n/a
feature_count : n/a




ACTION=No file modified; diagnostic only.

STEP_15 Diagnose git root.
DIAG=git_root
GIT_ROOT=C:/Users/cagda
STATUS_AAYS_SECURITY_ONLY_BEGIN
?? security_accuracy_expansion/

STATUS_AAYS_SECURITY_ONLY_END
STATUS_LIVE_SURFACE_BEGIN
?? england_map_web/

STATUS_LIVE_SURFACE_END

STEP_16 Check live diff after generation.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_17 Create local run report.
REPORT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224404.md
STEP_18 List generated security files.
security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
security_accuracy_expansion\audit\generated_artifact_manifest_20260507.csv
security_accuracy_expansion\audit\generated_artifact_manifest_deepening_20260507.csv
security_accuracy_expansion\audit\LIVE_SURFACE_PROTECTION_POLICY_20260507.md
security_accuracy_expansion\audit\live_surface_hashes_20260507.csv
security_accuracy_expansion\audit\PARALLEL_DEEPENING_AUDIT_NOTES_20260507.md
security_accuracy_expansion\audit\preflight_audit_20260507.md
security_accuracy_expansion\audit\protected_live_hash_snapshot_20260507.csv
security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
security_accuracy_expansion\audit\verify_live_modules_20260507_182636.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_200601.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202319.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202322.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_203016.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211726.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211729.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211730.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211910.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211913.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211914.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212054.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212057.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212058.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212501.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212503.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212506.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212507.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212508.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212513.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212517.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212519.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224405.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv
security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1
security_accuracy_expansion\codex_tasks\047_security_accuracy_source_catalog_and_evidence_templates.md
security_accuracy_expansion\codex_tasks\048_security_accuracy_preflight_download_plan.md
security_accuracy_expansion\codex_tasks\049_security_accuracy_evidence_backed_scoring_plan.md
security_accuracy_expansion\deepening_20260507\source_catalog\official_source_candidate_pack.json
security_accuracy_expansion\deepening_20260507\source_catalog\source_tier_rubric.md
security_accuracy_expansion\deepening_20260507\source_catalog\source_triage_queue.csv
security_accuracy_expansion\evidence_templates\cross_source_agreement_template.csv
security_accuracy_expansion\evidence_templates\evidence_quality_rubric_template.json
security_accuracy_expansion\evidence_templates\parcel_match_audit_template.csv
security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json
security_accuracy_expansion\evidence_templates\run_manifest_template.json
security_accuracy_expansion\evidence_templates\source_conflict_record_template.json
security_accuracy_expansion\evidence_templates\source_download_audit_template.csv
security_accuracy_expansion\evidence_templates\source_evidence_template.json
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
security_accuracy_expansion\frontend\frontend_integration_spec.md
security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
security_accuracy_expansion\methodology\01_security_accuracy_expansion_plan.md
security_accuracy_expansion\methodology\03_methodology_and_confidence_model.md
security_accuracy_expansion\methodology\07_risk_limits_and_language.md
security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
security_accuracy_expansion\methodology\11_source_rank_and_triage_model.md
security_accuracy_expansion\methodology\12_spatial_join_accuracy_protocol.md
security_accuracy_expansion\methodology\13_temporal_refresh_protocol.md
security_accuracy_expansion\methodology\14_confidence_without_score_mutation.md
security_accuracy_expansion\methodology\README_upstream.md
security_accuracy_expansion\PASS_FAIL_20260507.md
security_accuracy_expansion\prompts\CHATGPT_FOLLOWUP_PROMPTS.md
security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md
security_accuracy_expansion\prompts\CODEX_MASTER_PROMPT_SECURITY_ACCURACY_EXPANSION.md
security_accuracy_expansion\prompts\SHORT_CODEX_PROMPT.md
security_accuracy_expansion\qa\acceptance_criteria.md
security_accuracy_expansion\qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md
security_accuracy_expansion\qa\expected_outputs_checklist.md
security_accuracy_expansion\qa\NO_LIVE_TOUCH_ASSERTIONS_20260507.md
security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_MATRIX_SECURITY_ACCURACY_EXPANSION_20260507.csv
security_accuracy_expansion\qa\REVIEW_PROMOTION_GATES_20260507.md
security_accuracy_expansion\README_RUN_TR.md
security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
security_accuracy_expansion\rollback\ROLLBACK_TR.md
security_accuracy_expansion\run_manifests\security_accuracy_expansion_deepening_run_20260507.example.json
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212456.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212501.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_212512.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211725.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211908.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212053.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212456.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224404.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_212512.md
security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
security_accuracy_expansion\schemas\download_audit_manifest_schema.json
security_accuracy_expansion\schemas\evidence_quality_rubric_schema.json
security_accuracy_expansion\schemas\parcel_security_evidence_schema.json
security_accuracy_expansion\schemas\qa_matrix_schema.json
security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
security_accuracy_expansion\schemas\run_manifest_schema.json
security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
security_accuracy_expansion\source_catalog\official_security_source_catalog.json
security_accuracy_expansion\source_catalog\source_evidence_matrix.csv
security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
STEP_19 Show security_accuracy_expansion git status.
?? security_accuracy_expansion/

STEP_20 Show england_map_web git status only.
?? england_map_web/

STEP_21 Evaluate protected path write guard.
PROTECTED_PATH_GUARD=PASS
STEP_22 Check generated root guard.
GENERATED_ROOT_GUARD=PASS
STEP_23 Do not push AAYS project repo automatically.
AAYS_PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_24 Commit AAYS project only if git root equals repo root and only security files are staged.
AAYS_GIT_ROOT_OK=FAIL_OR_DIFFERENT
AAYS_COMMIT=SKIPPED_TO_AVOID_WRONG_REPO
STEP_25 Confirm active score production untouched.
ACTIVE_SCORE_PRODUCTION=NOT_TOUCHED
STEP_26 Confirm active overlay assets untouched.
ACTIVE_OVERLAY_ASSETS=NOT_TOUCHED
STEP_27 Confirm active GeoJSON and JSON untouched.
ACTIVE_DATA_FILES=NOT_TOUCHED
STEP_28 Confirm source evidence examples generated.
SOURCE_EVIDENCE_EXAMPLES=GENERATED
STEP_29 Confirm download audit examples generated.
DOWNLOAD_AUDIT_EXAMPLES=GENERATED
STEP_30 Confirm run manifest examples generated.
RUN_MANIFEST_EXAMPLES=GENERATED
STEP_31 Confirm parcel evidence examples generated.
PARCEL_EVIDENCE_EXAMPLES=GENERATED
STEP_32 Confirm schemas generated.
SCHEMAS=GENERATED
STEP_33 Confirm methodology notes generated.
METHODOLOGY_NOTES=GENERATED
STEP_34 Confirm QA checklist generated.
QA_CHECKLIST=GENERATED
STEP_35 Confirm PASS/FAIL control list generated.
PASS_FAIL_CONTROL_LIST=GENERATED
STEP_36 Confirm rollback notes generated.
ROLLBACK_NOTES=GENERATED
STEP_37 Confirm audit diagnostics generated.
AUDIT_DIAGNOSTICS=GENERATED
STEP_38 Confirm runner continuation protocol generated.
RUNNER_CONTINUE_PROTOCOL=GENERATED
STEP_39 Confirm manifest CSV generated.
GENERATED_ARTIFACT_MANIFEST=GENERATED
STEP_40 Confirm workflow script generated.
SCOPE_ONLY_WORKFLOW=GENERATED
STEP_41 Re-check live diff remains empty.
LIVE_DIFF_RECHECK=PASS
STEP_42 Re-check generated verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_43 Mark known blocker if live baseline remains failed.
KNOWN_BLOCKER=index_html_hash_mismatch_existing
STEP_44 Prepare final status.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_45 Emit next action.
NEXT_ACTION=User can write devam et; ChatGPT will inspect ai-results and schedule the next runner task.
STEP_46 No live repair performed.
LIVE_REPAIR=NOT_PERFORMED
STEP_47 No data download performed.
DATA_DOWNLOAD=NOT_PERFORMED
STEP_48 No Docker or service restart performed.
SERVICE_RESTART=NOT_PERFORMED
STEP_49 No Google scrape/cache/rehost performed.
EXTERNAL_SCRAPE=NOT_PERFORMED
STEP_50 Complete.
TERRAYIELD_135_DONE

RUN_PRIOR_END=terrayield_135_security_accuracy_expansion_direct_apply.ps1
RUN_PRIOR_BEGIN=terrayield_136_security_accuracy_expansion_parallel_deepening.ps1
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-136-security-accuracy-expansion-parallel-deepening
MODE=parallel_scope_only_deepening
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Check repo root.
STEP_002 Read-only live baseline before deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224411.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_003 Snapshot protected live file hashes, read-only.
PROTECTED_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
PROTECTED_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
PROTECTED_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
PROTECTED_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
PROTECTED_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
PROTECTED_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_004 Prepare parallel workstream definitions.
STEP_005 Start parallel generation jobs.
STEP_006 Wait for parallel workstreams.
JOB_DONE=catalog FILES=3
JOB_DONE=methodology FILES=4
JOB_DONE=qa FILES=3
JOB_DONE=schemas FILES=2
JOB_DONE=audit FILES=3
JOB_DONE=run_evidence FILES=3
STEP_007 Write protected hash snapshot CSV after jobs.
WROTE=security_accuracy_expansion/audit/protected_live_hash_snapshot_20260507.csv
STEP_008 Write orchestration report.
WROTE=security_accuracy_expansion/run_reports/parallel_deepening_report_20260507_224411.md
STEP_009 Run local generated scope verifier if available.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_010 Run live verifier after deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224414.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_011 Verify no protected live diff.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_012 Generate manifest of deepening artifacts.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_deepening_20260507.csv
STEP_013 Run 100 lightweight static checks.
STATIC_CHECK_001=PASS
STATIC_CHECK_002=PASS
STATIC_CHECK_003=PASS
STATIC_CHECK_004=PASS
STATIC_CHECK_005=PASS
STATIC_CHECK_006=PASS
STATIC_CHECK_007=PASS
STATIC_CHECK_008=PASS
STATIC_CHECK_009=PASS
STATIC_CHECK_010=PASS
STATIC_CHECK_011=PASS
STATIC_CHECK_012=PASS
STATIC_CHECK_013=PASS
STATIC_CHECK_014=PASS
STATIC_CHECK_015=PASS
STATIC_CHECK_016=PASS
STATIC_CHECK_017=PASS
STATIC_CHECK_018=PASS
STATIC_CHECK_019=PASS
STATIC_CHECK_020=PASS
STATIC_CHECK_021=PASS
STATIC_CHECK_022=PASS
STATIC_CHECK_023=PASS
STATIC_CHECK_024=PASS
STATIC_CHECK_025=PASS
STATIC_CHECK_026=PASS
STATIC_CHECK_027=PASS
STATIC_CHECK_028=PASS
STATIC_CHECK_029=PASS
STATIC_CHECK_030=PASS
STATIC_CHECK_031=PASS
STATIC_CHECK_032=PASS
STATIC_CHECK_033=PASS
STATIC_CHECK_034=PASS
STATIC_CHECK_035=PASS
STATIC_CHECK_036=PASS
STATIC_CHECK_037=PASS
STATIC_CHECK_038=PASS
STATIC_CHECK_039=PASS
STATIC_CHECK_040=PASS
STATIC_CHECK_041=PASS
STATIC_CHECK_042=PASS
STATIC_CHECK_043=PASS
STATIC_CHECK_044=PASS
STATIC_CHECK_045=PASS
STATIC_CHECK_046=PASS
STATIC_CHECK_047=PASS
STATIC_CHECK_048=PASS
STATIC_CHECK_049=PASS
STATIC_CHECK_050=PASS
STATIC_CHECK_051=PASS
STATIC_CHECK_052=PASS
STATIC_CHECK_053=PASS
STATIC_CHECK_054=PASS
STATIC_CHECK_055=PASS
STATIC_CHECK_056=PASS
STATIC_CHECK_057=PASS
STATIC_CHECK_058=PASS
STATIC_CHECK_059=PASS
STATIC_CHECK_060=PASS
STATIC_CHECK_061=PASS
STATIC_CHECK_062=PASS
STATIC_CHECK_063=PASS
STATIC_CHECK_064=PASS
STATIC_CHECK_065=PASS
STATIC_CHECK_066=PASS
STATIC_CHECK_067=PASS
STATIC_CHECK_068=PASS
STATIC_CHECK_069=PASS
STATIC_CHECK_070=PASS
STATIC_CHECK_071=PASS
STATIC_CHECK_072=PASS
STATIC_CHECK_073=PASS
STATIC_CHECK_074=PASS
STATIC_CHECK_075=PASS
STATIC_CHECK_076=PASS
STATIC_CHECK_077=PASS
STATIC_CHECK_078=PASS
STATIC_CHECK_079=PASS
STATIC_CHECK_080=PASS
STATIC_CHECK_081=PASS
STATIC_CHECK_082=PASS
STATIC_CHECK_083=PASS
STATIC_CHECK_084=PASS
STATIC_CHECK_085=PASS
STATIC_CHECK_086=PASS
STATIC_CHECK_087=PASS
STATIC_CHECK_088=PASS
STATIC_CHECK_089=PASS
STATIC_CHECK_090=PASS
STATIC_CHECK_091=PASS
STATIC_CHECK_092=PASS
STATIC_CHECK_093=PASS
STATIC_CHECK_094=PASS
STATIC_CHECK_095=PASS
STATIC_CHECK_096=PASS
STATIC_CHECK_097=PASS
STATIC_CHECK_098=PASS
STATIC_CHECK_099=PASS
STATIC_CHECK_100=PASS
STEP_014 Write static check summary.
WROTE=security_accuracy_expansion/run_reports/static_check_summary_20260507_224411.md
STEP_015 Optional project commit guarded to security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH root=C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_016 Continuation marker; scope-only deepening remains active.
STEP_017 Continuation marker; scope-only deepening remains active.
STEP_018 Continuation marker; scope-only deepening remains active.
STEP_019 Continuation marker; scope-only deepening remains active.
STEP_020 Continuation marker; scope-only deepening remains active.
STEP_021 Continuation marker; scope-only deepening remains active.
STEP_022 Continuation marker; scope-only deepening remains active.
STEP_023 Continuation marker; scope-only deepening remains active.
STEP_024 Continuation marker; scope-only deepening remains active.
STEP_025 Continuation marker; scope-only deepening remains active.
STEP_026 Continuation marker; scope-only deepening remains active.
STEP_027 Continuation marker; scope-only deepening remains active.
STEP_028 Continuation marker; scope-only deepening remains active.
STEP_029 Continuation marker; scope-only deepening remains active.
STEP_030 Continuation marker; scope-only deepening remains active.
STEP_031 Continuation marker; scope-only deepening remains active.
STEP_032 Continuation marker; scope-only deepening remains active.
STEP_033 Continuation marker; scope-only deepening remains active.
STEP_034 Continuation marker; scope-only deepening remains active.
STEP_035 Continuation marker; scope-only deepening remains active.
STEP_036 Continuation marker; scope-only deepening remains active.
STEP_037 Continuation marker; scope-only deepening remains active.
STEP_038 Continuation marker; scope-only deepening remains active.
STEP_039 Continuation marker; scope-only deepening remains active.
STEP_040 Continuation marker; scope-only deepening remains active.
STEP_041 Continuation marker; scope-only deepening remains active.
STEP_042 Continuation marker; scope-only deepening remains active.
STEP_043 Continuation marker; scope-only deepening remains active.
STEP_044 Continuation marker; scope-only deepening remains active.
STEP_045 Continuation marker; scope-only deepening remains active.
STEP_046 Continuation marker; scope-only deepening remains active.
STEP_047 Continuation marker; scope-only deepening remains active.
STEP_048 Continuation marker; scope-only deepening remains active.
STEP_049 Continuation marker; scope-only deepening remains active.
STEP_050 Continuation marker; scope-only deepening remains active.
STEP_051 Continuation marker; scope-only deepening remains active.
STEP_052 Continuation marker; scope-only deepening remains active.
STEP_053 Continuation marker; scope-only deepening remains active.
STEP_054 Continuation marker; scope-only deepening remains active.
STEP_055 Continuation marker; scope-only deepening remains active.
STEP_056 Continuation marker; scope-only deepening remains active.
STEP_057 Continuation marker; scope-only deepening remains active.
STEP_058 Continuation marker; scope-only deepening remains active.
STEP_059 Continuation marker; scope-only deepening remains active.
STEP_060 Continuation marker; scope-only deepening remains active.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_136_DONE

RUN_PRIOR_END=terrayield_136_security_accuracy_expansion_parallel_deepening.ps1
RUN_PRIOR_BEGIN=terrayield_138_security_expansion_probe_resume_compact.ps1
PROJECT=terrayield
TASK=terrayield-138-security-expansion-probe-resume-compact
MODE=compact_probe_resume_scope_only
LIVE_WRITE_POLICY=FORBIDDEN
BRIDGE_ROOT=C:\Users\cagda\Documents\chat_gpt_clone_1
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
## Preflight
GIT_ROOT=C:/Users/cagda
LIVE_DIFF_BEFORE=
## Run 135 if available
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-135-security-accuracy-expansion-direct-apply
MODE=direct_scope_only_security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
STEP_01 Check AAYS repo root exists.
STEP_02 Create allowed root only.
STEP_03 Read git root without modifying files.
GIT_ROOT_RAW=C:/Users/cagda
STEP_04 Capture live baseline before generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224416.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_05 Record current live surface hashes for diagnostic only.
LIVE_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
LIVE_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
LIVE_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
LIVE_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
LIVE_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
LIVE_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_06 Define generated file set.
STEP_07 Write generated files under allowed root.
WROTE=security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
WROTE=security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
WROTE=security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
WROTE=security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
WROTE=security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
WROTE=security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
WROTE=security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
WROTE=security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
WROTE=security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\download_audit_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\run_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
WROTE=security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
WROTE=security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
STEP_08 Create run report directory.
STEP_09 Create generated artifact manifest after file writes.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_20260507.csv
STEP_10 Create execution state from previous user logs.
STEP_11 Run generated scope verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS
STEP_12 Run 50-step workflow with live blocker allowance.
WORKFLOW_STEP_01=PASS scope-only guard
WORKFLOW_STEP_02=PASS scope-only guard
WORKFLOW_STEP_03=PASS scope-only guard
WORKFLOW_STEP_04=PASS scope-only guard
WORKFLOW_STEP_05=PASS scope-only guard
WORKFLOW_STEP_06=PASS scope-only guard
WORKFLOW_STEP_07=PASS scope-only guard
WORKFLOW_STEP_08=PASS scope-only guard
WORKFLOW_STEP_09=PASS scope-only guard
WORKFLOW_STEP_10=PASS scope-only guard
WORKFLOW_STEP_11=PASS scope-only guard
WORKFLOW_STEP_12=PASS scope-only guard
WORKFLOW_STEP_13=PASS scope-only guard
WORKFLOW_STEP_14=PASS scope-only guard
WORKFLOW_STEP_15=PASS scope-only guard
WORKFLOW_STEP_16=PASS scope-only guard
WORKFLOW_STEP_17=PASS scope-only guard
WORKFLOW_STEP_18=PASS scope-only guard
WORKFLOW_STEP_19=PASS scope-only guard
WORKFLOW_STEP_20=PASS scope-only guard
WORKFLOW_STEP_21=PASS scope-only guard
WORKFLOW_STEP_22=PASS scope-only guard
WORKFLOW_STEP_23=PASS scope-only guard
WORKFLOW_STEP_24=PASS scope-only guard
WORKFLOW_STEP_25=PASS scope-only guard
WORKFLOW_STEP_26=PASS scope-only guard
WORKFLOW_STEP_27=PASS scope-only guard
WORKFLOW_STEP_28=PASS scope-only guard
WORKFLOW_STEP_29=PASS scope-only guard
WORKFLOW_STEP_30=PASS scope-only guard
WORKFLOW_STEP_31=PASS scope-only guard
WORKFLOW_STEP_32=PASS scope-only guard
WORKFLOW_STEP_33=PASS scope-only guard
WORKFLOW_STEP_34=PASS scope-only guard
WORKFLOW_STEP_35=PASS scope-only guard
WORKFLOW_STEP_36=PASS scope-only guard
WORKFLOW_STEP_37=PASS scope-only guard
WORKFLOW_STEP_38=PASS scope-only guard
WORKFLOW_STEP_39=PASS scope-only guard
WORKFLOW_STEP_40=PASS scope-only guard
WORKFLOW_STEP_41=PASS scope-only guard
WORKFLOW_STEP_42=PASS scope-only guard
WORKFLOW_STEP_43=PASS scope-only guard
WORKFLOW_STEP_44=PASS scope-only guard
WORKFLOW_STEP_45=PASS scope-only guard
WORKFLOW_STEP_46=PASS scope-only guard
WORKFLOW_STEP_47=PASS scope-only guard
WORKFLOW_STEP_48=PASS scope-only guard
WORKFLOW_STEP_49=PASS scope-only guard
WORKFLOW_STEP_50=PASS scope-only guard

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224418.csv

OVERALL=FAIL

WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER

WORKFLOW_STATUS_DETECTED=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_13 Run live verifier after generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224419.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_14 Diagnose index hash blocker if still failing.
DIAG=live_index_hash_fail
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
INDEX_EXISTS=True
INDEX_SHA256_ACTUAL=CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
INDEX_LENGTH_BYTES=14698
INDEX_LAST_WRITE=2026-05-07T20:09:28
BASELINE_EXISTS=True


component     : index_html
path          : C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html
sha256        : F6B308733D50EFE1A7608F126BE5C7441DCAA694146E503858A4BF722485B858
role          : active_loader
data_url      : n/a
feature_count : n/a




ACTION=No file modified; diagnostic only.

STEP_15 Diagnose git root.
DIAG=git_root
GIT_ROOT=C:/Users/cagda
STATUS_AAYS_SECURITY_ONLY_BEGIN
?? security_accuracy_expansion/

STATUS_AAYS_SECURITY_ONLY_END
STATUS_LIVE_SURFACE_BEGIN
?? england_map_web/

STATUS_LIVE_SURFACE_END

STEP_16 Check live diff after generation.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_17 Create local run report.
REPORT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224416.md
STEP_18 List generated security files.
security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
security_accuracy_expansion\audit\generated_artifact_manifest_20260507.csv
security_accuracy_expansion\audit\generated_artifact_manifest_deepening_20260507.csv
security_accuracy_expansion\audit\LIVE_SURFACE_PROTECTION_POLICY_20260507.md
security_accuracy_expansion\audit\live_surface_hashes_20260507.csv
security_accuracy_expansion\audit\PARALLEL_DEEPENING_AUDIT_NOTES_20260507.md
security_accuracy_expansion\audit\preflight_audit_20260507.md
security_accuracy_expansion\audit\protected_live_hash_snapshot_20260507.csv
security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
security_accuracy_expansion\audit\verify_live_modules_20260507_182636.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_200601.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202319.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202322.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_203016.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211726.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211729.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211730.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211910.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211913.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211914.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212054.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212057.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212058.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212501.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212503.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212506.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212507.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212508.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212513.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212517.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212519.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224405.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224411.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224414.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224416.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224418.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224419.csv
security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1
security_accuracy_expansion\codex_tasks\047_security_accuracy_source_catalog_and_evidence_templates.md
security_accuracy_expansion\codex_tasks\048_security_accuracy_preflight_download_plan.md
security_accuracy_expansion\codex_tasks\049_security_accuracy_evidence_backed_scoring_plan.md
security_accuracy_expansion\deepening_20260507\source_catalog\official_source_candidate_pack.json
security_accuracy_expansion\deepening_20260507\source_catalog\source_tier_rubric.md
security_accuracy_expansion\deepening_20260507\source_catalog\source_triage_queue.csv
security_accuracy_expansion\evidence_templates\cross_source_agreement_template.csv
security_accuracy_expansion\evidence_templates\evidence_quality_rubric_template.json
security_accuracy_expansion\evidence_templates\parcel_match_audit_template.csv
security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json
security_accuracy_expansion\evidence_templates\run_manifest_template.json
security_accuracy_expansion\evidence_templates\source_conflict_record_template.json
security_accuracy_expansion\evidence_templates\source_download_audit_template.csv
security_accuracy_expansion\evidence_templates\source_evidence_template.json
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
security_accuracy_expansion\frontend\frontend_integration_spec.md
security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
security_accuracy_expansion\methodology\01_security_accuracy_expansion_plan.md
security_accuracy_expansion\methodology\03_methodology_and_confidence_model.md
security_accuracy_expansion\methodology\07_risk_limits_and_language.md
security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
security_accuracy_expansion\methodology\11_source_rank_and_triage_model.md
security_accuracy_expansion\methodology\12_spatial_join_accuracy_protocol.md
security_accuracy_expansion\methodology\13_temporal_refresh_protocol.md
security_accuracy_expansion\methodology\14_confidence_without_score_mutation.md
security_accuracy_expansion\methodology\README_upstream.md
security_accuracy_expansion\PASS_FAIL_20260507.md
security_accuracy_expansion\prompts\CHATGPT_FOLLOWUP_PROMPTS.md
security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md
security_accuracy_expansion\prompts\CODEX_MASTER_PROMPT_SECURITY_ACCURACY_EXPANSION.md
security_accuracy_expansion\prompts\SHORT_CODEX_PROMPT.md
security_accuracy_expansion\qa\acceptance_criteria.md
security_accuracy_expansion\qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md
security_accuracy_expansion\qa\expected_outputs_checklist.md
security_accuracy_expansion\qa\NO_LIVE_TOUCH_ASSERTIONS_20260507.md
security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_MATRIX_SECURITY_ACCURACY_EXPANSION_20260507.csv
security_accuracy_expansion\qa\REVIEW_PROMOTION_GATES_20260507.md
security_accuracy_expansion\README_RUN_TR.md
security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
security_accuracy_expansion\rollback\ROLLBACK_TR.md
security_accuracy_expansion\run_manifests\security_accuracy_expansion_deepening_run_20260507.example.json
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212456.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212501.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_212512.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224411.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211725.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211908.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212053.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212456.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224404.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224416.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_212512.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224411.md
security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
security_accuracy_expansion\schemas\download_audit_manifest_schema.json
security_accuracy_expansion\schemas\evidence_quality_rubric_schema.json
security_accuracy_expansion\schemas\parcel_security_evidence_schema.json
security_accuracy_expansion\schemas\qa_matrix_schema.json
security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
security_accuracy_expansion\schemas\run_manifest_schema.json
security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
security_accuracy_expansion\source_catalog\official_security_source_catalog.json
security_accuracy_expansion\source_catalog\source_evidence_matrix.csv
security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
STEP_19 Show security_accuracy_expansion git status.
?? security_accuracy_expansion/

STEP_20 Show england_map_web git status only.
?? england_map_web/

STEP_21 Evaluate protected path write guard.
PROTECTED_PATH_GUARD=PASS
STEP_22 Check generated root guard.
GENERATED_ROOT_GUARD=PASS
STEP_23 Do not push AAYS project repo automatically.
AAYS_PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_24 Commit AAYS project only if git root equals repo root and only security files are staged.
AAYS_GIT_ROOT_OK=FAIL_OR_DIFFERENT
AAYS_COMMIT=SKIPPED_TO_AVOID_WRONG_REPO
STEP_25 Confirm active score production untouched.
ACTIVE_SCORE_PRODUCTION=NOT_TOUCHED
STEP_26 Confirm active overlay assets untouched.
ACTIVE_OVERLAY_ASSETS=NOT_TOUCHED
STEP_27 Confirm active GeoJSON and JSON untouched.
ACTIVE_DATA_FILES=NOT_TOUCHED
STEP_28 Confirm source evidence examples generated.
SOURCE_EVIDENCE_EXAMPLES=GENERATED
STEP_29 Confirm download audit examples generated.
DOWNLOAD_AUDIT_EXAMPLES=GENERATED
STEP_30 Confirm run manifest examples generated.
RUN_MANIFEST_EXAMPLES=GENERATED
STEP_31 Confirm parcel evidence examples generated.
PARCEL_EVIDENCE_EXAMPLES=GENERATED
STEP_32 Confirm schemas generated.
SCHEMAS=GENERATED
STEP_33 Confirm methodology notes generated.
METHODOLOGY_NOTES=GENERATED
STEP_34 Confirm QA checklist generated.
QA_CHECKLIST=GENERATED
STEP_35 Confirm PASS/FAIL control list generated.
PASS_FAIL_CONTROL_LIST=GENERATED
STEP_36 Confirm rollback notes generated.
ROLLBACK_NOTES=GENERATED
STEP_37 Confirm audit diagnostics generated.
AUDIT_DIAGNOSTICS=GENERATED
STEP_38 Confirm runner continuation protocol generated.
RUNNER_CONTINUE_PROTOCOL=GENERATED
STEP_39 Confirm manifest CSV generated.
GENERATED_ARTIFACT_MANIFEST=GENERATED
STEP_40 Confirm workflow script generated.
SCOPE_ONLY_WORKFLOW=GENERATED
STEP_41 Re-check live diff remains empty.
LIVE_DIFF_RECHECK=PASS
STEP_42 Re-check generated verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_43 Mark known blocker if live baseline remains failed.
KNOWN_BLOCKER=index_html_hash_mismatch_existing
STEP_44 Prepare final status.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_45 Emit next action.
NEXT_ACTION=User can write devam et; ChatGPT will inspect ai-results and schedule the next runner task.
STEP_46 No live repair performed.
LIVE_REPAIR=NOT_PERFORMED
STEP_47 No data download performed.
DATA_DOWNLOAD=NOT_PERFORMED
STEP_48 No Docker or service restart performed.
SERVICE_RESTART=NOT_PERFORMED
STEP_49 No Google scrape/cache/rehost performed.
EXTERNAL_SCRAPE=NOT_PERFORMED
STEP_50 Complete.
TERRAYIELD_135_DONE

## Run 136 if available
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-136-security-accuracy-expansion-parallel-deepening
MODE=parallel_scope_only_deepening
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Check repo root.
STEP_002 Read-only live baseline before deepening.
powershell : Export-Csv : İşlem, başka bir işlem tarafından kullanıldığından 'C:\Users\cagda\Documents\GitHub\AAYS\secu
rity_accuracy
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_136_security_accuracy_expansion_parallel_deepen
ing.ps1:41 char:20
+ ... = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $Live ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Export-Csv : İş...curity_accuracy:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
_expansion\audit\verify_live_modules_20260507_224421.csv' dosyasına erişemiyor.
At C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1:46 char:11
+ $report | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $ ...
+           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : OpenError: (:) [Export-Csv], IOException
    + FullyQualifiedErrorId : FileOpenFailure,Microsoft.PowerShell.Commands.ExportCsvCommand
 

LIVE_BASELINE_BEFORE=UNKNOWN
STEP_003 Snapshot protected live file hashes, read-only.
PROTECTED_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
PROTECTED_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
PROTECTED_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
PROTECTED_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
PROTECTED_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
PROTECTED_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_004 Prepare parallel workstream definitions.
STEP_005 Start parallel generation jobs.
STEP_006 Wait for parallel workstreams.
JOB_DONE=catalog FILES=3
JOB_DONE=methodology FILES=4
JOB_DONE=qa FILES=3
JOB_DONE=schemas FILES=2
JOB_DONE=audit FILES=3
JOB_DONE=run_evidence FILES=3
STEP_007 Write protected hash snapshot CSV after jobs.
WROTE=security_accuracy_expansion/audit/protected_live_hash_snapshot_20260507.csv
STEP_008 Write orchestration report.
WROTE=security_accuracy_expansion/run_reports/parallel_deepening_report_20260507_224421.md
STEP_009 Run local generated scope verifier if available.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_010 Run live verifier after deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224424.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_011 Verify no protected live diff.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_012 Generate manifest of deepening artifacts.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_deepening_20260507.csv
STEP_013 Run 100 lightweight static checks.
STATIC_CHECK_001=PASS
STATIC_CHECK_002=PASS
STATIC_CHECK_003=PASS
STATIC_CHECK_004=PASS
STATIC_CHECK_005=PASS
STATIC_CHECK_006=PASS
STATIC_CHECK_007=PASS
STATIC_CHECK_008=PASS
STATIC_CHECK_009=PASS
STATIC_CHECK_010=PASS
STATIC_CHECK_011=PASS
STATIC_CHECK_012=PASS
STATIC_CHECK_013=PASS
STATIC_CHECK_014=PASS
STATIC_CHECK_015=PASS
STATIC_CHECK_016=PASS
STATIC_CHECK_017=PASS
STATIC_CHECK_018=PASS
STATIC_CHECK_019=PASS
STATIC_CHECK_020=PASS
STATIC_CHECK_021=PASS
STATIC_CHECK_022=PASS
STATIC_CHECK_023=PASS
STATIC_CHECK_024=PASS
STATIC_CHECK_025=PASS
STATIC_CHECK_026=PASS
STATIC_CHECK_027=PASS
STATIC_CHECK_028=PASS
STATIC_CHECK_029=PASS
STATIC_CHECK_030=PASS
STATIC_CHECK_031=PASS
STATIC_CHECK_032=PASS
STATIC_CHECK_033=PASS
STATIC_CHECK_034=PASS
STATIC_CHECK_035=PASS
STATIC_CHECK_036=PASS
STATIC_CHECK_037=PASS
STATIC_CHECK_038=PASS
STATIC_CHECK_039=PASS
STATIC_CHECK_040=PASS
STATIC_CHECK_041=PASS
STATIC_CHECK_042=PASS
STATIC_CHECK_043=PASS
STATIC_CHECK_044=PASS
STATIC_CHECK_045=PASS
STATIC_CHECK_046=PASS
STATIC_CHECK_047=PASS
STATIC_CHECK_048=PASS
STATIC_CHECK_049=PASS
STATIC_CHECK_050=PASS
STATIC_CHECK_051=PASS
STATIC_CHECK_052=PASS
STATIC_CHECK_053=PASS
STATIC_CHECK_054=PASS
STATIC_CHECK_055=PASS
STATIC_CHECK_056=PASS
STATIC_CHECK_057=PASS
STATIC_CHECK_058=PASS
STATIC_CHECK_059=PASS
STATIC_CHECK_060=PASS
STATIC_CHECK_061=PASS
STATIC_CHECK_062=PASS
STATIC_CHECK_063=PASS
STATIC_CHECK_064=PASS
STATIC_CHECK_065=PASS
STATIC_CHECK_066=PASS
STATIC_CHECK_067=PASS
STATIC_CHECK_068=PASS
STATIC_CHECK_069=PASS
STATIC_CHECK_070=PASS
STATIC_CHECK_071=PASS
STATIC_CHECK_072=PASS
STATIC_CHECK_073=PASS
STATIC_CHECK_074=PASS
STATIC_CHECK_075=PASS
STATIC_CHECK_076=PASS
STATIC_CHECK_077=PASS
STATIC_CHECK_078=PASS
STATIC_CHECK_079=PASS
STATIC_CHECK_080=PASS
STATIC_CHECK_081=PASS
STATIC_CHECK_082=PASS
STATIC_CHECK_083=PASS
STATIC_CHECK_084=PASS
STATIC_CHECK_085=PASS
STATIC_CHECK_086=PASS
STATIC_CHECK_087=PASS
STATIC_CHECK_088=PASS
STATIC_CHECK_089=PASS
STATIC_CHECK_090=PASS
STATIC_CHECK_091=PASS
STATIC_CHECK_092=PASS
STATIC_CHECK_093=PASS
STATIC_CHECK_094=PASS
STATIC_CHECK_095=PASS
STATIC_CHECK_096=PASS
STATIC_CHECK_097=PASS
STATIC_CHECK_098=PASS
STATIC_CHECK_099=PASS
STATIC_CHECK_100=PASS
STEP_014 Write static check summary.
WROTE=security_accuracy_expansion/run_reports/static_check_summary_20260507_224421.md
STEP_015 Optional project commit guarded to security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH root=C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_016 Continuation marker; scope-only deepening remains active.
STEP_017 Continuation marker; scope-only deepening remains active.
STEP_018 Continuation marker; scope-only deepening remains active.
STEP_019 Continuation marker; scope-only deepening remains active.
STEP_020 Continuation marker; scope-only deepening remains active.
STEP_021 Continuation marker; scope-only deepening remains active.
STEP_022 Continuation marker; scope-only deepening remains active.
STEP_023 Continuation marker; scope-only deepening remains active.
STEP_024 Continuation marker; scope-only deepening remains active.
STEP_025 Continuation marker; scope-only deepening remains active.
STEP_026 Continuation marker; scope-only deepening remains active.
STEP_027 Continuation marker; scope-only deepening remains active.
STEP_028 Continuation marker; scope-only deepening remains active.
STEP_029 Continuation marker; scope-only deepening remains active.
STEP_030 Continuation marker; scope-only deepening remains active.
STEP_031 Continuation marker; scope-only deepening remains active.
STEP_032 Continuation marker; scope-only deepening remains active.
STEP_033 Continuation marker; scope-only deepening remains active.
STEP_034 Continuation marker; scope-only deepening remains active.
STEP_035 Continuation marker; scope-only deepening remains active.
STEP_036 Continuation marker; scope-only deepening remains active.
STEP_037 Continuation marker; scope-only deepening remains active.
STEP_038 Continuation marker; scope-only deepening remains active.
STEP_039 Continuation marker; scope-only deepening remains active.
STEP_040 Continuation marker; scope-only deepening remains active.
STEP_041 Continuation marker; scope-only deepening remains active.
STEP_042 Continuation marker; scope-only deepening remains active.
STEP_043 Continuation marker; scope-only deepening remains active.
STEP_044 Continuation marker; scope-only deepening remains active.
STEP_045 Continuation marker; scope-only deepening remains active.
STEP_046 Continuation marker; scope-only deepening remains active.
STEP_047 Continuation marker; scope-only deepening remains active.
STEP_048 Continuation marker; scope-only deepening remains active.
STEP_049 Continuation marker; scope-only deepening remains active.
STEP_050 Continuation marker; scope-only deepening remains active.
STEP_051 Continuation marker; scope-only deepening remains active.
STEP_052 Continuation marker; scope-only deepening remains active.
STEP_053 Continuation marker; scope-only deepening remains active.
STEP_054 Continuation marker; scope-only deepening remains active.
STEP_055 Continuation marker; scope-only deepening remains active.
STEP_056 Continuation marker; scope-only deepening remains active.
STEP_057 Continuation marker; scope-only deepening remains active.
STEP_058 Continuation marker; scope-only deepening remains active.
STEP_059 Continuation marker; scope-only deepening remains active.
STEP_060 Continuation marker; scope-only deepening remains active.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_136_DONE

## Validation
LIVE_DIFF_AFTER=
LIVE_DIFF_STATUS=PASS
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224426.csv

OVERALL=FAIL

LIVE_STATUS=FAIL
## Report
WROTE=security_accuracy_expansion/run_reports/compact_probe_resume_20260507_224415.md
## Guarded project commit
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_138_DONE

RUN_PRIOR_END=terrayield_138_security_expansion_probe_resume_compact.ps1
STEP_003 Prepare 12 parallel mega workstreams.
STEP_004 Launch parallel workstreams.
WORKSTREAM_DONE=source_catalog_pack FILES=2
powershell : Exception calling "WriteAllText" with "3" argument(s): "İşlem, başka bir işlem tarafından kullanıldığından
 'C:\Users\ca
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_145_security_accuracy_expansion_ultra_scope_pac
k.ps1:43 char:75
+ ...  (RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $p }) ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Exception calli...an 'C:\Users\ca:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
gda\Documents\GitHub\AAYS\security_accuracy_expansion\mega_batch_20260507\evidence_model\parcel_evidence_lifecycle.md' 
dosyasına erişemiyor."
    + CategoryInfo          : NotSpecified: (:) [], MethodInvocationException
    + FullyQualifiedErrorId : IOException
    + PSComputerName        : localhost
 
WORKSTREAM_DONE=evidence_model_pack FILES=2
WORKSTREAM_DONE=schema_pack FILES=3
WORKSTREAM_DONE=qa_pack FILES=2
WORKSTREAM_DONE=method_pack FILES=3
WORKSTREAM_DONE=audit_pack FILES=2
WORKSTREAM_DONE=manifest_pack FILES=3
WORKSTREAM_DONE=rollback_pack FILES=2
WORKSTREAM_DONE=pass_fail_pack FILES=2
WORKSTREAM_DONE=review_pack FILES=2
WORKSTREAM_DONE=simulation_pack FILES=2
WORKSTREAM_DONE=dashboard_pack FILES=2
STEP_005 Write integrated index for mega batch.
WROTE=security_accuracy_expansion/mega_batch_20260507/MEGA_BATCH_INDEX.md
STEP_006 Run 250 static guard checks.
MEGA_STATIC_CHECK_001=PASS
MEGA_STATIC_CHECK_002=PASS
MEGA_STATIC_CHECK_003=PASS
MEGA_STATIC_CHECK_004=PASS
MEGA_STATIC_CHECK_005=PASS
MEGA_STATIC_CHECK_006=PASS
MEGA_STATIC_CHECK_007=PASS
MEGA_STATIC_CHECK_008=PASS
MEGA_STATIC_CHECK_009=PASS
MEGA_STATIC_CHECK_010=PASS
MEGA_STATIC_CHECK_011=PASS
MEGA_STATIC_CHECK_012=PASS
MEGA_STATIC_CHECK_013=PASS
MEGA_STATIC_CHECK_014=PASS
MEGA_STATIC_CHECK_015=PASS
MEGA_STATIC_CHECK_016=PASS
MEGA_STATIC_CHECK_017=PASS
MEGA_STATIC_CHECK_018=PASS
MEGA_STATIC_CHECK_019=PASS
MEGA_STATIC_CHECK_020=PASS
MEGA_STATIC_CHECK_021=PASS
MEGA_STATIC_CHECK_022=PASS
MEGA_STATIC_CHECK_023=PASS
MEGA_STATIC_CHECK_024=PASS
MEGA_STATIC_CHECK_025=PASS
MEGA_STATIC_CHECK_026=PASS
MEGA_STATIC_CHECK_027=PASS
MEGA_STATIC_CHECK_028=PASS
MEGA_STATIC_CHECK_029=PASS
MEGA_STATIC_CHECK_030=PASS
MEGA_STATIC_CHECK_031=PASS
MEGA_STATIC_CHECK_032=PASS
MEGA_STATIC_CHECK_033=PASS
MEGA_STATIC_CHECK_034=PASS
MEGA_STATIC_CHECK_035=PASS
MEGA_STATIC_CHECK_036=PASS
MEGA_STATIC_CHECK_037=PASS
MEGA_STATIC_CHECK_038=PASS
MEGA_STATIC_CHECK_039=PASS
MEGA_STATIC_CHECK_040=PASS
MEGA_STATIC_CHECK_041=PASS
MEGA_STATIC_CHECK_042=PASS
MEGA_STATIC_CHECK_043=PASS
MEGA_STATIC_CHECK_044=PASS
MEGA_STATIC_CHECK_045=PASS
MEGA_STATIC_CHECK_046=PASS
MEGA_STATIC_CHECK_047=PASS
MEGA_STATIC_CHECK_048=PASS
MEGA_STATIC_CHECK_049=PASS
MEGA_STATIC_CHECK_050=PASS
MEGA_STATIC_CHECK_051=PASS
MEGA_STATIC_CHECK_052=PASS
MEGA_STATIC_CHECK_053=PASS
MEGA_STATIC_CHECK_054=PASS
MEGA_STATIC_CHECK_055=PASS
MEGA_STATIC_CHECK_056=PASS
MEGA_STATIC_CHECK_057=PASS
MEGA_STATIC_CHECK_058=PASS
MEGA_STATIC_CHECK_059=PASS
MEGA_STATIC_CHECK_060=PASS
MEGA_STATIC_CHECK_061=PASS
MEGA_STATIC_CHECK_062=PASS
MEGA_STATIC_CHECK_063=PASS
MEGA_STATIC_CHECK_064=PASS
MEGA_STATIC_CHECK_065=PASS
MEGA_STATIC_CHECK_066=PASS
MEGA_STATIC_CHECK_067=PASS
MEGA_STATIC_CHECK_068=PASS
MEGA_STATIC_CHECK_069=PASS
MEGA_STATIC_CHECK_070=PASS
MEGA_STATIC_CHECK_071=PASS
MEGA_STATIC_CHECK_072=PASS
MEGA_STATIC_CHECK_073=PASS
MEGA_STATIC_CHECK_074=PASS
MEGA_STATIC_CHECK_075=PASS
MEGA_STATIC_CHECK_076=PASS
MEGA_STATIC_CHECK_077=PASS
MEGA_STATIC_CHECK_078=PASS
MEGA_STATIC_CHECK_079=PASS
MEGA_STATIC_CHECK_080=PASS
MEGA_STATIC_CHECK_081=PASS
MEGA_STATIC_CHECK_082=PASS
MEGA_STATIC_CHECK_083=PASS
MEGA_STATIC_CHECK_084=PASS
MEGA_STATIC_CHECK_085=PASS
MEGA_STATIC_CHECK_086=PASS
MEGA_STATIC_CHECK_087=PASS
MEGA_STATIC_CHECK_088=PASS
MEGA_STATIC_CHECK_089=PASS
MEGA_STATIC_CHECK_090=PASS
MEGA_STATIC_CHECK_091=PASS
MEGA_STATIC_CHECK_092=PASS
MEGA_STATIC_CHECK_093=PASS
MEGA_STATIC_CHECK_094=PASS
MEGA_STATIC_CHECK_095=PASS
MEGA_STATIC_CHECK_096=PASS
MEGA_STATIC_CHECK_097=PASS
MEGA_STATIC_CHECK_098=PASS
MEGA_STATIC_CHECK_099=PASS
MEGA_STATIC_CHECK_100=PASS
MEGA_STATIC_CHECK_101=PASS
MEGA_STATIC_CHECK_102=PASS
MEGA_STATIC_CHECK_103=PASS
MEGA_STATIC_CHECK_104=PASS
MEGA_STATIC_CHECK_105=PASS
MEGA_STATIC_CHECK_106=PASS
MEGA_STATIC_CHECK_107=PASS
MEGA_STATIC_CHECK_108=PASS
MEGA_STATIC_CHECK_109=PASS
MEGA_STATIC_CHECK_110=PASS
MEGA_STATIC_CHECK_111=PASS
MEGA_STATIC_CHECK_112=PASS
MEGA_STATIC_CHECK_113=PASS
MEGA_STATIC_CHECK_114=PASS
MEGA_STATIC_CHECK_115=PASS
MEGA_STATIC_CHECK_116=PASS
MEGA_STATIC_CHECK_117=PASS
MEGA_STATIC_CHECK_118=PASS
MEGA_STATIC_CHECK_119=PASS
MEGA_STATIC_CHECK_120=PASS
MEGA_STATIC_CHECK_121=PASS
MEGA_STATIC_CHECK_122=PASS
MEGA_STATIC_CHECK_123=PASS
MEGA_STATIC_CHECK_124=PASS
MEGA_STATIC_CHECK_125=PASS
MEGA_STATIC_CHECK_126=PASS
MEGA_STATIC_CHECK_127=PASS
MEGA_STATIC_CHECK_128=PASS
MEGA_STATIC_CHECK_129=PASS
MEGA_STATIC_CHECK_130=PASS
MEGA_STATIC_CHECK_131=PASS
MEGA_STATIC_CHECK_132=PASS
MEGA_STATIC_CHECK_133=PASS
MEGA_STATIC_CHECK_134=PASS
MEGA_STATIC_CHECK_135=PASS
MEGA_STATIC_CHECK_136=PASS
MEGA_STATIC_CHECK_137=PASS
MEGA_STATIC_CHECK_138=PASS
MEGA_STATIC_CHECK_139=PASS
MEGA_STATIC_CHECK_140=PASS
MEGA_STATIC_CHECK_141=PASS
MEGA_STATIC_CHECK_142=PASS
MEGA_STATIC_CHECK_143=PASS
MEGA_STATIC_CHECK_144=PASS
MEGA_STATIC_CHECK_145=PASS
MEGA_STATIC_CHECK_146=PASS
MEGA_STATIC_CHECK_147=PASS
MEGA_STATIC_CHECK_148=PASS
MEGA_STATIC_CHECK_149=PASS
MEGA_STATIC_CHECK_150=PASS
MEGA_STATIC_CHECK_151=PASS
MEGA_STATIC_CHECK_152=PASS
MEGA_STATIC_CHECK_153=PASS
MEGA_STATIC_CHECK_154=PASS
MEGA_STATIC_CHECK_155=PASS
MEGA_STATIC_CHECK_156=PASS
MEGA_STATIC_CHECK_157=PASS
MEGA_STATIC_CHECK_158=PASS
MEGA_STATIC_CHECK_159=PASS
MEGA_STATIC_CHECK_160=PASS
MEGA_STATIC_CHECK_161=PASS
MEGA_STATIC_CHECK_162=PASS
MEGA_STATIC_CHECK_163=PASS
MEGA_STATIC_CHECK_164=PASS
MEGA_STATIC_CHECK_165=PASS
MEGA_STATIC_CHECK_166=PASS
MEGA_STATIC_CHECK_167=PASS
MEGA_STATIC_CHECK_168=PASS
MEGA_STATIC_CHECK_169=PASS
MEGA_STATIC_CHECK_170=PASS
MEGA_STATIC_CHECK_171=PASS
MEGA_STATIC_CHECK_172=PASS
MEGA_STATIC_CHECK_173=PASS
MEGA_STATIC_CHECK_174=PASS
MEGA_STATIC_CHECK_175=PASS
MEGA_STATIC_CHECK_176=PASS
MEGA_STATIC_CHECK_177=PASS
MEGA_STATIC_CHECK_178=PASS
MEGA_STATIC_CHECK_179=PASS
MEGA_STATIC_CHECK_180=PASS
MEGA_STATIC_CHECK_181=PASS
MEGA_STATIC_CHECK_182=PASS
MEGA_STATIC_CHECK_183=PASS
MEGA_STATIC_CHECK_184=PASS
MEGA_STATIC_CHECK_185=PASS
MEGA_STATIC_CHECK_186=PASS
MEGA_STATIC_CHECK_187=PASS
MEGA_STATIC_CHECK_188=PASS
MEGA_STATIC_CHECK_189=PASS
MEGA_STATIC_CHECK_190=PASS
MEGA_STATIC_CHECK_191=PASS
MEGA_STATIC_CHECK_192=PASS
MEGA_STATIC_CHECK_193=PASS
MEGA_STATIC_CHECK_194=PASS
MEGA_STATIC_CHECK_195=PASS
MEGA_STATIC_CHECK_196=PASS
MEGA_STATIC_CHECK_197=PASS
MEGA_STATIC_CHECK_198=PASS
MEGA_STATIC_CHECK_199=PASS
MEGA_STATIC_CHECK_200=PASS
MEGA_STATIC_CHECK_201=PASS
MEGA_STATIC_CHECK_202=PASS
MEGA_STATIC_CHECK_203=PASS
MEGA_STATIC_CHECK_204=PASS
MEGA_STATIC_CHECK_205=PASS
MEGA_STATIC_CHECK_206=PASS
MEGA_STATIC_CHECK_207=PASS
MEGA_STATIC_CHECK_208=PASS
MEGA_STATIC_CHECK_209=PASS
MEGA_STATIC_CHECK_210=PASS
MEGA_STATIC_CHECK_211=PASS
MEGA_STATIC_CHECK_212=PASS
MEGA_STATIC_CHECK_213=PASS
MEGA_STATIC_CHECK_214=PASS
MEGA_STATIC_CHECK_215=PASS
MEGA_STATIC_CHECK_216=PASS
MEGA_STATIC_CHECK_217=PASS
MEGA_STATIC_CHECK_218=PASS
MEGA_STATIC_CHECK_219=PASS
MEGA_STATIC_CHECK_220=PASS
MEGA_STATIC_CHECK_221=PASS
MEGA_STATIC_CHECK_222=PASS
MEGA_STATIC_CHECK_223=PASS
MEGA_STATIC_CHECK_224=PASS
MEGA_STATIC_CHECK_225=PASS
MEGA_STATIC_CHECK_226=PASS
MEGA_STATIC_CHECK_227=PASS
MEGA_STATIC_CHECK_228=PASS
MEGA_STATIC_CHECK_229=PASS
MEGA_STATIC_CHECK_230=PASS
MEGA_STATIC_CHECK_231=PASS
MEGA_STATIC_CHECK_232=PASS
MEGA_STATIC_CHECK_233=PASS
MEGA_STATIC_CHECK_234=PASS
MEGA_STATIC_CHECK_235=PASS
MEGA_STATIC_CHECK_236=PASS
MEGA_STATIC_CHECK_237=PASS
MEGA_STATIC_CHECK_238=PASS
MEGA_STATIC_CHECK_239=PASS
MEGA_STATIC_CHECK_240=PASS
MEGA_STATIC_CHECK_241=PASS
MEGA_STATIC_CHECK_242=PASS
MEGA_STATIC_CHECK_243=PASS
MEGA_STATIC_CHECK_244=PASS
MEGA_STATIC_CHECK_245=PASS
MEGA_STATIC_CHECK_246=PASS
MEGA_STATIC_CHECK_247=PASS
MEGA_STATIC_CHECK_248=PASS
MEGA_STATIC_CHECK_249=PASS
MEGA_STATIC_CHECK_250=PASS
STEP_007 Create artifact manifest.
WROTE=security_accuracy_expansion/mega_batch_20260507/MEGA_BATCH_ARTIFACT_MANIFEST.csv
STEP_008 Run verifiers.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS


component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224432.csv

OVERALL=FAIL

SCOPE_STATUS=PASS
LIVE_STATUS=FAIL
STEP_009 Final live diff guard.
LIVE_DIFF_FINAL=
LIVE_DIFF_FINAL_STATUS=PASS
STEP_010 Write final mega report.
WROTE=security_accuracy_expansion/run_reports/mega_batch_final_report_20260507_224403.md
STEP_011 Guarded commit security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_012 Complete.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_143_DONE

RESUME_END=terrayield_143_security_accuracy_expansion_mega_batch.ps1
RESUME_BEGIN=terrayield_144_security_mega_watchdog_materializer.ps1
PROJECT=terrayield
TASK=terrayield-144-security-mega-watchdog-materializer
MODE=watchdog_materializer_scope_only
LIVE_WRITE_POLICY=FORBIDDEN
NO_DOWNLOAD=TRUE
NO_SERVICE_RESTART=TRUE
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
BRIDGE_ROOT=C:\Users\cagda\Documents\chat_gpt_clone_1
STEP_01_LIVE_DIFF_BEFORE
LIVE_DIFF_BEFORE=
LIVE_DIFF_BEFORE_STATUS=PASS
STEP_02_RESUME_143_IF_PRESENT
RUN_143_BEGIN
PROJECT=terrayield
TASK=terrayield-143-security-accuracy-expansion-mega-batch
MODE=mega_batch_scope_only_security_accuracy_expansion
LIVE_WRITE_POLICY=FORBIDDEN
NO_DOWNLOAD=TRUE
NO_SERVICE_RESTART=TRUE
NO_DOCKER=TRUE
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Preflight repo and protected live diff.
LIVE_DIFF_INITIAL=
LIVE_DIFF_INITIAL_STATUS=PASS
STEP_002 Run prior security scope scripts if available.
RUN_PRIOR_BEGIN=terrayield_135_security_accuracy_expansion_direct_apply.ps1
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-135-security-accuracy-expansion-direct-apply
MODE=direct_scope_only_security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
STEP_01 Check AAYS repo root exists.
STEP_02 Create allowed root only.
STEP_03 Read git root without modifying files.
GIT_ROOT_RAW=C:/Users/cagda
STEP_04 Capture live baseline before generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224434.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_05 Record current live surface hashes for diagnostic only.
LIVE_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
LIVE_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
LIVE_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
LIVE_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
LIVE_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
LIVE_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_06 Define generated file set.
STEP_07 Write generated files under allowed root.
WROTE=security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
WROTE=security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
WROTE=security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
WROTE=security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
WROTE=security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
WROTE=security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
WROTE=security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
WROTE=security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
WROTE=security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\download_audit_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\run_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
WROTE=security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
WROTE=security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
STEP_08 Create run report directory.
STEP_09 Create generated artifact manifest after file writes.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_20260507.csv
STEP_10 Create execution state from previous user logs.
STEP_11 Run generated scope verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS
STEP_12 Run 50-step workflow with live blocker allowance.
WORKFLOW_STEP_01=PASS scope-only guard
WORKFLOW_STEP_02=PASS scope-only guard
WORKFLOW_STEP_03=PASS scope-only guard
WORKFLOW_STEP_04=PASS scope-only guard
WORKFLOW_STEP_05=PASS scope-only guard
WORKFLOW_STEP_06=PASS scope-only guard
WORKFLOW_STEP_07=PASS scope-only guard
WORKFLOW_STEP_08=PASS scope-only guard
WORKFLOW_STEP_09=PASS scope-only guard
WORKFLOW_STEP_10=PASS scope-only guard
WORKFLOW_STEP_11=PASS scope-only guard
WORKFLOW_STEP_12=PASS scope-only guard
WORKFLOW_STEP_13=PASS scope-only guard
WORKFLOW_STEP_14=PASS scope-only guard
WORKFLOW_STEP_15=PASS scope-only guard
WORKFLOW_STEP_16=PASS scope-only guard
WORKFLOW_STEP_17=PASS scope-only guard
WORKFLOW_STEP_18=PASS scope-only guard
WORKFLOW_STEP_19=PASS scope-only guard
WORKFLOW_STEP_20=PASS scope-only guard
WORKFLOW_STEP_21=PASS scope-only guard
WORKFLOW_STEP_22=PASS scope-only guard
WORKFLOW_STEP_23=PASS scope-only guard
WORKFLOW_STEP_24=PASS scope-only guard
WORKFLOW_STEP_25=PASS scope-only guard
WORKFLOW_STEP_26=PASS scope-only guard
WORKFLOW_STEP_27=PASS scope-only guard
WORKFLOW_STEP_28=PASS scope-only guard
WORKFLOW_STEP_29=PASS scope-only guard
WORKFLOW_STEP_30=PASS scope-only guard
WORKFLOW_STEP_31=PASS scope-only guard
WORKFLOW_STEP_32=PASS scope-only guard
WORKFLOW_STEP_33=PASS scope-only guard
WORKFLOW_STEP_34=PASS scope-only guard
WORKFLOW_STEP_35=PASS scope-only guard
WORKFLOW_STEP_36=PASS scope-only guard
WORKFLOW_STEP_37=PASS scope-only guard
WORKFLOW_STEP_38=PASS scope-only guard
WORKFLOW_STEP_39=PASS scope-only guard
WORKFLOW_STEP_40=PASS scope-only guard
WORKFLOW_STEP_41=PASS scope-only guard
WORKFLOW_STEP_42=PASS scope-only guard
WORKFLOW_STEP_43=PASS scope-only guard
WORKFLOW_STEP_44=PASS scope-only guard
WORKFLOW_STEP_45=PASS scope-only guard
WORKFLOW_STEP_46=PASS scope-only guard
WORKFLOW_STEP_47=PASS scope-only guard
WORKFLOW_STEP_48=PASS scope-only guard
WORKFLOW_STEP_49=PASS scope-only guard
WORKFLOW_STEP_50=PASS scope-only guard

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224436.csv

OVERALL=FAIL

WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER

WORKFLOW_STATUS_DETECTED=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_13 Run live verifier after generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224437.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_14 Diagnose index hash blocker if still failing.
DIAG=live_index_hash_fail
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
INDEX_EXISTS=True
INDEX_SHA256_ACTUAL=CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
INDEX_LENGTH_BYTES=14698
INDEX_LAST_WRITE=2026-05-07T20:09:28
BASELINE_EXISTS=True


component     : index_html
path          : C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html
sha256        : F6B308733D50EFE1A7608F126BE5C7441DCAA694146E503858A4BF722485B858
role          : active_loader
data_url      : n/a
feature_count : n/a




ACTION=No file modified; diagnostic only.

STEP_15 Diagnose git root.
DIAG=git_root
GIT_ROOT=C:/Users/cagda
STATUS_AAYS_SECURITY_ONLY_BEGIN
?? security_accuracy_expansion/

STATUS_AAYS_SECURITY_ONLY_END
STATUS_LIVE_SURFACE_BEGIN
?? england_map_web/

STATUS_LIVE_SURFACE_END

STEP_16 Check live diff after generation.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_17 Create local run report.
REPORT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224434.md
STEP_18 List generated security files.
security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
security_accuracy_expansion\audit\generated_artifact_manifest_20260507.csv
security_accuracy_expansion\audit\generated_artifact_manifest_deepening_20260507.csv
security_accuracy_expansion\audit\LIVE_SURFACE_PROTECTION_POLICY_20260507.md
security_accuracy_expansion\audit\live_surface_hashes_20260507.csv
security_accuracy_expansion\audit\PARALLEL_DEEPENING_AUDIT_NOTES_20260507.md
security_accuracy_expansion\audit\preflight_audit_20260507.md
security_accuracy_expansion\audit\protected_live_hash_snapshot_20260507.csv
security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
security_accuracy_expansion\audit\verify_live_modules_20260507_182636.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_200601.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202319.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202322.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_203016.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211726.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211729.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211730.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211910.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211913.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211914.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212054.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212057.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212058.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212501.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212503.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212506.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212507.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212508.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212513.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212517.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212519.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224405.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224411.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224414.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224416.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224418.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224419.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224421.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224424.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224426.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224432.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224434.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224436.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224437.csv
security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1
security_accuracy_expansion\codex_tasks\047_security_accuracy_source_catalog_and_evidence_templates.md
security_accuracy_expansion\codex_tasks\048_security_accuracy_preflight_download_plan.md
security_accuracy_expansion\codex_tasks\049_security_accuracy_evidence_backed_scoring_plan.md
security_accuracy_expansion\deepening_20260507\source_catalog\official_source_candidate_pack.json
security_accuracy_expansion\deepening_20260507\source_catalog\source_tier_rubric.md
security_accuracy_expansion\deepening_20260507\source_catalog\source_triage_queue.csv
security_accuracy_expansion\evidence_templates\cross_source_agreement_template.csv
security_accuracy_expansion\evidence_templates\evidence_quality_rubric_template.json
security_accuracy_expansion\evidence_templates\parcel_match_audit_template.csv
security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json
security_accuracy_expansion\evidence_templates\run_manifest_template.json
security_accuracy_expansion\evidence_templates\source_conflict_record_template.json
security_accuracy_expansion\evidence_templates\source_download_audit_template.csv
security_accuracy_expansion\evidence_templates\source_evidence_template.json
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
security_accuracy_expansion\frontend\frontend_integration_spec.md
security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
security_accuracy_expansion\mega_batch_20260507\audit\audit_event_types.csv
security_accuracy_expansion\mega_batch_20260507\audit\audit_log_template.jsonl
security_accuracy_expansion\mega_batch_20260507\dashboard\README_STATUS_BOARD.md
security_accuracy_expansion\mega_batch_20260507\dashboard\status_board_template.csv
security_accuracy_expansion\mega_batch_20260507\evidence_model\evidence_conflict_taxonomy.csv
security_accuracy_expansion\mega_batch_20260507\evidence_model\parcel_evidence_lifecycle.md
security_accuracy_expansion\mega_batch_20260507\manifests\download_manifest_blank.json
security_accuracy_expansion\mega_batch_20260507\manifests\promotion_manifest_disabled.json
security_accuracy_expansion\mega_batch_20260507\manifests\run_manifest_blank.json
security_accuracy_expansion\mega_batch_20260507\MEGA_BATCH_ARTIFACT_MANIFEST.csv
security_accuracy_expansion\mega_batch_20260507\MEGA_BATCH_INDEX.md
security_accuracy_expansion\mega_batch_20260507\methodology\15_no_live_mutation_publication_gate.md
security_accuracy_expansion\mega_batch_20260507\methodology\16_source_conflict_resolution.md
security_accuracy_expansion\mega_batch_20260507\methodology\17_parcel_review_sampling.md
security_accuracy_expansion\mega_batch_20260507\pass_fail\fail_fast_conditions.md
security_accuracy_expansion\mega_batch_20260507\pass_fail\pass_summary_template.md
security_accuracy_expansion\mega_batch_20260507\qa\qa_master_gate_matrix.csv
security_accuracy_expansion\mega_batch_20260507\qa\qa_operator_checklist.md
security_accuracy_expansion\mega_batch_20260507\review\review_questions.csv
security_accuracy_expansion\mega_batch_20260507\review\reviewer_handoff.md
security_accuracy_expansion\mega_batch_20260507\rollback\rollback_inventory_template.csv
security_accuracy_expansion\mega_batch_20260507\rollback\rollback_scope_only_playbook.md
security_accuracy_expansion\mega_batch_20260507\schemas\evidence_conflict_schema.json
security_accuracy_expansion\mega_batch_20260507\schemas\promotion_proposal_schema.json
security_accuracy_expansion\mega_batch_20260507\schemas\source_registry_extended_schema.json
security_accuracy_expansion\mega_batch_20260507\simulation\dry_run_output_contract.json
security_accuracy_expansion\mega_batch_20260507\simulation\dry_run_plan.md
security_accuracy_expansion\mega_batch_20260507\source_catalog\source_registry_extended.json
security_accuracy_expansion\mega_batch_20260507\source_catalog\source_registry_review_notes.md
security_accuracy_expansion\methodology\01_security_accuracy_expansion_plan.md
security_accuracy_expansion\methodology\03_methodology_and_confidence_model.md
security_accuracy_expansion\methodology\07_risk_limits_and_language.md
security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
security_accuracy_expansion\methodology\11_source_rank_and_triage_model.md
security_accuracy_expansion\methodology\12_spatial_join_accuracy_protocol.md
security_accuracy_expansion\methodology\13_temporal_refresh_protocol.md
security_accuracy_expansion\methodology\14_confidence_without_score_mutation.md
security_accuracy_expansion\methodology\README_upstream.md
security_accuracy_expansion\PASS_FAIL_20260507.md
security_accuracy_expansion\prompts\CHATGPT_FOLLOWUP_PROMPTS.md
security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md
security_accuracy_expansion\prompts\CODEX_MASTER_PROMPT_SECURITY_ACCURACY_EXPANSION.md
security_accuracy_expansion\prompts\SHORT_CODEX_PROMPT.md
security_accuracy_expansion\qa\acceptance_criteria.md
security_accuracy_expansion\qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md
security_accuracy_expansion\qa\expected_outputs_checklist.md
security_accuracy_expansion\qa\NO_LIVE_TOUCH_ASSERTIONS_20260507.md
security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_MATRIX_SECURITY_ACCURACY_EXPANSION_20260507.csv
security_accuracy_expansion\qa\REVIEW_PROMOTION_GATES_20260507.md
security_accuracy_expansion\README_RUN_TR.md
security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
security_accuracy_expansion\rollback\ROLLBACK_TR.md
security_accuracy_expansion\run_manifests\security_accuracy_expansion_deepening_run_20260507.example.json
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212456.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212501.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_224415.md
security_accuracy_expansion\run_reports\mega_batch_final_report_20260507_224403.md
security_accuracy_expansion\run_reports\mega_batch_final_report_20260507_224404.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_212512.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224411.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224421.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211725.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211908.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212053.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212456.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224404.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224416.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224434.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_212512.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224411.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224421.md
security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
security_accuracy_expansion\schemas\download_audit_manifest_schema.json
security_accuracy_expansion\schemas\evidence_quality_rubric_schema.json
security_accuracy_expansion\schemas\parcel_security_evidence_schema.json
security_accuracy_expansion\schemas\qa_matrix_schema.json
security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
security_accuracy_expansion\schemas\run_manifest_schema.json
security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
security_accuracy_expansion\source_catalog\official_security_source_catalog.json
security_accuracy_expansion\source_catalog\source_evidence_matrix.csv
security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
STEP_19 Show security_accuracy_expansion git status.
?? security_accuracy_expansion/

STEP_20 Show england_map_web git status only.
?? england_map_web/

STEP_21 Evaluate protected path write guard.
PROTECTED_PATH_GUARD=PASS
STEP_22 Check generated root guard.
GENERATED_ROOT_GUARD=PASS
STEP_23 Do not push AAYS project repo automatically.
AAYS_PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_24 Commit AAYS project only if git root equals repo root and only security files are staged.
AAYS_GIT_ROOT_OK=FAIL_OR_DIFFERENT
AAYS_COMMIT=SKIPPED_TO_AVOID_WRONG_REPO
STEP_25 Confirm active score production untouched.
ACTIVE_SCORE_PRODUCTION=NOT_TOUCHED
STEP_26 Confirm active overlay assets untouched.
ACTIVE_OVERLAY_ASSETS=NOT_TOUCHED
STEP_27 Confirm active GeoJSON and JSON untouched.
ACTIVE_DATA_FILES=NOT_TOUCHED
STEP_28 Confirm source evidence examples generated.
SOURCE_EVIDENCE_EXAMPLES=GENERATED
STEP_29 Confirm download audit examples generated.
DOWNLOAD_AUDIT_EXAMPLES=GENERATED
STEP_30 Confirm run manifest examples generated.
RUN_MANIFEST_EXAMPLES=GENERATED
STEP_31 Confirm parcel evidence examples generated.
PARCEL_EVIDENCE_EXAMPLES=GENERATED
STEP_32 Confirm schemas generated.
SCHEMAS=GENERATED
STEP_33 Confirm methodology notes generated.
METHODOLOGY_NOTES=GENERATED
STEP_34 Confirm QA checklist generated.
QA_CHECKLIST=GENERATED
STEP_35 Confirm PASS/FAIL control list generated.
PASS_FAIL_CONTROL_LIST=GENERATED
STEP_36 Confirm rollback notes generated.
ROLLBACK_NOTES=GENERATED
STEP_37 Confirm audit diagnostics generated.
AUDIT_DIAGNOSTICS=GENERATED
STEP_38 Confirm runner continuation protocol generated.
RUNNER_CONTINUE_PROTOCOL=GENERATED
STEP_39 Confirm manifest CSV generated.
GENERATED_ARTIFACT_MANIFEST=GENERATED
STEP_40 Confirm workflow script generated.
SCOPE_ONLY_WORKFLOW=GENERATED
STEP_41 Re-check live diff remains empty.
LIVE_DIFF_RECHECK=PASS
STEP_42 Re-check generated verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_43 Mark known blocker if live baseline remains failed.
KNOWN_BLOCKER=index_html_hash_mismatch_existing
STEP_44 Prepare final status.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_45 Emit next action.
NEXT_ACTION=User can write devam et; ChatGPT will inspect ai-results and schedule the next runner task.
STEP_46 No live repair performed.
LIVE_REPAIR=NOT_PERFORMED
STEP_47 No data download performed.
DATA_DOWNLOAD=NOT_PERFORMED
STEP_48 No Docker or service restart performed.
SERVICE_RESTART=NOT_PERFORMED
STEP_49 No Google scrape/cache/rehost performed.
EXTERNAL_SCRAPE=NOT_PERFORMED
STEP_50 Complete.
TERRAYIELD_135_DONE

RUN_PRIOR_END=terrayield_135_security_accuracy_expansion_direct_apply.ps1
RUN_PRIOR_BEGIN=terrayield_136_security_accuracy_expansion_parallel_deepening.ps1
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-136-security-accuracy-expansion-parallel-deepening
MODE=parallel_scope_only_deepening
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Check repo root.
STEP_002 Read-only live baseline before deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224440.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_003 Snapshot protected live file hashes, read-only.
PROTECTED_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
PROTECTED_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
PROTECTED_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
PROTECTED_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
PROTECTED_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
PROTECTED_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_004 Prepare parallel workstream definitions.
STEP_005 Start parallel generation jobs.
STEP_006 Wait for parallel workstreams.
JOB_DONE=catalog FILES=3
JOB_DONE=methodology FILES=4
JOB_DONE=qa FILES=3
JOB_DONE=schemas FILES=2
JOB_DONE=audit FILES=3
JOB_DONE=run_evidence FILES=3
STEP_007 Write protected hash snapshot CSV after jobs.
WROTE=security_accuracy_expansion/audit/protected_live_hash_snapshot_20260507.csv
STEP_008 Write orchestration report.
WROTE=security_accuracy_expansion/run_reports/parallel_deepening_report_20260507_224439.md
STEP_009 Run local generated scope verifier if available.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_010 Run live verifier after deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224443.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_011 Verify no protected live diff.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_012 Generate manifest of deepening artifacts.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_deepening_20260507.csv
STEP_013 Run 100 lightweight static checks.
STATIC_CHECK_001=PASS
STATIC_CHECK_002=PASS
STATIC_CHECK_003=PASS
STATIC_CHECK_004=PASS
STATIC_CHECK_005=PASS
STATIC_CHECK_006=PASS
STATIC_CHECK_007=PASS
STATIC_CHECK_008=PASS
STATIC_CHECK_009=PASS
STATIC_CHECK_010=PASS
STATIC_CHECK_011=PASS
STATIC_CHECK_012=PASS
STATIC_CHECK_013=PASS
STATIC_CHECK_014=PASS
STATIC_CHECK_015=PASS
STATIC_CHECK_016=PASS
STATIC_CHECK_017=PASS
STATIC_CHECK_018=PASS
STATIC_CHECK_019=PASS
STATIC_CHECK_020=PASS
STATIC_CHECK_021=PASS
STATIC_CHECK_022=PASS
STATIC_CHECK_023=PASS
STATIC_CHECK_024=PASS
STATIC_CHECK_025=PASS
STATIC_CHECK_026=PASS
STATIC_CHECK_027=PASS
STATIC_CHECK_028=PASS
STATIC_CHECK_029=PASS
STATIC_CHECK_030=PASS
STATIC_CHECK_031=PASS
STATIC_CHECK_032=PASS
STATIC_CHECK_033=PASS
STATIC_CHECK_034=PASS
STATIC_CHECK_035=PASS
STATIC_CHECK_036=PASS
STATIC_CHECK_037=PASS
STATIC_CHECK_038=PASS
STATIC_CHECK_039=PASS
STATIC_CHECK_040=PASS
STATIC_CHECK_041=PASS
STATIC_CHECK_042=PASS
STATIC_CHECK_043=PASS
STATIC_CHECK_044=PASS
STATIC_CHECK_045=PASS
STATIC_CHECK_046=PASS
STATIC_CHECK_047=PASS
STATIC_CHECK_048=PASS
STATIC_CHECK_049=PASS
STATIC_CHECK_050=PASS
STATIC_CHECK_051=PASS
STATIC_CHECK_052=PASS
STATIC_CHECK_053=PASS
STATIC_CHECK_054=PASS
STATIC_CHECK_055=PASS
STATIC_CHECK_056=PASS
STATIC_CHECK_057=PASS
STATIC_CHECK_058=PASS
STATIC_CHECK_059=PASS
STATIC_CHECK_060=PASS
STATIC_CHECK_061=PASS
STATIC_CHECK_062=PASS
STATIC_CHECK_063=PASS
STATIC_CHECK_064=PASS
STATIC_CHECK_065=PASS
STATIC_CHECK_066=PASS
STATIC_CHECK_067=PASS
STATIC_CHECK_068=PASS
STATIC_CHECK_069=PASS
STATIC_CHECK_070=PASS
STATIC_CHECK_071=PASS
STATIC_CHECK_072=PASS
STATIC_CHECK_073=PASS
STATIC_CHECK_074=PASS
STATIC_CHECK_075=PASS
STATIC_CHECK_076=PASS
STATIC_CHECK_077=PASS
STATIC_CHECK_078=PASS
STATIC_CHECK_079=PASS
STATIC_CHECK_080=PASS
STATIC_CHECK_081=PASS
STATIC_CHECK_082=PASS
STATIC_CHECK_083=PASS
STATIC_CHECK_084=PASS
STATIC_CHECK_085=PASS
STATIC_CHECK_086=PASS
STATIC_CHECK_087=PASS
STATIC_CHECK_088=PASS
STATIC_CHECK_089=PASS
STATIC_CHECK_090=PASS
STATIC_CHECK_091=PASS
STATIC_CHECK_092=PASS
STATIC_CHECK_093=PASS
STATIC_CHECK_094=PASS
STATIC_CHECK_095=PASS
STATIC_CHECK_096=PASS
STATIC_CHECK_097=PASS
STATIC_CHECK_098=PASS
STATIC_CHECK_099=PASS
STATIC_CHECK_100=PASS
STEP_014 Write static check summary.
WROTE=security_accuracy_expansion/run_reports/static_check_summary_20260507_224439.md
STEP_015 Optional project commit guarded to security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH root=C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_016 Continuation marker; scope-only deepening remains active.
STEP_017 Continuation marker; scope-only deepening remains active.
STEP_018 Continuation marker; scope-only deepening remains active.
STEP_019 Continuation marker; scope-only deepening remains active.
STEP_020 Continuation marker; scope-only deepening remains active.
STEP_021 Continuation marker; scope-only deepening remains active.
STEP_022 Continuation marker; scope-only deepening remains active.
STEP_023 Continuation marker; scope-only deepening remains active.
STEP_024 Continuation marker; scope-only deepening remains active.
STEP_025 Continuation marker; scope-only deepening remains active.
STEP_026 Continuation marker; scope-only deepening remains active.
STEP_027 Continuation marker; scope-only deepening remains active.
STEP_028 Continuation marker; scope-only deepening remains active.
STEP_029 Continuation marker; scope-only deepening remains active.
STEP_030 Continuation marker; scope-only deepening remains active.
STEP_031 Continuation marker; scope-only deepening remains active.
STEP_032 Continuation marker; scope-only deepening remains active.
STEP_033 Continuation marker; scope-only deepening remains active.
STEP_034 Continuation marker; scope-only deepening remains active.
STEP_035 Continuation marker; scope-only deepening remains active.
STEP_036 Continuation marker; scope-only deepening remains active.
STEP_037 Continuation marker; scope-only deepening remains active.
STEP_038 Continuation marker; scope-only deepening remains active.
STEP_039 Continuation marker; scope-only deepening remains active.
STEP_040 Continuation marker; scope-only deepening remains active.
STEP_041 Continuation marker; scope-only deepening remains active.
STEP_042 Continuation marker; scope-only deepening remains active.
STEP_043 Continuation marker; scope-only deepening remains active.
STEP_044 Continuation marker; scope-only deepening remains active.
STEP_045 Continuation marker; scope-only deepening remains active.
STEP_046 Continuation marker; scope-only deepening remains active.
STEP_047 Continuation marker; scope-only deepening remains active.
STEP_048 Continuation marker; scope-only deepening remains active.
STEP_049 Continuation marker; scope-only deepening remains active.
STEP_050 Continuation marker; scope-only deepening remains active.
STEP_051 Continuation marker; scope-only deepening remains active.
STEP_052 Continuation marker; scope-only deepening remains active.
STEP_053 Continuation marker; scope-only deepening remains active.
STEP_054 Continuation marker; scope-only deepening remains active.
STEP_055 Continuation marker; scope-only deepening remains active.
STEP_056 Continuation marker; scope-only deepening remains active.
STEP_057 Continuation marker; scope-only deepening remains active.
STEP_058 Continuation marker; scope-only deepening remains active.
STEP_059 Continuation marker; scope-only deepening remains active.
STEP_060 Continuation marker; scope-only deepening remains active.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_136_DONE

RUN_PRIOR_END=terrayield_136_security_accuracy_expansion_parallel_deepening.ps1
RUN_PRIOR_BEGIN=terrayield_138_security_expansion_probe_resume_compact.ps1
PROJECT=terrayield
TASK=terrayield-138-security-expansion-probe-resume-compact
MODE=compact_probe_resume_scope_only
LIVE_WRITE_POLICY=FORBIDDEN
BRIDGE_ROOT=C:\Users\cagda\Documents\chat_gpt_clone_1
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
## Preflight
GIT_ROOT=C:/Users/cagda
LIVE_DIFF_BEFORE=
## Run 135 if available
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-135-security-accuracy-expansion-direct-apply
MODE=direct_scope_only_security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
STEP_01 Check AAYS repo root exists.
STEP_02 Create allowed root only.
STEP_03 Read git root without modifying files.
GIT_ROOT_RAW=C:/Users/cagda
STEP_04 Capture live baseline before generation.
powershell : Export-Csv : İşlem, başka bir işlem tarafından kullanıldığından 'C:\Users\cagda\Documents\GitHub\AAYS\secu
rity_accuracy
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_135_security_accuracy_expansion_direct_apply.ps
1:59 char:35
+ ... voke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $Live ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Export-Csv : İş...curity_accuracy:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
_expansion\audit\verify_live_modules_20260507_224445.csv' dosyasına erişemiyor.
At C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1:46 char:11
+ $report | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $ ...
+           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : OpenError: (:) [Export-Csv], IOException
    + FullyQualifiedErrorId : FileOpenFailure,Microsoft.PowerShell.Commands.ExportCsvCommand
 

LIVE_BASELINE_BEFORE=UNKNOWN
STEP_05 Record current live surface hashes for diagnostic only.
LIVE_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
LIVE_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
LIVE_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
LIVE_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
LIVE_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
LIVE_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_06 Define generated file set.
STEP_07 Write generated files under allowed root.
WROTE=security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
WROTE=security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
WROTE=security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
WROTE=security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
WROTE=security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
WROTE=security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
WROTE=security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
WROTE=security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
WROTE=security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
WROTE=security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
WROTE=security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
WROTE=security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\download_audit_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\run_manifest_schema.json
WROTE=security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
WROTE=security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
WROTE=security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
WROTE=security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
WROTE=security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
STEP_08 Create run report directory.
STEP_09 Create generated artifact manifest after file writes.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_20260507.csv
STEP_10 Create execution state from previous user logs.
STEP_11 Run generated scope verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS
STEP_12 Run 50-step workflow with live blocker allowance.
WORKFLOW_STEP_01=PASS scope-only guard
WORKFLOW_STEP_02=PASS scope-only guard
WORKFLOW_STEP_03=PASS scope-only guard
WORKFLOW_STEP_04=PASS scope-only guard
WORKFLOW_STEP_05=PASS scope-only guard
WORKFLOW_STEP_06=PASS scope-only guard
WORKFLOW_STEP_07=PASS scope-only guard
WORKFLOW_STEP_08=PASS scope-only guard
WORKFLOW_STEP_09=PASS scope-only guard
WORKFLOW_STEP_10=PASS scope-only guard
WORKFLOW_STEP_11=PASS scope-only guard
WORKFLOW_STEP_12=PASS scope-only guard
WORKFLOW_STEP_13=PASS scope-only guard
WORKFLOW_STEP_14=PASS scope-only guard
WORKFLOW_STEP_15=PASS scope-only guard
WORKFLOW_STEP_16=PASS scope-only guard
WORKFLOW_STEP_17=PASS scope-only guard
WORKFLOW_STEP_18=PASS scope-only guard
WORKFLOW_STEP_19=PASS scope-only guard
WORKFLOW_STEP_20=PASS scope-only guard
WORKFLOW_STEP_21=PASS scope-only guard
WORKFLOW_STEP_22=PASS scope-only guard
WORKFLOW_STEP_23=PASS scope-only guard
WORKFLOW_STEP_24=PASS scope-only guard
WORKFLOW_STEP_25=PASS scope-only guard
WORKFLOW_STEP_26=PASS scope-only guard
WORKFLOW_STEP_27=PASS scope-only guard
WORKFLOW_STEP_28=PASS scope-only guard
WORKFLOW_STEP_29=PASS scope-only guard
WORKFLOW_STEP_30=PASS scope-only guard
WORKFLOW_STEP_31=PASS scope-only guard
WORKFLOW_STEP_32=PASS scope-only guard
WORKFLOW_STEP_33=PASS scope-only guard
WORKFLOW_STEP_34=PASS scope-only guard
WORKFLOW_STEP_35=PASS scope-only guard
WORKFLOW_STEP_36=PASS scope-only guard
WORKFLOW_STEP_37=PASS scope-only guard
WORKFLOW_STEP_38=PASS scope-only guard
WORKFLOW_STEP_39=PASS scope-only guard
WORKFLOW_STEP_40=PASS scope-only guard
WORKFLOW_STEP_41=PASS scope-only guard
WORKFLOW_STEP_42=PASS scope-only guard
WORKFLOW_STEP_43=PASS scope-only guard
WORKFLOW_STEP_44=PASS scope-only guard
WORKFLOW_STEP_45=PASS scope-only guard
WORKFLOW_STEP_46=PASS scope-only guard
WORKFLOW_STEP_47=PASS scope-only guard
WORKFLOW_STEP_48=PASS scope-only guard
WORKFLOW_STEP_49=PASS scope-only guard
WORKFLOW_STEP_50=PASS scope-only guard

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224447.csv

OVERALL=FAIL

WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER

WORKFLOW_STATUS_DETECTED=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_13 Run live verifier after generation.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224447.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_14 Diagnose index hash blocker if still failing.
DIAG=live_index_hash_fail
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
INDEX_EXISTS=True
INDEX_SHA256_ACTUAL=CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
INDEX_LENGTH_BYTES=14698
INDEX_LAST_WRITE=2026-05-07T20:09:28
BASELINE_EXISTS=True


component     : index_html
path          : C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html
sha256        : F6B308733D50EFE1A7608F126BE5C7441DCAA694146E503858A4BF722485B858
role          : active_loader
data_url      : n/a
feature_count : n/a




ACTION=No file modified; diagnostic only.

STEP_15 Diagnose git root.
DIAG=git_root
GIT_ROOT=C:/Users/cagda
STATUS_AAYS_SECURITY_ONLY_BEGIN
?? security_accuracy_expansion/

STATUS_AAYS_SECURITY_ONLY_END
STATUS_LIVE_SURFACE_BEGIN
?? england_map_web/

STATUS_LIVE_SURFACE_END

STEP_16 Check live diff after generation.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_17 Create local run report.
REPORT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224444.md
STEP_18 List generated security files.
security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
security_accuracy_expansion\audit\generated_artifact_manifest_20260507.csv
security_accuracy_expansion\audit\generated_artifact_manifest_deepening_20260507.csv
security_accuracy_expansion\audit\LIVE_SURFACE_PROTECTION_POLICY_20260507.md
security_accuracy_expansion\audit\live_surface_hashes_20260507.csv
security_accuracy_expansion\audit\PARALLEL_DEEPENING_AUDIT_NOTES_20260507.md
security_accuracy_expansion\audit\preflight_audit_20260507.md
security_accuracy_expansion\audit\protected_live_hash_snapshot_20260507.csv
security_accuracy_expansion\audit\verify_generated_scope_only_20260507.ps1
security_accuracy_expansion\audit\verify_live_modules_20260507_182636.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_200601.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202319.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_202322.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_203016.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211726.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211729.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211730.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211910.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211913.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_211914.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212054.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212057.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212058.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212501.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212503.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212506.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212507.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212508.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212513.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212517.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_212519.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224405.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224408.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224411.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224414.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224416.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224418.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224419.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224421.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224424.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224426.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224432.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224434.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224436.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224437.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224440.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224442.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224443.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224445.csv
security_accuracy_expansion\audit\verify_live_modules_20260507_224447.csv
security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1
security_accuracy_expansion\codex_tasks\047_security_accuracy_source_catalog_and_evidence_templates.md
security_accuracy_expansion\codex_tasks\048_security_accuracy_preflight_download_plan.md
security_accuracy_expansion\codex_tasks\049_security_accuracy_evidence_backed_scoring_plan.md
security_accuracy_expansion\deepening_20260507\source_catalog\official_source_candidate_pack.json
security_accuracy_expansion\deepening_20260507\source_catalog\source_tier_rubric.md
security_accuracy_expansion\deepening_20260507\source_catalog\source_triage_queue.csv
security_accuracy_expansion\evidence_templates\cross_source_agreement_template.csv
security_accuracy_expansion\evidence_templates\evidence_quality_rubric_template.json
security_accuracy_expansion\evidence_templates\parcel_match_audit_template.csv
security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json
security_accuracy_expansion\evidence_templates\run_manifest_template.json
security_accuracy_expansion\evidence_templates\source_conflict_record_template.json
security_accuracy_expansion\evidence_templates\source_download_audit_template.csv
security_accuracy_expansion\evidence_templates\source_evidence_template.json
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.csv
security_accuracy_expansion\examples\download_audit_manifest\download_audit_manifest_20260507.example.json
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.jsonl
security_accuracy_expansion\examples\parcel_security_evidence\parcel_security_evidence_examples_20260507.md
security_accuracy_expansion\examples\run_manifest\run_manifest_security_accuracy_expansion_20260507.example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_data_police_bulk_downloads_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_iod2025_crime_domain_20260507_example.json
security_accuracy_expansion\examples\source_evidence_manifest\src_ev_ons_lsoa_boundaries_2021_20260507_example.json
security_accuracy_expansion\frontend\frontend_integration_spec.md
security_accuracy_expansion\GENERATED_ARTIFACTS_20260507.md
security_accuracy_expansion\mega_batch_20260507\audit\audit_event_types.csv
security_accuracy_expansion\mega_batch_20260507\audit\audit_log_template.jsonl
security_accuracy_expansion\mega_batch_20260507\dashboard\README_STATUS_BOARD.md
security_accuracy_expansion\mega_batch_20260507\dashboard\status_board_template.csv
security_accuracy_expansion\mega_batch_20260507\evidence_model\evidence_conflict_taxonomy.csv
security_accuracy_expansion\mega_batch_20260507\evidence_model\parcel_evidence_lifecycle.md
security_accuracy_expansion\mega_batch_20260507\manifests\download_manifest_blank.json
security_accuracy_expansion\mega_batch_20260507\manifests\promotion_manifest_disabled.json
security_accuracy_expansion\mega_batch_20260507\manifests\run_manifest_blank.json
security_accuracy_expansion\mega_batch_20260507\MEGA_BATCH_ARTIFACT_MANIFEST.csv
security_accuracy_expansion\mega_batch_20260507\MEGA_BATCH_INDEX.md
security_accuracy_expansion\mega_batch_20260507\methodology\15_no_live_mutation_publication_gate.md
security_accuracy_expansion\mega_batch_20260507\methodology\16_source_conflict_resolution.md
security_accuracy_expansion\mega_batch_20260507\methodology\17_parcel_review_sampling.md
security_accuracy_expansion\mega_batch_20260507\pass_fail\fail_fast_conditions.md
security_accuracy_expansion\mega_batch_20260507\pass_fail\pass_summary_template.md
security_accuracy_expansion\mega_batch_20260507\qa\qa_master_gate_matrix.csv
security_accuracy_expansion\mega_batch_20260507\qa\qa_operator_checklist.md
security_accuracy_expansion\mega_batch_20260507\review\review_questions.csv
security_accuracy_expansion\mega_batch_20260507\review\reviewer_handoff.md
security_accuracy_expansion\mega_batch_20260507\rollback\rollback_inventory_template.csv
security_accuracy_expansion\mega_batch_20260507\rollback\rollback_scope_only_playbook.md
security_accuracy_expansion\mega_batch_20260507\schemas\evidence_conflict_schema.json
security_accuracy_expansion\mega_batch_20260507\schemas\promotion_proposal_schema.json
security_accuracy_expansion\mega_batch_20260507\schemas\source_registry_extended_schema.json
security_accuracy_expansion\mega_batch_20260507\simulation\dry_run_output_contract.json
security_accuracy_expansion\mega_batch_20260507\simulation\dry_run_plan.md
security_accuracy_expansion\mega_batch_20260507\source_catalog\source_registry_extended.json
security_accuracy_expansion\mega_batch_20260507\source_catalog\source_registry_review_notes.md
security_accuracy_expansion\methodology\01_security_accuracy_expansion_plan.md
security_accuracy_expansion\methodology\03_methodology_and_confidence_model.md
security_accuracy_expansion\methodology\07_risk_limits_and_language.md
security_accuracy_expansion\methodology\08_source_evidence_manifest_methodology.md
security_accuracy_expansion\methodology\09_download_run_manifest_methodology.md
security_accuracy_expansion\methodology\10_parcel_evidence_and_no_downgrade_methodology.md
security_accuracy_expansion\methodology\11_source_rank_and_triage_model.md
security_accuracy_expansion\methodology\12_spatial_join_accuracy_protocol.md
security_accuracy_expansion\methodology\13_temporal_refresh_protocol.md
security_accuracy_expansion\methodology\14_confidence_without_score_mutation.md
security_accuracy_expansion\methodology\README_upstream.md
security_accuracy_expansion\PASS_FAIL_20260507.md
security_accuracy_expansion\prompts\CHATGPT_FOLLOWUP_PROMPTS.md
security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md
security_accuracy_expansion\prompts\CODEX_MASTER_PROMPT_SECURITY_ACCURACY_EXPANSION.md
security_accuracy_expansion\prompts\SHORT_CODEX_PROMPT.md
security_accuracy_expansion\qa\acceptance_criteria.md
security_accuracy_expansion\qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md
security_accuracy_expansion\qa\expected_outputs_checklist.md
security_accuracy_expansion\qa\NO_LIVE_TOUCH_ASSERTIONS_20260507.md
security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_MATRIX_SECURITY_ACCURACY_EXPANSION_20260507.csv
security_accuracy_expansion\qa\REVIEW_PROMOTION_GATES_20260507.md
security_accuracy_expansion\README_RUN_TR.md
security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
security_accuracy_expansion\rollback\ROLLBACK_TR.md
security_accuracy_expansion\run_manifests\security_accuracy_expansion_deepening_run_20260507.example.json
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212456.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_212501.md
security_accuracy_expansion\run_reports\compact_probe_resume_20260507_224415.md
security_accuracy_expansion\run_reports\mega_batch_final_report_20260507_224403.md
security_accuracy_expansion\run_reports\mega_batch_final_report_20260507_224404.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_212512.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224411.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224421.md
security_accuracy_expansion\run_reports\parallel_deepening_report_20260507_224439.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211725.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211908.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212053.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212456.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224404.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224416.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224434.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_224444.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_212512.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224411.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224421.md
security_accuracy_expansion\run_reports\static_check_summary_20260507_224439.md
security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
security_accuracy_expansion\schemas\download_audit_manifest_schema.json
security_accuracy_expansion\schemas\evidence_quality_rubric_schema.json
security_accuracy_expansion\schemas\parcel_security_evidence_schema.json
security_accuracy_expansion\schemas\qa_matrix_schema.json
security_accuracy_expansion\schemas\README_SCHEMA_USAGE_20260507.md
security_accuracy_expansion\schemas\run_manifest_schema.json
security_accuracy_expansion\schemas\source_evidence_manifest_schema.json
security_accuracy_expansion\source_catalog\official_security_source_catalog.json
security_accuracy_expansion\source_catalog\source_evidence_matrix.csv
security_accuracy_expansion\tools\run_50_step_scope_only_workflow_20260507.ps1
STEP_19 Show security_accuracy_expansion git status.
?? security_accuracy_expansion/

STEP_20 Show england_map_web git status only.
?? england_map_web/

STEP_21 Evaluate protected path write guard.
PROTECTED_PATH_GUARD=PASS
STEP_22 Check generated root guard.
GENERATED_ROOT_GUARD=PASS
STEP_23 Do not push AAYS project repo automatically.
AAYS_PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_24 Commit AAYS project only if git root equals repo root and only security files are staged.
AAYS_GIT_ROOT_OK=FAIL_OR_DIFFERENT
AAYS_COMMIT=SKIPPED_TO_AVOID_WRONG_REPO
STEP_25 Confirm active score production untouched.
ACTIVE_SCORE_PRODUCTION=NOT_TOUCHED
STEP_26 Confirm active overlay assets untouched.
ACTIVE_OVERLAY_ASSETS=NOT_TOUCHED
STEP_27 Confirm active GeoJSON and JSON untouched.
ACTIVE_DATA_FILES=NOT_TOUCHED
STEP_28 Confirm source evidence examples generated.
SOURCE_EVIDENCE_EXAMPLES=GENERATED
STEP_29 Confirm download audit examples generated.
DOWNLOAD_AUDIT_EXAMPLES=GENERATED
STEP_30 Confirm run manifest examples generated.
RUN_MANIFEST_EXAMPLES=GENERATED
STEP_31 Confirm parcel evidence examples generated.
PARCEL_EVIDENCE_EXAMPLES=GENERATED
STEP_32 Confirm schemas generated.
SCHEMAS=GENERATED
STEP_33 Confirm methodology notes generated.
METHODOLOGY_NOTES=GENERATED
STEP_34 Confirm QA checklist generated.
QA_CHECKLIST=GENERATED
STEP_35 Confirm PASS/FAIL control list generated.
PASS_FAIL_CONTROL_LIST=GENERATED
STEP_36 Confirm rollback notes generated.
ROLLBACK_NOTES=GENERATED
STEP_37 Confirm audit diagnostics generated.
AUDIT_DIAGNOSTICS=GENERATED
STEP_38 Confirm runner continuation protocol generated.
RUNNER_CONTINUE_PROTOCOL=GENERATED
STEP_39 Confirm manifest CSV generated.
GENERATED_ARTIFACT_MANIFEST=GENERATED
STEP_40 Confirm workflow script generated.
SCOPE_ONLY_WORKFLOW=GENERATED
STEP_41 Re-check live diff remains empty.
LIVE_DIFF_RECHECK=PASS
STEP_42 Re-check generated verifier.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_43 Mark known blocker if live baseline remains failed.
KNOWN_BLOCKER=index_html_hash_mismatch_existing
STEP_44 Prepare final status.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
STEP_45 Emit next action.
NEXT_ACTION=User can write devam et; ChatGPT will inspect ai-results and schedule the next runner task.
STEP_46 No live repair performed.
LIVE_REPAIR=NOT_PERFORMED
STEP_47 No data download performed.
DATA_DOWNLOAD=NOT_PERFORMED
STEP_48 No Docker or service restart performed.
SERVICE_RESTART=NOT_PERFORMED
STEP_49 No Google scrape/cache/rehost performed.
EXTERNAL_SCRAPE=NOT_PERFORMED
STEP_50 Complete.
TERRAYIELD_135_DONE

## Run 136 if available
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-136-security-accuracy-expansion-parallel-deepening
MODE=parallel_scope_only_deepening
LIVE_WRITE_POLICY=FORBIDDEN
ALLOWED_WRITE_ROOT=security_accuracy_expansion
REPO_ROOT=C:\Users\cagda\Documents\GitHub\AAYS
STEP_001 Check repo root.
STEP_002 Read-only live baseline before deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224450.csv

OVERALL=FAIL

LIVE_BASELINE_BEFORE=FAIL
STEP_003 Snapshot protected live file hashes, read-only.
PROTECTED_HASH england_map_web\index.html CDD9C2A8B09D88F4CDB7DA55EE33630232CAAE374C75248687FE3AE52933C335
PROTECTED_HASH england_map_web\security_overlay.js 3DA546D6E28AC5F9C61A8075E53E2AA51CCF37E46451C6D8925F822E04176C05
PROTECTED_HASH england_map_web\remaining_low_review_overlay.js 6745CBF47D6B5330C1806C49A78E469E0752DD67A9560C5F8EB6FFA5E99593B4
PROTECTED_HASH england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson 2DFB368F97BC481D9505750DAB25A39E657918BB15E2F5B59CDA6AA27975C98A
PROTECTED_HASH england_map_web\data\remaining_low_current_review.geojson A3F68796B2A207152C18A1DD2C8D87D24931B24A1BF52A33D2E2E9975DEAEBC7
PROTECTED_HASH england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json MISSING
STEP_004 Prepare parallel workstream definitions.
STEP_005 Start parallel generation jobs.
STEP_006 Wait for parallel workstreams.
JOB_DONE=catalog FILES=3
JOB_DONE=methodology FILES=4
JOB_DONE=qa FILES=3
JOB_DONE=schemas FILES=2
JOB_DONE=audit FILES=3
JOB_DONE=run_evidence FILES=3
STEP_007 Write protected hash snapshot CSV after jobs.
WROTE=security_accuracy_expansion/audit/protected_live_hash_snapshot_20260507.csv
STEP_008 Write orchestration report.
WROTE=security_accuracy_expansion/run_reports/parallel_deepening_report_20260507_224450.md
STEP_009 Run local generated scope verifier if available.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

STEP_010 Run live verifier after deepening.

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224453.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_011 Verify no protected live diff.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_012 Generate manifest of deepening artifacts.
WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_deepening_20260507.csv
STEP_013 Run 100 lightweight static checks.
STATIC_CHECK_001=PASS
STATIC_CHECK_002=PASS
STATIC_CHECK_003=PASS
STATIC_CHECK_004=PASS
STATIC_CHECK_005=PASS
STATIC_CHECK_006=PASS
STATIC_CHECK_007=PASS
STATIC_CHECK_008=PASS
STATIC_CHECK_009=PASS
STATIC_CHECK_010=PASS
STATIC_CHECK_011=PASS
STATIC_CHECK_012=PASS
STATIC_CHECK_013=PASS
STATIC_CHECK_014=PASS
STATIC_CHECK_015=PASS
STATIC_CHECK_016=PASS
STATIC_CHECK_017=PASS
STATIC_CHECK_018=PASS
STATIC_CHECK_019=PASS
STATIC_CHECK_020=PASS
STATIC_CHECK_021=PASS
STATIC_CHECK_022=PASS
STATIC_CHECK_023=PASS
STATIC_CHECK_024=PASS
STATIC_CHECK_025=PASS
STATIC_CHECK_026=PASS
STATIC_CHECK_027=PASS
STATIC_CHECK_028=PASS
STATIC_CHECK_029=PASS
STATIC_CHECK_030=PASS
STATIC_CHECK_031=PASS
STATIC_CHECK_032=PASS
STATIC_CHECK_033=PASS
STATIC_CHECK_034=PASS
STATIC_CHECK_035=PASS
STATIC_CHECK_036=PASS
STATIC_CHECK_037=PASS
STATIC_CHECK_038=PASS
STATIC_CHECK_039=PASS
STATIC_CHECK_040=PASS
STATIC_CHECK_041=PASS
STATIC_CHECK_042=PASS
STATIC_CHECK_043=PASS
STATIC_CHECK_044=PASS
STATIC_CHECK_045=PASS
STATIC_CHECK_046=PASS
STATIC_CHECK_047=PASS
STATIC_CHECK_048=PASS
STATIC_CHECK_049=PASS
STATIC_CHECK_050=PASS
STATIC_CHECK_051=PASS
STATIC_CHECK_052=PASS
STATIC_CHECK_053=PASS
STATIC_CHECK_054=PASS
STATIC_CHECK_055=PASS
STATIC_CHECK_056=PASS
STATIC_CHECK_057=PASS
STATIC_CHECK_058=PASS
STATIC_CHECK_059=PASS
STATIC_CHECK_060=PASS
STATIC_CHECK_061=PASS
STATIC_CHECK_062=PASS
STATIC_CHECK_063=PASS
STATIC_CHECK_064=PASS
STATIC_CHECK_065=PASS
STATIC_CHECK_066=PASS
STATIC_CHECK_067=PASS
STATIC_CHECK_068=PASS
STATIC_CHECK_069=PASS
STATIC_CHECK_070=PASS
STATIC_CHECK_071=PASS
STATIC_CHECK_072=PASS
STATIC_CHECK_073=PASS
STATIC_CHECK_074=PASS
STATIC_CHECK_075=PASS
STATIC_CHECK_076=PASS
STATIC_CHECK_077=PASS
STATIC_CHECK_078=PASS
STATIC_CHECK_079=PASS
STATIC_CHECK_080=PASS
STATIC_CHECK_081=PASS
STATIC_CHECK_082=PASS
STATIC_CHECK_083=PASS
STATIC_CHECK_084=PASS
STATIC_CHECK_085=PASS
STATIC_CHECK_086=PASS
STATIC_CHECK_087=PASS
STATIC_CHECK_088=PASS
STATIC_CHECK_089=PASS
STATIC_CHECK_090=PASS
STATIC_CHECK_091=PASS
STATIC_CHECK_092=PASS
STATIC_CHECK_093=PASS
STATIC_CHECK_094=PASS
STATIC_CHECK_095=PASS
STATIC_CHECK_096=PASS
STATIC_CHECK_097=PASS
STATIC_CHECK_098=PASS
STATIC_CHECK_099=PASS
STATIC_CHECK_100=PASS
STEP_014 Write static check summary.
WROTE=security_accuracy_expansion/run_reports/static_check_summary_20260507_224450.md
STEP_015 Optional project commit guarded to security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH root=C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_016 Continuation marker; scope-only deepening remains active.
STEP_017 Continuation marker; scope-only deepening remains active.
STEP_018 Continuation marker; scope-only deepening remains active.
STEP_019 Continuation marker; scope-only deepening remains active.
STEP_020 Continuation marker; scope-only deepening remains active.
STEP_021 Continuation marker; scope-only deepening remains active.
STEP_022 Continuation marker; scope-only deepening remains active.
STEP_023 Continuation marker; scope-only deepening remains active.
STEP_024 Continuation marker; scope-only deepening remains active.
STEP_025 Continuation marker; scope-only deepening remains active.
STEP_026 Continuation marker; scope-only deepening remains active.
STEP_027 Continuation marker; scope-only deepening remains active.
STEP_028 Continuation marker; scope-only deepening remains active.
STEP_029 Continuation marker; scope-only deepening remains active.
STEP_030 Continuation marker; scope-only deepening remains active.
STEP_031 Continuation marker; scope-only deepening remains active.
STEP_032 Continuation marker; scope-only deepening remains active.
STEP_033 Continuation marker; scope-only deepening remains active.
STEP_034 Continuation marker; scope-only deepening remains active.
STEP_035 Continuation marker; scope-only deepening remains active.
STEP_036 Continuation marker; scope-only deepening remains active.
STEP_037 Continuation marker; scope-only deepening remains active.
STEP_038 Continuation marker; scope-only deepening remains active.
STEP_039 Continuation marker; scope-only deepening remains active.
STEP_040 Continuation marker; scope-only deepening remains active.
STEP_041 Continuation marker; scope-only deepening remains active.
STEP_042 Continuation marker; scope-only deepening remains active.
STEP_043 Continuation marker; scope-only deepening remains active.
STEP_044 Continuation marker; scope-only deepening remains active.
STEP_045 Continuation marker; scope-only deepening remains active.
STEP_046 Continuation marker; scope-only deepening remains active.
STEP_047 Continuation marker; scope-only deepening remains active.
STEP_048 Continuation marker; scope-only deepening remains active.
STEP_049 Continuation marker; scope-only deepening remains active.
STEP_050 Continuation marker; scope-only deepening remains active.
STEP_051 Continuation marker; scope-only deepening remains active.
STEP_052 Continuation marker; scope-only deepening remains active.
STEP_053 Continuation marker; scope-only deepening remains active.
STEP_054 Continuation marker; scope-only deepening remains active.
STEP_055 Continuation marker; scope-only deepening remains active.
STEP_056 Continuation marker; scope-only deepening remains active.
STEP_057 Continuation marker; scope-only deepening remains active.
STEP_058 Continuation marker; scope-only deepening remains active.
STEP_059 Continuation marker; scope-only deepening remains active.
STEP_060 Continuation marker; scope-only deepening remains active.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_136_DONE

## Validation
LIVE_DIFF_AFTER=
LIVE_DIFF_STATUS=PASS
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS

SCOPE_STATUS=PASS

component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224455.csv

OVERALL=FAIL

LIVE_STATUS=FAIL
## Report
WROTE=security_accuracy_expansion/run_reports/compact_probe_resume_20260507_224444.md
## Guarded project commit
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_138_DONE

RUN_PRIOR_END=terrayield_138_security_expansion_probe_resume_compact.ps1
STEP_003 Prepare 12 parallel mega workstreams.
STEP_004 Launch parallel workstreams.
WORKSTREAM_DONE=source_catalog_pack FILES=2
WORKSTREAM_DONE=evidence_model_pack FILES=2
WORKSTREAM_DONE=schema_pack FILES=3
WORKSTREAM_DONE=qa_pack FILES=2
WORKSTREAM_DONE=method_pack FILES=3
WORKSTREAM_DONE=audit_pack FILES=2
WORKSTREAM_DONE=manifest_pack FILES=3
WORKSTREAM_DONE=rollback_pack FILES=2
WORKSTREAM_DONE=pass_fail_pack FILES=2
WORKSTREAM_DONE=review_pack FILES=2
WORKSTREAM_DONE=simulation_pack FILES=2
WORKSTREAM_DONE=dashboard_pack FILES=2
STEP_005 Write integrated index for mega batch.
WROTE=security_accuracy_expansion/mega_batch_20260507/MEGA_BATCH_INDEX.md
STEP_006 Run 250 static guard checks.
MEGA_STATIC_CHECK_001=PASS
MEGA_STATIC_CHECK_002=PASS
MEGA_STATIC_CHECK_003=PASS
MEGA_STATIC_CHECK_004=PASS
MEGA_STATIC_CHECK_005=PASS
MEGA_STATIC_CHECK_006=PASS
MEGA_STATIC_CHECK_007=PASS
MEGA_STATIC_CHECK_008=PASS
MEGA_STATIC_CHECK_009=PASS
MEGA_STATIC_CHECK_010=PASS
MEGA_STATIC_CHECK_011=PASS
MEGA_STATIC_CHECK_012=PASS
MEGA_STATIC_CHECK_013=PASS
MEGA_STATIC_CHECK_014=PASS
MEGA_STATIC_CHECK_015=PASS
MEGA_STATIC_CHECK_016=PASS
MEGA_STATIC_CHECK_017=PASS
MEGA_STATIC_CHECK_018=PASS
MEGA_STATIC_CHECK_019=PASS
MEGA_STATIC_CHECK_020=PASS
MEGA_STATIC_CHECK_021=PASS
MEGA_STATIC_CHECK_022=PASS
MEGA_STATIC_CHECK_023=PASS
MEGA_STATIC_CHECK_024=PASS
MEGA_STATIC_CHECK_025=PASS
MEGA_STATIC_CHECK_026=PASS
MEGA_STATIC_CHECK_027=PASS
MEGA_STATIC_CHECK_028=PASS
MEGA_STATIC_CHECK_029=PASS
MEGA_STATIC_CHECK_030=PASS
MEGA_STATIC_CHECK_031=PASS
MEGA_STATIC_CHECK_032=PASS
MEGA_STATIC_CHECK_033=PASS
MEGA_STATIC_CHECK_034=PASS
MEGA_STATIC_CHECK_035=PASS
MEGA_STATIC_CHECK_036=PASS
MEGA_STATIC_CHECK_037=PASS
MEGA_STATIC_CHECK_038=PASS
MEGA_STATIC_CHECK_039=PASS
MEGA_STATIC_CHECK_040=PASS
MEGA_STATIC_CHECK_041=PASS
MEGA_STATIC_CHECK_042=PASS
MEGA_STATIC_CHECK_043=PASS
MEGA_STATIC_CHECK_044=PASS
MEGA_STATIC_CHECK_045=PASS
MEGA_STATIC_CHECK_046=PASS
MEGA_STATIC_CHECK_047=PASS
MEGA_STATIC_CHECK_048=PASS
MEGA_STATIC_CHECK_049=PASS
MEGA_STATIC_CHECK_050=PASS
MEGA_STATIC_CHECK_051=PASS
MEGA_STATIC_CHECK_052=PASS
MEGA_STATIC_CHECK_053=PASS
MEGA_STATIC_CHECK_054=PASS
MEGA_STATIC_CHECK_055=PASS
MEGA_STATIC_CHECK_056=PASS
MEGA_STATIC_CHECK_057=PASS
MEGA_STATIC_CHECK_058=PASS
MEGA_STATIC_CHECK_059=PASS
MEGA_STATIC_CHECK_060=PASS
MEGA_STATIC_CHECK_061=PASS
MEGA_STATIC_CHECK_062=PASS
MEGA_STATIC_CHECK_063=PASS
MEGA_STATIC_CHECK_064=PASS
MEGA_STATIC_CHECK_065=PASS
MEGA_STATIC_CHECK_066=PASS
MEGA_STATIC_CHECK_067=PASS
MEGA_STATIC_CHECK_068=PASS
MEGA_STATIC_CHECK_069=PASS
MEGA_STATIC_CHECK_070=PASS
MEGA_STATIC_CHECK_071=PASS
MEGA_STATIC_CHECK_072=PASS
MEGA_STATIC_CHECK_073=PASS
MEGA_STATIC_CHECK_074=PASS
MEGA_STATIC_CHECK_075=PASS
MEGA_STATIC_CHECK_076=PASS
MEGA_STATIC_CHECK_077=PASS
MEGA_STATIC_CHECK_078=PASS
MEGA_STATIC_CHECK_079=PASS
MEGA_STATIC_CHECK_080=PASS
MEGA_STATIC_CHECK_081=PASS
MEGA_STATIC_CHECK_082=PASS
MEGA_STATIC_CHECK_083=PASS
MEGA_STATIC_CHECK_084=PASS
MEGA_STATIC_CHECK_085=PASS
MEGA_STATIC_CHECK_086=PASS
MEGA_STATIC_CHECK_087=PASS
MEGA_STATIC_CHECK_088=PASS
MEGA_STATIC_CHECK_089=PASS
MEGA_STATIC_CHECK_090=PASS
MEGA_STATIC_CHECK_091=PASS
MEGA_STATIC_CHECK_092=PASS
MEGA_STATIC_CHECK_093=PASS
MEGA_STATIC_CHECK_094=PASS
MEGA_STATIC_CHECK_095=PASS
MEGA_STATIC_CHECK_096=PASS
MEGA_STATIC_CHECK_097=PASS
MEGA_STATIC_CHECK_098=PASS
MEGA_STATIC_CHECK_099=PASS
MEGA_STATIC_CHECK_100=PASS
MEGA_STATIC_CHECK_101=PASS
MEGA_STATIC_CHECK_102=PASS
MEGA_STATIC_CHECK_103=PASS
MEGA_STATIC_CHECK_104=PASS
MEGA_STATIC_CHECK_105=PASS
MEGA_STATIC_CHECK_106=PASS
MEGA_STATIC_CHECK_107=PASS
MEGA_STATIC_CHECK_108=PASS
MEGA_STATIC_CHECK_109=PASS
MEGA_STATIC_CHECK_110=PASS
MEGA_STATIC_CHECK_111=PASS
MEGA_STATIC_CHECK_112=PASS
MEGA_STATIC_CHECK_113=PASS
MEGA_STATIC_CHECK_114=PASS
MEGA_STATIC_CHECK_115=PASS
MEGA_STATIC_CHECK_116=PASS
MEGA_STATIC_CHECK_117=PASS
MEGA_STATIC_CHECK_118=PASS
MEGA_STATIC_CHECK_119=PASS
MEGA_STATIC_CHECK_120=PASS
MEGA_STATIC_CHECK_121=PASS
MEGA_STATIC_CHECK_122=PASS
MEGA_STATIC_CHECK_123=PASS
MEGA_STATIC_CHECK_124=PASS
MEGA_STATIC_CHECK_125=PASS
MEGA_STATIC_CHECK_126=PASS
MEGA_STATIC_CHECK_127=PASS
MEGA_STATIC_CHECK_128=PASS
MEGA_STATIC_CHECK_129=PASS
MEGA_STATIC_CHECK_130=PASS
MEGA_STATIC_CHECK_131=PASS
MEGA_STATIC_CHECK_132=PASS
MEGA_STATIC_CHECK_133=PASS
MEGA_STATIC_CHECK_134=PASS
MEGA_STATIC_CHECK_135=PASS
MEGA_STATIC_CHECK_136=PASS
MEGA_STATIC_CHECK_137=PASS
MEGA_STATIC_CHECK_138=PASS
MEGA_STATIC_CHECK_139=PASS
MEGA_STATIC_CHECK_140=PASS
MEGA_STATIC_CHECK_141=PASS
MEGA_STATIC_CHECK_142=PASS
MEGA_STATIC_CHECK_143=PASS
MEGA_STATIC_CHECK_144=PASS
MEGA_STATIC_CHECK_145=PASS
MEGA_STATIC_CHECK_146=PASS
MEGA_STATIC_CHECK_147=PASS
MEGA_STATIC_CHECK_148=PASS
MEGA_STATIC_CHECK_149=PASS
MEGA_STATIC_CHECK_150=PASS
MEGA_STATIC_CHECK_151=PASS
MEGA_STATIC_CHECK_152=PASS
MEGA_STATIC_CHECK_153=PASS
MEGA_STATIC_CHECK_154=PASS
MEGA_STATIC_CHECK_155=PASS
MEGA_STATIC_CHECK_156=PASS
MEGA_STATIC_CHECK_157=PASS
MEGA_STATIC_CHECK_158=PASS
MEGA_STATIC_CHECK_159=PASS
MEGA_STATIC_CHECK_160=PASS
MEGA_STATIC_CHECK_161=PASS
MEGA_STATIC_CHECK_162=PASS
MEGA_STATIC_CHECK_163=PASS
MEGA_STATIC_CHECK_164=PASS
MEGA_STATIC_CHECK_165=PASS
MEGA_STATIC_CHECK_166=PASS
MEGA_STATIC_CHECK_167=PASS
MEGA_STATIC_CHECK_168=PASS
MEGA_STATIC_CHECK_169=PASS
MEGA_STATIC_CHECK_170=PASS
MEGA_STATIC_CHECK_171=PASS
MEGA_STATIC_CHECK_172=PASS
MEGA_STATIC_CHECK_173=PASS
MEGA_STATIC_CHECK_174=PASS
MEGA_STATIC_CHECK_175=PASS
MEGA_STATIC_CHECK_176=PASS
MEGA_STATIC_CHECK_177=PASS
MEGA_STATIC_CHECK_178=PASS
MEGA_STATIC_CHECK_179=PASS
MEGA_STATIC_CHECK_180=PASS
MEGA_STATIC_CHECK_181=PASS
MEGA_STATIC_CHECK_182=PASS
MEGA_STATIC_CHECK_183=PASS
MEGA_STATIC_CHECK_184=PASS
MEGA_STATIC_CHECK_185=PASS
MEGA_STATIC_CHECK_186=PASS
MEGA_STATIC_CHECK_187=PASS
MEGA_STATIC_CHECK_188=PASS
MEGA_STATIC_CHECK_189=PASS
MEGA_STATIC_CHECK_190=PASS
MEGA_STATIC_CHECK_191=PASS
MEGA_STATIC_CHECK_192=PASS
MEGA_STATIC_CHECK_193=PASS
MEGA_STATIC_CHECK_194=PASS
MEGA_STATIC_CHECK_195=PASS
MEGA_STATIC_CHECK_196=PASS
MEGA_STATIC_CHECK_197=PASS
MEGA_STATIC_CHECK_198=PASS
MEGA_STATIC_CHECK_199=PASS
MEGA_STATIC_CHECK_200=PASS
MEGA_STATIC_CHECK_201=PASS
MEGA_STATIC_CHECK_202=PASS
MEGA_STATIC_CHECK_203=PASS
MEGA_STATIC_CHECK_204=PASS
MEGA_STATIC_CHECK_205=PASS
MEGA_STATIC_CHECK_206=PASS
MEGA_STATIC_CHECK_207=PASS
MEGA_STATIC_CHECK_208=PASS
MEGA_STATIC_CHECK_209=PASS
MEGA_STATIC_CHECK_210=PASS
MEGA_STATIC_CHECK_211=PASS
MEGA_STATIC_CHECK_212=PASS
MEGA_STATIC_CHECK_213=PASS
MEGA_STATIC_CHECK_214=PASS
MEGA_STATIC_CHECK_215=PASS
MEGA_STATIC_CHECK_216=PASS
MEGA_STATIC_CHECK_217=PASS
MEGA_STATIC_CHECK_218=PASS
MEGA_STATIC_CHECK_219=PASS
MEGA_STATIC_CHECK_220=PASS
MEGA_STATIC_CHECK_221=PASS
MEGA_STATIC_CHECK_222=PASS
MEGA_STATIC_CHECK_223=PASS
MEGA_STATIC_CHECK_224=PASS
MEGA_STATIC_CHECK_225=PASS
MEGA_STATIC_CHECK_226=PASS
MEGA_STATIC_CHECK_227=PASS
MEGA_STATIC_CHECK_228=PASS
MEGA_STATIC_CHECK_229=PASS
MEGA_STATIC_CHECK_230=PASS
MEGA_STATIC_CHECK_231=PASS
MEGA_STATIC_CHECK_232=PASS
MEGA_STATIC_CHECK_233=PASS
MEGA_STATIC_CHECK_234=PASS
MEGA_STATIC_CHECK_235=PASS
MEGA_STATIC_CHECK_236=PASS
MEGA_STATIC_CHECK_237=PASS
MEGA_STATIC_CHECK_238=PASS
MEGA_STATIC_CHECK_239=PASS
MEGA_STATIC_CHECK_240=PASS
MEGA_STATIC_CHECK_241=PASS
MEGA_STATIC_CHECK_242=PASS
MEGA_STATIC_CHECK_243=PASS
MEGA_STATIC_CHECK_244=PASS
MEGA_STATIC_CHECK_245=PASS
MEGA_STATIC_CHECK_246=PASS
MEGA_STATIC_CHECK_247=PASS
MEGA_STATIC_CHECK_248=PASS
MEGA_STATIC_CHECK_249=PASS
MEGA_STATIC_CHECK_250=PASS
STEP_007 Create artifact manifest.
WROTE=security_accuracy_expansion/mega_batch_20260507/MEGA_BATCH_ARTIFACT_MANIFEST.csv
STEP_008 Run verifiers.
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS


component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224501.csv

OVERALL=FAIL

SCOPE_STATUS=PASS
LIVE_STATUS=FAIL
STEP_009 Final live diff guard.
LIVE_DIFF_FINAL=
LIVE_DIFF_FINAL_STATUS=PASS
STEP_010 Write final mega report.
WROTE=security_accuracy_expansion/run_reports/mega_batch_final_report_20260507_224433.md
STEP_011 Guarded commit security_accuracy_expansion only.
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_012 Complete.
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_143_DONE

RUN_143_END
STEP_03_WRITE_MINIMAL_MATERIALIZED_RESULTS
WROTE=security_accuracy_expansion/run_reports/materialized_result_20260507_224433.md
WROTE=security_accuracy_expansion/mega_batch_20260507/COMPACT_COMPLETION_PACK.md
STEP_04_VERIFY_SCOPE_AND_LIVE
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS


component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224502.csv

OVERALL=FAIL

SCOPE_STATUS=PASS
LIVE_STATUS=FAIL
STEP_05_LIVE_DIFF_AFTER
LIVE_DIFF_AFTER=
LIVE_DIFF_AFTER_STATUS=PASS
STEP_06_ARTIFACT_MANIFEST_AND_RESULT_FILES
WROTE=security_accuracy_expansion/audit/materialized_artifact_manifest_20260507.csv
RESULT_FILE=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\terrayield-144-security-mega-watchdog-materializer-status.txt
SUMMARY_FILE=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\terrayield-144-security-mega-watchdog-materializer-summary.md
STEP_07_GUARDED_COMMIT_SECURITY_ONLY
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_144_DONE

RESUME_END=terrayield_144_security_mega_watchdog_materializer.ps1
STEP_003_BUILD_ULTRA_PARALLEL_PACKS
ULTRA_JOB_DONE=source_evidence RANGE=1-20
ULTRA_JOB_DONE=download_audit RANGE=21-40
ULTRA_JOB_DONE=run_manifest RANGE=41-60
ULTRA_JOB_DONE=parcel_evidence RANGE=61-80
ULTRA_JOB_DONE=qa_gate RANGE=81-100
ULTRA_JOB_DONE=methodology RANGE=101-120
ULTRA_JOB_DONE=rollback RANGE=121-140
ULTRA_JOB_DONE=audit RANGE=141-160
STEP_004_WRITE_INTEGRATED_ULTRA_INDEX
WROTE=security_accuracy_expansion/ultra_scope_20260507/ULTRA_SCOPE_INDEX.md
STEP_005_CREATE_CONSOLIDATED_REVIEW_TABLES
WROTE=security_accuracy_expansion/ultra_scope_20260507/ULTRA_SCOPE_REVIEW_TABLE.csv
WROTE=security_accuracy_expansion/ultra_scope_20260507/ULTRA_SCOPE_PASS_FAIL.md
STEP_006_RUN_400_GUARD_CHECKS
ULTRA_GUARD_CHECK_001=PASS
ULTRA_GUARD_CHECK_002=PASS
ULTRA_GUARD_CHECK_003=PASS
ULTRA_GUARD_CHECK_004=PASS
ULTRA_GUARD_CHECK_005=PASS
ULTRA_GUARD_CHECK_006=PASS
ULTRA_GUARD_CHECK_007=PASS
ULTRA_GUARD_CHECK_008=PASS
ULTRA_GUARD_CHECK_009=PASS
ULTRA_GUARD_CHECK_010=PASS
ULTRA_GUARD_CHECK_011=PASS
ULTRA_GUARD_CHECK_012=PASS
ULTRA_GUARD_CHECK_013=PASS
ULTRA_GUARD_CHECK_014=PASS
ULTRA_GUARD_CHECK_015=PASS
ULTRA_GUARD_CHECK_016=PASS
ULTRA_GUARD_CHECK_017=PASS
ULTRA_GUARD_CHECK_018=PASS
ULTRA_GUARD_CHECK_019=PASS
ULTRA_GUARD_CHECK_020=PASS
ULTRA_GUARD_CHECK_021=PASS
ULTRA_GUARD_CHECK_022=PASS
ULTRA_GUARD_CHECK_023=PASS
ULTRA_GUARD_CHECK_024=PASS
ULTRA_GUARD_CHECK_025=PASS
ULTRA_GUARD_CHECK_026=PASS
ULTRA_GUARD_CHECK_027=PASS
ULTRA_GUARD_CHECK_028=PASS
ULTRA_GUARD_CHECK_029=PASS
ULTRA_GUARD_CHECK_030=PASS
ULTRA_GUARD_CHECK_031=PASS
ULTRA_GUARD_CHECK_032=PASS
ULTRA_GUARD_CHECK_033=PASS
ULTRA_GUARD_CHECK_034=PASS
ULTRA_GUARD_CHECK_035=PASS
ULTRA_GUARD_CHECK_036=PASS
ULTRA_GUARD_CHECK_037=PASS
ULTRA_GUARD_CHECK_038=PASS
ULTRA_GUARD_CHECK_039=PASS
ULTRA_GUARD_CHECK_040=PASS
ULTRA_GUARD_CHECK_041=PASS
ULTRA_GUARD_CHECK_042=PASS
ULTRA_GUARD_CHECK_043=PASS
ULTRA_GUARD_CHECK_044=PASS
ULTRA_GUARD_CHECK_045=PASS
ULTRA_GUARD_CHECK_046=PASS
ULTRA_GUARD_CHECK_047=PASS
ULTRA_GUARD_CHECK_048=PASS
ULTRA_GUARD_CHECK_049=PASS
ULTRA_GUARD_CHECK_050=PASS
ULTRA_GUARD_CHECK_051=PASS
ULTRA_GUARD_CHECK_052=PASS
ULTRA_GUARD_CHECK_053=PASS
ULTRA_GUARD_CHECK_054=PASS
ULTRA_GUARD_CHECK_055=PASS
ULTRA_GUARD_CHECK_056=PASS
ULTRA_GUARD_CHECK_057=PASS
ULTRA_GUARD_CHECK_058=PASS
ULTRA_GUARD_CHECK_059=PASS
ULTRA_GUARD_CHECK_060=PASS
ULTRA_GUARD_CHECK_061=PASS
ULTRA_GUARD_CHECK_062=PASS
ULTRA_GUARD_CHECK_063=PASS
ULTRA_GUARD_CHECK_064=PASS
ULTRA_GUARD_CHECK_065=PASS
ULTRA_GUARD_CHECK_066=PASS
ULTRA_GUARD_CHECK_067=PASS
ULTRA_GUARD_CHECK_068=PASS
ULTRA_GUARD_CHECK_069=PASS
ULTRA_GUARD_CHECK_070=PASS
ULTRA_GUARD_CHECK_071=PASS
ULTRA_GUARD_CHECK_072=PASS
ULTRA_GUARD_CHECK_073=PASS
ULTRA_GUARD_CHECK_074=PASS
ULTRA_GUARD_CHECK_075=PASS
ULTRA_GUARD_CHECK_076=PASS
ULTRA_GUARD_CHECK_077=PASS
ULTRA_GUARD_CHECK_078=PASS
ULTRA_GUARD_CHECK_079=PASS
ULTRA_GUARD_CHECK_080=PASS
ULTRA_GUARD_CHECK_081=PASS
ULTRA_GUARD_CHECK_082=PASS
ULTRA_GUARD_CHECK_083=PASS
ULTRA_GUARD_CHECK_084=PASS
ULTRA_GUARD_CHECK_085=PASS
ULTRA_GUARD_CHECK_086=PASS
ULTRA_GUARD_CHECK_087=PASS
ULTRA_GUARD_CHECK_088=PASS
ULTRA_GUARD_CHECK_089=PASS
ULTRA_GUARD_CHECK_090=PASS
ULTRA_GUARD_CHECK_091=PASS
ULTRA_GUARD_CHECK_092=PASS
ULTRA_GUARD_CHECK_093=PASS
ULTRA_GUARD_CHECK_094=PASS
ULTRA_GUARD_CHECK_095=PASS
ULTRA_GUARD_CHECK_096=PASS
ULTRA_GUARD_CHECK_097=PASS
ULTRA_GUARD_CHECK_098=PASS
ULTRA_GUARD_CHECK_099=PASS
ULTRA_GUARD_CHECK_100=PASS
ULTRA_GUARD_CHECK_101=PASS
ULTRA_GUARD_CHECK_102=PASS
ULTRA_GUARD_CHECK_103=PASS
ULTRA_GUARD_CHECK_104=PASS
ULTRA_GUARD_CHECK_105=PASS
ULTRA_GUARD_CHECK_106=PASS
ULTRA_GUARD_CHECK_107=PASS
ULTRA_GUARD_CHECK_108=PASS
ULTRA_GUARD_CHECK_109=PASS
ULTRA_GUARD_CHECK_110=PASS
ULTRA_GUARD_CHECK_111=PASS
ULTRA_GUARD_CHECK_112=PASS
ULTRA_GUARD_CHECK_113=PASS
ULTRA_GUARD_CHECK_114=PASS
ULTRA_GUARD_CHECK_115=PASS
ULTRA_GUARD_CHECK_116=PASS
ULTRA_GUARD_CHECK_117=PASS
ULTRA_GUARD_CHECK_118=PASS
ULTRA_GUARD_CHECK_119=PASS
ULTRA_GUARD_CHECK_120=PASS
ULTRA_GUARD_CHECK_121=PASS
ULTRA_GUARD_CHECK_122=PASS
ULTRA_GUARD_CHECK_123=PASS
ULTRA_GUARD_CHECK_124=PASS
ULTRA_GUARD_CHECK_125=PASS
ULTRA_GUARD_CHECK_126=PASS
ULTRA_GUARD_CHECK_127=PASS
ULTRA_GUARD_CHECK_128=PASS
ULTRA_GUARD_CHECK_129=PASS
ULTRA_GUARD_CHECK_130=PASS
ULTRA_GUARD_CHECK_131=PASS
ULTRA_GUARD_CHECK_132=PASS
ULTRA_GUARD_CHECK_133=PASS
ULTRA_GUARD_CHECK_134=PASS
ULTRA_GUARD_CHECK_135=PASS
ULTRA_GUARD_CHECK_136=PASS
ULTRA_GUARD_CHECK_137=PASS
ULTRA_GUARD_CHECK_138=PASS
ULTRA_GUARD_CHECK_139=PASS
ULTRA_GUARD_CHECK_140=PASS
ULTRA_GUARD_CHECK_141=PASS
ULTRA_GUARD_CHECK_142=PASS
ULTRA_GUARD_CHECK_143=PASS
ULTRA_GUARD_CHECK_144=PASS
ULTRA_GUARD_CHECK_145=PASS
ULTRA_GUARD_CHECK_146=PASS
ULTRA_GUARD_CHECK_147=PASS
ULTRA_GUARD_CHECK_148=PASS
ULTRA_GUARD_CHECK_149=PASS
ULTRA_GUARD_CHECK_150=PASS
ULTRA_GUARD_CHECK_151=PASS
ULTRA_GUARD_CHECK_152=PASS
ULTRA_GUARD_CHECK_153=PASS
ULTRA_GUARD_CHECK_154=PASS
ULTRA_GUARD_CHECK_155=PASS
ULTRA_GUARD_CHECK_156=PASS
ULTRA_GUARD_CHECK_157=PASS
ULTRA_GUARD_CHECK_158=PASS
ULTRA_GUARD_CHECK_159=PASS
ULTRA_GUARD_CHECK_160=PASS
ULTRA_GUARD_CHECK_161=PASS
ULTRA_GUARD_CHECK_162=PASS
ULTRA_GUARD_CHECK_163=PASS
ULTRA_GUARD_CHECK_164=PASS
ULTRA_GUARD_CHECK_165=PASS
ULTRA_GUARD_CHECK_166=PASS
ULTRA_GUARD_CHECK_167=PASS
ULTRA_GUARD_CHECK_168=PASS
ULTRA_GUARD_CHECK_169=PASS
ULTRA_GUARD_CHECK_170=PASS
ULTRA_GUARD_CHECK_171=PASS
ULTRA_GUARD_CHECK_172=PASS
ULTRA_GUARD_CHECK_173=PASS
ULTRA_GUARD_CHECK_174=PASS
ULTRA_GUARD_CHECK_175=PASS
ULTRA_GUARD_CHECK_176=PASS
ULTRA_GUARD_CHECK_177=PASS
ULTRA_GUARD_CHECK_178=PASS
ULTRA_GUARD_CHECK_179=PASS
ULTRA_GUARD_CHECK_180=PASS
ULTRA_GUARD_CHECK_181=PASS
ULTRA_GUARD_CHECK_182=PASS
ULTRA_GUARD_CHECK_183=PASS
ULTRA_GUARD_CHECK_184=PASS
ULTRA_GUARD_CHECK_185=PASS
ULTRA_GUARD_CHECK_186=PASS
ULTRA_GUARD_CHECK_187=PASS
ULTRA_GUARD_CHECK_188=PASS
ULTRA_GUARD_CHECK_189=PASS
ULTRA_GUARD_CHECK_190=PASS
ULTRA_GUARD_CHECK_191=PASS
ULTRA_GUARD_CHECK_192=PASS
ULTRA_GUARD_CHECK_193=PASS
ULTRA_GUARD_CHECK_194=PASS
ULTRA_GUARD_CHECK_195=PASS
ULTRA_GUARD_CHECK_196=PASS
ULTRA_GUARD_CHECK_197=PASS
ULTRA_GUARD_CHECK_198=PASS
ULTRA_GUARD_CHECK_199=PASS
ULTRA_GUARD_CHECK_200=PASS
ULTRA_GUARD_CHECK_201=PASS
ULTRA_GUARD_CHECK_202=PASS
ULTRA_GUARD_CHECK_203=PASS
ULTRA_GUARD_CHECK_204=PASS
ULTRA_GUARD_CHECK_205=PASS
ULTRA_GUARD_CHECK_206=PASS
ULTRA_GUARD_CHECK_207=PASS
ULTRA_GUARD_CHECK_208=PASS
ULTRA_GUARD_CHECK_209=PASS
ULTRA_GUARD_CHECK_210=PASS
ULTRA_GUARD_CHECK_211=PASS
ULTRA_GUARD_CHECK_212=PASS
ULTRA_GUARD_CHECK_213=PASS
ULTRA_GUARD_CHECK_214=PASS
ULTRA_GUARD_CHECK_215=PASS
ULTRA_GUARD_CHECK_216=PASS
ULTRA_GUARD_CHECK_217=PASS
ULTRA_GUARD_CHECK_218=PASS
ULTRA_GUARD_CHECK_219=PASS
ULTRA_GUARD_CHECK_220=PASS
ULTRA_GUARD_CHECK_221=PASS
ULTRA_GUARD_CHECK_222=PASS
ULTRA_GUARD_CHECK_223=PASS
ULTRA_GUARD_CHECK_224=PASS
ULTRA_GUARD_CHECK_225=PASS
ULTRA_GUARD_CHECK_226=PASS
ULTRA_GUARD_CHECK_227=PASS
ULTRA_GUARD_CHECK_228=PASS
ULTRA_GUARD_CHECK_229=PASS
ULTRA_GUARD_CHECK_230=PASS
ULTRA_GUARD_CHECK_231=PASS
ULTRA_GUARD_CHECK_232=PASS
ULTRA_GUARD_CHECK_233=PASS
ULTRA_GUARD_CHECK_234=PASS
ULTRA_GUARD_CHECK_235=PASS
ULTRA_GUARD_CHECK_236=PASS
ULTRA_GUARD_CHECK_237=PASS
ULTRA_GUARD_CHECK_238=PASS
ULTRA_GUARD_CHECK_239=PASS
ULTRA_GUARD_CHECK_240=PASS
ULTRA_GUARD_CHECK_241=PASS
ULTRA_GUARD_CHECK_242=PASS
ULTRA_GUARD_CHECK_243=PASS
ULTRA_GUARD_CHECK_244=PASS
ULTRA_GUARD_CHECK_245=PASS
ULTRA_GUARD_CHECK_246=PASS
ULTRA_GUARD_CHECK_247=PASS
ULTRA_GUARD_CHECK_248=PASS
ULTRA_GUARD_CHECK_249=PASS
ULTRA_GUARD_CHECK_250=PASS
ULTRA_GUARD_CHECK_251=PASS
ULTRA_GUARD_CHECK_252=PASS
ULTRA_GUARD_CHECK_253=PASS
ULTRA_GUARD_CHECK_254=PASS
ULTRA_GUARD_CHECK_255=PASS
ULTRA_GUARD_CHECK_256=PASS
ULTRA_GUARD_CHECK_257=PASS
ULTRA_GUARD_CHECK_258=PASS
ULTRA_GUARD_CHECK_259=PASS
ULTRA_GUARD_CHECK_260=PASS
ULTRA_GUARD_CHECK_261=PASS
ULTRA_GUARD_CHECK_262=PASS
ULTRA_GUARD_CHECK_263=PASS
ULTRA_GUARD_CHECK_264=PASS
ULTRA_GUARD_CHECK_265=PASS
ULTRA_GUARD_CHECK_266=PASS
ULTRA_GUARD_CHECK_267=PASS
ULTRA_GUARD_CHECK_268=PASS
ULTRA_GUARD_CHECK_269=PASS
ULTRA_GUARD_CHECK_270=PASS
ULTRA_GUARD_CHECK_271=PASS
ULTRA_GUARD_CHECK_272=PASS
ULTRA_GUARD_CHECK_273=PASS
ULTRA_GUARD_CHECK_274=PASS
ULTRA_GUARD_CHECK_275=PASS
ULTRA_GUARD_CHECK_276=PASS
ULTRA_GUARD_CHECK_277=PASS
ULTRA_GUARD_CHECK_278=PASS
ULTRA_GUARD_CHECK_279=PASS
ULTRA_GUARD_CHECK_280=PASS
ULTRA_GUARD_CHECK_281=PASS
ULTRA_GUARD_CHECK_282=PASS
ULTRA_GUARD_CHECK_283=PASS
ULTRA_GUARD_CHECK_284=PASS
ULTRA_GUARD_CHECK_285=PASS
ULTRA_GUARD_CHECK_286=PASS
ULTRA_GUARD_CHECK_287=PASS
ULTRA_GUARD_CHECK_288=PASS
ULTRA_GUARD_CHECK_289=PASS
ULTRA_GUARD_CHECK_290=PASS
ULTRA_GUARD_CHECK_291=PASS
ULTRA_GUARD_CHECK_292=PASS
ULTRA_GUARD_CHECK_293=PASS
ULTRA_GUARD_CHECK_294=PASS
ULTRA_GUARD_CHECK_295=PASS
ULTRA_GUARD_CHECK_296=PASS
ULTRA_GUARD_CHECK_297=PASS
ULTRA_GUARD_CHECK_298=PASS
ULTRA_GUARD_CHECK_299=PASS
ULTRA_GUARD_CHECK_300=PASS
ULTRA_GUARD_CHECK_301=PASS
ULTRA_GUARD_CHECK_302=PASS
ULTRA_GUARD_CHECK_303=PASS
ULTRA_GUARD_CHECK_304=PASS
ULTRA_GUARD_CHECK_305=PASS
ULTRA_GUARD_CHECK_306=PASS
ULTRA_GUARD_CHECK_307=PASS
ULTRA_GUARD_CHECK_308=PASS
ULTRA_GUARD_CHECK_309=PASS
ULTRA_GUARD_CHECK_310=PASS
ULTRA_GUARD_CHECK_311=PASS
ULTRA_GUARD_CHECK_312=PASS
ULTRA_GUARD_CHECK_313=PASS
ULTRA_GUARD_CHECK_314=PASS
ULTRA_GUARD_CHECK_315=PASS
ULTRA_GUARD_CHECK_316=PASS
ULTRA_GUARD_CHECK_317=PASS
ULTRA_GUARD_CHECK_318=PASS
ULTRA_GUARD_CHECK_319=PASS
ULTRA_GUARD_CHECK_320=PASS
ULTRA_GUARD_CHECK_321=PASS
ULTRA_GUARD_CHECK_322=PASS
ULTRA_GUARD_CHECK_323=PASS
ULTRA_GUARD_CHECK_324=PASS
ULTRA_GUARD_CHECK_325=PASS
ULTRA_GUARD_CHECK_326=PASS
ULTRA_GUARD_CHECK_327=PASS
ULTRA_GUARD_CHECK_328=PASS
ULTRA_GUARD_CHECK_329=PASS
ULTRA_GUARD_CHECK_330=PASS
ULTRA_GUARD_CHECK_331=PASS
ULTRA_GUARD_CHECK_332=PASS
ULTRA_GUARD_CHECK_333=PASS
ULTRA_GUARD_CHECK_334=PASS
ULTRA_GUARD_CHECK_335=PASS
ULTRA_GUARD_CHECK_336=PASS
ULTRA_GUARD_CHECK_337=PASS
ULTRA_GUARD_CHECK_338=PASS
ULTRA_GUARD_CHECK_339=PASS
ULTRA_GUARD_CHECK_340=PASS
ULTRA_GUARD_CHECK_341=PASS
ULTRA_GUARD_CHECK_342=PASS
ULTRA_GUARD_CHECK_343=PASS
ULTRA_GUARD_CHECK_344=PASS
ULTRA_GUARD_CHECK_345=PASS
ULTRA_GUARD_CHECK_346=PASS
ULTRA_GUARD_CHECK_347=PASS
ULTRA_GUARD_CHECK_348=PASS
ULTRA_GUARD_CHECK_349=PASS
ULTRA_GUARD_CHECK_350=PASS
ULTRA_GUARD_CHECK_351=PASS
ULTRA_GUARD_CHECK_352=PASS
ULTRA_GUARD_CHECK_353=PASS
ULTRA_GUARD_CHECK_354=PASS
ULTRA_GUARD_CHECK_355=PASS
ULTRA_GUARD_CHECK_356=PASS
ULTRA_GUARD_CHECK_357=PASS
ULTRA_GUARD_CHECK_358=PASS
ULTRA_GUARD_CHECK_359=PASS
ULTRA_GUARD_CHECK_360=PASS
ULTRA_GUARD_CHECK_361=PASS
ULTRA_GUARD_CHECK_362=PASS
ULTRA_GUARD_CHECK_363=PASS
ULTRA_GUARD_CHECK_364=PASS
ULTRA_GUARD_CHECK_365=PASS
ULTRA_GUARD_CHECK_366=PASS
ULTRA_GUARD_CHECK_367=PASS
ULTRA_GUARD_CHECK_368=PASS
ULTRA_GUARD_CHECK_369=PASS
ULTRA_GUARD_CHECK_370=PASS
ULTRA_GUARD_CHECK_371=PASS
ULTRA_GUARD_CHECK_372=PASS
ULTRA_GUARD_CHECK_373=PASS
ULTRA_GUARD_CHECK_374=PASS
ULTRA_GUARD_CHECK_375=PASS
ULTRA_GUARD_CHECK_376=PASS
ULTRA_GUARD_CHECK_377=PASS
ULTRA_GUARD_CHECK_378=PASS
ULTRA_GUARD_CHECK_379=PASS
ULTRA_GUARD_CHECK_380=PASS
ULTRA_GUARD_CHECK_381=PASS
ULTRA_GUARD_CHECK_382=PASS
ULTRA_GUARD_CHECK_383=PASS
ULTRA_GUARD_CHECK_384=PASS
ULTRA_GUARD_CHECK_385=PASS
ULTRA_GUARD_CHECK_386=PASS
ULTRA_GUARD_CHECK_387=PASS
ULTRA_GUARD_CHECK_388=PASS
ULTRA_GUARD_CHECK_389=PASS
ULTRA_GUARD_CHECK_390=PASS
ULTRA_GUARD_CHECK_391=PASS
ULTRA_GUARD_CHECK_392=PASS
ULTRA_GUARD_CHECK_393=PASS
ULTRA_GUARD_CHECK_394=PASS
ULTRA_GUARD_CHECK_395=PASS
ULTRA_GUARD_CHECK_396=PASS
ULTRA_GUARD_CHECK_397=PASS
ULTRA_GUARD_CHECK_398=PASS
ULTRA_GUARD_CHECK_399=PASS
ULTRA_GUARD_CHECK_400=PASS
STEP_007_VERIFY_SCOPE_LIVE_AND_MANIFEST
VERIFY=generated_scope_only
ALLOWED_ROOT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion
GENERATED_SCOPE=PASS


component             status path                                                                                      
---------             ------ ----                                                                                      
index_html            FAIL   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\index.html                           
security_overlay_js   PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\security_overlay.js                  
low_review_overlay_js PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\remaining_low_review_overlay.js      
security_geojson      PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_scores_rechec...
low_review_geojson    PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\remaining_low_current_review....
security_summary_json PASS   C:\Users\cagda\Documents\GitHub\AAYS\england_map_web\data\parcel_security_match_summary...



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_224509.csv

OVERALL=FAIL

SCOPE_STATUS=PASS
LIVE_STATUS=FAIL
LIVE_DIFF_FINAL=
LIVE_DIFF_FINAL_STATUS=PASS
WROTE=security_accuracy_expansion/ultra_scope_20260507/ULTRA_SCOPE_ARTIFACT_MANIFEST.csv
STEP_008_FINAL_REPORT_AND_RESULT_MATERIALIZATION
WROTE=security_accuracy_expansion/run_reports/ultra_scope_final_report_20260507_224402.md
RESULT_FILE=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\terrayield-145-security-accuracy-expansion-ultra-scope-pack-status.txt
STEP_009_GUARDED_COMMIT_SECURITY_ONLY
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
STEP_010_COMPLETE
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_145_DONE

``

## Error
``text

``
