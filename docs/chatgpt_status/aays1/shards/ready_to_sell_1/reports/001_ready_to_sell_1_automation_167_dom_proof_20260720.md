# Ready to Sell 1 — V53 Web Recovery Evidence

- SLOT_ID: `ready_to_sell_1`
- Continuation key: `6a91b39620b1c0a5f98eb2831178dff6108c64dce6db205f58296ca657e4e8be`
- Task: `ready_to_sell_1_automation_167_dom_proof_20260720_01`
- State: `PUBLISH_PENDING`
- Updated: `2026-07-29T11:28:52Z`
- Final ready: `false`

## Aggregate state

- Operations: `290/291` (`99.66%`)
- Geometry rows: `1264`
- Raw candidates: `519`
- Duplicate exclusions: `12`
- Unique candidates: `507`
- Internet-reverified candidates: `483`
- Verified sources: `1388`
- Exact INSPIRE matches: `2`
- Published unverified parcel values: `0`

## Current recovery work

Seven Batch 51 candidates were re-read from live Acuitus property pages. All seven pages were live and their stored core price, rent, tenure, use and historical sale-status facts matched. Four Companies House entity records were also read. This covers `7/31` Batch 51 candidates (`22.58%`) in this recovery pass.

| Row | Listing | Result | New or strengthened evidence | Parcel binding |
|---:|---|---|---|---|
| 489 | ACUITUS-5374 | PASS | Sold £2,402,000; £179,964 rent; retail plus seven flats; BHF lease to 2029; outstanding 2024 review; VAT not applicable; retail EPC C; BHF company 00699547 active | UNBOUND |
| 490 | ACUITUS-5357 | PASS | Sold £275,000; £20,500 rent; lease from 25 Nov 2024 with 2027 option; freehold; VAT not applicable; EPC C73; Specsavers company 01721624 active | UNBOUND |
| 491 | ACUITUS-5377 | PASS | Sold Post; £43,000 rent; Ryman unit; two flats; June 2025 break not exercised; outside LTA 1954; freehold | UNBOUND |
| 503 | ACUITUS-5296 | PASS | Sold Prior; £55,840 rent; restaurant lease to Feb 2037; four flats; freehold; VAT not applicable | UNBOUND |
| 504 | ACUITUS-5290 | PASS | Sold Post; £8,400 rent; agreement for lease; four long-lease flats; VAT applicable; Section 5B statement; six-week completion term | UNBOUND |
| 505 | ACUITUS-5292 | PASS | Sold £308,000; £32,684 rent; café/bar; two flats; storage/distribution; five parking spaces; VAT applicable | UNBOUND |
| 507 | ACUITUS-5302 | PASS WITH MATERIAL RISK | Sold £470,000; £50,000 rent; tenant company 04560776 active and registered at the property; guarantor company 03738249 is in liquidation | UNBOUND |

## Material risk correction

`STEPS TO WORK` (company `03738249`), stated on the primary listing as guarantor for row 507, is currently recorded by Companies House as **Liquidation**. The guarantee must therefore not be treated as strengthening current income security without legal-pack and insolvency reconciliation.

## Runtime and publication

No new task or parallel runner was created. The full 1,264-row geometry DOM and 51-batch progress DOM gate was not falsely marked complete because this page does not have the shared coordinator browser/worktree runtime. Operation 291 remains pending.

The row-by-row website is already wired through:

- `england_map_web/data/aays_21_slots/ready_to_sell_1/progress.html`
- `england_map_web/geometry_review_3of4_1264_live.html`

## Remaining blockers

- `WAITING_SHARED_COORDINATOR_FULL_V53_BROWSER_DOM_ACCEPTANCE`
- `EXACT_GEOMETRY_IDENTITY_MISSING_FOR_505_CANDIDATE_ROWS`
- `GUARANTOR_IN_LIQUIDATION_ROW_507_REQUIRES_RISK_RECONCILIATION`

## Source URLs

- https://www.acuitus.co.uk/property/5374/
- https://www.acuitus.co.uk/property/5357/
- https://www.acuitus.co.uk/property/5377/
- https://www.acuitus.co.uk/property/5296/
- https://www.acuitus.co.uk/property/5290/
- https://www.acuitus.co.uk/property/5292/
- https://www.acuitus.co.uk/property/5302/
- https://find-and-update.company-information.service.gov.uk/company/00699547
- https://find-and-update.company-information.service.gov.uk/company/01721624
- https://find-and-update.company-information.service.gov.uk/company/04560776
- https://find-and-update.company-information.service.gov.uk/company/03738249
