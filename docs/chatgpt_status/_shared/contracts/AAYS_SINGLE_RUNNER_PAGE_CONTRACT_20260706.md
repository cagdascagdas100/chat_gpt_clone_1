# AAYS Single Shared Runner Page Contract — 2026-07-06

This contract standardizes every ChatGPT page under `docs/chatgpt_status/<PAGE_KEY>/` so the single shared canonical runner can discover, pick up, execute, report, and resume work without page-specific assumptions.

## Required page key rules

Each page must have one stable `page_key` value. The canonical page folder is:

```text
docs/chatgpt_status/<PAGE_KEY>/
```

The runner must infer page ownership from the queue path and verify it matches the queue payload:

```text
queue path: docs/chatgpt_status/<PAGE_KEY>/queue/<TASK_ID>.json
payload.page_key: <PAGE_KEY>
```

If these do not match, the queue is invalid and must be reported as `PAGE_KEY_PATH_MISMATCH` rather than executed.

## Required folder structure per page

```text
docs/chatgpt_status/<PAGE_KEY>/queue/
docs/chatgpt_status/<PAGE_KEY>/status/
docs/chatgpt_status/<PAGE_KEY>/reports/
docs/chatgpt_status/<PAGE_KEY>/heartbeat/
docs/chatgpt_status/<PAGE_KEY>/completed/
docs/chatgpt_status/<PAGE_KEY>/runner_outputs/
docs/chatgpt_status/<PAGE_KEY>/automation/
docs/chatgpt_status/<PAGE_KEY>/fixtures/
```

`completed/` is optional for legacy pages, but every new page must include it. Status mirrors may still be written under `status/` for compatibility.

## Valid queue JSON contract

Every executable queue file must be JSON and must include:

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
  "no_fake_final_ready": true,
  "no_db_write": true,
  "no_migration": true,
  "no_production_deploy": true,
  "final_ready": false
}
```

The runner may accept `script_path` or `automation_script`, but new tasks must provide both with the same relative path.

## Valid queue statuses

Executable:

```text
queued
ready
pending
pending_repo_queue
pickup_requested
queued_for_single_shared_runner
```

Non-executable:

```text
running
done
done_on_target_branch
superseded
superseded_by_force_pickup
blocked
failed
```

## Required output contract

For task id `<TASK_ID>`, the runner should write real evidence files:

```text
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_started.json
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_gate.json
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_completed.json
docs/chatgpt_status/<PAGE_KEY>/reports/<TASK_ID>_runner_output.txt
docs/chatgpt_status/<PAGE_KEY>/heartbeat/<TASK_ID>_heartbeat.txt
docs/chatgpt_status/_shared/status/queue_result_mirror_<TASK_ID>.json
```

For new pages, also write:

```text
docs/chatgpt_status/<PAGE_KEY>/completed/<TASK_ID>_completed.json
```

## Required completed JSON fields

```json
{
  "task_id": "stable-task-id",
  "page_key": "example_page_key",
  "completed_at": "ISO-UTC",
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

## Legacy queue normalization rules

For old or broken queue files:

1. If `page_key` is missing, infer it from `docs/chatgpt_status/<PAGE_KEY>/queue/` and create a normalized alias JSON instead of mutating evidence.
2. If `script_path` is missing but `automation_script` exists, copy it into `script_path`.
3. If `automation_script` is missing but `script_path` exists, copy it into `automation_script`.
4. If both script fields are missing, mark the queue invalid with `MISSING_script_path_OR_automation_script`.
5. If `allowed_paths` is missing, use the page folder only: `docs/chatgpt_status/<PAGE_KEY>/`.
6. If safety flags are missing, normalized aliases must set:
   - `no_fake_final_ready=true`
   - `no_db_write=true`
   - `no_migration=true`
   - `no_production_deploy=true`
7. Never set `final_ready=true` in a normalization pass.
8. Never fabricate data rows, source URLs, source dates, browser proof, or production readiness evidence.

## Panel status contract

The status panel should read a shared index at:

```text
docs/chatgpt_status/_shared/panel/page_status_index_latest.json
```

Each page entry should contain:

```json
{
  "page_key": "example_page_key",
  "display_name": "Example Page",
  "latest_queue_status": "queued|running|done|blocked|unknown",
  "latest_task_id": "stable-task-id",
  "completion_percent": 0,
  "remaining_percent": 100,
  "final_ready": false,
  "last_heartbeat_at": null,
  "last_completed_at": null,
  "blockers": [],
  "evidence_paths": []
}
```

## New ChatGPT page pickup rule

A new ChatGPT page must create exactly one canonical queue JSON under its own page key folder. It must not open a new runner. It must rely on the existing shared runner:

```text
docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
```

A new page is pickup-ready when:

```text
page_key exists
queue JSON is valid
script_path exists
allowed_paths are present
safety flags are true
status is queued/ready/pending
```

## Safety invariants

The following are always forbidden:

```text
new parallel runner
fake completed
fake final_ready
fake percent 100
fake rows
fake source_url/source_date
DB write
migration
production deploy
allowed_paths escape
```
