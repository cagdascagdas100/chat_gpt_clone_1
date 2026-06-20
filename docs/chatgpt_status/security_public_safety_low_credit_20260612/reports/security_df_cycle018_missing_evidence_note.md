# Security DF cycle018 missing evidence note

PAGE_KEY: security_public_safety_low_credit_20260612
TASK_ID: security_public_safety_20260619_df_parcel_contract

Current usable entrypoint:
- docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/vrun.ps1

Expected evidence files still needed:
- docs/chatgpt_status/security_public_safety_low_credit_20260612/runner_outputs/security_20260619_df_headerfix_runner_output_YYYYMMDD_HHMMSS.md
- docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/security_df_worktree_smoke_report_YYYYMMDD_HHMMSS.md
- docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/security_df_worktree_final_wrapper_YYYYMMDD_HHMMSS.md

Required final markers:
- FINAL_STATUS=FINAL_READY_CONFIRMED
- PRODUCT_PROGRESS_ESTIMATE=100
- PRODUCTION_COMPLETE=true

Status:
- Do not create a fake final wrapper.
- Use the existing vrun.ps1 entrypoint to produce real runner evidence.
- Keep separate_runner=false.
- Keep db_write=false, ddl=false, migration=false, production_deploy=false, fake_data=false.
