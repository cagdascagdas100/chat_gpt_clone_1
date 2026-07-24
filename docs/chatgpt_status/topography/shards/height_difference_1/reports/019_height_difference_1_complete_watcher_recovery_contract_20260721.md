# Height Difference 1 complete existing-watcher recovery contract

## Result

- The original watcher was pinned to `origin/main` and only copied `aays1/automation`, `queue`, and `control`.
- Revision 9 executes from `docs/chatgpt_status/topography/shards/height_difference_1/automation`, so queue visibility alone was insufficient.
- The complete recovery synchronizes only this slot's automation and validation directories plus the two same-task queue files.
- Shared control is not copied or overridden.
- The existing portable runner is never stopped; restoration is opt-in and allowed only when no runner process exists.
- Bridge task detection reads the JSON `task_id`, rather than relying only on file names.
- The recovered watcher writes a local heartbeat and periodically publishes the heartbeat to the authoritative source branch.
- A separate post-apply verifier checks one watcher, one runner, fresh branch heartbeat, active-repo assets, bridge task visibility, slot claim, and official output.
- A one-command wrapper chains guarded apply, existing-runner restore, and post-apply verification.

## Validation

- Static safety and contract tests: `25/25` passed.
- Windows PowerShell 5.1-compatible JSON readback is used.
- Runtime execution was not performed because the F portable host and bridge processes are not accessible from this page.
- No heartbeat, task claim, candidate geometry, or elevation result was fabricated.

## Current state

- Candidate rows: `3`
- Official HMLR boundary rows: `0`
- Official EA 1 m height-difference rows: `0`
- Accuracy: `2.5/4 fallback`
- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
