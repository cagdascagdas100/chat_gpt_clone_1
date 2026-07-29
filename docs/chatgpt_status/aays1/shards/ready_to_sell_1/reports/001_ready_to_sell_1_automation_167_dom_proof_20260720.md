# Ready to Sell 1 — V53 Web Recovery Evidence

- SLOT_ID: `ready_to_sell_1`
- Continuation key: `6a91b39620b1c0a5f98eb2831178dff6108c64dce6db205f58296ca657e4e8be`
- Task: `ready_to_sell_1_automation_167_dom_proof_20260720_01`
- State: `PUBLISH_PENDING`
- Updated: `2026-07-29T12:15:00Z`
- Final ready: `false`

## Aggregate

- Operations: `290/291` (`99.66%`)
- Unique candidates: `507`
- Internet-reverified candidates: `483`
- Verified sources: `1388`
- Geometry rows: `1264`
- Exact INSPIRE matches: `2`
- Published unverified parcel values: `0`

## Recovery coverage

- Batch 51: `31/31` rows checked (`100%`)
- Batch 50 current pass: `12/34` rows checked (`35.29%`)
- Combined Batch 50–51: `43/65` rows (`66.15%`)
- Combined recovery coverage across all unique candidates: `43/507` (`8.48%`)
- New primary price/historical-status contradictions in this pass: `0`
- Known tenure contradictions retained: `2`
- Known source-internal conflicts: `3`
- Parcel-bound rows added: `0`

## Batch 50 rows 455–466

| Row | Listing | Result | Live evidence and material limitation | Parcel |
|---:|---|---|---|---|
| 455 | ACUITUS-5460 | PASS WITH RECONCILIATION | Sold Prior; £182,862 stated income; freehold eight-unit parade; 9,163 sq ft; about 20 parking spaces. Unit 103 income includes a seller-funded one-year guarantee after a break. The page has an impossible notice/break date sequence; the addendum separately says the Unit 99 replacement lease was agreed but not documented. Luxury Leisure 02448035 is active. | UNBOUND |
| 456 | ACUITUS-5461 | PASS WITH COMPLETION DEPENDENCY | Sold Post; £24,000 rent; retail lease to 2033; virtual freehold for 999 years from completion; VAT not applicable; EPC B. Auction status is not completion evidence. | UNBOUND |
| 457 | ACUITUS-5462 | PASS WITH PLANNING READBACK PENDING | Withdrawn Post; vacant 0.56 ha freehold site; primary page states 16 dwellings under 19/503810/OUT, reserved matters and 2025 condition approval; £182,000 section 106; no CIL. Council decision documents were not independently read in this pass. | UNBOUND |
| 458 | ACUITUS-5463 | PASS WITH COMPLETION DEPENDENCY | Withdrawn Post; £25,000 rent; barber lease from April 2017; stated 80-year long leasehold from completion; VAT not applicable. Because the sale was withdrawn, the superior lease cannot be treated as commenced. | UNBOUND |
| 459 | ACUITUS-5464 | PASS WITH RECEIVERSHIP/FILING RISK | Sold £700,000; £78,732 rent; freehold 0.49-acre office and warehouse site; receiver sale; office EPC B and warehouse EPC C. Rocket Vehicle Group 13716702 is active. Konnexa 14955935 is active and registered at the property, but accounts are overdue. | UNBOUND |
| 460 | ACUITUS-5465 | PASS WITH HOLDING-OVER RISK | Sold Prior; £28,000 rent; 4,032 sq ft office; title TY25093; long leasehold to 2114; EPC C. Education Development Trust 00867944 is active, but the occupational term ended in September 2018 and the tenant is described as holding over. | UNBOUND |
| 461 | ACUITUS-5466 | PASS WITH IDENTITY/PLANNING LIMIT | Withdrawn Post; £102,000 stated rent; freehold church and upper HMO; 6,481 sq ft; redevelopment subject to consent. Exact corporate identity is not provided for all occupiers and redevelopment potential is not permission. | UNBOUND |
| 462 | ACUITUS-5467 | PASS | Sold £310,000; £28,000 rent; renewed Holland & Barrett lease from May 2025 with May 2028 break; freehold; 1,736 sq ft; VAT not applicable. Holland & Barrett Retail 02758955 is active. | UNBOUND |
| 463 | ACUITUS-5468 | PASS WITH EXPIRED AST/FILING RISK | Withdrawn Post; £139,243 stated rent; freehold 12-studio building; single AST for 12 months from 25 July 2024. The AST expired in July 2025. WH Broadway 10589255 is active but its accounts are overdue. Current occupation and rent remain unknown. | UNBOUND |
| 464 | ACUITUS-5469 | PASS WITH SOURCE RENT CONFLICT | Sold Prior; headline rent £73,351; Heron Foods lease to 2032; RPI review in 2028; freehold; EPC C. The tenancy table total states £73,315, creating an unresolved £36 source arithmetic conflict. Heron Foods 01392197 is active. | UNBOUND |
| 465 | ACUITUS-5473 | PASS WITH SUPERIOR-LEASE DEPENDENCY | Sold £154,000; £12,000 rent; Bain Plumbing lease to March 2028; 2,296 sq ft; 150-year long leasehold from completion; EPC E. Bain Plumbing Services 05972282 is active and registered at Unit 6A. Auction result is not Land Registry completion evidence. | UNBOUND |
| 466 | ACUITUS-5474 | PASS WITH UNEXECUTED LEASE/DEVELOPMENT RISK | Sold £2,500,000; £157,000 rent plus vacant flat, storage and land; freehold; three shops and three maisonettes. Terms with The Sushi Co were agreed but not evidenced as an executed lease. Rear development is supported only by pre-application feedback and remains subject to consent. | UNBOUND |

## Existing Batch 51 mandatory corrections retained

1. Row 498: live primary page says `Leasehold`; stored record says `Freehold`.
2. Row 510: live primary page says `Leasehold`; stored record says `Freehold`.
3. Row 499: source headline and tenancy table disagree on area.
4. Row 507: guarantor `STEPS TO WORK` is in liquidation.
5. Rows 506, 514 and 519 require current occupation or rent confirmation because stated dates have passed.
6. Row 496 company name changed after the historical auction record.

## Runtime and website

No second task or parallel runner was created. The existing single coordinator remains authoritative. The full 1,264-row geometry DOM and 51-batch progress DOM acceptance is still operation `291` and was not falsely marked complete.

Current task write permissions cover only this JSON and Markdown report. Therefore canonical candidate files and the England map website were not mutated. This Markdown report is rendered row by row on the GitHub child branch.

Existing project pages:

- `england_map_web/data/aays_21_slots/ready_to_sell_1/progress.html`
- `england_map_web/geometry_review_3of4_1264_live.html`

## Remaining blockers

- `WAITING_SHARED_COORDINATOR_FULL_V53_BROWSER_DOM_ACCEPTANCE`
- `EXACT_GEOMETRY_IDENTITY_MISSING_FOR_505_CANDIDATE_ROWS`
- `CANONICAL_CANDIDATE_CORRECTIONS_NOT_YET_ALLOWED_OUTSIDE_EXACT_WRITE_PATHS`
