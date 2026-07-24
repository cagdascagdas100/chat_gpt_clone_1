# AAYS Five-Slot Ownership and Gate Contract

`WORKSTREAM_ID=AAYS_5_SLOT_SAFE_PARALLEL_V1`

1. A ChatGPT page belongs to exactly the `slot_id` embedded in its ZIP.
2. ZIP content is historical context. GitHub branch HEAD and the matching slot checkpoint are authoritative.
3. A page must read `manifest_latest.json`, its own ownership, checkpoint, heartbeat, current-task, and status files before writing.
4. A page may claim only its own slot. A non-stale lease owned by another page blocks writes.
5. A stale lease can be replaced only after a fresh GitHub HEAD read and remote readback of the replacement commit.
6. Slot-local evidence may progress concurrently. The local Windows runner remains one canonical process and executes queued local tasks serially.
7. Shared application/index paths require the single `shared_publish_gate` in `gates_status_latest.json`.
8. A slot must not modify another slot root or create a runner, guardian, coordinator, or duplicate task.
9. Terminal tasks are never replayed. Stale heartbeat is never treated as active work.
10. Completed, 100 percent, or `final_ready=true` requires real commit, push, remote readback, and requested browser/output evidence.

This contract prevents cross-slot ownership and shared-file collisions without creating parallel runner processes.
