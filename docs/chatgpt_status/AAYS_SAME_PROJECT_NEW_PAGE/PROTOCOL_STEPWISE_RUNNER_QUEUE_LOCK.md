# AAYS SAME PROJECT NEW PAGE - Stepwise Runner Protocol

PageKey: AAYS_SAME_PROJECT_NEW_PAGE
Project: AAYS_TerraYield

## Current confirmed issue

The previous V11/V12 approach failed because long interactive PowerShell blocks were pasted and executed in fragments. The `finally` block was executed outside the original `try/catch` context, so the report writer did not run and the expected result file was not created.

## Required operating model

1. Never paste large patch logic directly into an interactive shell.
2. Use a small local runner script file for each task.
3. Each task must write a checkpoint line before and after every major step.
4. Each task must write two reports:
   - Bridge report under `C:/AAYS_GITHUB_BRIDGE_CLEAN2/ai-results/`
   - Repo report under `C:/Users/cagda/Documents/GitHub/AAYS/docs/chatgpt_status/`
5. Each task must preserve a single runner and queue-lock.
6. If a task fails, the next task must be a diagnosis-only task that reads the report and writes the next corrective command.
7. Do not run DB write, production deploy, migration/DDL, fake data, destructive git, force push, reset hard, or git clean.

## Progress state

Current progress estimate: 41
Current blocker: V11/V12 patch flow did not complete because the report writer did not execute as intended.

## Next safe task

Create and run a small diagnostic-only task that:

- checks whether `app.js` exists,
- checks whether `topography.overlay.json` exists,
- checks whether `.queue-lock` exists,
- checks whether a V12 backup exists,
- checks whether a V12 report exists,
- writes a clean status report,
- does not modify runtime files.

Expected progress after successful diagnostic report: 42

## Safety flags

- db_write=false
- production_deploy=false
- migration_ddl=false
- fake_data=false
- destructive_git=false
- read_only_first=true
