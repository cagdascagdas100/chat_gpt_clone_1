# AAYS Secret-Safe HF PMTiles Proxy Plan

## Objective
Provide server-side, secret-safe access/probing for Hugging Face PMTiles sources without exposing tokens in browser logs, output files, or Git history.

## Token policy
Use the first available environment variable in this order: AAYS_HF_TOKEN, HF_TOKEN, HUGGINGFACE_TOKEN.
Only report 	oken_present and 	oken_source; never print token values or Authorization headers.

## Required proxy behavior
- Accept a known region key, not arbitrary untrusted URL by default.
- Resolve the region key to a manifest URL server-side.
- Attach Authorization: Bearer <token> only server-side when token is present.
- Preserve client Range requests for PMTiles.
- Return 206 for valid range responses.
- Classify 401/403 as uth_required.
- Never mark remote source verified unless Range probe returns 206 with bytes.

## Current probe summary
- token_present: False
- token_source: NONE
- remote_hf_configured_count: 6
- remote_hf_auth_required_count: 0
- remote_hf_verified_count: 0
- wales_remote_config_missing: True
- scotland_remote_config_missing: True
- full_coverage_verified: False

## Current decision
Keep overall_progress=99 and status=REGION_GATE_MAPPING_MISMATCH_COVERAGE_PENDING until all required remote/local sources are runtime verified and Wales/Scotland are explicitly configured or otherwise covered by real verified sources.

## Safety
- db_write=false
- deploy=false
- migration=false
- fake_data=false
- secret_values_printed=false
