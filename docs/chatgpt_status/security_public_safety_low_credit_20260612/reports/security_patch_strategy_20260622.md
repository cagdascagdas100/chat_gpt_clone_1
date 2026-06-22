# Safety / Security Gap Completion - ChatGPT Patch Strategy - 2026-06-22

Final decision: `BLOCKED_MISSING_REAL_PARCEL_CARRIER_OR_CANONICAL_FIELDS`

Exact files:
- `england_map_web/app.js`
- `england_map_web/security_overlay.js`
- `england_map_web/security_overlay.css`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/automation/vrun.ps1`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/runner_tasks/current-task.json`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/status/latest.json`
- `docs/chatgpt_status/security_public_safety_low_credit_20260612/reports/*`

Carrier join: use `/map/parcels?bbox=<current map bounds>&limit=5000`; join only by real non-synthetic parcel keys. Reject `security_parcel_id` values matching `^parcel_\d+$` as canonical final IDs. Render only `Polygon` or `MultiPolygon` features.

Canonical fields required: `parcel_id`, `security_score`, `security_level`, `security_level_label`, `security_color_category`, `security_color_hex`, `source_name`, `source_url`, `source_date`, `evidence`, `matching_method`, `calculation_explanation`, `confidence_score`, `accuracy_rating`.

Acceptance: `FINAL_READY_PARCEL_ACCEPTANCE` only after polygon thematic render, full popup/right-panel canonical fields, and toggle regression smoke pass.
