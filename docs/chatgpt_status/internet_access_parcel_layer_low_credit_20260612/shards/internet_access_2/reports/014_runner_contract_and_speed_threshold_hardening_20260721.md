# internet_access_2 — runner contract repair and speed-threshold hardening

Date: 2026-07-21  
Slot: `internet_access_2`  
Range: `30762-61522` (`30,761` rows)

## Defect found and repaired

The V2 validator had expanded from 18 to 26 deterministic checks and changed its successful status to `PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED`, but the PowerShell orchestrator still required 18 checks and the superseded status. A networked runner would therefore have stopped even after valid official-source validation.

The orchestrator now:

- requires the expanded validator selftest count of `32/32`;
- accepts the current correction-and-semantics status;
- requires `coverage_speed_threshold_order_validated=true`;
- records the current Ofcom web-listed ZIP metadata as `32.3 MB`;
- retains byte-size, ZIP signature, SHA-256, r1 rejection, exact r2 count, no-business-write and fail-closed gates.

## New source-integrity rule

Ofcom defines fixed coverage fields as thresholds of at least 30, 100 and 300 Mbit/s, plus gigabit-capable service. For each postcode row the validator now requires:

`SFBB 30+ >= UFBB 100+ >= UFBB 300+ >= Gigabit capable`

Missing values are not invented. Equal values are allowed. Any higher threshold exceeding the preceding lower threshold fails the package before slicing, joining or web publication.

## Executed validation

- expanded Ofcom V2 validator: `32/32 PASS`
- repaired runner static contract: `23/23 PASS`
- combined deterministic validation: `105/105 PASS`
- real source rows extracted: `0`
- business rows written: `0`
- `final_ready=false`

The real `30,761`-row run remains blocked by stale watcher/runner heartbeats and the existing `security_public_safety_3` queue-head task.
