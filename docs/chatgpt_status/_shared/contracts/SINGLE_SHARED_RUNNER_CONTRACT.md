# Single Shared Runner Contract

This file mirrors `AAYS_SINGLE_RUNNER_PAGE_CONTRACT_20260706.md` for older
prompts that look for the generic contract name.

Canonical entry:

```text
docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1
```

Root entry:

```text
devam.ps1
```

The runner must use a single lock, enforce each task's allowed paths, write
queue/status/report/heartbeat/completed or blocked evidence, and keep
`final_ready=false` unless real gate evidence exists. It must not start a
parallel runner, fabricate completion, write fake evidence, run migrations, or
deploy production.
