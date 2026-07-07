# Stable Runner Low Memory Fetch Fix - 2026-07-07

Status: fixed for codex/aays-single-runner-v5-20260706

Root cause:
- Stable runner was active, but controller fetch used a heavier branch fetch and repeatedly failed with Git OOM: malloc failed trying to allocate 1048576000 bytes.
- Some runner output still used V4 labels, which confused GitHub/ChatGPT health checks.

Change:
- Controller, task, and post-sync fetch calls now use --no-tags --depth=1 with explicit refspec and lower pack memory settings.
- Stable runner heartbeat/output labels now use RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.
- The existing safe.directory injection remains in every runner git call.

Safety:
- final_ready=false
- product_final_ready=false
- fake_data=false
- db_write=false
- migration=false
- production_deploy=false
