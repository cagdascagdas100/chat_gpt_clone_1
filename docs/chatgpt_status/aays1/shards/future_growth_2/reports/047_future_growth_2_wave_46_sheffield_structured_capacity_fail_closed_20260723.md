# future_growth_2 Wave 46 — Sheffield structured capacity fail-closed audit

## Scope
Only `future_growth_2` source candidates were changed. No canonical parcel row, score, database, migration, deployment, ownership, heartbeat or runner state was changed.

## Official evidence
Thirty Sheffield City Council brownfield-land entities were read from the official MHCLG Planning Data service. The national dataset readback reported 37,666 records from 354 providers, authoritative quality and Open Government Licence coverage. The Sheffield local-planning-authority entity was identified, but a direct Sheffield provider record count and a direct `period=current` API response were not obtained.

## Decisions
- 8 records are eligible for point-only source review.
- 12 records are held because the production entity JSON omits structured `maximum-net-dwellings`; narrative dwelling text was not silently promoted into the structured field.
- 2 records are held for structured/narrative capacity mismatch.
- 5 records are held as primary low-capacity small-site anomalies.
- 1 missing-maximum record also carries a low-capacity flag.
- 3 explicit-end records are historical exclusions.
- S03857 is fail-closed because the production entity JSON omits the maximum while a staging/search representation exposes 10; production structured evidence controls.

## Validation
- Structural checks: 136/136 PASS.
- Official remote field checks: 120/120 PASS.
- Five grouped exact-reference repository screens returned zero indexed overlap.
- 30 = 8 eligible + 19 current held + 3 historical excluded.
- Cumulative: 578 researched = 316 eligible + 262 held/excluded.

## Product guard
Candidate points are locators, not parcel boundaries. Canonical rows, exact HMLR intersections, parcel matches, Future Growth scores and business writes remain zero.
