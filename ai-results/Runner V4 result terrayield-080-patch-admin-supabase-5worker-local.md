# Runner V4 result terrayield-080-patch-admin-supabase-5worker-local  PROJECT=terrayield DISPLAY_PROJECT=TerraYield CHATGPT_PAGE_PROJECT=aays1 TASK=terrayield-080-patch-admin-supabase-5worker-local TIME=2026-05-06T18:37:46 RUN_LOG=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\terrayield-080-collect-20260506_183746.log 
LATEST_RUN_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918

## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\terrayield__080_scorecard.csv
```text
metric,score
workers,5
completed_slots,
5
blocked_slots,
0
timeout_slots,
0
pytest_failure_markers,
16
passed_markers,
1
program_completion,
91
platform_readiness,92

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\terrayield__080_status.txt
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK=
terrayield-080-patch-admin-supabase-5worker
PATCH_ADMIN_PUBLISH=
patched
PATCH_SUPABASE_ADMIN=
patched
WORKERS=5
COMPLETED_SLOTS=
5
BLOCKED_SLOTS=
0
TIMEOUT_SLOTS=
0
PYTEST_FAILURE_MARKERS=
16
PASSED_MARKERS=
1
PROGRAM_COMPLETION=
91
/100
PLATFORM_READINESS=92/100
NEXT_ACTION=devam et

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\terrayield__080_summary.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-080-patch-admin-supabase-5worker
MODE=patch admin publish and supabase admin service then run five workers
PATCH_ADMIN_PUBLISH=patched
PATCH_SUPABASE_ADMIN=patched
WORKER_STARTED=slot_1_patch_diff
WORKER_STARTED=slot_2_compile
WORKER_STARTED=slot_3_admin_publish
WORKER_STARTED=slot_4_supabase_admin
WORKER_STARTED=slot_5_admin_supabase_bundle
COMPLETED_SLOTS=5
BLOCKED_SLOTS=0
TIMEOUT_SLOTS=0
PYTEST_FAILURE_MARKERS=16
PASSED_MARKERS=1
PROGRAM_COMPLETION=91/100

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\slots\terrayield__080__slot_1_patch_diff.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-080-patch-admin-supabase-5worker
SLOT=
slot_1_patch_diff
AREA=
patch_diff
STARTED=
2026-05-06T18:29:19
CMD=git diff -- app/services/admin_publish_service.py app/services/supabase_admin_service.py

EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T18:29:20

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\slots\terrayield__080__slot_2_compile.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-080-patch-admin-supabase-5worker
SLOT=
slot_2_compile
AREA=
compile
STARTED=
2026-05-06T18:29:20
CMD=python -m compileall app
Listing 'app'...
Listing 'app\\api'...
Listing 'app\\api\\routes'...
Listing 'app\\cli'...
Listing 'app\\clients'...
Listing 'app\\core'...
Listing 'app\\db'...
Listing 'app\\etl'...
Listing 'app\\etl\\match'...
Listing 'app\\etl\\normalize'...
Listing 'app\\etl\\publish'...
Listing 'app\\etl\\score'...
Listing 'app\\etl\\sources'...
Listing 'app\\etl\\sources\\facilities'...
Listing 'app\\etl\\sources\\market'...
Listing 'app\\middleware'...
Listing 'app\\schemas'...
Listing 'app\\services'...
Compiling 'app\\services\\admin_publish_service.py'...
Compiling 'app\\services\\supabase_admin_service.py'...
***   File "app\services\supabase_admin_service.py", line 2
    from __future__ import annotations
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: from __future__ imports must occur at the beginning of the file


EXIT=1
RESULT=slot_completed
FINISHED=2026-05-06T18:29:21

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\slots\terrayield__080__slot_3_admin_publish.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-080-patch-admin-supabase-5worker
SLOT=
slot_3_admin_publish
AREA=
admin_publish
STARTED=
2026-05-06T18:29:20
CMD=python -m pytest tests/test_admin_publish_service.py -q
..                                                                       [100%]
2 passed in 7.28s

EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T18:29:29

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\slots\terrayield__080__slot_4_supabase_admin.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-080-patch-admin-supabase-5worker
SLOT=
slot_4_supabase_admin
AREA=
supabase_admin
STARTED=
2026-05-06T18:29:20
CMD=python -m pytest tests/test_supabase_admin_service.py -q

=================================== ERRORS ====================================
____________ ERROR collecting tests/test_supabase_admin_service.py ____________
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\python.py:507: in importtestmodule
    mod = import_path(
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\pathlib.py:587: in import_path
    importlib.import_module(module_name)
C:\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\assertion\rewrite.py:197: in exec_module
    exec(co, module.__dict__)
tests\test_supabase_admin_service.py:8: in <module>
    from app.services import supabase_admin_service
E     File "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py", line 2
E       from __future__ import annotations
E       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   SyntaxError: from __future__ imports must occur at the beginning of the file
=========================== short test summary info ===========================
ERROR tests/test_supabase_admin_service.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.51s

EXIT=2
RESULT=slot_completed
FINISHED=2026-05-06T18:29:23

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__20260506_182918\slots\terrayield__080__slot_5_admin_supabase_bundle.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-080-patch-admin-supabase-5worker
SLOT=
slot_5_admin_supabase_bundle
AREA=
admin_supabase_bundle
STARTED=
2026-05-06T18:29:20
CMD=python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q

=================================== ERRORS ====================================
____________ ERROR collecting tests/test_supabase_admin_service.py ____________
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\python.py:507: in importtestmodule
    mod = import_path(
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\pathlib.py:587: in import_path
    importlib.import_module(module_name)
C:\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\..\AppData\Roaming\Python\Python312\site-packages\_pytest\assertion\rewrite.py:197: in exec_module
    exec(co, module.__dict__)
tests\test_supabase_admin_service.py:8: in <module>
    from app.services import supabase_admin_service
E     File "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app\services\supabase_admin_service.py", line 2
E       from __future__ import annotations
E       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   SyntaxError: from __future__ imports must occur at the beginning of the file
=========================== short test summary info ===========================
ERROR tests/test_supabase_admin_service.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 7.76s

EXIT=2
RESULT=slot_completed
FINISHED=2026-05-06T18:29:30

```
