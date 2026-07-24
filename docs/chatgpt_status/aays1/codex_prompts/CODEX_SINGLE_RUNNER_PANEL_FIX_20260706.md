# CODEX_SINGLE_RUNNER_PANEL_FIX_20260706

This file restores the branch prompt path that was referenced by the repair task.

Apply the shared single-runner contract only:
- do not create parallel runners
- use START_AAYS_SINGLE_RUNNER_PANEL.cmd or equivalent root launcher only
- keep docs/chatgpt_status/_shared/locks/single_runner.lock as the canonical lock
- keep panel menus config-driven through docs/chatgpt_status/_shared/panel/PANEL_MENU_CONFIG.json
- use docs/chatgpt_status/_shared/prompts/AAYS_CHATGPT_COMMON_DEVAM_PROMPT_20260706.md for all new ChatGPT continuation pages
- do not fake completed, heartbeat, percent, final_ready=true, 115 metrics, fake data, DB writes, migrations, or production deploys
- skip main integration unless explicitly requested as a separate task

If a page has missing contract fields, repair only that page_key's queue/status/report files with real evidence. If evidence is missing, write a blocker and leave final_ready=false.
