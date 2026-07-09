status=runner_pickup_missing_local_pull_required
page_key=distance_property_types
active_branch=codex/aays-single-runner-v5-20260706
canonical_portable_root=F:\TerraYield_AAYS_Portable
canonical_runner_repo_root=F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707
single_runner_only=true
new_runner=false
parallel_runner=false
final_ready=false
product_final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false

Observed:
- dpt_queue_compaction_bundle_started: missing
- distance_property_types_source_seed_priority_20260708_started: missing

Do next on the existing F single runner only:
1. Pull active branch in canonical runner repo root.
2. Run existing one-click launcher only if the runner is stopped.
3. Do not create a second runner, clone, or worktree.
4. Process queue by priority.
5. Write real started/completed/report evidence after execution.
