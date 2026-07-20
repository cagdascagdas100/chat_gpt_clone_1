# Gas Emissions shard 3 — DESNZ cross-version candidate batch 2

- SLOT_ID: `gas_emissions_3`
- Parcel range: `61523-92283`
- Scope: source-revision candidates only; no parcel values
- Previous official series: DESNZ 2005–2023, updated 19 August 2025
- Current official series: DESNZ 2005–2024, published 25 June 2026 and updated 30 June 2026

## Method

Twenty Hartlepool rows were matched across the two official GOV.UK CSV previews using the exact composite key:

`local_authority_code + calendar_year + sector + sub-sector + greenhouse_gas`

Each old and new value was transcribed from the corresponding official preview line. Relative change is `(new-old)/old*100`. Candidates with an absolute change of at least 10% are marked `HIGH_IMPACT_REVISION_CANDIDATE`.

## Result

- New exact-key candidates: `20`
- Total site-visible candidates: `30`
- New high-impact candidates: `4`
- Total high-impact candidates: `8`
- Source authority score: `100/100`
- Exact row-key match score: `100/100`
- Candidate source confidence: `98%`
- Parcel binding confidence: `0%`
- Measured parcel values produced: `0`

Largest new changes:

1. Commercial 'Other' CO2: `2.30030235 -> 2.961661559` (`+28.750969%`)
2. Agriculture 'Other' N2O: `0.025949642 -> 0.0305` (`+17.535340%`)
3. Agriculture 'Other' CO2: `2.450639815 -> 2.876425879` (`+17.374486%`)
4. Agriculture 'Other' CH4: `0.0207 -> 0.0229` (`+10.628019%`)

## Evidence and site visibility

- Evidence: `docs/chatgpt_status/gas_emissions/shards/gas_emissions_3/evidence/003_gas_emissions_3_desnz_cross_version_batch2_20260720.json`
- Site JSON: `england_map_web/data/aays_18_slots/gas_emissions_3/progress_latest.json`
- Site table: `england_map_web/data/aays_18_slots/gas_emissions_3/progress_latest.html`

## Remaining blocker

The browser acceptance remains `66/100`. The existing canonical F shared runner and local port `8012` are required to produce a real 100-row DOM/browser proof. Until that proof is committed and remotely read back, `final_ready=false` and no 100% claim is permitted.

## Safety

- `final_ready=false`
- `fake_data=false`
- `db_write=false`
- `migration=false`
- `production_deploy=false`
