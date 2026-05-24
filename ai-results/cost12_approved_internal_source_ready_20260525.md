# COST12 Approved Internal Source Ready — 2026-05-25

Decision: APPROVED_INTERNAL_SOURCE_WITH_LIMITATIONS_READY_FOR_READONLY_IMPORT

## User-provided approval metadata

- approved_by: Cagdas Cagdas / Project Owner
- approval_date: 2026-05-25
- reliability_score: 0.60
- approval_reason: No-contact source search, public proxy research and internal file search completed. No direct BCIS/RICS/QS/contractor source was found. Existing retail fit-out seed/catalog row is accepted as an internal benchmark with limitations for read-only candidate staging.
- scope_note: Retail fit-out / shopfront signage benchmark only; not full shell construction. Restaurant/supermarket scope may require adjustment.
- limitation_note: Seed/catalog row, not direct BCIS/RICS extract. No base month. Must remain flagged as approved internal source with limitations and should be replaced when verified external source is obtained.

## Candidate

- scenario_version: cost_uk_v1
- building_type: retail
- spec_grade: mid
- region: UK
- base_rate_gbp_per_gia_m2: 1200
- base_rate_range_gbp_per_gia_m2: 400-3500
- source_file: tools/cost_uk_real_engine/config/cost_item_catalog_12cost.csv
- source_type: approved_internal_source_with_limitations
- confidence_band: MEDIUM_WITH_LIMITATIONS

## Local files created

- docs/chatgpt_handoff/cost12_internal_approval_source_path/cost12_internal_approval_template.csv
- docs/chatgpt_handoff/cost12_internal_approval_source_path/cost12_approved_internal_source_with_limitations_candidate.csv
- docs/chatgpt_handoff/cost12_internal_approval_source_path/COST12_INTERNAL_APPROVAL_SOURCE_PATH_STATUS.json
- docs/chatgpt_handoff/cost12_internal_approval_source_path/COST12_INTERNAL_APPROVAL_READY_FOR_IMPORT_TR.md

## Safety flags

- production_ready_candidate: true
- final_ready_confirmed: false
- review_mode: false
- db_write=false
- production_deploy=false
- fake_data=false

## Next step

Codex should stage/import this candidate in read-only mode and run POST /cost/estimate/preview validation.
Do not mark FINAL_READY_CONFIRMED unless final policy explicitly allows approved_internal_source_with_limitations.
