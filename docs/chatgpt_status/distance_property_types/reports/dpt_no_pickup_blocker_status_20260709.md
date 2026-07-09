status=BLOCKED_WAITING_SINGLE_RUNNER_PICKUP
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

Checked evidence:
- distance_property_types_source_seed_priority_20260708_completed: missing
- dpt_final_qa_bundle_completed: missing

Blocker:
- existing F single runner has not yet written real started/completed/report evidence for this page.

Next:
- continue with existing F single runner only
- do not create a second runner/worktree/clone
- keep queued tasks pending until real pickup evidence appears
