# AAYS single shared runner contract

This contract is the canonical shape for all ChatGPT page continuation work.

## Runner entry

Root `devam.ps1` must call only:

`docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`

The wrapper calls the current V4 runner:

`docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V4_20260706.ps1`

## Canonical page layout

For each page key:

```text
docs/chatgpt_status/<page_key>/queue
docs/chatgpt_status/<page_key>/status
docs/chatgpt_status/<page_key>/reports
docs/chatgpt_status/<page_key>/heartbeat
docs/chatgpt_status/<page_key>/runner_outputs
```

## Queue task required fields

```json
{
  "task_id": "short-unique-task-id",
  "page_key": "page_key_matching_folder",
  "status": "pending",
  "target_branch": "main",
  "script_path": "docs/chatgpt_status/<page_key>/automation/<script>.ps1",
  "allowed_paths": [
    "docs/chatgpt_status/<page_key>",
    "docs/chatgpt_status/_shared/status",
    "docs/chatgpt_status/_shared/reports",
    "docs/chatgpt_status/_shared/heartbeat"
  ],
  "no_fake_final_ready": true,
  "no_db_write": true,
  "no_migration": true,
  "no_production_deploy": true
}
```

`automation_script` is accepted as a backward-compatible alias, but new files must use `script_path`.

## Lifecycle

A valid task must move through this lifecycle:

```text
pending -> running -> done
```

If the automation cannot run, the queue must not stay ambiguous. It must write a status file and report file under the same page key.

## Evidence gates

The runner may write `final_ready=true` only after real output evidence exists and the page-specific gate passes. In all other cases it must write `final_ready=false` and a blocker/status explanation.

## Panel source

The panel should read:

`docs/chatgpt_status/_shared/status/page_panel_index.json`

This index is built from `PAGE_KEY_REGISTRY.json`, queue files, heartbeat files, completion files, reports, and page latest changes files.
