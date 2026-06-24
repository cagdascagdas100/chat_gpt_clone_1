# aays1 runner pickup blocker

status: blocker
page_key: aays1
task_id: aays1_fg100_runner_contract_blocker_20260623_008
repo_root: F:\chatgpt\chat_gpt_clone_1_main
bridge_root: F:\AAYS_GITHUB_BRIDGE_CLEAN2

## Proven

- Shared runner is active on F bridge.
- Repo root is F repo.
- Remote is cagdascagdas100/chat_gpt_clone_1.
- Branch is main.
- aays1 task was copied to F bridge pending.
- Push chain works because this report and previous runner test reports are visible on GitHub main.

## Not proven

- aays1 task pickup by portable_queue_runner.ps1.
- aays1 expected runner output.
- aays1 expected heartbeat.

Expected output path:

docs/chatgpt_status/aays1/reports/aays1_fg100_runner_contract_blocker_20260623_008_runner_output.txt

Expected heartbeat path:

docs/chatgpt_status/aays1/heartbeat/aays1_fg100_runner_contract_blocker_20260623_008_heartbeat.txt

## Root cause hypothesis

The shared runner is alive but does not pick the aays1 pending task. The likely cause is a task format/parser mismatch or queue movement rule mismatch inside F:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1.

The latest bootstrap report showed pending_count greater than zero and running_count zero. That means the runner can be alive but still not consuming pending tasks.

## Required next fix

Inspect the active runner parser on F bridge and align the aays1 task with the exact format it consumes.

Do not fabricate output, heartbeat, or final-ready markers.
