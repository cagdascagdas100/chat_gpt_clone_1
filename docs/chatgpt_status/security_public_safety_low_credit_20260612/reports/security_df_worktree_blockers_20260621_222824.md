# Security/Public Safety Blockers

status=BLOCKED_MISSING_POLYGON_CARRIER_OR_CONTRACT_FIELDS
completion_percent=50
blocker_count=6
warning_count=4

## Blockers
- clean_worktree_missing:F:\chatgpt\AAYS_WORK\security_public_safety_20260619_clean|D:\chatgpt\AAYS_WORK\security_public_safety_20260619_clean
- app_js_missing
- live_security_geometry_still_point
- missing_canonical_fields:parcel_id,security_score,security_level,security_level_label,security_color_category,security_color_hex,source_name,source_url,source_date,evidence,matching_method,calculation_explanation,accuracy_rating
- index_html_missing
- security_overlay_js_missing

## Warnings
- local_user_must_create_df_clean_worktree
- using_runner_repo_product_root_not_df_worktree
- web_runtime_not_reachable
- map_parcels_probe_failed

next_action=fix listed blockers in D/F worktree and rerun this same single shared runner task
