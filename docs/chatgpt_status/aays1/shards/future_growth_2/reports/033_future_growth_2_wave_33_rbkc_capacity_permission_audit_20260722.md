# future_growth_2 wave 33 — RBKC capacity and permission consistency audit

## Scope
Twenty official Royal Borough of Kensington and Chelsea brownfield-land entity pages were reviewed. This remains source-candidate preparation only; points are not parcel boundaries and all product fields remain null.

## Result
- 20 researched records
- 2 eligible source-review candidates
- 17 held fail-closed
- 1 historical record excluded
- 15 structured-versus-narrative capacity mismatches
- 1 permission-status versus official-note conflict
- 1 older official duplicate/superseded reference
- 20 exact entity repository index searches with no indexed overlap; this is not completeness proof
- structural validation 86/86 PASS
- manual official field readback 80/80 PASS

## Eligible
- RBKC004 — 257-265 Odeon Cinema, Kensington High Street — structured 106 dwellings, blank end date, authoritative point and dated permission; stale-delivery review only.
- 17200047 — Kensal Gasworks — structured and narrative 3,500 dwellings, consistently not-permissioned, blank end date; site-allocation review only.

## Fail-closed examples
RBKC031, RBKC019, RBKC030, RBKC011, RBKC008, RBKC002, RBKC009, RBKC024, RBKC017, RBKC016, RBKC012, RBKC013, RBKC014, 17200007 and 17200001 have structured capacities that conflict with their official narratives. RBKC023 says permissioned in structured fields while its official note says permission is yet to be sought. 17200106 duplicates the site, point and capacity of newer RBKC009. RBKC046 has an explicit 2021-06-30 end date.

## Product gate
Canonical shard rows exported: 0. Parcel matches: 0. Future Growth scores: 0. Actual business rows: 0. Direct period=current responses: 0. Actual HMLR downloads/intersections: 0.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
