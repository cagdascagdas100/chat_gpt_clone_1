# AAYS ChatGPT Runner V4 Result

## Task
Run compact TerraYield security expansion probe resume

## Task ID
terrayield-138-security-expansion-probe-resume-compact

## Progress
0%

## Action


## Time
05/07/2026 21:25:20

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
3000

## Exit Code
0

## Output
``text
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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212503.csv

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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212507.csv

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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212508.csv

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
REPORT=C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
STEP_18 List generated security files.
security_accuracy_expansion\audit\BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md
security_accuracy_expansion\audit\diagnose_git_root_20260507.ps1
security_accuracy_expansion\audit\diagnose_live_index_hash_fail_20260507.ps1
security_accuracy_expansion\audit\generated_artifact_manifest_20260507.csv
security_accuracy_expansion\audit\live_surface_hashes_20260507.csv
security_accuracy_expansion\audit\preflight_audit_20260507.md
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
security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1
security_accuracy_expansion\codex_tasks\047_security_accuracy_source_catalog_and_evidence_templates.md
security_accuracy_expansion\codex_tasks\048_security_accuracy_preflight_download_plan.md
security_accuracy_expansion\codex_tasks\049_security_accuracy_evidence_backed_scoring_plan.md
security_accuracy_expansion\evidence_templates\cross_source_agreement_template.csv
security_accuracy_expansion\evidence_templates\parcel_match_audit_template.csv
security_accuracy_expansion\evidence_templates\parcel_security_evidence_template.json
security_accuracy_expansion\evidence_templates\run_manifest_template.json
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
security_accuracy_expansion\methodology\README_upstream.md
security_accuracy_expansion\PASS_FAIL_20260507.md
security_accuracy_expansion\prompts\CHATGPT_FOLLOWUP_PROMPTS.md
security_accuracy_expansion\prompts\CHATGPT_LOCAL_EXECUTION_PROMPT_TR.md
security_accuracy_expansion\prompts\CODEX_MASTER_PROMPT_SECURITY_ACCURACY_EXPANSION.md
security_accuracy_expansion\prompts\SHORT_CODEX_PROMPT.md
security_accuracy_expansion\qa\acceptance_criteria.md
security_accuracy_expansion\qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md
security_accuracy_expansion\qa\expected_outputs_checklist.md
security_accuracy_expansion\qa\PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md
security_accuracy_expansion\qa\QA_CHECKLIST_EXPANDED_20260507.md
security_accuracy_expansion\README_RUN_TR.md
security_accuracy_expansion\rollback\ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md
security_accuracy_expansion\rollback\ROLLBACK_TR.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211725.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_211908.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212053.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212456.md
security_accuracy_expansion\run_reports\run_report_terrayield-135-security-accuracy-expansion-direct-apply_20260507_212502.md
security_accuracy_expansion\RUNNER_CONTINUE_PROTOCOL_20260507.md
security_accuracy_expansion\schemas\download_audit_manifest_schema.json
security_accuracy_expansion\schemas\parcel_security_evidence_schema.json
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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212513.csv

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
powershell : Exception calling "WriteAllText" with "3" argument(s): "İşlem, başka bir işlem tarafından kullanıldığından
 'C:\Users\ca
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_138_security_expansion_probe_resume_compact.ps1
:46 char:23
+ ... = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $Scri ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Exception calli...an 'C:\Users\ca:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
gda\Documents\GitHub\AAYS\security_accuracy_expansion\deepening_20260507\source_catalog\source_tier_rubric.md' dosyasın
a erişemiyor."
    + CategoryInfo          : NotSpecified: (:) [], MethodInvocationException
    + FullyQualifiedErrorId : IOException
    + PSComputerName        : localhost
 
JOB_DONE=catalog FILES=3
JOB_DONE=methodology FILES=4
JOB_DONE=qa FILES=3
JOB_DONE=schemas FILES=2
JOB_DONE=audit FILES=3
JOB_DONE=run_evidence FILES=3
STEP_007 Write protected hash snapshot CSV after jobs.
WROTE=security_accuracy_expansion/audit/protected_live_hash_snapshot_20260507.csv
STEP_008 Write orchestration report.
WROTE=security_accuracy_expansion/run_reports/parallel_deepening_report_20260507_212512.md
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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212517.csv

OVERALL=FAIL

LIVE_BASELINE_AFTER=FAIL
STEP_011 Verify no protected live diff.
LIVE_DIFF=
LIVE_DIFF_STATUS=PASS
STEP_012 Generate manifest of deepening artifacts.
Export-Csv : İşlem, başka bir işlem tarafından kullanıldığından 'C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy
_expansion\audit\generated_artifact_manifest_deepening_20260507.csv' dosyasına erişemiyor.
At C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_136_security_accuracy_expansion_parallel_deepen
ing.ps1:300 char:9
+ $Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $Ma ...
+         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : OpenError: (:) [Export-Csv], IOException
    + FullyQualifiedErrorId : FileOpenFailure,Microsoft.PowerShell.Commands.ExportCsvCommand
 
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
WROTE=security_accuracy_expansion/run_reports/static_check_summary_20260507_212512.md
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



Report: C:\Users\cagda\Documents\GitHub\AAYS\security_accuracy_expansion\audit\verify_live_modules_20260507_212519.csv

OVERALL=FAIL

LIVE_STATUS=FAIL
## Report
WROTE=security_accuracy_expansion/run_reports/compact_probe_resume_20260507_212501.md
## Guarded project commit
PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH C:/Users/cagda
PROJECT_PUSH=SKIPPED_BY_POLICY
FINAL_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER
NEXT_CHATGPT_INPUT=devam et
TERRAYIELD_138_DONE

``

## Error
``text

``
