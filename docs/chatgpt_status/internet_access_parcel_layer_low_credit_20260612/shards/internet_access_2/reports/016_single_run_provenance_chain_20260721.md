# internet_access_2 — single-run provenance chain

Date: 2026-07-21  
Slot: `internet_access_2`  
Range: `30762-61522` (`30,761` rows)

## Gap closed

The existing published-bundle auditor proved that `runner_readback_latest.json` and `verified_examples_latest.json` agreed with each other. It did not prove that diagnostics, the official V2 validation report, bounded canonical/legacy slices, extraction manifest, candidate JSONL and web files all came from the same runner execution.

## New fail-closed chain

`019_verify_single_run_provenance.py` recomputes and links:

1. official ZIP SHA-256 and terminal diagnostics state;
2. V2 report SHA-256, exact 121 corrected r2 files and 1,741,096 unique postcode rows;
3. canonical and legacy source/slice SHA-256 pairs;
4. bounded slice SHA-256 values to extraction source SHA-256 values;
5. extraction manifest and candidate JSONL SHA-256 values to runner readback;
6. published readback/examples SHA-256 values to the bundle audit;
7. exact direct + legacy-pending-spatial-QA + NO_DATA totals across extraction, readback and audit;
8. one final `provenance_chain_sha256` over the ordered run artifacts.

Any missing file, stale/mixed artifact, count mismatch, malformed hash, incomplete diagnostics state, business-row write, score, migration, deployment or `final_ready=true` fails the run.

## Executed deterministic validation

- single-run provenance verifier: `19/19 PASS`
- upgraded run-and-audit wrapper contract: `21/21 PASS`
- combined deterministic validation: `177/177 PASS`
- real source rows extracted: `0`
- business rows written: `0`
- `final_ready=false`

The real run remains blocked by the occupied shared-runner queue head, stale watcher/runner heartbeat and absence of final authoritative integration.
