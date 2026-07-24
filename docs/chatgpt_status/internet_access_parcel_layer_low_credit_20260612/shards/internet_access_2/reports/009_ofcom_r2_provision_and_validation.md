# internet_access_2 — Ofcom archive provision and validation

- State: `OFFICIAL_SOURCE_SCHEMA_VALIDATED_ARCHIVE_BYTES_PENDING`
- Continuation key: `40ce1dc4f1ad5a0ab95078c6b920881699b36760c9c4579f3050b21d6cd68e36`
- Canonical progress: `2/3` (`66.67%`, change `+0.00%`)
- Support checks: `8/9`
- Prepared postcode samples: `24`
- Postcode identities confirmed: `24/24`
- Official coverage verified candidates: `0`
- Accuracy values written: `0`

## Official-source checks

1. Ofcom Connected Nations Spring 2026 publication page: PASS.
2. Direct official fixed-broadband ZIP link, labelled 32.2 MB: PASS link discovery.
3. Provider scope: 52 fixed-network and 18 FWA providers.
4. Premise base: Ordnance Survey AddressBase Premium and Islands, Epoch 123.
5. All-premises postcode contract: 121 files, 1,741,096 rows.
6. Residential postcode contract: 121 files, 1,606,191 rows.
7. Postcode identity fields: `postcode`, `postcode_space`, `postcode area`.
8. Coverage fields: SFBB, UFBB 100, UFBB 300, Gigabit and unable-to-receive percentages.

Ofcom records that full-fibre coverage is not published at postcode or census-output-area level because of commercial confidentiality. No full-fibre postcode value is inferred.

## Archive execution

Two bounded download attempts were made in this execution environment. The managed downloader failed, and the local urllib attempt failed at DNS resolution. No archive bytes, hash, CRC, file count or coverage values were accepted.

The P0 canonical-runner task remains queued under commit `ee739529f01bbf983a3469ff33f5db66d4014fdc`. The expected runner output is `status/009_status.json`; this page-side status file records source/schema preparation only and must be replaced by a tested archive result when the runner completes.

- Fake data: false
- Database write: false
- Migration: false
- Production deploy: false
- final_ready: false
