# internet_access_2 — low-memory resilient official V2 r2 execution hardening

Date: 2026-07-21  
Slot: `internet_access_2`  
Partition: `30762-61522` (`30,761` canonical rows)

## Fresh remote state

- authoritative HEAD readback: `0d4770d7cce88e53f53b205cd85ba8c92ef6628e`
- checkpoint sequence: `0`
- status: `ready_for_claim`
- ownership/heartbeat: `unclaimed`, stale
- current task: `idle`
- first unverified step unchanged
- `final_ready=false`

## Internet source refresh

- Ofcom Spring 2026 publication readback confirms publication on 13 May 2026, a January 2026 coverage snapshot and a currently listed 32.3 MB fixed broadband download.
- The download-size value is metadata only; acceptance still requires actual downloaded bytes, ZIP signature and SHA-256 readback.
- Ofcom V2 documentation dated 7 July 2026 states that the CW all-premises postcode file had duplicated CV and MK had duplicated ME; both were corrected and all 121 all-premises postcode files were renamed from r1 to r2.
- ONSPD May 2026 hosted table is current as at May 2026 and was updated 10 June 2026.
- Online ONSPD Live states live postcode centroids as at May 2026 and was updated 17 June 2026.
- NSPL May 2026 is retained as secondary best-fit geography QA.
- OS Code-Point Open remains a quarterly fallback current-postcode locator.
- Ofcom planned deployments 2026 is rejected for current coverage rows because it is forward-looking.

## Hardened execution path

1. Stream the minified 92,283-row canonical GeoJSON and sparse legacy internet GeoJSON without loading either entire file into memory.
2. Write only rows 30,762–61,522 and capture source/output SHA-256.
3. Run deterministic preflight suites before network work.
4. Resolve Ofcom DNS, retry the official download, reject undersized/non-ZIP bytes, hash the package, reject all-premises r1 files and require exactly 121 corrected r2 files.
5. Validate 1,741,096 unique postcode rows, UK postcode syntax, exact `postcode_space` separator, postcode-area consistency, unique normalized headers, non-empty area files and finite 0–100 percentages.
6. Reject postcode-level Full Fibre fields, preserve documented metric denominators and keep fixed-line/FWA semantics explicit.
7. Hash all area files and fail closed unless `CW != CV` and `MK != ME`, directly guarding the two defects identified by Ofcom V2.
8. Perform the exact current-r2 join and publish only strict review readback.

## Executed deterministic validation

- extractor: `12/12 PASS`
- streaming slicer: `12/12 PASS`
- publisher: `10/10 PASS`
- V2-aware runner static contract: `20/20 PASS`
- dispatch readiness: `16/16 PASS`
- Ofcom V2 correction and semantics validator: `26/26 PASS`
- combined retained validation: `96/96 PASS`
- actual business rows written: `0`

## Current network and runner evidence

The assistant container can read official web metadata but direct byte retrieval remains unavailable. Therefore no ZIP SHA-256 or real slot counts are claimed. The watcher heartbeat is stale, shared-runner pickup is not observed, and `security_public_safety_3` attempt `008` is the watcher-visible numeric-priority-1 queue head for 48 rows in four chunks.

Frozen review PR `#96` is mergeable and contains only the `internet_access_2` shard plus authorized `aays_18` web files. It is review-only; final integration requires one fresh transplant onto the then-current authoritative HEAD.

## Remaining gate

After the existing queue-head task becomes terminal, restore fresh watcher and runner heartbeats, transplant the frozen clean review diff once onto the then-current authoritative HEAD, pass all 13 dispatch-readiness gates, then run `009_probe_download_slice_join_publish_slot2.ps1` on the existing canonical single runner.
