# Height Difference 1 — revision-aware watcher recovery v4

- Slot: `height_difference_1`
- Task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Payload revision: `9`
- Idempotency key: `height_difference_1-004-20260720`
- Runtime application: **not performed**; F portable host access is required.

## New correctness gates

1. Bridge marker identity requires the same `task_id`, `payload_revision`, `script_path`, and `idempotency_key`.
2. Markers from older payload revisions do not suppress the revision 9 queue item.
3. Matching `pending` or `running` markers prevent duplicate publication.
4. Matching `done` or `processed` markers are accepted only when the expected revision 9 output exists.
5. Matching `failed` or `error` markers are not automatically retried; operator policy is required.
6. Unrelated tasks and filename-only matches are ignored.
7. Shared control is not synchronized or overridden.
8. Existing portable runner is never stopped; restoration is opt-in only when no runner exists.
9. Local and remote heartbeat signatures include task, revision, script and idempotency identity.
10. Post-apply verification reports marker state, revision, slot claim and official output separately.

## Static validation

- Passed: `46/46`
- Runtime evidence fabricated: `false`
- Official measured rows written: `0`
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
