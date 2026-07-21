# internet_access_2 — low-memory resilient official r2 execution hardening

Date: 2026-07-21  
Slot: `internet_access_2`  
Partition: `30762-61522` (`30,761` canonical rows)

## Fresh remote state

- checkpoint sequence: `0`
- status: `ready_for_claim`
- ownership/heartbeat: `unclaimed`, stale
- current task: `idle`
- first unverified step unchanged
- `final_ready=false`

## Internet source refresh

- Ofcom Spring 2026 publication readback confirms publication on 13 May 2026, a January 2026 coverage snapshot and a listed 32.2 MB fixed broadband download.
- ONSPD May 2026 hosted table is current as at May 2026 and was updated 10 June 2026.
- Online ONSPD Live states live postcode centroids as at May 2026 and was updated 17 June 2026.
- NSPL May 2026 is added as secondary best-fit geography QA.
- OS Code-Point Open remains a quarterly fallback current-postcode locator.
- Ofcom planned deployments 2026 is rejected for current coverage rows because it is forward-looking.

## New execution path

1. Stream the minified 92,283-row canonical GeoJSON and sparse legacy internet GeoJSON without loading either entire file into memory.
2. Write only rows 30,762–61,522 and capture source/output SHA-256.
3. Run three deterministic preflight suites: extractor 12/12, slicer 12/12 and publisher 10/10.
4. Resolve Ofcom DNS, retry the official download, reject undersized/non-ZIP bytes, hash the package, reject all-premises r1 files and require exactly 121 corrected r2 files.
5. Perform the exact current-r2 join and publish only strict review readback.

## Executed validation

- streaming slicer: `12/12 PASS`
- resilient runner static contract: `16/16 PASS`
- combined retained validation: `50/50 PASS`
- actual business rows written: `0`

## Current network evidence

The assistant container could read the official web metadata, but direct byte retrieval failed because `www.ofcom.org.uk` could not be resolved. `curl` exited with code 6. Therefore no ZIP hash or real slot counts are claimed.

## Remaining gate

Run `009_probe_download_slice_join_publish_slot2.ps1` on the existing canonical single runner, then publish the generated hashes, exact 30,761-row status counts and review examples through the serial publisher.
