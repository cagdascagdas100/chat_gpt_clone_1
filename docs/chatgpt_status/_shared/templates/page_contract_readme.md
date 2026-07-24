# AAYS Page Contract

Every page lives under `docs/chatgpt_status/<PAGE_KEY>/` and uses the single
shared runner. Queue files must include `page_key`, `task_id`, `script_path`,
`automation_script`, `allowed_paths`, safety flags, and `final_ready=false`.

The runner writes status, report, heartbeat, completed, or blocked evidence. A
page is not product-final until real gate evidence exists.
