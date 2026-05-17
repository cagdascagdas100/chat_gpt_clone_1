# Static Cloud Readiness Validation - 2026-05-17

## Purpose

This report records the static cloud-readiness validation when GitHub Actions workflow runs are not visible from the connector.

## Files expected and present by repository history

Cloud scaffold:

- `terrayield_land_intelligence/Dockerfile.cloud`
- `terrayield_land_intelligence/render.example.yaml`
- `terrayield_land_intelligence/.env.cloud.example`
- `terrayield_land_intelligence/scripts/cloud_smoke_check.py`
- `terrayield_land_intelligence/docs/cloud_ready/STATUS.md`
- `terrayield_land_intelligence/docs/cloud_ready/PROVIDER_CHECKLIST_TR.md`
- `terrayield_land_intelligence/docs/cloud_ready/HOSTED_SMOKE_USAGE_TR.md`
- `terrayield_land_intelligence/docs/cloud_ready/FINAL_CLOUD_READY_CLOSURE_TR.md`

Handoff controls:

- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt`
- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/BLOCKERS.md`
- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/LOCATION_EVIDENCE_SAMPLE.jsonl`
- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/PERF_SUMMARY.txt`
- `terrayield_land_intelligence/docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt`

## Verified classification

`CLOUD_READY_PENDING_PROVIDER`

## Why not CLOUD_RUNTIME_READY

- Public hosted HTTPS API URL is not verified.
- Cloud database provider configuration is not verified.
- The latest successful runtime smoke is local and uses `http://127.0.0.1:8010`.

## Next single action

`ADD_PROVIDER_PUBLIC_URL_AND_CLOUD_DB_SETTINGS_OUTSIDE_REPO`

## Safety

- `db_write=none`
- `ddl=none`
- `migration_apply=none`
- `prod_deploy=none`
- `secret_values_printed=false`

## Notes

GitHub Actions workflow file exists at `.github/workflows/terrayield-cloud-readiness.yml`, but workflow runs were not visible through the connector after the trigger commit. This report therefore provides a repository-level static validation record.
