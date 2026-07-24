# New ChatGPT Page Runner Contract

Use one shared runner for all pages. Each page owns its queue under:

`docs/chatgpt_status/<PAGE_KEY>/queue/current.task.json`

Required task fields:
- `task_id`
- `page_key`
- `status`
- `script_path`
- `automation_script`
- `allowed_paths`
- `no_fake_final_ready=true`
- `no_db_write=true`
- `no_migration=true`
- `no_production_deploy=true`
- `final_ready=false`

The runner writes lifecycle evidence to:
- `docs/chatgpt_status/<PAGE_KEY>/status/heartbeat_latest.txt`
- `docs/chatgpt_status/<PAGE_KEY>/status/`
- `docs/chatgpt_status/<PAGE_KEY>/blocked/`
- `docs/chatgpt_status/_shared/status/`
- `docs/chatgpt_status/_shared/panel/page_status_index_latest.json`
