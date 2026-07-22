# Ready to Sell 2 — Wave 28 Company Registry Source Upgrades

- Slot: `ready_to_sell_2`
- Parcel partition: `30762-61522`
- Source snapshot: `2026-07-22`
- Result: `SOURCE_UPGRADE_ONLY_AUTOMATION_167_PENDING`

## Screening result

| Metric | Count |
|---|---:|
| Current official rows screened | 6 |
| Confirmed prior-candidate duplicates not rewritten | 5 |
| Withheld pending conclusive repository identity check | 1 |
| New unique candidates written | 0 |
| Existing candidate source upgrades | 4 |
| Registry integrity rows | 4 |

`29 Lowther Street, Carlisle` was not counted as new because repository-wide identity evidence was not conclusive in this pass.

## High-confidence source upgrades

| Candidate | Property evidence | Official registry evidence | Confidence |
|---|---|---|---:|
| Pizza Express, 50 Blue Boar Row | Acuitus direct page: lease to 2034 without breaks, GBP 56,950 rent | Companies House `02805490`, active | 100/100 |
| Holland & Barrett, 253 High Street | Acuitus direct page: renewed five-year lease from 24 February 2026, GBP 18,000 rent | Companies House `02758955`, active | 100/100 |
| Sports Direct, 638 High Road | Acuitus direct page: GBP 175,000 rent | Companies House `03406347`, active; current name Frasers Group Trading Limited; former Sportsdirect.com Retail Limited name preserved | 100/100 |
| Tesco and Flats, 58-60 Calverton Road | Acuitus direct page: Tesco lease to August 2039 subject to option | Companies House `00519500`, active | 100/100 |

Property sources:
- https://www.acuitus.co.uk/property/5809/
- https://www.acuitus.co.uk/property/5751/
- https://www.acuitus.co.uk/property/5800/
- https://www.acuitus.co.uk/property/5717/

Registry sources:
- https://find-and-update.company-information.service.gov.uk/company/02805490
- https://find-and-update.company-information.service.gov.uk/company/02758955
- https://find-and-update.company-information.service.gov.uk/company/03406347
- https://find-and-update.company-information.service.gov.uk/company/00519500

## Progress

- Completed operations: `289/290`
- Batch progress: `99.66%`
- Batch increase: `+0.01` percentage points
- Overall progress: `99.67%`
- Overall increase: `+0.01` percentage points
- Unique researched candidates preserved: `178`
- Current/upcoming/available candidates preserved: `175`
- Cumulative duplicate removals: `12`
- Cumulative source upgrades: `139`
- Cumulative integrity repairs: `8`
- Aggregate source confidence: `98.64/100`
- Latest upgrade confidence: `100/100`
- Promoted rows: `0`

## Remaining gate

`AUTOMATION_167_DOM_PROOF` remains the first unverified step. The existing shared runner has not published the required port-8012 real headless-browser acceptance truth. No new or parallel runner was created and no global current task was overwritten.

Safety remains: `final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
