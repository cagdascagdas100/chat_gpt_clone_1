# future_growth_3 — Parallel waves 80–87 — 2026-07-23

## Scope
Milton Keynes, Ipswich, Peterborough, Swindon, Cheltenham, Gloucester, Colchester and Derby were researched in parallel against the public MHCLG Planning Data service. Derby returned no reliable positive-capacity candidate in the bounded official search and is recorded as `NO_DATA_CONTINUE`; no row was invented.

## Verified result
- researched rows: 50
- eligible: 29
- excluded: 21
- confidence >=98: 28
- average eligible confidence: 98.59/100
- direct-live attempts: 39
- direct-live PASS: 33
- direct-live cache-miss FAIL: 6
- visible candidate rows: 50
- visible verification operation rows: 350
- eligible official POINT coverage: 29/29
- eligible positive residential capacity: 29/29
- structured min/max capacity rows: 18
- official-notes capacity rows: 11

## Quality gate
Six direct entity cache misses were not promoted from search-cache results. Eight historical end-date records were excluded. Seven records with no positive residential capacity exposed in the bounded readback were excluded. `BLR/IP059b` remains confidence 97 because the 103-dwelling figure is shared across IP059a/IP059b and is not treated as an exact parcel capacity.

## Examples
- Milton Keynes `BR109`: official POINT, permissioned, up to 288 residential units in official notes.
- Milton Keynes `BR104`: official POINT, 133 maximum net dwellings.
- Ipswich `BLR/IP041`: official POINT, 58/58 dwellings.
- Ipswich `BLR/IP066`: official POINT, 55/55 dwellings.
- Peterborough `PDL/0014/17`: official POINT, 100/100 dwellings.
- Gloucester `GLOSBR008`: official POINT, 30–40 dwellings.

## Guardrails
No Planning Data POINT is treated as a canonical parcel polygon. Canonical rows 61,523–92,283 are still unavailable, so canonical parcel matching, the 30,761-row evidence matrix and future-growth scoring remain unstarted. `final_ready=false`; no DB write, migration or deploy occurred.
