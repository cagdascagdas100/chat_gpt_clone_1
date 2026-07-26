# future_growth_3 — Wave 55 official source report

- Date: 2026-07-23
- Continuation key: `61383520c6a16ecbb0bd2f3d65f26f06ed73185e4b2d7845f096dbcd3a985d91`
- Authorities: Plymouth City Council, Barnsley Metropolitan Borough Council, City of Doncaster Council
- Official platform: MHCLG Planning Data brownfield-land

## Results

- Researched: 30
- Eligible official source candidates: 15
- Excluded: 15
- High confidence: 6
- Average eligible confidence: 97.33/100
- Direct live readback: 18 PASS / 12 cache-miss FAIL
- Eligible exact POINT: 15/15
- Structured capacity: 14
- Explicit notes-only capacity: 1
- Visible candidate rows: 30
- Visible operation rows: 195

## Quality gates

Twelve failed direct live readbacks were excluded without promoting search-cache fields. BR0107a and BR0026a were excluded with zero residential capacity. H2841 was excluded because the official site-area field is zero hectares. Missing minimum capacities, structured/notes conflicts, old permissions and lapsed-permission notes remain explicit QA flags. No coordinates or capacities were inferred.

## Canonical blocker

Two new exact repository searches increased the canonical search total to 197 with zero indexed matches. The exact 30,761-row canonical export for rows 61,523–92,283, stable parcel identifier, row-count/range receipt and CRS declaration remain absent. No canonical parcel assignment, geometry intersection or future-growth scoring was performed.

## Product guardrails

- Canonical rows matched: 0
- Future-growth scores: 0
- Actual business data rows: 0
- `fake_data=false`
- `final_ready=false`
