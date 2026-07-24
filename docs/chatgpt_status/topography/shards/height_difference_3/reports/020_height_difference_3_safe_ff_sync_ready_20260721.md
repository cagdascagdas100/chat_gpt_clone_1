# Height Difference 3 — Sequence 20 Safe Fast-Forward Readiness

## Scope
- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761`)
- Existing shared F runner only; no queue, lease, owner, heartbeat, new runner, or parallel runner created.

## Work completed
1. Re-read sequence 19 remote state; runtime remained not started and all real counts remained zero.
2. Revalidated current HMLR INSPIRE, EA DTM 1m/WCS, and OS Terrain 50 official contracts.
3. Identified that exact remote parity alone blocks a clean but stale F checkout instead of safely advancing it.
4. Added `035_sync_existing_f_worktree_ff_only.py`.
5. Wired `032` to run `035` before `034`, then continue through the existing measurement and transactional publication chain.
6. Updated the existing `012` task contract; no new task or queue item was created.
7. Passed `21/21` new fixture tests; cumulative result is `253/253`.

## Safety behavior
- Fast-forward occurs only when tracked worktree/index are clean and local HEAD is an ancestor of the freshly fetched remote HEAD.
- Dirty, staged, local-ahead, diverged, wrong-repository, wrong-branch, or active Git-operation states fail closed.
- No reset, rebase, force checkout, or commit creation is permitted.
- Untracked files are not modified.

## Real-result status
- Canonical shard exported: `0/30,761`
- Real candidates/HMLR/EA/Terrain50/published examples: `0/0/0/0/0`
- Port 8012 acceptance: pending

## Next step
`RUN_032_WITH_035_SAFE_FF_SYNC_THEN_034_REMOTE_PARITY_029_030_026_027_AND_TRANSACTIONAL_033_031_PORT_8012_ACCEPTANCE_ON_EXISTING_F_RUNNER`

`final_ready=false`; all safety flags remain false.
