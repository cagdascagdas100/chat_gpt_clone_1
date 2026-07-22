# future_growth_2 wave 32 — Lewisham current-register audit

## Scope

Only `future_growth_2` source-candidate preparation was changed. Twelve official Planning Data brownfield entities were read from the London Borough of Lewisham register. No parcel identity, product score, database row, ownership, heartbeat, task or runner state was created.

## Result

- 12 official records reviewed
- 8 eligible point-only source-review candidates
- 4 records held fail-closed
- 54/54 structural checks passed
- 48/48 official field readbacks passed
- 12 exact entity/reference GitHub index queries returned no indexed overlap; this is screening evidence, not runtime completeness proof

## Eligible records

- `BR009` — 72 Loampit Hill — 8 dwellings
- `CP010` — 241 Stanstead Road — 6 dwellings
- `RG011` — 83-85a Rushey Green — 9 dwellings
- `LC022` — 1 Wearside Road — 9 dwellings
- `NX011` — Former Tidemill School / Giffin Street masterplan area — 193 dwellings
- `RG017` — 128 Catford Hill — 13 dwellings
- `LC008` — Nightingale Grove / Maythorne Cottages — 27 dwellings
- `BK013` — 12a Eton Grove — 10 dwellings

## Fail-closed records

- `EV029` is held because the official point `POINT (-0.369 51.483)` conflicts with the site-address and authority spatial context.
- `EV020` is held because the record is structured as permissioned with no end date while its official note says the permission is now lapsed.
- `RG012` is held because a not-permissioned record also carries a permission date and combines a 602-unit allocation with a lapsed 52-unit application.
- `LC016` is held because structured capacity is 451 while the official narrative states a 365-unit allocation and status is pending-decision.

## Product boundary

All official geometries are points and are not site boundaries or HMLR parcels. Canonical shard export, HMLR download, exact intersection, INSPIRE-ID matching, Future Growth scoring and business-row writes remain zero. `period=current` has not been obtained and the approved score-decision contract is absent.

`fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`, `final_ready=false`.
