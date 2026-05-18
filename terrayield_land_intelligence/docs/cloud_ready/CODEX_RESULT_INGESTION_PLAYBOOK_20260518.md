# Codex Result Ingestion Playbook - 2026-05-18

## Current operating rule

Codex implementation plans and Codex result documents are treated as the operational source of truth unless they conflict with safety rules or verified repository evidence.

## Current classification

`CLOUD_READY_PENDING_PROVIDER`

## Current next action

`WAIT_FOR_USER_PROVIDER_DECISION`

## Purpose

Define how ChatGPT/GitHub-side automation should process new Codex outputs without asking the user for manual files.

## Accepted Codex evidence sources

- Codex handoff ZIP reports committed to the repository.
- Codex-generated result documents under `docs/chatgpt_handoff`.
- Runner outputs pushed by Codex/local automation.
- GitHub-visible implementation files created or modified by Codex.
- Codex checkpoint summaries committed to the branch.

## Ingestion steps

1. Search repository for new Codex result files.
2. Prefer Codex result classification if it is backed by files or logs.
3. Cross-check against safety invariants.
4. Update current status files only when evidence changes.
5. Do not ask the user to manually re-upload files unless the content is unavailable in GitHub or Codex outputs.

## Safety rejection rules

Reject or downgrade Codex output if it claims completion while any of these are missing:

- public hosted backend URL for cloud runtime claims,
- cloud DB/PostGIS verification for DB-backed cloud claims,
- hosted smoke evidence for `CLOUD_RUNTIME_READY`,
- free-tier acceptance evidence for `FREE_TIER_BEST_EFFORT_READY`.

Reject unsafe outputs involving:

- real secrets committed to repo,
- `.env` or `.env.local` committed,
- DB write without approval,
- DDL without approval,
- migration apply without approval,
- production deploy without approval.

## Classification handling

If Codex reports GitHub-only readiness:

- keep `CLOUD_READY_PENDING_PROVIDER`.

If Codex reports local runner success only:

- update local evidence fields,
- keep cloud classification pending.

If Codex reports hosted backend + cloud DB + hosted smoke success:

- update to `CLOUD_RUNTIME_READY`.

If Codex reports hosted success and accepted free-tier limits:

- update to `FREE_TIER_BEST_EFFORT_READY`.

## Files to update after ingesting Codex results

- `docs/cloud_ready/CURRENT_STATUS_20260517.md`
- `docs/cloud_ready/CURRENT_STATUS_MACHINE_20260518.json`
- `docs/cloud_ready/FINAL_MANIFEST_20260517.json`
- `docs/cloud_ready/INDEX_TR.md`
- `docs/cloud_ready/RUNTIME_PROOF_GAP_REGISTER_20260518.md`
- `docs/cloud_ready/NEXT_OPERATOR_HANDOFF_20260518.md`

## Safety invariant

- db_write=none
- ddl=none
- migration_apply=none
- prod_deploy=none
- secret_values_printed=false
