# internet_access_2 — runner contract, speed-threshold and postcode-level schema hardening

Date: 2026-07-21  
Slot: `internet_access_2`  
Range: `30762-61522` (`30,761` rows)

## Previously repaired runner defect

The V2 validator had expanded while the PowerShell orchestrator still required an obsolete test count and success status. A networked runner would therefore have stopped even after valid official-source validation.

The orchestrator now:

- requires the expanded validator selftest count of `43/43`;
- accepts `PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED`;
- requires the corrected duplicate, folder, postcode-level field, percentage-range and speed-threshold readbacks;
- records the current Ofcom web-listed ZIP metadata as `32.3 MB` while treating it as metadata only;
- retains byte-size, ZIP signature, SHA-256, r1 rejection, exact r2 count, no-business-write and fail-closed gates.

## Official postcode-level structure rules added

The Ofcom V2 document states that the 121 all-premises postcode files are in the `postcode_files` folder and contain 1,741,096 rows. It also marks `All Premises`, `All Matched Premises` and all `Number of premises ...` fields as unavailable at postcode level.

The validator therefore now fails closed when:

1. an all-premises r2 file is outside a folder named `postcode_files`;
2. a postcode file contains `All Premises`, `All Matched Premises` or any `Number of premises ...` count column;
3. any percentage column, including columns not used by the current join, is non-numeric, non-finite or outside `0-100`.

The existing rules remain active:

- `CW != CV` and `MK != ME` by SHA-256;
- exactly 121 corrected r2 files and 1,741,096 unique postcode rows;
- exact postcode and `postcode_space` agreement;
- no postcode-level full-fibre fields;
- `SFBB 30+ >= UFBB 100+ >= UFBB 300+ >= Gigabit capable`;
- metric denominators preserved without inventing complements or parcel performance.

## Executed validation

- expanded Ofcom V2 validator: `43/43 PASS`
- repaired runner static contract: `26/26 PASS`
- extractor: `12/12 PASS`
- streaming slicer: `12/12 PASS`
- publisher: `10/10 PASS`
- dispatch readiness contract: `16/16 PASS`
- combined deterministic validation: `119/119 PASS`
- real source rows extracted: `0`
- business rows written: `0`
- `final_ready=false`

The real `30,761`-row run remains blocked by stale watcher/runner heartbeats and the existing `security_public_safety_3` queue-head task.