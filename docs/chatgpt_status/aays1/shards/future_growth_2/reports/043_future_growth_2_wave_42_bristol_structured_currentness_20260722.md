# future_growth_2 Wave 42 — Bristol structured capacity and currentness

## Scope

Thirty official Planning Data brownfield-land entities from Bristol City Council were reviewed as source candidates only. No canonical parcel identity, HMLR exact intersection, Future Growth score or business row was produced.

## Result

- 30 official records researched
- 26 blank-end, positive structured-capacity records retained as point-only review candidates
- 4 explicit-end historical records excluded fail-closed
- 23 current permissioned records and 3 current not-permissioned records
- 22 permissioned candidates retained with stale-delivery review because the structured permission date is before 2023
- structural checks 128/128 PASS
- official remote field checks 120/120 PASS
- five grouped repository duplicate screens returned zero indexed matches

Largest current structured capacities include Former School Site Hawkfield Road (350), Little Paradise and Stafford Street (316), Dove Lane (230), Flowers Hill (160), and Plot ND6 Temple Quay (120).

Historical exclusions are Parkview Office Campus (368, end 2022-12-18), Bristol Water Bishopsworth Road (62, end 2024-04-01), Open Space Kingswear Road (16, end 2024-04-01), and Tavistock Road (12, end 2024-04-01).

## Guards

All source geometries are points and remain capped as candidate locators rather than site boundaries. Source confidence is not parcel identity. Product fields remain null until direct `period=current` validation, real HMLR ZIP/GML acquisition, exact INSPIRE-ID shard intersection and an approved score-decision contract are available.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.