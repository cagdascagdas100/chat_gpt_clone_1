# Runner Push Chain Check

page_key=security_public_safety_low_credit_20260612
task_file=terrayield-050-security-single-runner-contract-alignment-20260625_002339.task.json
repo_task=C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\security_public_safety_low_credit_20260612\queue\terrayield-050-security-single-runner-contract-alignment-20260625_002339.task.json
bridge_task=F:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue\pending\terrayield-050-security-single-runner-contract-alignment-20260625_002339.task.json
script_path=C:\Users\cagda\Documents\GitHub\AAYS\docs\chatgpt_status\security_public_safety_low_credit_20260612\automation\vrun.ps1
bridge_root=F:\AAYS_GITHUB_BRIDGE_CLEAN2

pending_exists=False
expected_output_glob=docs/chatgpt_status/security_public_safety_low_credit_20260612/runner_outputs/050_runner_output_*.log
expected_report_glob=docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/050_single_runner_apply_*.md

runner_pickup_check=if pending_exists stays true, runner did not pick up task
runner_push_check=if 050_* files are absent on GitHub, push chain failed
