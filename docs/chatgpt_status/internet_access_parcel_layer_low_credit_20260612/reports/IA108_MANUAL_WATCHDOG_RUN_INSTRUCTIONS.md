# IA108 manual watchdog run instructions

Use this only after the GitHub pointer files are present but the runner has not produced the IA108 reports.

Repository: cagdascagdas100/chat_gpt_clone_1
Branch: feature/terrayield-aays-integration
Page key: internet_access_parcel_layer_low_credit_20260612

Run from the repository root:

```powershell
git checkout feature/terrayield-aays-integration
powershell -NoProfile -ExecutionPolicy Bypass -File "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/automation/ia108_runner_watchdog_v2_execute.ps1"
git add "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports" "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/status" "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/runner_outputs" "docs/chatgpt_status/reports"
git commit -m "ia108 run watchdog and publish reports"
git push
```

Expected generated evidence:

```text
docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/ia108_runner_watchdog_v2_execute_report.json
docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/reports/ia108_real_geometry_join_v2_schema_probe_report.json
docs/chatgpt_status/reports/internet-access-108-real-parcel-final-gate.json
```

Do not hand-create final JSON reports. They must be produced by the watchdog or v2 script.
