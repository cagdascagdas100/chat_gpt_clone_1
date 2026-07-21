# height_difference_3 — sequence 19 remote HEAD parity ready

## Scope
- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761`)
- Single existing shared runner only.
- `final_ready=false`; no fabricated parcel, geometry or elevation values.

## Remote readback
Sequence 18 remained authoritative at cycle start. The heartbeat was stale and unclaimed, runtime was `NOT_STARTED`, and no real `032` output, canonical shard, candidate manifest, HMLR match, measurement or port-8012 acceptance artefact existed.

## Gap closed
The previous `034` gate compared required files with the local Git HEAD, but did not prove that local HEAD was the current remote continuation-branch HEAD. A clean but stale F worktree after the minimum commit could therefore pass.

The updated gate now:
1. validates the expected GitHub repository identity from the configured remote URL;
2. fetches the exact continuation branch into `refs/remotes/origin/...` with interactive prompts disabled;
3. requires local HEAD to equal the freshly fetched remote HEAD exactly;
4. rejects stale local HEAD, local-ahead HEAD, wrong repository, wrong branch, missing remote ref, dirty required files and non-ancestor minimum commit;
5. continues to verify 20 critical pipeline/task files against their HEAD Git blobs before official source access.

`032` passes the remote name, repository identity and Git timeout into `034`. The existing `012` task contract was updated; no queue, lease, owner, heartbeat, new runner or parallel runner was created.

## Validation
- New tests: `24/24 PASS`
- Cumulative tests: `232/232 PASS`
- Fixture data was not promoted.
- Real network downloads: `0`
- Real candidates/measurements/examples: `0`

## Current blocker
The existing F portable runner must execute:
`RUN_032_WITH_EXACT_FETCHED_REMOTE_HEAD_PARITY_THEN_029_030_026_027_AND_TRANSACTIONAL_033_031_PORT_8012_ACCEPTANCE_ON_EXISTING_F_RUNNER`

Real completion still requires exactly three canonical rows (`61523-61525`), official HMLR polygons, EA DTM 1m measurements, OS Terrain 50 crosschecks and transactional port `8012` readback.
