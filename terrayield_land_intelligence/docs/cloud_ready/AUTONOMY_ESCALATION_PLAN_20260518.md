# Autonomy Escalation Plan - 2026-05-18

## Current state

`CLOUD_READY_PENDING_PROVIDER`

`WAIT_FOR_USER_PROVIDER_DECISION`

## Layer 1 - GitHub only

Can complete:

- docs
- scripts
- manifests
- checklists
- issue tracking
- workflow definitions
- static reports

Cannot prove:

- live local runtime
- live hosted runtime
- cloud database connectivity
- hosted smoke success

## Layer 2 - Persistent local runner

Use when fresh local evidence is required.

Expected duties:

- pull branch
- run queued tasks
- run tests
- run local smoke
- run performance checks
- publish reports to GitHub

## Layer 3 - Hosted CI

Use for static and non-secret checks.

Good for:

- file presence
- syntax checks
- static validator
- public-safe unit checks

Not enough for:

- provider DB proof
- hosted cloud proof

## Layer 4 - Provider setup

Use when public cloud operation is required.

Needs:

- backend hosting choice
- cloud database choice
- frontend hosting choice
- public backend URL
- hosted smoke approval

## Classification rules

Keep `CLOUD_READY_PENDING_PROVIDER` until public runtime and cloud DB are verified.

Use `CLOUD_RUNTIME_READY` only after hosted smoke passes.

Use `FREE_TIER_BEST_EFFORT_READY` only after hosted smoke passes and free-tier limits are accepted.
