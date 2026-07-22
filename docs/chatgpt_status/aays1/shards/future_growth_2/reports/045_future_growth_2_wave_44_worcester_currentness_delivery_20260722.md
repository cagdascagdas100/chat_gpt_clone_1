# future_growth_2 Wave 44 — Worcester currentness and delivery audit

## Scope
Only `future_growth_2` was touched. Thirty official Worcester City Council brownfield-land records were reviewed as source candidates. These are not parcel matches or Future Growth scores.

## Official source readback
- Planning Data brownfield-land dataset and Worcester provider overview.
- Provider readback: 109 records, Open Government Licence, endpoint last updated 2025-12-20 and last accessed 2026-07-20.
- Thirty selected records received structured entity field checks.
- Five grouped exact-reference repository searches returned no indexed overlap; this is duplicate screening only, not completeness proof.

## Decisions
- 8 eligible current point-review candidates.
- 9 current records held fail-closed.
- 13 explicit-end historical records excluded.
- Eligible examples: Navigation Road (495), Woodside Point (75), Ribble Close and Gas Holder Site (50), County Council Offices (20), Old Brewery Service Station (18).
- SWDP43/c was held for planning status/type/date conflict.
- SWDP43/7 was held because structured maximum is 35 while the official narrative references a current 40-dwelling application.
- Three current records showing construction or partial completion were held.
- Two blank-end records carrying expired-permission notes were held.
- Three low-capacity anomalies and one missing-spatial record were held.

## Validation
- Structural checks: 132/132 PASS.
- Official remote field checks: 120/120 PASS.
- Decision arithmetic: 30 = 8 eligible + 22 held/excluded.
- Cumulative arithmetic: 518 = 302 eligible + 216 held/excluded.

## Product guard
Canonical shard rows, parcel matches, scores and business rows remain zero. Direct `period=current`, live HMLR ZIP/GML download, exact intersection and an approved score-decision contract are still required.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
