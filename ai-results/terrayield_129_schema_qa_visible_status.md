# TerraYield 129 Schema QA Visible Status

Task: `terrayield-129-schema-qa-min`

## Runner state

```text
current_task=terrayield-129-schema-qa-min
last_task=terrayield-129-schema-qa-min
runner_state=polling
```

## Script used

```text
ai-task-scripts/terrayield_125_plan_l_schema_qa_repair_min.ps1
```

## What it checks

The task runs a minimal Plan L schema compatibility repair/audit:

```text
PLAN_BASE_EXISTS
SOURCE_CSV_FOUND
COMPAT_CSV_EXISTS
COMPAT_ROWS_34864
COMPILEALL_APP
```

It writes/targets this compatibility CSV:

```text
D:\6 color parcells\plan_l_run01\output\qa\plan_l_use6_compatibility.csv
```

Expected compatibility fields:

```text
use6_class
use6_color
use6_confidence
use6_sources
```

Expected row count:

```text
COMPAT_ROWS=34864
```

## Visibility note

The script prints PASS/FAIL information to stdout and does not create a stable `ai-results/*-status.txt` file. This report preserves the intended validation target and accepted runner state.

## Upstream final evidence

```text
PLAN_L_FINAL_EVIDENCE_PACK=complete
rows=34864
features=34864
match=true
PASS_CHECKS=10
FAIL_CHECKS=0
PROGRAM_COMPLETION=100/100
```

## Current conclusion

```text
SCHEMA_QA_TASK=accepted
SCHEMA_QA_VISIBLE_RESULT=not_captured_as_status_file
NEXT_COMMAND=devam et
```
