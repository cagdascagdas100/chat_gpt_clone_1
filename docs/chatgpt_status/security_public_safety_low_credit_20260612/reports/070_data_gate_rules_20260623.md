# Data Gate Rules

page_key: security_public_safety_low_credit_20260612
cycle: cycle050
status: QUEUED_POLICY_ADDENDUM
final_ready: false
progress_effect: no_percent_increase

## Required rules added for the runner task

1. Use only repo files, existing local disk files, or open free internet sources.
2. Do not use paid, login-only, contact-required, or invitation-only sources.
3. Do not use synthetic parcel geometry, synthetic parcel id, synthetic point, or synthetic polygon as final evidence.
4. If open data is not parcel-level, report one of these layer statuses:
   - POSTCODE_LEVEL_ONLY
   - POINT_LEVEL_ONLY
   - OPEN_DATA_PROXY_READY
   - DATA_GATE_BLOCKED
5. FINAL_READY or 100 percent is allowed only when all are proven together:
   - live map visibility
   - non-empty feature set
   - required popup or right-panel fields
   - geometry accuracy

## Current blocker

The task remains blocked until the existing shared runner writes real 050 runner reports under this page-key folder.
