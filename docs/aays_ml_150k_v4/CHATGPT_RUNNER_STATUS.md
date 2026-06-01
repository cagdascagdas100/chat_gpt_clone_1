# AAYS TerraYield ML 150k V4 Runner Status

PageKey: AAYS_SAME_PROJECT_NEW_PAGE
Project: AAYS_TerraYield

ChatGPT sandbox package generated: aays_ml_150k_v4_runner_smoke_outputs_queue_pack.zip

Completed locally:
- 150000 demo input rows read
- queue-safe smoke ML run completed
- 72 candidate model result rows produced
- 1152 factor-model result rows produced
- 288 selected final rows produced
- 16-row final factor table produced

Security flags:
- db_write=false
- production_deploy=false
- migration_ddl=false
- fake_data=false
- destructive_git=false
- read_only_reference_only=true

Bridge rule: use existing single runner and queue-lock. Do not overwrite current-task.json. Put the V4 task JSON under ai-queue/pending if a new task is needed.

Next user command: devam
