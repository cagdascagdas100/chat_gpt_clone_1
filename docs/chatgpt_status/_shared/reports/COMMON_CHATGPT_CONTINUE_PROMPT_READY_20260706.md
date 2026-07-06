# AAYS / TerraYield - Common Continue Prompt Ready 20260706

Generated at: 2026-07-06T20:57:17.3861282Z

Common prompt file:
- docs/chatgpt_status/_shared/prompts/AAYS_CHATGPT_COMMON_DEVAM_PROMPT_20260706.md

Restored prompt paths:
- docs/chatgpt_status/aays1/codex_prompts/CODEX_SINGLE_RUNNER_PANEL_FIX_20260706.md
- docs/chatgpt_status/_shared/automation/CODEX_SINGLE_RUNNER_PANEL_REPAIR_PROMPT_20260706.md
- docs/chatgpt_status/_shared/prompts/CODEX_SINGLE_RUNNER_PANEL_FIX_PROMPT_20260706.md

Required work completed in this pass:
- Missing branch prompt paths were created.
- A single common ChatGPT continuation prompt was created.
- The prompt tells ChatGPT pages to repair only their own page_key contract blockers.
- The prompt tells ChatGPT pages to skip unnecessary/unsafe work: main integration, DB write, migration, production deploy, fake completed, fake heartbeat, fake 100 percent, fake final_ready=true, new parallel runner, F drive canonical switch, and unverified 115 metric changes.

Still not fake-completed:
- final_ready=false
- product_final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
