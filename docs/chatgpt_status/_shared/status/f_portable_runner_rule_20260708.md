# AAYS F Portable Runner Rule

status=canonical_runner_rule_updated
active_page_key=distance_property_types
active_task_id=distance_property_types_source_seed_priority_20260708
portable_drive=F
portable_root_name=TerraYield_AAYS_Portable
runner_repo_root_relative=runner_system/AAYS_WT/AAYS_RUNNER_HEALTHY_20260707
runner_workroot_relative=runner_system/AAYS_WT/AAYS_STABLE_RUNNER_WORKTREES
launcher_relative=RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd

Rules:
- Use the F portable root as canonical storage.
- Do not create a new runner.
- Do not create a parallel worktree.
- Keep single shared runner mode.
- Keep final_ready=false until real validation and evidence gates pass.
- Keep fake_data=false, db_write=false, migration=false, production_deploy=false.

Current DPT state:
- source_input_rows=6
- priority_queue_task=docs/chatgpt_status/distance_property_types/queue/0000_distance_property_types_source_seed_priority_20260708.task.json
- waiting_for=single_runner_validation_output
