# 016 Clean Full Pytest Trigger - 2026-05-19

This file intentionally triggers the `016 clean full pytest` GitHub Actions workflow on branch `security-accuracy-expansion-20260508`.

## Scope

- Run clean full pytest after `pytest.ini` limited collection to `tests/`.
- Do not repeat 012A, 012B, 014, or 015.
- Do not perform DB writes, DDL, migration apply, production deploy, or secret printing.

## Latest retrigger reason

Import compatibility fixes have been added for:

- `app.main` optional router loading
- `app.services.sale_land_verification`
- `app.services.admin_service`
- `app.services.source_manifest_status`
- `app.etl.validate_live_listing_manifests`
- `app.db.models`
- `app.core.config`
- `app.services.source_catalog`

## Expected report

`docs/chatgpt_handoff/cloud_ready_20260517/016_CLEAN_FULL_PYTEST_REPORT.txt`

## Classification rule

Keep `CLOUD_READY_PENDING_PROVIDER` after this task. Public runtime blockers remain provider-dependent.

## Retrigger

run_id_hint=20260519_016_import_fixes_rerun_001
