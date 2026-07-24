# future_growth_3 — Wave 36

- Slot: `future_growth_3`
- Shard: `61523–92283` (`30761` canonical rows expected)
- Sources: Leicester City Council, Reading Borough Council, Newcastle City Council through official MHCLG Planning Data
- Candidate rows: 24 researched / 24 eligible / 0 excluded / 24 high-confidence
- Mean source confidence: 98.13/100
- Visible web rows: 24 candidate + 36 operation rows

## QA

- 24/24 exact authoritative entities with official WGS84 points
- 20 structured-capacity rows and 4 described-capacity-only rows
- 6 historical end-date rows
- 3 entity/CURIE temporal version differences retained as explicit conflicts
- 4 missing planning-status fields retained as null
- Canonical row, canonical parcel and score fields remain null
- Fake data: 0

## Canonical export acquisition

Ten new repository searches increased the audit total from 131 to 141. No exact 30,761-row canonical parcel export, stable parcel geometry identifier, CRS manifest or workflow artifact was found. The inspected Wave 36 commit had no PR-triggered workflow runs.

## Progress

- Completed operations: 7/12
- Partial operations: 1/12
- Operational progress: 58.33% (+0.00)
- Verified product rows: 0/30,761 (0%)
- `final_ready=false`
- No DB write, migration or production deployment
