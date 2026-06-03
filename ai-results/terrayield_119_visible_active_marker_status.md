# TerraYield 119 Visible Active Marker Status

Task: `terrayield-119-plan-l-active-min`

## Observed runner state

- `current-task.json` points to `terrayield-119-plan-l-active-min`.
- `.last-task-id` also points to `terrayield-119-plan-l-active-min`.
- Runner heartbeat is current and polling.

## What the 119 task materializes

The 119 script writes these active delivery marker files into the TerraYield project:

```text
data/live_feeds/active/terrayield_l4_fail_closed_current.json
data/live_feeds/active/terrayield_london_locations_current.csv
data/live_feeds/active/README_TERRAYIELD_L4_FAIL_CLOSED.md
```

The manifest is expected to contain:

```text
status=active_read_only_plan_l_manifest_accept
rows=34864
features=34864
match=true
ui_patch_applied=false
db_import_applied=false
```

## Intended safety semantics

```text
NO_DB_IMPORT=true
NO_UI_PATCH=true
READ_ONLY_ACTIVE_MARKER=true
```

## Known upstream Plan L evidence

From task `terrayield-114-runner-probe-plan-l-minipack`:

```text
PLAN_L_RUN_EXIT=0
CLASSIFIED_ROWS=34864
RESULT=runner_alive_plan_l_outputs_present
```

From task `terrayield-115-plan-l-final-pack-wide-qa`:

```text
CLASSIFIER_EXIT=0
DEEP_QA_EXIT=0
CSV_ROWS=34864
GEOJSON_FEATURES=34864
rows_features_match=True
summary_exists=True
confidence_summary_exists=True
```

## Conclusion

119 is accepted as the last task and is intended to close the active marker visibility gap. Because the script writes checks to stdout rather than a stable `ai-results/*-status.txt`, this report preserves the visible interpretation for Codex and for the continue workflow.

Current acceptance position:

```text
PLAN_L_CLASSIFICATION=complete
PLAN_L_QA=complete
ACTIVE_MARKER_TASK=accepted
DATABASE_IMPORT=not_applied
UI_PATCH=not_applied
NEXT_COMMAND=devam et
```
