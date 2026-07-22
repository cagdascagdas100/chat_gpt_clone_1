# future_growth_2 wave 31 — Barking and Dagenham structured-capacity review

Scope is limited to source-candidate preparation for `future_growth_2`, shard rows `30762-61522`. No parcel identity, Future Growth score, database write, migration or deployment is asserted.

## Results

- 10 official Planning Data brownfield entities reviewed.
- 9 eligible source-review candidates and 1 fail-closed hold.
- All 10 expose point coordinates, structured maximum dwelling capacity and 2024-12-31 register entry dates.
- Eight eligible records are explicitly `not-permissioned`.
- Town Quay Wharf is permissioned with a structured 2022-02-15 permission date and remains a stale-delivery review candidate.
- GSR and Gill Sites is held because the official entity says `permissioned` but exposes no structured planning-permission date.
- Exact entity/reference repository index searches returned no matches; this is duplicate-screening evidence only, not completeness proof.

## Eligible examples

- Gascoigne Business Area — 2,296 dwellings.
- Dagenham Heathway Mall — 500 minimum / 860 maximum dwellings.
- Ibscott Close Estate — 658 minimum / 831 maximum dwellings.
- Phoenix House — 188 dwellings.
- 90 Stour Road — 150 dwellings.
- Town Quay Wharf — 147 dwellings.
- IBIS Barking — 136 dwellings.
- Barking Foyer — 134 dwellings.
- Rainham Road South — 43 dwellings.

## Validation

- Structural registry checks: 46/46 PASS.
- Official-field readbacks: 40/40 PASS.
- Product fields remain null for all 10 records.
- Canonical parcel matches, HMLR intersections, verified product rows and business writes remain zero.

## Fail-closed limitations

Planning Data points are candidate locators, not site boundaries or parcel identifiers. Direct `period=current` API evidence, actual HMLR ZIP/GML acquisition, exact INSPIRE-ID intersection and an approved Future Growth scoring contract are still required before any product score can be produced.
