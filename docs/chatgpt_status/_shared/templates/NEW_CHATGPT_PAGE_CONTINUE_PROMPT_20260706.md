# AAYS / TerraYield - New ChatGPT Page Continue Prompt 20260706

Use this prompt in a new ChatGPT page when the user says only "devam et".

Fill these fields before starting:
- repo_root: C:\AAYS_WT\AAYS_REPAIR_20260706_1738
- repo: cagdascagdas100/chat_gpt_clone_1
- branch: codex/aays-single-runner-v5-20260706
- page_key: <PAGE_KEY>
- task_id: <TASK_ID>

Rules:
- Use the existing single shared runner only.
- Do not start a new or parallel runner.
- Put queue tasks only under docs/chatgpt_status/<PAGE_KEY>/queue/.
- Put status, heartbeat, reports, completed, and blocked evidence only under docs/chatgpt_status/<PAGE_KEY>/.
- Every queue task must include allowed_paths and expected_outputs.
- Keep fake_data=false, db_write=false, migration=false, production_deploy=false.
- Keep final_ready=false until real GitHub evidence proves every acceptance criterion.
- Do not write fake completed, fake heartbeat, fake percent, fake 115-output, or fake final_ready=true.
- Main integration is separate; do not claim product completion while product_final_ready=false.

When the user says "devam et":
1. Read docs/chatgpt_status/_shared/status/page_panel_index.json and docs/chatgpt_status/_shared/panel/page_status_index_latest.json.
2. Check this page_key queue/status/report evidence.
3. If work is needed, create or update a .task.json using NEW_CHATGPT_PAGE_QUEUE_TEMPLATE_20260706.json.
4. Let the shared runner pick it up; do not launch a page-specific runner.
5. Report real blockers if runner status is not active, if lock is stale, if push/fetch fails, or if contract fields are missing.

Safe launcher for the user:
- START_AAYS_SINGLE_RUNNER_PANEL.cmd
- START_AAYS_RUNNER.bat
- AAYS_RUNNER_BASLAT.bat
- RUN_AAYS_SINGLE_RUNNER_PANEL.cmd
