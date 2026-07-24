# internet_access_3 — Ofcom Spring 2026 source revalidation

- Slot: `internet_access_3`
- Parcel range: `61523-92283`
- Verified at: `2026-07-22T03:31:15+03:00`
- Final ready: `false`

## Verified official source

Ofcom published **Connected Nations update: Spring 2026** on 13 May 2026, using a January 2026 fixed-broadband availability snapshot. The accompanying fixed-coverage package contains postcode-level coverage data.

Official page:
`https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026`

Official package:
`https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620`

Official schema document:
`https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf?v=422757`

## Important correction gate

The schema document records a **v2 correction dated 7 July 2026**:

1. the earlier CW file duplicated CV and was corrected;
2. the earlier MK file duplicated ME and was corrected;
3. all 121 all-premises postcode files are now expected as `202601_fixed_postcode_coverage_r2_XX.csv`.

Any task that accepts an `r1` all-premises postcode member, or that does not verify the corrected CW/MK members, must fail closed.

## Dataset contract

- Expected all-premises postcode files: `121`
- Reported postcode rows: `1,741,096`
- Reported uncompressed size: `165 MB`
- Postcode fields: normalized and spaced postcode
- Confirmed coverage fields: SFBB 30 Mbit/s, UFBB 100 Mbit/s, UFBB 300 Mbit/s, gigabit-capable availability and unavailable-speed percentages
- Postcode-level full-fibre percentage is not published because of commercial confidentiality

## Accuracy decision

- Source authority and freshness: `95/100`
- Current parcel-to-postcode relation: remains `50/100` until independently revalidated
- Current overall row confidence ceiling: `50/100`
- Coverage must not be described as measured speed
- Postcode coverage must not be described as a parcel-level measurement

## Next executable step

Run the existing migration first, then deterministically select a small set of migrated rows from this shard and compare their legacy postcode coverage values against the corrected January 2026 Ofcom postcode files. Only exact postcode matches may become revalidated candidates. Mismatches and absent postcodes remain blocked or `NO_DATA`.

Safety remains: `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
