# TerraYield 118 Visible Active Delivery Gap Report

Task: `terrayield-118-plan-l-active-delivery-check`

## Current observed state

- `current-task.json` points to `terrayield-118-plan-l-active-delivery-check`.
- `.last-task-id` also points to `terrayield-118-plan-l-active-delivery-check`.
- Runner heartbeat is current and polling.

## What 118 checks

The 118 script validates these files inside the TerraYield project:

```text
data/live_feeds/active/terrayield_l4_fail_closed_current.json
data/live_feeds/active/terrayield_london_locations_current.csv
data/live_feeds/active/README_TERRAYIELD_L4_FAIL_CLOSED.md
```

It checks:

```text
manifest exists
London CSV exists
README exists
manifest status starts with active
rows_total == 3110
rows_london == 606
ui_patch_applied == false
db_import_applied == false
London CSV row count == 606
python -m compileall app succeeds
```

## Visibility issue

The 118 script writes most validation output to stdout but does not persist a stable status file under `ai-results`. Because of that, the task is accepted as last-task but the exact PASS/FAIL result is not visible in GitHub search.

## Known previous successful Plan L results

From task `terrayield-114-runner-probe-plan-l-minipack`:

```text
PLAN_L_RUN_EXIT=0
CLASSIFIED_ROWS=34864
RESULT=runner_alive_plan_l_outputs_present
```

From task `terrayield-115-plan-l-final-pack-wide-qa` / script `terrayield-112-plan-l-recovery-final-pack`:

```text
CLASSIFIER_EXIT=0
DEEP_QA_EXIT=0
CSV_ROWS=34864
GEOJSON_FEATURES=34864
rows_features_match=True
summary_exists=True
confidence_summary_exists=True
final_zip_exists=False
```

## Conclusion

Plan L classification and QA succeeded, but final ZIP packaging needed repair. 118 was intended to validate the active delivery manifest after the manifest acceptance step. The next useful automation should persist a visible active-delivery result file with:

```text
PLAN_L_ACTIVE_DELIVERY=100/100 or needs_attention
PASS_CHECKS=<count>
FAIL_CHECKS=<count>
ROWS_TOTAL=3110
ROWS_LONDON=606
LONDON_CSV_ROWS=606
NO_UI_PATCH=true
NO_DB_IMPORT=true
```
