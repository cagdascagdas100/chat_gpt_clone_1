# AAYS 109B Timeout Safe Integration Build/Test Result

Generated: 2026-05-15T22:24:53
STATUS=completed_with_blockers
BRANCH_READY=True
BUILD_ATTEMPTED=True
BUILD_PASSED=False
TESTS_ATTEMPTED=True
TESTS_PASSED=False
INTEGRATION_READY=False

## Blockers
- python compileall failed or timed out
- pytest failed or timed out

## Steps
### git status
exit_code=124 timed_out=True
```text
TIMEOUT after 30 seconds
```
### stash dirty worktree
exit_code=124 timed_out=True
```text
TIMEOUT after 60 seconds
```
### git fetch origin
exit_code=0 timed_out=False
```text
Nothing new to pack.

From https://github.com/cagdascagdas100/chat_gpt_clone_1
   3d8cb790..ceab9792  main       -> origin/main
Auto packing the repository for optimum performance.
See "git help gc" for manual housekeeping.
warning: There are too many unreachable loose objects; run 'git prune' to remove them.
```
### checkout branch
exit_code=0 timed_out=False
```text
M	england_map_web/aays_contractor_integration_panel.js
M	england_map_web/app.js
M	terrayield_land_intelligence/.env.example
M	terrayield_land_intelligence/app/api/routes/contractor.py
M	terrayield_land_intelligence/app/schemas/contractor.py
M	terrayield_land_intelligence/docs/chatgpt_handoff/db_readiness_probe_20260515/STEP10_CONTROLLED_GO_LIVE_GATE_REPORT.txt
M	terrayield_land_intelligence/tests/test_contractor_api.py

Switched to a new branch 'feature/terrayield-aays-integration'
```
### TerraYield python compileall
exit_code=124 timed_out=True
```text
TIMEOUT after 240 seconds
```
### TerraYield pytest
exit_code=2 timed_out=False
```text
=================================== ERRORS ====================================
______________ ERROR collecting tests/facility-adapter-5qtl4e17 _______________
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\runner.py:353: in from_call
    result: TResult | None = func()
                             ^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\runner.py:398: in collect
    return list(collector.collect())
           ^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\main.py:557: in collect
    for direntry in scandir(self.path):
                    ^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\pathlib.py:963: in scandir
    scandir_iter = os.scandir(path)
                   ^^^^^^^^^^^^^^^^
E   PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\tests\\facility-adapter-5qtl4e17'
=========================== short test summary info ===========================
ERROR tests/facility-adapter-5qtl4e17 - PermissionError: [WinError 5] Eri■im ...
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 12.54s
```
### git add integration report
exit_code=0 timed_out=False
```text

```
### git commit integration report
exit_code=0 timed_out=False
```text
[feature/terrayield-aays-integration b6b9029f] AAYS 109B timeout safe integration build test report
 1 file changed, 8 insertions(+)
 create mode 100644 integration-reports/aays-109b-branch-integration-build-test-timeout-20260515-2215.md

Auto packing the repository for optimum performance.
See "git help gc" for manual housekeeping.
warning: There are too many unreachable loose objects; run 'git prune' to remove them.
```

PLAN_PROGRESS_PERCENT=100
TASK_COMPLETION=100/100
AAYS_BRANCH_INTEGRATION_BUILD_TEST_DONE=true
