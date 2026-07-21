# height_difference_3 — Sequence 23 transient retry readiness

- Slot: `height_difference_3`
- Parcel rows: `61523-92283` (`30,761`)
- Canonical source count: `92,283`
- Final ready: `false`

## Completed

1. Re-read sequence 22 remote checkpoint, status, heartbeat, current-task, runtime and task contract.
2. Confirmed the existing F runner remains unclaimed and no real 037/032 output exists.
3. Revalidated official HMLR INSPIRE 5 July 2026 publication, persistent EA DTM 1m WCS and OS Terrain 50 July 2026 release.
4. Audited official-source acquisition behavior. OS Terrain 50 already has bounded atomic retries; the full audited chain lacked a common transient-only retry layer for HMLR/EA/service failures.
5. Added `038_retry_audited_entrypoint_transient.py`.
6. Updated existing task `012` to execute `038 -> 037 -> 032` without creating a new task, queue, lease, claim or runner.
7. Exposed the retry contract in current-task and website runtime files.
8. Passed `26/26` new tests; cumulative tests are `318/318`.

## Retry policy

Retry is limited to DNS temporary failure, timeout, connection reset/refused, HTTP 429/500/502/503/504 and temporary TLS handshake failures. The maximum is three sequential attempts in the same existing runner process with delays of 2 and 4 seconds. Each attempt repeats safe synchronization, control-plane audit and resumable artefact validation.

Checksum mismatch, dirty/wrong worktree, identity or alias inconsistency, invalid geometry/CRS, unsafe archive, duplicate/gapped runtime and safety-flag failures stop immediately and are never retried.

## Real data state

- Canonical shard rows exported: `0/30,761`
- Real parcel candidates: `0`
- HMLR polygon matches: `0`
- EA DTM samples: `0`
- OS Terrain 50 crosschecks: `0`
- Verified website examples: `0`
- Port 8012 accepted: `false`

## Blocker

The existing F runner has not claimed or executed the updated audited task. Real canonical rows, official polygon/elevation results and transactional port 8012 readback remain required.

## Next step

`RUN_038_TRANSIENT_RETRY_WRAPPER_THEN_037_SAFE_SYNC_CONTROL_AUDIT_AND_EXISTING_032_TRANSACTIONAL_PORT_8012_ACCEPTANCE`
