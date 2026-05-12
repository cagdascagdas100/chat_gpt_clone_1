# TerraYield Autopilot V8.4 Result

task_id: cost50-013b-artifact-manifest-audit-retry-20260512
title: Cost50 Step 013 artifact manifest audit retry
exit_code: 0
message: completed_by_v84
time: 2026-05-12T13:28:16

## Output
```text
[2026-05-12T13:28:14] TASK=cost50-013-artifact-manifest-audit-20260512
[2026-05-12T13:28:14] PROJECT_ROOT=E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence
[2026-05-12T13:28:15] project_root=True :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence
[2026-05-12T13:28:15] app_main=True :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\app\main.py
[2026-05-12T13:28:15] models=True :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\app\db\models.py
[2026-05-12T13:28:15] alembic=True :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\alembic
[2026-05-12T13:28:15] requirements=False :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\requirements.txt
[2026-05-12T13:28:15] readme=False :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\README.md
[2026-05-12T13:28:15] tests=False :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\tests
[2026-05-12T13:28:15] scripts=False :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\scripts
[2026-05-12T13:28:15] tools=True :: E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence\tools
[2026-05-12T13:28:15] quality_reports=True :: E:\AAYS_DATA\cost\quality_reports
[2026-05-12T13:28:15] PYTHON_COUNT=9
[2026-05-12T13:28:15] MARKDOWN_COUNT=4
[2026-05-12T13:28:15] SQL_COUNT=0
[2026-05-12T13:28:15] CSV_COUNT=9
[2026-05-12T13:28:15] JSON_COUNT=4
[2026-05-12T13:28:15] YAML_COUNT=0
[2026-05-12T13:28:15] REPORTS_COUNT=4
[2026-05-12T13:28:16] REPORT_PATH=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\cost50-013-artifact-manifest-audit-20260512.report.md
[2026-05-12T13:28:16] EXTERNAL_REPORT_PATH=E:\AAYS_DATA\cost\quality_reports\cost50-013-artifact-manifest-audit-20260512.report.md
[2026-05-12T13:28:16] MANIFEST_PATH=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\cost50-013-artifact-manifest-audit-20260512.manifest.json
[2026-05-12T13:28:16] MANIFEST_EXTERNAL=E:\AAYS_DATA\cost\quality_reports\cost50-013-artifact-manifest-audit-20260512.manifest.json
[2026-05-12T13:28:16] PLAN_PROGRESS_PERCENT=67
[2026-05-12T13:28:16] TASK_COMPLETION=100/100
[2026-05-12T13:28:16] TERRAYIELD_TASK_DONE

```

## Error
```text
Set-Content : Ak�� okunabilir de�ildi.
At C:\AAYS_GITHUB_BRIDGE_CLEAN\ai-task-scripts\terrayield_cost50_013_artifact_manifest_audit.ps1:51 char:41
+ ... ertTo-Json -Depth 8) | Set-Content -Path $manifestPath -Encoding UTF8
+                            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (C:\Users\cagda\...2.manifest.json:String) [Set-Content], ArgumentExcep 
   tion
    + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
 
Set-Content : ��lem, ba�ka bir i�lem taraf�ndan kullan�ld���ndan 'C:\Users\cagda\Documents\chat_gpt_clone_1\ai-results\
cost50-013-artifact-manifest-audit-20260512.report.md' dosyas�na eri�emiyor.
At C:\AAYS_GITHUB_BRIDGE_CLEAN\ai-task-scripts\terrayield_cost50_013_artifact_manifest_audit.ps1:86 char:11
+ $report | Set-Content -Path $out -Encoding UTF8
+           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:) [Set-Content], IOException
    + FullyQualifiedErrorId : System.IO.IOException,Microsoft.PowerShell.Commands.SetContentCommand
 

```
