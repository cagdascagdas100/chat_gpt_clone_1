# AAYS Shared Single Runner Policy

Purpose: all AAYS page-level ChatGPT/Codex tasks must flow through one local runner process. Do not create a separate runner per page.

Repository branch:
`aays-runner-v17-icon-work-20260603-232706`

Single runner script:
`docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1`

## Contract for every page

Each page keeps its own page key folder:

`docs/chatgpt_status/<PAGE_KEY>/`

Allowed input folders:

- `queue/`
- `current-task/`

Allowed output folders:

- `reports/`
- `status/`
- `heartbeat/`
- `runner_outputs/`

A page task must point to a page-local automation script under:

`docs/chatgpt_status/<PAGE_KEY>/automation/<SCRIPT>.ps1`

The shared runner will only execute automation scripts that match that page-local path. It will not execute arbitrary commands copied into queue files.

## Rules for other pages

1. Do not start another runner window.
2. Do not create another scheduled task for another page.
3. Do not write tasks into another page key.
4. Write only the page-specific task into that page key's `queue/` or `current-task/`.
5. The one shared runner reads all page keys and executes one task at a time.
6. Each automation must write its evidence back to that same page key's `reports/`, `status/`, `heartbeat/`, or `runner_outputs/` folder.
7. A page may only claim `FINAL_READY` after its own report proves the acceptance criteria.

## Operational note

If two runner processes are visible, close one. Exactly one multi-page runner process should remain active.
