# AAYS ChatGPT Runner V4 Result

## Task
TerraYield supabase failure stdout 5worker safe

## Task ID
terrayield-100-supabase-failure-stdout-5worker-safe

## Progress
99%

## Action


## Time
05/07/2026 01:36:38

## Working Directory
C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence

## Timeout Seconds
3000

## Exit Code
0

## Output
``text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-100-supabase-failure-stdout-5worker-safe
MODE=print final Supabase admin failure details to runner stdout with five workers
WORKER_STARTED=slot_1_firstfail_long
WORKER_STARTED=slot_2_admin_short
WORKER_STARTED=slot_3_combo_short
WORKER_STARTED=slot_4_controls
WORKER_STARTED=slot_5_compile_collect
PASS_SLOTS=2
FAIL_SLOTS=3
ASSERTION_MARKERS=15
PROGRAM_COMPLETION=99/100
--- FAILED SLOT EXCERPTS BEGIN ---
--- FAILED_FILE=terrayield__100__slot_1_firstfail_long.md ---

  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:31:            search="alpha site",
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:32:            limit=25,
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:33:        )
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:34:    
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:35:        assert len(rows) == 1
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:36:>       assert rows[0].listing_title == "Managed Parcel Listing"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:37:               ^^^^^^^^^^^^^^^^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:38:E       AttributeError: 'dict' object has no attribute 'listing_title'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:39:
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:40:tests\test_supabase_admin_service.py:45: AttributeError
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:41:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:42:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filter
s - AttributeError: 'dict' object has no attribute 'listing_title'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:43:!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:44:============================== 1 failed in 2.49s ==============================
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:45:
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:46:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:47:OWN_RESULT=fail
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_1_f
irstfail_long.md:48:FINISHED=2026-05-07T01:36:31



--- FAILED_FILE=terrayield__100__slot_2_admin_short.md ---

  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:2:FFF.                                                                     [100%]
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:3:================================== FAILURES ===================================
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:4:___________ test_list_supabase_admin_records_builds_backend_filters ___________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:5:tests\test_supabase_admin_service.py:45: in test_list_supabase_admin_records_builds_backend_filters
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:6:    assert rows[0].listing_title == "Managed Parcel Listing"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:7:           ^^^^^^^^^^^^^^^^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:8:E   AttributeError: 'dict' object has no attribute 'listing_title'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:9:_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:10:tests\test_supabase_admin_service.py:65: in test_list_supabase_parcel_records_uses_parcel_ref_or_filte
r
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:11:    assert rows[0].parcel_ref == "P-1"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:12:           ^^^^^^^^^^^^^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:13:E   AttributeError: 'dict' object has no attribute 'parcel_ref'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:14:_____________ test_upsert_supabase_admin_record_returns_saved_row _____________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:15:tests\test_supabase_admin_service.py:90: in test_upsert_supabase_admin_record_returns_saved_row
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:16:    assert row.id == "22222222-2222-2222-2222-222222222222"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:17:           ^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:18:E   AttributeError: 'dict' object has no attribute 'id'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:19:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:20:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filters
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:21:FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_or_filt
er
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:22:FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_returns_saved_row
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:23:3 failed, 1 passed in 2.51s
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:24:
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:25:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:26:OWN_RESULT=fail
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_2_a
dmin_short.md:27:FINISHED=2026-05-07T01:36:31



--- FAILED_FILE=terrayield__100__slot_3_combo_short.md ---

  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:2:..FFF....                                                                [100%]
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:3:================================== FAILURES ===================================
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:4:___________ test_list_supabase_admin_records_builds_backend_filters ___________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:5:tests\test_supabase_admin_service.py:45: in test_list_supabase_admin_records_builds_backend_filters
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:6:    assert rows[0].listing_title == "Managed Parcel Listing"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:7:           ^^^^^^^^^^^^^^^^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:8:E   AttributeError: 'dict' object has no attribute 'listing_title'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:9:_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:10:tests\test_supabase_admin_service.py:65: in test_list_supabase_parcel_records_uses_parcel_ref_or_filte
r
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:11:    assert rows[0].parcel_ref == "P-1"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:12:           ^^^^^^^^^^^^^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:13:E   AttributeError: 'dict' object has no attribute 'parcel_ref'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:14:_____________ test_upsert_supabase_admin_record_returns_saved_row _____________
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:15:tests\test_supabase_admin_service.py:90: in test_upsert_supabase_admin_record_returns_saved_row
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:16:    assert row.id == "22222222-2222-2222-2222-222222222222"
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:17:           ^^^^^^
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:18:E   AttributeError: 'dict' object has no attribute 'id'
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:19:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:20:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filters
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:21:FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_or_filt
er
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:22:FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_returns_saved_row
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:23:3 failed, 6 passed in 4.88s
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:24:
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:25:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:26:OWN_RESULT=fail
  .aays_real_runs\terrayield__100_supabase_failure_stdout_5worker_safe__20260507_013625\slots\terrayield__100__slot_3_c
ombo_short.md:27:FINISHED=2026-05-07T01:36:33



--- FAILED SLOT EXCERPTS END ---
TERRAYIELD_100_SUPABASE_FAILURE_STDOUT_5WORKER_SAFE_DONE

``

## Error
``text

``
