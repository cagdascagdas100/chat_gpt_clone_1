# Runner V4 result terrayield-078-safe-test-execution-5worker-direct  PROJECT=terrayield DISPLAY_PROJECT=TerraYield CHATGPT_PAGE_PROJECT=aays1 TASK=terrayield-078-safe-test-execution-5worker-direct EXIT_CODE=0 RUN_LOG=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\terrayield-078-direct-20260506_170003.log TIME=2026-05-06T17:00:16 
LATEST_RUN_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004

## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\terrayield__078_scorecard.csv
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
0
program_completion,
88
platform_readiness,86

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\terrayield__078_status.txt
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK=
terrayield-078-safe-test-execution-5worker
WORKERS=5
COMPLETED_SLOTS=
5
BLOCKED_SLOTS=
0
TIMEOUT_SLOTS=
0
PYTEST_FAILURE_MARKERS=
0
PROGRAM_COMPLETION=
88
/100
PLATFORM_READINESS=86/100
NEXT_ACTION=devam et

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\terrayield__078_summary.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-078-safe-test-execution-5worker
MODE=safe actual test execution with five workers
WORKER_STARTED=slot_1_compile
WORKER_STARTED=slot_2_core_tests
WORKER_STARTED=slot_3_listing_tests
WORKER_STARTED=slot_4_facility_tests
WORKER_STARTED=slot_5_source_tests
COMPLETED_SLOTS=5
BLOCKED_SLOTS=0
TIMEOUT_SLOTS=0
PYTEST_FAILURE_MARKERS=0
PROGRAM_COMPLETION=88/100

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\slots\terrayield__078__slot_1_compile.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-078-safe-test-execution-5worker
SLOT=
slot_1_compile
AREA=
compile
STARTED=
2026-05-06T17:00:05
CHECK=python_compile_app
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

RESULT=slot_completed
FINISHED=2026-05-06T17:00:05

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\slots\terrayield__078__slot_2_core_tests.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-078-safe-test-execution-5worker
SLOT=
slot_2_core_tests
AREA=
core_tests
STARTED=
2026-05-06T17:00:05
CHECK=pytest_actual tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_area.py tests/test_storage_selection.py tests/test_storage_resolution.py
IGNORED_PATH=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17
CMD=python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_area.py tests/test_storage_selection.py tests/test_storage_resolution.py -q --ignore "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17"
...............                                                          [100%]
15 passed in 3.37s

PYTEST_EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T17:00:10

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\slots\terrayield__078__slot_3_listing_tests.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-078-safe-test-execution-5worker
SLOT=
slot_3_listing_tests
AREA=
listing_tests
STARTED=
2026-05-06T17:00:05
CHECK=pytest_actual tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_sale_filters.py tests/test_parcel_portal_filter.py tests/test_sale_link_utils.py
IGNORED_PATH=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17
CMD=python -m pytest tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_sale_filters.py tests/test_parcel_portal_filter.py tests/test_sale_link_utils.py -q --ignore "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17"
...............                                                          [100%]
15 passed in 1.57s

PYTEST_EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T17:00:08

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\slots\terrayield__078__slot_4_facility_tests.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-078-safe-test-execution-5worker
SLOT=
slot_4_facility_tests
AREA=
facility_tests
STARTED=
2026-05-06T17:00:05
CHECK=pytest_actual tests/test_facility_adapters.py tests/test_facility_api.py tests/test_facility_etl_publish.py tests/test_facility_resolution.py tests/test_facility_scoring_engine.py
IGNORED_PATH=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17
CMD=python -m pytest tests/test_facility_adapters.py tests/test_facility_api.py tests/test_facility_etl_publish.py tests/test_facility_resolution.py tests/test_facility_scoring_engine.py -q --ignore "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17"
................                                                         [100%]
16 passed in 5.21s

PYTEST_EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T17:00:13

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__078_safe_test_execution_5worker__20260506_170004\slots\terrayield__078__slot_5_source_tests.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-078-safe-test-execution-5worker
SLOT=
slot_5_source_tests
AREA=
source_tests
STARTED=
2026-05-06T17:00:06
CHECK=pytest_actual tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_live_normalization.py tests/test_sample_adapters.py tests/test_manifests.py
IGNORED_PATH=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17
CMD=python -m pytest tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_live_normalization.py tests/test_sample_adapters.py tests/test_manifests.py -q --ignore "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\tests\facility-adapter-5qtl4e17"
...........................                                              [100%]
27 passed in 5.06s

PYTEST_EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T17:00:12

```
