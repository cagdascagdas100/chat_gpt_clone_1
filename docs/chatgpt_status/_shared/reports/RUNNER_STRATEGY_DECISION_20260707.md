# AAYS Runner Strategy Decision 20260707

Generated at: 2026-07-07T00:47:16.3821287Z

Decision: use stable legacy worktree runner as the default continuation path.

Why:
- The apparent old canonical runner was a V5 wrapper, so it still hit the V5 path.
- Direct V4 old runner was F-drive-only, which is not canonical.
- The stable 20260707 runner keeps V4's safer worktree model but runs from C:\AAYS_WT\AAYS_REPAIR_20260706_1738.
- V5 is left as diagnostic/evidence code and is skipped by the default launcher.

Default user action:
- Double-click START_AAYS_SINGLE_RUNNER_PANEL.cmd.
- Then ChatGPT pages should use docs/chatgpt_status/_shared/prompts/AAYS_CHATGPT_COMMON_DEVAM_PROMPT_20260706.md.

Skip:
- V5 default runner path until separately repaired.
- F drive as canonical.
- Main integration in this pass.
- DB write, migration, production deploy.
- Fake completed, fake heartbeat, fake 100 percent, fake final_ready=true.

Safety flags:
- final_ready=false
- product_final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
