# internet_access_2 — hardened official r2 extraction contract

- Slot: `internet_access_2`
- Canonical rows: `30762-61522` (`30,761`)
- Authoritative checkpoint sequence: `0`
- Authoritative state: `ready_for_claim`; ownership/heartbeat unclaimed and stale; current task idle
- First unverified step: `MIGRATE_33785_VERIFIED_ROWS_THEN_CLOSE_58498_WITH_VERIFIED_POSTCODE_OR_NO_DATA`

## Completed

1. Re-read all five authoritative slot files after the remote branch advanced.
2. Resolved the deterministic canonical identity carrier to `security.geojson` (`92,283` features).
3. Limited `internet.geojson` (`33,785` features) to legacy postcode evidence only.
4. Locked the Ofcom January 2026 v2 correction gate: `121` all-premises `r2` files and `1,741,096` rows; all-premises `r1` files are rejected.
5. Added the exact official ZIP URL, SHA-256 proof step, guarded expansion and exact slot-count validation.
6. Split ordinary coordinates from percentage parsing so negative longitude values are not incorrectly rejected.
7. Added deterministic contract tests for direct postcode, legacy postcode, NO_DATA, no-score, negative longitude, r1 rejection, invalid percentage rejection, duplicate canonical row rejection and zero business writes.
8. Local self-test result: `12/12 PASS`.
9. Expanded the website to `18` line-by-line operations, `6` source decisions and `12` validation checks.

## Truth boundary

The source values are postcode-level availability percentages, not measured parcel speeds. Direct canonical postcodes may proceed to review; legacy postcode matches require spatial QA; missing or absent current-r2 matches remain `NO_DATA`. No score, migration or business row is emitted by this preparation package.

## Remaining blocker

The existing canonical runner must download/hash the official Ofcom ZIP, run the real `30,761`-row extraction, validate status totals and publish remote readback through the serial publisher.

`actual_business_data_rows_written=0`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`; `final_ready=false`.
