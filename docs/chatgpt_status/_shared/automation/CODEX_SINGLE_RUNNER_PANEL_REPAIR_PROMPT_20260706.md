# CODEX_SINGLE_RUNNER_PANEL_REPAIR_PROMPT_20260706

Canonical repair prompt path restored for branch automation.

Required work:
- Keep one shared V5 runner.
- Keep root launchers pointing to START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1.
- Keep the visible panel reading real status/index files and PANEL_MENU_CONFIG.json.
- Keep new ChatGPT pages using the common continuation prompt.
- Repair only necessary page contract gaps inside the owning page_key.

Skip as unnecessary for this continuation flow:
- main merge/integration
- DB writes
- migrations
- production deploy
- fake final/completed/heartbeat/100 percent
- new runner processes or page-specific runners

When in doubt, write a real blocker instead of manufacturing success.
