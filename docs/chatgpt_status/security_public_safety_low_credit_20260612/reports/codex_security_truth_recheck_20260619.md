status: PARTIAL_IMPLEMENTATION_RUNTIME_OPEN_BUT_NOT_FULL_PARCEL_ACCEPTANCE
layer_name: Safety / Security
page_key: security_public_safety_low_credit_20260612
audit_date: 2026-06-19

what_is_true_now:
- application opens on `http://127.0.0.1:8010/england_map_web/`
- `security_overlay.js` now serves from root and loads
- `security_overlay.css` now serves from root and loads
- security summary JSON serves from `dist_worker/data`
- security GeoJSON serves from `dist_worker/data`

what_was_fixed_by_codex:
- missing root runtime assets were restored:
  - `england_map_web/security_overlay.js`
  - `england_map_web/security_overlay.css`
- root security overlay now points to:
  - `./dist_worker/data/parcel_security_match_summary.json`
  - `./dist_worker/data/parcel_security_scores_rechecked_0_120m_spatial.geojson`

what_is_still_not_complete:
- live security data is still `Point` geometry
- live data is not a real parcel polygon thematic layer
- popup currently shows only legacy fields:
  - `safety_level`
  - `safety_score`
  - `confidence_label`
  - `confidence_score`
  - `security_lsoa_code`
  - `security_borough`
  - `confidence_flags`
- required product fields are still missing or not surfaced as required:
  - `parcel_id`
  - `security_score` as canonical field
  - `security_level`
  - `security_level_label`
  - `security_color_category`
  - `security_color_hex`
  - `source_name`
  - `source_url`
  - `source_date`
  - `evidence`
  - `matching_method` as canonical field
  - `calculation_explanation`
  - `accuracy_rating`
- right-side parcel detail contract is not proven

critical_data_evidence:
- `england_map_web/dist_worker/data/parcel_security_scores_rechecked_0_120m_spatial.geojson` starts with `geometry.type = Point`
- the same file contains `security_parcel_id`, not a proven canonical frontend `parcel_id`
- summary file states parcel source came from:
  - `england_map_web/london_6color_active_final_preview_points.js`

acceptance_conclusion:
- runtime open: PASS
- icon/toggle load: PASS
- parcel polygon acceptance: FAIL
- required popup/right panel contract completeness: FAIL
- overall final product acceptance against original user prompt: FAIL

next_required_fix:
- replace point-only security overlay with a stable parcel polygon carrier join
- then surface the full contract fields in popup and/or right panel
