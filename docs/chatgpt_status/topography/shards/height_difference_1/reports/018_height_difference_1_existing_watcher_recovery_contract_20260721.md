# Height Difference 1 — existing watcher recovery contract

- Slot: `height_difference_1`
- Task: `height-difference-1-official-boundary-elevation-samples-20260720`
- Source branch: `codex/aays-single-runner-v5-20260706`
- Existing watcher was designed to reset its worktree to `origin/main`.
- The slot queue and revision 9 automation are present on the source branch but absent on watcher `main`.
- Recovery defaults to read-only preflight. `-Apply` is required for mutation.
- Recovery refuses to proceed when bridge running files exist, or when multiple watcher/runner processes are detected.
- Apply mode stops only the existing watcher; it does not stop the portable runner.
- Existing runner restoration is opt-in with `-RestoreRunner` and only occurs when the runner process count is zero.
- Queue-only mirroring to `main` remains forbidden because it would omit the automation dependency chain.
- Static safety validation: `12/12`.
- Runtime execution was not performed because F portable host access is required.
- No new task, new runner, parallel runner, fabricated heartbeat or fabricated elevation output was created.
- `final_ready=false`
