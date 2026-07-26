# Distance Property Types Pickup Request

page_key=distance_property_types
task_id=distance_property_types_runner_pickup_20260703_0918
status=READY_FOR_SINGLE_RUNNER_PICKUP
priority=100
continue_command=devam et
blocker_issue=19

## Required behavior

- Use the existing single shared worker only.
- Do not create a second worker.
- Pick up the repo queue task for distance_property_types.
- Write real output reports back under the distance_property_types reports or runner_outputs folders.
- If no real evidence batch exists, keep final_ready=false.
- If the worker is unavailable, write RUNNER_NOT_RUNNING with proof.
- Do not create fake parcel, fake evidence, fake source, fake photo AI result, or fake final_ready.

## ChatGPT continuation behavior

When the user writes `devam et`, this page reads current_task, continuation_state, latest progress report, Issue #19, and any committed output files. Then this page updates GitHub reports and output files only from real evidence.
