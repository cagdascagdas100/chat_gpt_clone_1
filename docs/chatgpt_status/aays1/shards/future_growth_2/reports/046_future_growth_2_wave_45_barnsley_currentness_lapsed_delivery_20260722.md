# future_growth_2 Wave 45 — Barnsley currentness, lapsed-permission and delivery audit

## Scope
Only `future_growth_2` was changed. Thirty official Barnsley Metropolitan Borough Council brownfield-land records were reviewed as source candidates. They are not parcel matches or Future Growth scores.

## Official source readback
- Planning Data brownfield-land dataset, Barnsley provider overview and official register review information.
- Provider readback: 99 records, Open Government Licence, endpoint last updated 2024-12-07 and last accessed 2026-07-09; the provider overview reports one issue requiring improvement.
- Thirty selected entity records received structured field readbacks and fail-closed decision checks.
- Five grouped exact-reference repository searches returned no indexed overlap; this is duplicate screening only, not completeness proof.

## Decisions
- 6 eligible current point-review candidates.
- 11 current records held fail-closed.
- 13 explicit-end historical records excluded.
- Eligible examples: MU3 (1,346), H2129 (136), HS3 (102), HS49 (65), H2371 (32) and HS53 (25 dwellings).
- H2129 and H2371 remain stale-delivery reviews; HS3 is only an active reserved-matters review.
- TCDS2 was held for planning status/type/date conflict.
- TCDS3 and HS80 were held for construction or partial-delivery evidence.
- Seven current records with lapsed, withdrawn or superseded evidence were held.
- Four low-capacity or zero-hectare current records were held.
- Two historical predecessor records were excluded as superseded versions.

## Validation
- Structural checks: 134/134 PASS.
- Official remote field checks: 120/120 PASS.
- Decision arithmetic: 30 = 6 eligible + 24 held/excluded.
- Cumulative arithmetic: 548 = 308 eligible + 240 held/excluded.

## Product guard
Canonical shard rows, parcel matches, scores and business rows remain zero. Direct `period=current`, live HMLR ZIP/GML download, exact intersection and an approved score-decision contract are still required.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
