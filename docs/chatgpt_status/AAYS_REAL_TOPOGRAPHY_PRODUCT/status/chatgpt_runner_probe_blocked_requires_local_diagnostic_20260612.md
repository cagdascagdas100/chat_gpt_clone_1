# AAYS_REAL_TOPOGRAPHY_PRODUCT Runner Probe Blocked — Local Diagnostic Required

Scope:
- repo: cagdascagdas100/chat_gpt_clone_1
- branch: aays-runner-v17-icon-work-20260603-232706
- page_key: AAYS_REAL_TOPOGRAPHY_PRODUCT
- status_root: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT

Current GitHub evidence checked:
- Expected runner report is missing: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/runner_contract_probe_20260612_istanbul.txt
- Current task exists: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/current-task/runner_contract_probe_20260612_istanbul.md
- Previous ChatGPT observation exists: docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status/chatgpt_runner_probe_observation_20260612.md
- GitHub search did not expose a page-specific heartbeat or runner output for AAYS_REAL_TOPOGRAPHY_PRODUCT.

Classification:
- status: BLOCKED_ON_RUNNER_CONTRACT
- runner_alive: unknown
- current_task_seen_by_runner: unknown
- product_task_allowed: false until runner intake contract is known

Required next action:
Run exactly one local diagnostic that writes its output into this same GitHub status tree and pushes it back to the same branch. The diagnostic must not modify product code, DB, migrations, imports, indexes, or deployment state.

Expected diagnostic report path:
- docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/local_runner_contract_diagnostic_20260612.txt

Completion gate for ChatGPT:
ChatGPT may issue the next Topography product task only after the diagnostic report or runner contract probe report exists in GitHub and identifies a safe runner intake path/schema.
