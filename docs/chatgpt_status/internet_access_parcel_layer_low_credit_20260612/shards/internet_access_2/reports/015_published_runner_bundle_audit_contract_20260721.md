# internet_access_2 — published runner bundle audit contract

Date: 2026-07-21  
Slot: `internet_access_2`  
Range: `30762-61522` (`30,761` rows)

## Fresh remote finding

The current authoritative branch does not contain either:

- `england_map_web/data/aays_18_slots/internet_access_2/runner_readback_latest.json`
- `england_map_web/data/aays_18_slots/internet_access_2/verified_examples_latest.json`

Both reads returned `Not Found`. Therefore real extracted rows, source hashes and parcel examples remain zero/unverified.

## New fail-closed audit

`015_verify_published_runner_bundle.py` validates the two files only after the existing canonical runner publishes them. It requires:

- exact slot ID, range and `30,761` canonical rows;
- exact direct-current-r2 + legacy-pending-spatial-QA + `NO_DATA` total;
- valid lowercase SHA-256 evidence for the source manifest and candidate JSONL;
- at most nine examples and at most three examples per status;
- unique in-range row numbers and parcel IDs;
- postcode-only truth boundary and strict `NO_DATA` null/confidence rules;
- zero scores, zero business rows, no DB/migration/deploy and `final_ready=false`.

It writes only `runner_bundle_audit_latest.json` under the authorized slot web path.

## Canonical execution wrapper

`017_run_and_audit_slot2.ps1` runs the existing `009` network/extraction/publisher stage, propagates any failure, then requires the bundle audit to pass. The task must use `017` as its execution entry. No new runner is created.

## Executed validation

- published bundle verifier self-test: `18/18 PASS`
- run-and-audit wrapper static contract: `14/14 PASS`
- prior deterministic validation: `119/119 PASS`
- combined deterministic validation: `151/151 PASS`
- real source rows extracted: `0`
- business rows written: `0`
- `final_ready=false`

The real run remains blocked by stale watcher/runner heartbeats, another watcher-visible queue-head task, and the missing final authoritative integration.
