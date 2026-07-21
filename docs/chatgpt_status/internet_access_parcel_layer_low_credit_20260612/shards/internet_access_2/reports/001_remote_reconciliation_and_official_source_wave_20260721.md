# internet_access_2 — Remote reconciliation and official source wave 1

- Authoritative branch: `codex/aays-single-runner-v5-20260706`
- Authoritative HEAD readback: `0f8f89d53bde7536791de12853904ad24c5044e9`
- Slot: `internet_access_2`
- Partition: `30762-61522` (`30,761` rows)
- First unverified step: `MIGRATE_33785_VERIFIED_ROWS_THEN_CLOSE_58498_WITH_VERIFIED_POSTCODE_OR_NO_DATA`
- Remote ownership: `unclaimed`
- Remote heartbeat: `stale`
- Remote current task: `idle`
- Final ready: `false`

## Work completed in this review wave

1. Re-read authoritative checkpoint, status, heartbeat, current-task and ownership.
2. Confirmed the first unverified step and blocker counts are unchanged.
3. Corrected the proposed allowed paths from stale `slots_18/aays_18` roots to `slots_21/aays_21`.
4. Verified the Ofcom Connected Nations Spring 2026 fixed broadband download.
5. Verified the Ofcom v2 postcode schema and 7 July 2026 correction.
6. Verified two May 2026 ONS postcode directory/crosswalk candidates.
7. Prepared a shard-bounded candidate extractor for row numbers `30762-61522`.
8. Published a line-by-line review page and JSON source table.

## Official source candidates

| # | Source | Authority | Snapshot/update | Data level | Confidence | Status |
|---|---|---|---|---|---:|---|
| 1 | Connected Nations Spring 2026 fixed broadband ZIP | Ofcom | Jan 2026 / 13 May 2026 | POSTCODE_LEVEL_ONLY | 100% | download candidate |
| 2 | About this data v2 | Ofcom | Jan 2026 / 7 Jul 2026 correction | POSTCODE_LEVEL_ONLY | 100% | schema verified |
| 3 | ONSPD May 2026 hosted table | ONS | 10 Jun 2026 | POSTCODE_CROSSWALK_ONLY | 99% | crosswalk candidate |
| 4 | Online ONSPD Live May 2026 | ONS | 17 Jun 2026 | POSTCODE_CENTROID_ONLY | 99% | QA candidate |

Average source confidence: `99.5%`.

## Verified source facts

- The Ofcom update is a January 2026 snapshot.
- The v2 methodology identifies 52 fixed network and 18 fixed wireless access providers.
- The all-premises postcode package has 121 postcode-area files and 1,741,096 rows.
- The corrected filename pattern is `202601_fixed_postcode_coverage_r2_XX.csv`.
- Relevant fields include SFBB, UFBB 100 Mbit/s, UFBB 300 Mbit/s, gigabit availability and percentages unable to receive threshold speeds.
- These metrics remain postcode-level area proxies, not parcel measurements.

## Truth boundary

- Candidate source rows visible: `4`
- Shard business rows extracted: `0`
- Promoted parcel rows: `0`
- Actual business rows written: `0`
- Source hashes: `0`
- Database write: `false`
- Migration: `false`
- Fake data: `false`
- Production deploy: `false`

The existing matrix can be read by the prepared extractor, but no row is promoted until the canonical single runner performs exact row-range extraction, exact-postcode Ofcom cross-check, provenance capture and remote readback. Missing source rows remain `NO_DATA`; no nearest-postcode or synthetic geometry fallback is allowed.
