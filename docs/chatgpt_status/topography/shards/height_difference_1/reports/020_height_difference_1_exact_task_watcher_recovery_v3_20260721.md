# Height Difference 1 exact-task watcher recovery v3

## Scope

This recovery hardens the existing single repo-to-bridge watcher for `height_difference_1`. It does not create a new logical task, new runner or parallel runner.

## Corrected execution risks

- The previous complete watcher could scan and copy every unseen `aays1/queue/*.task.json` task. V3 copies only task ID `height-difference-1-official-boundary-elevation-samples-20260720`.
- Task identity is read from JSON `task_id`; filename fallback is not accepted for the expected task.
- Automation and validation copy failures are fatal.
- Required revision 9 dependency files and the active watched queue task ID are verified after synchronization.
- Bridge task visibility uses strict JSON task identity.
- Local and remote source-branch watcher heartbeats must both be fresh and bound to the expected task.
- The post-apply verifier checks one watcher, one runner, exact task marker, active dependency files, slot claim and revision 9 output.

## Validation

- Static isolation and safety tests: `32/32`
- F portable runtime execution: not performed from this page.
- Runtime claims, heartbeats and official elevation rows remain unverified.

## Safety

- Shared control is not synchronized or overridden.
- Existing portable runner is never stopped.
- Runner restoration is opt-in and limited to the canonical existing runner script.
- `final_ready=false`
- `product_final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
