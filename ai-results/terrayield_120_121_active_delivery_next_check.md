# TerraYield 120 / 121 Active Delivery Next Check

## Current accepted state

```text
current_task=terrayield-120-status-check
last_task=terrayield-120-status-check
runner_state=polling
```

## Reason for next check

Task 120 was accepted by the runner but did not create a visible status file under `ai-results`. The next check should only verify the active Plan L marker files and write a stable result file.

## Files to verify in the TerraYield project

```text
data/live_feeds/active/terrayield_l4_fail_closed_current.json
data/live_feeds/active/terrayield_london_locations_current.csv
data/live_feeds/active/README_TERRAYIELD_L4_FAIL_CLOSED.md
```

## Expected active manifest values

```text
rows=34864
features=34864
match=true
ui_patch_applied=false
db_import_applied=false
```

## Known upstream evidence

```text
plan_l_run_exit=0
classified_rows=34864
csv_rows=34864
geojson_features=34864
rows_features_match=true
plan_l_active_marker=accepted
```

## Desired final visible status

```text
ACTIVE_FILES_ACCEPTANCE=100/100
PASS_CHECKS=<count>
FAIL_CHECKS=0
NO_UI_PATCH=true
NO_DB_IMPORT=true
NEXT_COMMAND=devam et
```
