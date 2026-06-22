# 052 runner pointer blocked

page_key: security_public_safety_low_credit_20260612
status: BLOCKED
percent: 89
reason: runner_tasks/current-task.json is stale at cycle049 while queue, control, status, and automation script are cycle050.
powershell_required: true_only_for_pointer_repair
separate_runner_required: false
expected_after_repair: 050_single_runner_apply, 050_field_contract, 050_smoke, 050_blockers, 050_runner_output
