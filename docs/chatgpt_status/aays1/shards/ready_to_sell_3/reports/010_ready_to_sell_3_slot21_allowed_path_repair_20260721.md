# ReadyToSell 3 — slot21 coordinator pickup path repair

- SLOT_ID: `ready_to_sell_3`
- Parcel partition: `61523-92283`
- Remote checkpoint read first: sequence `9`
- Repeated completed research work: `false`
- Other slot claimed: `false`

## Finding

`docs/chatgpt_status/_shared/slots_21/ready_to_sell_3/current_task_latest.json` was inside the `slots_21` workstream but its `allowed_paths` still referenced:

- `docs/chatgpt_status/_shared/slots_18/ready_to_sell_3`
- `england_map_web/data/aays_18_slots/ready_to_sell_3`

Both pending queue tasks write to the `slots_21` / `aays_21_slots` paths. This stale path contract could reject or prevent coordinator pickup.

## Repair

The idle slot current-task contract was corrected to:

- `docs/chatgpt_status/aays1/shards/ready_to_sell_3`
- `docs/chatgpt_status/_shared/slots_21/ready_to_sell_3`
- `england_map_web/data/aays_21_slots/ready_to_sell_3`

Remote readback confirmed the corrected paths.

## Remaining blocker

The canonical single coordinator is still not active:

- ownership: `unclaimed`
- heartbeat: absent and stale
- primary queue: `pending`
- secondary queue: `pending`
- runner output: absent

Next unverified step: existing canonical single runner must start or wake, claim this slot, execute HTTP/SHA256 and Automation 167 browser DOM acceptance, then publish through the serial publisher with remote readback.

- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
