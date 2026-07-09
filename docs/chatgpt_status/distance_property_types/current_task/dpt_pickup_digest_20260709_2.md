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

Latest pickup check:
- dpt_queue_compaction_bundle_started: missing
- dpt_final_qa_bundle_started: missing

Runner-safe next action:
1. Do not create a parallel runner.
2. Pull active branch on the F portable runner root.
3. Process queued distance_property_types tasks in priority order.
4. Start with source seed priority validation.
5. Then process QA bundles only after real started/completed/report markers are written.
6. Keep final_ready=false until evidence, geometry, distance, and site gates pass.
