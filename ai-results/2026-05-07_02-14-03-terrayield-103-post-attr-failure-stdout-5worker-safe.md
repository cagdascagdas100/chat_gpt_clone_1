# AAYS ChatGPT Runner V4 Result

## Task
TerraYield post attr failure stdout 5worker safe

## Task ID
terrayield-103-post-attr-failure-stdout-5worker-safe

## Progress
99%

## Action


## Time
05/07/2026 02:14:21

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
TASK=terrayield-103-post-attr-failure-stdout-5worker-safe
MODE=print post-attr Supabase failures to runner stdout with five workers
WORKER_STARTED=slot_1_admin_service_firstfail
WORKER_STARTED=slot_2_admin_service_all_short
WORKER_STARTED=slot_3_admin_combo_short
WORKER_STARTED=slot_4_control_compile
WORKER_STARTED=slot_5_service_tail
PASS_SLOTS=2
FAIL_SLOTS=3
ASSERTION_MARKERS=9
PROGRAM_COMPLETION=99/100
--- POST ATTR FAILED SLOT EXCERPTS BEGIN ---
--- FAILED_FILE=terrayield__103__slot_1_admin_service_firstfail.md ---

  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:31:            search="alpha site",
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:32:            limit=25,
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:33:        )
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:34:    
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:35:        assert len(rows) == 1
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:36:        assert rows[0].listing_title == "Managed Parcel Listing"
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:37:>       assert fake_client.calls[0]["filters"]["region_slug"] == "eq.london"
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:38:E       AssertionError: assert 'london' == 'eq.london'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:39:E         
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:40:E         - eq.london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:41:E         ? ---
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:42:E         + london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:43:
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:44:tests\test_supabase_admin_service.py:46: AssertionError
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:45:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:46:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_back
end_filters - AssertionError: assert 'london' == 'eq.london'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:47:  
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:48:  - eq.london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:49:  ? ---
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:50:  + london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:51:!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:52:============================== 1 failed in 2.51s ==============================
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:53:
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:54:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:55:OWN_RESULT=fail
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_1_
admin_service_firstfail.md:56:FINISHED=2026-05-07T02:14:11



--- FAILED_FILE=terrayield__103__slot_2_admin_service_all_short.md ---

  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:2:FF..                                                                     [100%]
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:3:================================== FAILURES ===================================
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:4:___________ test_list_supabase_admin_records_builds_backend_filters ___________
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:5:tests\test_supabase_admin_service.py:46: in test_list_supabase_admin_records_builds_backen
d_filters
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:6:    assert fake_client.calls[0]["filters"]["region_slug"] == "eq.london"
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:7:E   AssertionError: assert 'london' == 'eq.london'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:8:E     
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:9:E     - eq.london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:10:E     ? ---
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:11:E     + london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:12:_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:13:tests\test_supabase_admin_service.py:66: in test_list_supabase_parcel_records_uses_parcel
_ref_or_filter
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:14:    assert fake_client.calls[0]["filters"]["or"] == "(parcel_ref.eq.P-1,inspire_id.eq.P-1
)"
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:15:           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:16:E   KeyError: 'or'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:17:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:18:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_back
end_filters
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:19:FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parce
l_ref_or_filter
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:20:2 failed, 2 passed in 2.53s
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:21:
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:22:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:23:OWN_RESULT=fail
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_2_
admin_service_all_short.md:24:FINISHED=2026-05-07T02:14:11



--- FAILED_FILE=terrayield__103__slot_3_admin_combo_short.md ---

  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:2:..FF.....                                                                [100%]
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:3:================================== FAILURES ===================================
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:4:___________ test_list_supabase_admin_records_builds_backend_filters ___________
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:5:tests\test_supabase_admin_service.py:46: in test_list_supabase_admin_records_builds_backend_filt
ers
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:6:    assert fake_client.calls[0]["filters"]["region_slug"] == "eq.london"
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:7:E   AssertionError: assert 'london' == 'eq.london'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:8:E     
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:9:E     - eq.london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:10:E     ? ---
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:11:E     + london
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:12:_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:13:tests\test_supabase_admin_service.py:66: in test_list_supabase_parcel_records_uses_parcel_ref_o
r_filter
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:14:    assert fake_client.calls[0]["filters"]["or"] == "(parcel_ref.eq.P-1,inspire_id.eq.P-1)"
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:15:           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:16:E   KeyError: 'or'
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:17:=========================== short test summary info ===========================
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:18:FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_fi
lters
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:19:FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_
or_filter
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:20:2 failed, 7 passed in 11.50s
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:21:
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:22:OWN_EXIT_CODE=1
> .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:23:OWN_RESULT=fail
  .aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__20260507_021404\slots\terrayield__103__slot_3_
admin_combo_short.md:24:FINISHED=2026-05-07T02:14:20



--- POST ATTR FAILED SLOT EXCERPTS END ---
TERRAYIELD_103_POST_ATTR_FAILURE_STDOUT_5WORKER_SAFE_DONE

``

## Error
``text

``
