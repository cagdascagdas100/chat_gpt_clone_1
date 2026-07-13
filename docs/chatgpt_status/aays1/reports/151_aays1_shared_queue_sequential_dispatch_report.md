# AAYS1 ReadyToSell Shared Queue Sequential Dispatch

- Jobs with expected output: 5 / 5
- Failed jobs: 2
- Real progress count across child outputs: 3
- One canonical F portable shared runner; no parallel runner.
- Existing real task 146 output is not duplicated.
- Land/plot acceptance uses real HTTP response plus positive listing title/body evidence; generic page-script challenge terms do not override a positive title.
- Child detached commits are unwound; outer canonical runner owns commit, push and remote readback.

- 145: skipped_existing_real_output; output=True; real_progress=0; force_rerun=False; child_unwound=False; exit=0; log=docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711/job_145.log
- 146: skipped_existing_real_output; output=True; real_progress=3; force_rerun=False; child_unwound=False; exit=0; log=docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711/job_146.log
- 148: execution_exception; output=True; real_progress=0; force_rerun=True; child_unwound=False; exit=1; log=docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711/job_148.log
- 149: execution_exception; output=True; real_progress=0; force_rerun=True; child_unwound=False; exit=1; log=docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711/job_149.log
- 150: executed_output_created_no_new_progress; output=True; real_progress=0; force_rerun=True; child_unwound=True; exit=0; log=docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711/job_150.log

- Blockers: job_exception:148:source_signal_guard_pattern_not_found:148; job_exception:149:source_signal_guard_pattern_not_found:149

`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.
