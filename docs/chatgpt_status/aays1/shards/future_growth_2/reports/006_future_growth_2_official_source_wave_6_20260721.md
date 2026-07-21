# future_growth_2 — official source wave 6

## Scope
Only `future_growth_2`, canonical rows `30,762–61,522`.

## Official candidates
Six Camden records were read from official Planning Data entity pages:

- `LBCBLR002` — Euston Station — 10.6 ha — 250–900 dwellings — not permissioned.
- `LBCBLR068` — Former Liddell Industrial Estate — 0.57 ha — 106 dwellings — permissioned.
- `LBCBLR097` — Camden Goods Yard — 3.26 ha — 644 dwellings — permissioned.
- `LBCBLR007` — 156 West End Lane — 0.60 ha — 180 dwellings — permissioned.
- `LBCBLR003` — Mount Pleasant West — 1.12 ha — 345 dwellings — permissioned.
- `LBCBLR010` — Middlesex Hospital Annex — 0.29 ha — 57 dwellings — permissioned.

All six records show authoritative quality, an empty end date, a `2025-12-07` entry date and explicit point coordinates. They do not overlap the preceding 35 researched entity IDs.

## Provider quality caveat
Planning Data identifies the London Borough of Camden as the authoritative provider. Its provider page reports `6/18` authoritative datasets supplied, `0` URL-access errors and `5` issues for the brownfield dataset. The provider source is therefore promoted for provenance with a quality caveat; it does not raise parcel-match or product-score confidence.

## Executed validation
`008_validate_candidate_registry_bundle.py` was executed against the actual wave-6 file and the preceding entity registry. Result: `12/12 PASS`.

A separate official remote evidence audit records `10/10 PASS`.

## Product safety
No current HMLR polygon download, exact polygon intersection, explicit INSPIRE-ID shard match, verified evidence-matrix row or approved Future Growth score was produced.

`final_ready=false`, `fake_data=false`, `db_write=false`, `migration=false`, `production_deploy=false`.
