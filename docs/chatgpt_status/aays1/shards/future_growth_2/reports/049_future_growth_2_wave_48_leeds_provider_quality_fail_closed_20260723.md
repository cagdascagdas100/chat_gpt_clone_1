# future_growth_2 — Wave 48 Leeds provider-quality fail-closed review

## Scope

This wave reviews forty official Leeds City Council brownfield-land entity records as source candidates only. It does not claim canonical parcel identity, HMLR intersection, Future Growth scores, database writes or production readiness.

## Result

- 40 official records researched
- 12 retained for eligible point-only review
- 20 current records held fail-closed
- 8 explicit-end historical records excluded
- all 12 eligible candidates have source-evidence confidence 98/100
- five grouped repository duplicate screens returned zero indexed matches
- structural validation: 180/180 PASS
- official remote field evidence: 160/160 PASS

## Eligible review examples

- SHL00065 — Land at Kirkstall Road and land off Wellington Road — maximum 1,010 dwellings
- SHL01573 — Great George Street / LGI — maximum 329 dwellings
- SHL01942 — Leeds College of Building, Millwright Building — maximum 136 dwellings
- SHL02043 — Sandway Business Centre — maximum 85 dwellings
- SHL02025 — 2 Great George Street — maximum 83 dwellings

## Fail-closed guards

Eleven current records were held for low structured capacity, five for permission status/date conflicts, eleven for structured/narrative capacity mismatch and three for official entity/curie currentness conflicts. Some records trigger more than one guard. Eight records with explicit end dates were excluded as historical.

## Provider quality

The official Leeds provider overview reports three brownfield-land issues and a needs-improving quality state. No organisation-level URL access errors were reported. The provider caveat was retained and no new source contract was promoted.

## Product boundary

All locations remain point-only candidate locators, not site boundaries or parcel identity. Canonical shard rows, HMLR exact intersections, product scores and business rows remain zero until the live evidence chain and approved score-decision contract are executed.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.