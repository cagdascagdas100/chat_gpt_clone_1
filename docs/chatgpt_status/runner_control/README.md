# AAYS GitHub Controlled Runner Protocol

This folder is the control surface between ChatGPT and the local AAYS runner.

Rules:
- ChatGPT writes or updates `next_task.json`.
- The local runner reads `next_task.json` from GitHub.
- The local runner executes exactly one safe task per task id.
- The local runner writes results to `docs/chatgpt_status/runner_outputs/` on branch `chatgpt-local-sync`.
- DB write, DDL, migrations, production deploy, fake/demo data, destructive git commands are forbidden.

User flow after bootstrap:
1. User writes `devam` in ChatGPT.
2. ChatGPT reads latest runner output from GitHub.
3. ChatGPT updates the next task if needed.
4. Local runner executes and pushes the new output.
