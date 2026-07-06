# AAYS Runner Problem Fix Required - 2026-07-06

status=BLOCKED_LOCAL_RUNNER_REPAIR_REQUIRED
final_ready=false
fake_completed_written=false
fake_final_ready_written=false
fake_percent_100_written=false

## Confirmed GitHub evidence

The shared acceptance report exists but is partial only. It does not mark the system final-ready.

The shared runner contract exists and defines the required queue, status, report, heartbeat, completed, and blocked evidence rules.

The page registry exists, but it does not yet include all five requested panel menu mappings.

The panel index exists, but multiple pages are still unchecked or invalid. For `distance_property_types`, latest_queue_status is `unknown_not_checked_in_this_pass` and final_ready is false.

## Main local runner blocker

The current shared runner wrapper points to the V4 runner. The V4 runner has a hard local root assumption for F drive usage. The user's new local continuation prompt uses:

```text
C:\Users\cagda\Documents\GitHub\AAYS
```

If the runner is launched from the C repo, this root mismatch can block runner startup before queue pickup. This must be fixed locally or by Codex/Jodex in the repo.

## Required fix

Implement a V5 compatibility wrapper or patch the V4 runner so it accepts these canonical local roots:

```text
C:\Users\cagda\Documents\GitHub\AAYS
F:\chatgpt\chat_gpt_clone_1_main
F:\chatgpt\chat_gpt_clone_1_main_fresh
```

The fix must not weaken allowed_paths enforcement and must not start a second runner.

## Required launcher behavior

The launcher must:

```text
1. Resolve the active repo root.
2. Prefer C:\Users\cagda\Documents\GitHub\AAYS if that is the active repo.
3. Otherwise allow the F repo roots above.
4. Use a single runner lock.
5. Start only one canonical runner.
6. Open/update the runner panel.
7. Write GitHub-visible status, report, heartbeat, completed or blocked evidence.
```

## Required proof after repair

After the local fix, run the canonical launcher once and verify these files appear or update on GitHub/main:

```text
docs/chatgpt_status/_shared/heartbeat/MULTI_PAGE_heartbeat_latest.json
docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json
docs/chatgpt_status/_shared/reports/MULTI_PAGE_runner_output_<RUN_ID>.json
docs/chatgpt_status/_shared/panel/page_status_index_latest.json
```

For page tasks, verify one of these evidence chains exists:

```text
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_started.json
docs/chatgpt_status/<PAGE_KEY>/heartbeat/<TASK_ID>_heartbeat.txt
docs/chatgpt_status/<PAGE_KEY>/reports/<TASK_ID>_runner_output.txt
docs/chatgpt_status/<PAGE_KEY>/status/<TASK_ID>_completed.json
```

or a blocked evidence file/report with the real blocker.

## Current instruction to local operator

Run the repair in Codex/Jodex or locally. Do not start a parallel runner. Do not mark final_ready=true. Do not write 100 percent unless the page acceptance gates pass with real evidence.

## Blocker code

```text
RUNNER_ROOT_COMPATIBILITY_PATCH_REQUIRED
LOCAL_CANONICAL_RUNNER_NOT_PROVEN_AFTER_RESTART
PAGE_PANEL_INDEX_NOT_FULLY_VALIDATED
```
