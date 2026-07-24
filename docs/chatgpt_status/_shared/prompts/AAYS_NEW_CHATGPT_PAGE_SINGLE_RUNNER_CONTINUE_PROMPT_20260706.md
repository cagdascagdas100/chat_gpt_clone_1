# AAYS New ChatGPT Page - Single Runner Continue Prompt 20260706

Repo: cagdascagdas100/chat_gpt_clone_1
Branch: codex/aays-single-runner-v5-20260706

Use the existing single shared runner only. Do not start a new runner.

For a new page:
- Choose PAGE_KEY.
- Put queue tasks under `docs/chatgpt_status/<PAGE_KEY>/queue/*.task.json`.
- Put automation under `docs/chatgpt_status/<PAGE_KEY>/automation/*.ps1` only when needed.
- Put status, report, heartbeat, completed, and blocked evidence under the same PAGE_KEY folder.
- Set `allowed_paths` to the exact page folder and any shared status/report/panel paths needed.
- Keep all safety flags false: `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
- Keep `final_ready=false` unless real evidence proves acceptance. Never write fake completed, fake 100 percent, fake final_ready, or fake heartbeat.
- Let `docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1` pick up the queue.
- When the user says "devam et", inspect the shared panel/status files and continue by queue/status evidence, not by launching another runner.

Canonical launcher:
`START_AAYS_SINGLE_RUNNER_PANEL.cmd`

Shared status:
`docs/chatgpt_status/_shared/status/MULTI_PAGE_latest_status.json`
`docs/chatgpt_status/_shared/panel/page_status_index_latest.json`
