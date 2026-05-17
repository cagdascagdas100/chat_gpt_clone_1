# AAYS 111 Fix Pytest INI BOM Result

Generated: 2026-05-17T18:39:56
STATUS=completed
BRANCH_READY=True
CONFIG_FIXED=True
BUILD_PASSED=True
TESTS_PASSED=True
INTEGRATION_READY=True

## Blockers
- none

## Steps
### checkout integration branch
exit_code=0 timed_out=False
```text
M	england_map_web/aays_contractor_integration_panel.js
M	england_map_web/app.js
M	terrayield_land_intelligence/.env.example
M	terrayield_land_intelligence/app/api/routes/contractor.py
M	terrayield_land_intelligence/app/etl/match/parcel_matcher.py
M	terrayield_land_intelligence/app/main.py
M	terrayield_land_intelligence/app/schemas/contractor.py
M	terrayield_land_intelligence/docs/chatgpt_handoff/db_readiness_probe_20260515/STEP10_CONTROLLED_GO_LIVE_GATE_REPORT.txt
M	terrayield_land_intelligence/tests/test_contractor_api.py
M	terrayield_land_intelligence/tests/test_parcel_matcher_source_confidence.py

Already on 'feature/terrayield-aays-integration'
```
### compile app only
exit_code=0 timed_out=False
```text

```
### targeted pytest contractor api
exit_code=0 timed_out=False
```text
......                                                                   [100%]
```
### git add report and pytest config
exit_code=0 timed_out=False
```text

```
### git commit bom fix
exit_code=0 timed_out=False
```text
[feature/terrayield-aays-integration 829595e7d] AAYS 111 fix pytest ini BOM and rerun smoke
 1 file changed, 1 insertion(+), 1 deletion(-)
```

PLAN_PROGRESS_PERCENT=100
TASK_COMPLETION=100/100
AAYS_111_PYTEST_INI_BOM_FIX_DONE=true
