# 080 Restore Source CSV Missing - Queue Blocked

Status: blocked
Blocker: BLOCKED_080_REPAIR_SOURCE_CSV_MISSING
Updated: 2026-07-07T09:27:51Z

The 062/080 automation script is fail-closed and currently always throws this blocker until a real source CSV exists. These duplicate queue aliases were removed from the pending runner path by setting status=blocked. This is not a completed claim and not a final-ready claim.

Changed queue files:
- docs/chatgpt_status/aays1/queue/078_relative.task.json
- docs/chatgpt_status/aays1/queue/normalized_080_restore_75_rel_20260706.json
- docs/chatgpt_status/aays1/queue/terrayield_062_restore_2of4_table_from_f_repo_source_csv.task.json
- docs/chatgpt_status/aays1/queue/z111.task.json
- docs/chatgpt_status/aays1/queue/z122.task.json
- docs/chatgpt_status/aays1/queue/z123.task.json
- docs/chatgpt_status/aays1/queue/z124.task.json
- docs/chatgpt_status/aays1/queue/z278.task.json


Safety flags: final_ready=false, product_final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.
