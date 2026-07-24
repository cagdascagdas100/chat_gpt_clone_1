status=waiting_single_runner_pickup
page_key=distance_property_types
active_branch=codex/aays-single-runner-v5-20260706
single_runner_only=true
new_runner=false
parallel_runner=false
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false

Current pickup check:
- dpt_queue_compaction_bundle_started: missing
- dpt_runner_pickup_sweep_started: missing

Next action for single runner:
1. Pull active branch.
2. Read distance_property_types queue tasks in priority order.
3. Start with source seed priority task, then QA bundles.
4. Write real started/completed/report markers only after execution.
5. Keep final_ready=false until evidence, geometry, distance, and site gates pass.
