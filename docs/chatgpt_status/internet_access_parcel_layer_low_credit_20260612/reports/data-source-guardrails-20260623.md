# Internet Access Data Source Guardrails

Status: ACTIVE
Page key: internet_access_parcel_layer_low_credit_20260612

Allowed inputs:
- Existing repository files
- Existing local C, D, or F disk files
- Open and free public internet sources

Not allowed:
- Paid data sources
- Contact-required data sources
- Invitation-only data sources
- Login-required data sources

Geometry rule:
- Do not create synthetic parcel geometry, parcel ids, points, or polygons.
- If available data is not parcel-level, report the actual level clearly.

Allowed data-level labels:
- POSTCODE_LEVEL_ONLY
- POINT_LEVEL_ONLY
- OPEN_DATA_PROXY_READY
- DATA_GATE_BLOCKED
- PARCEL_LEVEL_READY

Final-ready rule:
FINAL_READY and 100 percent are allowed only when all of these are proven in GitHub-visible reports:
- live map visibility
- non-empty feature set
- popup or right panel required fields
- geometry accuracy

PowerShell from user: not required for this rule update.
