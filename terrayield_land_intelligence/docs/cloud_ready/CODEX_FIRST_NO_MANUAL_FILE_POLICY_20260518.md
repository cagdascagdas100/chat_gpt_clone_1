# Codex First / No Manual File Policy - 2026-05-18

## Rule

Use GitHub, repository files, Codex handoff outputs, Codex result documents and runner reports as the main working sources.

## Codex first

If Codex has produced a concrete implementation plan or result document, treat it as the operational source of truth unless it conflicts with safety rules or verified repository evidence.

## No manual file request

Do not ask the user for files during normal GitHub-side work.

Ask for a file only if the work truly depends on an expired upload and the same content is not available in GitHub or Codex outputs.

## No manual provider request unless required

Do not ask for manual provider data unless a public URL, provider config, hosted smoke approval, or local runner enablement is strictly required.

## Current state

`CLOUD_READY_PENDING_PROVIDER`

`WAIT_FOR_USER_PROVIDER_DECISION`

## Safety

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
