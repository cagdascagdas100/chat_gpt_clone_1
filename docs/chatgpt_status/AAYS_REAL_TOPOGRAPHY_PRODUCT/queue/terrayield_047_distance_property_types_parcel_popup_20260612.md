# Runner task 047: Distance Property Types parcel popup

Date: 2026-06-12
Priority: high
Mode: read-only audit first, then narrow patch only if evidence supports it.

## Handoff

Use the local handoff package named `distance_property_types_parcel_popup_low_credit_20260612` under the AAYS repo handoff folder. The package hash supplied by the user is:

`6647321CD9A0F5E9C66BEA93B162DCC8E2EEDBA5ED3162B6ED6501A890614761`

## Goal

Complete and audit the parcel-based layer named Distance to Nearby Property Types. Completion requires all of the following:

1. The UI action opens the layer.
2. The map shows matched parcel polygons with the six-category color dictionary.
3. A clicked parcel shows the required layer outputs in popup or right panel.
4. The Excel output includes every parcel as one row with these four columns: parcel_id, yapi_turu_ve_6_renk, kaynak_ve_belirleme_yontemi, dogruluk_skalasi.

## Required endpoint contract

Preferred endpoint: `/map/distance-property-types?bbox=west,south,east,north&limit=n`

Geometry must be parcel polygon or multipolygon. Do not return only point assets for this parcel-based layer.

Required fields include parcel_id, parcel_ref or inspire_id, layer_name, use6_code, building_type_label, color_hex, six nearest-distance metrics, score percent fields, class_level, source_name, source_url, source_date, evidence_ref, evidence_summary, confidence_level_4, accuracy_scale, matching_method, calculation_explanation, last_verified_at, calculation_version.

## Safety and completion rules

Do not mark the layer complete only because an icon, toggle, frontend binding or asset file exists.

Do not perform DB writes, migrations, imports, backfills or index creation without explicit user approval.

Use bbox, limit, spatial index and lazy loading. Do not request the entire country parcel set in one request.

If source tables or parcel matching data are missing, produce a diagnostic report and import-ready fixture schema. In that case, do not claim feature complete.

## Expected runner outputs

Write results under `docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports/`:

- readonly audit output summary
- endpoint evidence for the smoke tests
- patch summary or diagnostic blocker report
- acceptance test result for Distance to Nearby Property Types and the other parcel-based layers listed in the handoff matrix
