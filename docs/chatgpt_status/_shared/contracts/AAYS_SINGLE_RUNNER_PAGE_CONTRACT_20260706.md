# AAYS Single Shared Runner Page Contract 20260706

Repo: cagdascagdas100/chat_gpt_clone_1
Branch: main
Runner mode: single_shared_runner

## Non-Negotiable Rules

- Do not start a second parallel runner.
- Do not fabricate completed output.
- Do not mark `final_ready=true` without real gate evidence.
- Do not fabricate 100 percent progress.
- Do not write fake rows, source URLs, source dates, browser proof, or production evidence.
- Do not perform DB writes, migrations, DDL, or production deploys.
- Do not commit outside each task's `allowed_paths`.
- If evidence is missing, write a blocker and keep `final_ready=false`.

## Page Identity

Every page is identified by a directory:

```text
docs/chatgpt_status/<PAGE_KEY>/
```

Queue files live under:

```text
docs/chatgpt_status/<PAGE_KEY>/queue/<TASK_ID>.json
```

The queue payload `page_key` must match the page key from the path. If it does
not match, the runner must block the task with `PAGE_KEY_PATH_MISMATCH`.

## Required Page Directories

Each page key may have these directories. Creating the directories is only
structure setup; it is not proof of task completion.

```text
queue/
status/
reports/
heartbeat/
completed/
blocked/
runner_outputs/
automation/
fixtures/
```

## Runnable Queue Contract

Runnable queue JSON must include these fields:

```json
{
  "task_id": "stable-task-id",
  "page_key": "example_page_key",
  "status": "queued",
  "priority": 100,
  "target_branch": "main",
  "script_path": "docs/chatgpt_status/example_page_key/automation/example_task.ps1",
  "automation_script": "docs/chatgpt_status/example_page_key/automation/example_task.ps1",
  "allowed_paths": [
    "docs/chatgpt_status/example_page_key/"
  ],
  "new_runner_allowed": false,
  "single_shared_runner_required": true,
  "no_fake_final_ready": true,
  "no_db_write": true,
  "no_migration": true,
  "no_production_deploy": true,
  "final_ready": false
}
```

`script_path` and `automation_script` should both be present and should point to
the same relative path. Legacy files may contain only one of them; the
normalizer can produce a non-destructive normalized alias.

## Runnable Status Values

The runner may pick up only:

```text
queued
ready
pending
pending_repo_queue
pickup_requested
queued_for_single_shared_runner
retry_pending
failed_transient
```

The runner must not pick up:

```text
running
done
completed
done_on_target_branch
superseded
superseded_by_force_pickup
blocked
failed
failed_final
blocked_manual
archived
```

## Lifecycle Evidence

For each task, the runner must write task-level evidence under the same page:

```text
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_started.json
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_gate.json
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_completed.json
docs/chatgpt_status/<PAGE_KEY>/completed/<TASK_ID>_completed.json
docs/chatgpt_status/<PAGE_KEY>/reports/<TASK_ID>_runner_output.txt
docs/chatgpt_status/<PAGE_KEY>/heartbeat/<TASK_ID>_heartbeat.txt
docs/chatgpt_status/_shared/status/queue_result_mirror_<TASK_ID>.json
```

If the task is blocked, the runner writes blocker evidence instead of claiming
success:

```text
docs/chatgpt_status/<PAGE_KEY>/blocked/<TASK_ID>_blocked.json
docs/chatgpt_status/<PAGE_KEY>/reports/<TASK_ID>_runner_output.txt
docs/chatgpt_status/_shared/status/queue_result_mirror_<TASK_ID>.json
```

## Completed JSON Minimum Fields

```json
{
  "task_id": "<TASK_ID>",
  "page_key": "<PAGE_KEY>",
  "completed_at": "<ISO-UTC>",
  "queue_seen": true,
  "queue_started": true,
  "single_runner_lock_acquired": true,
  "task_runs_in_clean_worktree": true,
  "allowed_paths_enforced": true,
  "runner_output_uploaded": true,
  "post_sync_ok": true,
  "PUSH_SYNC_OK": true,
  "CONTINUE_RUNNER_READY": true,
  "final_ready": false,
  "fake_data": false,
  "db_write": false,
  "migration": false,
  "production_deploy": false,
  "blockers": []
}
```

## Panel Index

The canonical panel index is:

```text
docs/chatgpt_status/_shared/panel/page_status_index_latest.json
```

Compatibility mirrors may also be generated at:

```text
docs/chatgpt_status/_shared/status/page_panel_index.json
docs/chatgpt_status/_shared/status/pages_status_dashboard.json
england_map_web/data/runner_panel/page_status_index.json
```

Task-level completed/status/heartbeat evidence takes priority over stale shared
heartbeat files. Missing `script_path`, missing `automation_script`, missing
`allowed_paths`, and missing safety flags must remain visible in the panel
index.
