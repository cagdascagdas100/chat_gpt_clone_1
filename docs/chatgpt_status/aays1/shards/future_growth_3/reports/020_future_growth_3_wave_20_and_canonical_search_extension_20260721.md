# future_growth_3 — Wave 20 + canonical acquisition extension

- Slot: `future_growth_3`
- Partition: rows `61,523–92,283` (`30,761`)
- Checkpoint sequence: `21`
- Operational progress: `7/12` (`58.33%`)
- Wave 20: `24 researched`, `22 eligible`, `2 excluded`
- Total: `321 researched`, `293 eligible`, `28 excluded`, `309 high source confidence`
- Source families: Reading, Cambridge, Norwich, Milton Keynes; total `62`
- Browser evidence: `24 candidate rows`, `54 operation rows`
- Official source-location coverage: `293/293`
- Canonical search: `52 indexed queries`, `0 matches`, `0 known workflow runs`
- Canonical rows matched: `0/30,761`
- Scores produced: `0`
- `final_ready=false`

## Fail-closed controls

1. Reading `BL3022` excluded because the authoritative notes explicitly state expiry.
2. Cambridge `06/0552/FUL | 20/03429/FUL` excluded because the later scheme description no longer carries the older structured residential component.
3. Four Milton Keynes `reported_hectares_raw` values were retained but not interpreted or converted.
4. Notes-derived dwelling counts never overwrite structured dwelling fields.
5. Official points/GeoJSON are not canonical parcel polygons.

## Blockers

- `CANONICAL_SHARD_61523_92283_EXPORT_NOT_FOUND_IN_REMOTE_REPOSITORY`
- `CANDIDATE_TO_CANONICAL_PARCEL_GEOMETRY_CROSSWALK_NOT_STARTED`
- `VERIFIED_30761_ROW_FUTURE_GROWTH_EVIDENCE_MATRIX_NOT_BUILT`
