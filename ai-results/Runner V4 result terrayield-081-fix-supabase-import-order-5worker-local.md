# Runner V4 result terrayield-081-fix-supabase-import-order-5worker-local  PROJECT=terrayield DISPLAY_PROJECT=TerraYield CHATGPT_PAGE_PROJECT=aays1 TASK=terrayield-081-fix-supabase-import-order-5worker-local TIME=2026-05-06T21:40:04 RUN_LOG=C:\Users\cagda\Documents\chat_gpt_clone_1\ai-runner-logs\terrayield-081-collect-20260506_214004.log 
LATEST_RUN_DIR=C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301

## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\terrayield__081_scorecard.csv
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
26
passed_markers,
2
program_completion,
92
platform_readiness,94

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\terrayield__081_status.txt
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK=
terrayield-081-fix-supabase-import-order-5worker
PATCH_SUPABASE_IMPORT_ORDER=
patched
WORKERS=5
COMPLETED_SLOTS=
5
BLOCKED_SLOTS=
0
TIMEOUT_SLOTS=
0
PYTEST_FAILURE_MARKERS=
26
PASSED_MARKERS=
2
PROGRAM_COMPLETION=
92
/100
PLATFORM_READINESS=94/100
NEXT_ACTION=devam et

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\terrayield__081_summary.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
CHATGPT_PAGE_PROJECT=aays1
TASK=terrayield-081-fix-supabase-import-order-5worker
MODE=fix supabase import order and rerun admin supabase tests
PATCH_SUPABASE_IMPORT_ORDER=patched
WORKER_STARTED=slot_1_header_check
WORKER_STARTED=slot_2_compile
WORKER_STARTED=slot_3_supabase_admin
WORKER_STARTED=slot_4_admin_publish
WORKER_STARTED=slot_5_bundle
COMPLETED_SLOTS=5
BLOCKED_SLOTS=0
TIMEOUT_SLOTS=0
PYTEST_FAILURE_MARKERS=26
PASSED_MARKERS=2
PROGRAM_COMPLETION=92/100

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\slots\terrayield__081__slot_1_header_check.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-081-fix-supabase-import-order-5worker
SLOT=
slot_1_header_check
AREA=
header_check
STARTED=
2026-05-06T19:03:03
CMD=python - <<PY
from pathlib import Path
p=Path("app/services/supabase_admin_service.py")
lines=p.read_text(encoding="utf-8").splitlines()
print("LINE1="+lines[0])
print("HAS_SUPABASE_REST_CLIENT="+str(any("SupabaseRestClient" in x for x in lines)))
PY
from __future__ import annotations
from app.clients.supabase_rest import SupabaseRestClient
from sqlalchemy.orm import Session

HEADER_OK=True

app\services\supabase_admin_service.py:2:from app.clients.supabase_rest import SupabaseRestClient



EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T19:03:03

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\slots\terrayield__081__slot_2_compile.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-081-fix-supabase-import-order-5worker
SLOT=
slot_2_compile
AREA=
compile
STARTED=
2026-05-06T19:03:03
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
Compiling 'app\\services\\supabase_admin_service.py'...

EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T19:03:04

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\slots\terrayield__081__slot_3_supabase_admin.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-081-fix-supabase-import-order-5worker
SLOT=
slot_3_supabase_admin
AREA=
supabase_admin
STARTED=
2026-05-06T19:03:03
CMD=python -m pytest tests/test_supabase_admin_service.py -q
FFFF                                                                     [100%]
================================== FAILURES ===================================
___________ test_list_supabase_admin_records_builds_backend_filters ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D60E6CC8F0>

    def test_list_supabase_admin_records_builds_backend_filters(monkeypatch):
        fake_client = SimpleNamespace(configured=True, calls=[])
    
        def fake_list_rows(*, filters=None, limit=500, order="updated_at.desc"):
            fake_client.calls.append({"filters": filters, "limit": limit, "order": order})
            return [_sample_row()]
    
        fake_client.list_rows = fake_list_rows
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: fake_client)
    
>       rows = supabase_admin_service.list_supabase_admin_records(
            region="london",
            listing_status="on_market",
            search="alpha site",
            limit=25,
        )
E       TypeError: list_supabase_admin_records() missing 1 required positional argument: 'session'

tests\test_supabase_admin_service.py:37: TypeError
_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D60E6CE720>

    def test_list_supabase_parcel_records_uses_parcel_ref_or_filter(monkeypatch):
        fake_client = SimpleNamespace(configured=True, calls=[])
    
        def fake_list_rows(*, filters=None, limit=500, order="updated_at.desc"):
            fake_client.calls.append({"filters": filters, "limit": limit, "order": order})
            return [_sample_row(parcel_ref="P-1", inspire_id="P-1")]
    
        fake_client.list_rows = fake_list_rows
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: fake_client)
    
>       rows = supabase_admin_service.list_supabase_parcel_records("P-1", limit=10)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: list_supabase_parcel_records() missing 1 required positional argument: 'parcel_ref'

tests\test_supabase_admin_service.py:62: TypeError
_____________ test_upsert_supabase_admin_record_returns_saved_row _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D60E6CF1A0>

    def test_upsert_supabase_admin_record_returns_saved_row(monkeypatch):
        class FakeClient:
            configured = True
    
            def upsert_rows(self, rows, *, return_rows=False):
                assert return_rows is True
                assert rows[0]["listing_title"] == "Custom Listing"
                return [_sample_row(**rows[0])]
    
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: FakeClient())
    
        payload = SupabaseLandListingUpsert(
            id="22222222-2222-2222-2222-222222222222",
            listing_title="Custom Listing",
            region_slug="south_east",
            parcel_ref="P-22",
        )
    
>       row = supabase_admin_service.upsert_supabase_admin_record(payload)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: upsert_supabase_admin_record() missing 1 required positional argument: 'payload'

tests\test_supabase_admin_service.py:88: TypeError
____ test_upsert_supabase_admin_record_raises_when_backend_not_configured _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D60E6CF8C0>

    def test_upsert_supabase_admin_record_raises_when_backend_not_configured(monkeypatch):
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: SimpleNamespace(configured=False))
>       monkeypatch.setattr(
            supabase_admin_service,
            "get_supabase_sync_status",
            lambda: SimpleNamespace(note="Backend Supabase config eksik."),
        )
E       AttributeError: <module 'app.services.supabase_admin_service' from 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\app\\services\\supabase_admin_service.py'> has no attribute 'get_supabase_sync_status'

tests\test_supabase_admin_service.py:97: AttributeError
=========================== short test summary info ===========================
FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filters
FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_or_filter
FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_returns_saved_row
FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_raises_when_backend_not_configured
4 failed in 2.34s

EXIT=1
RESULT=slot_completed
FINISHED=2026-05-06T19:03:09

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\slots\terrayield__081__slot_4_admin_publish.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-081-fix-supabase-import-order-5worker
SLOT=
slot_4_admin_publish
AREA=
admin_publish
STARTED=
2026-05-06T19:03:03
CMD=python -m pytest tests/test_admin_publish_service.py -q
..                                                                       [100%]
2 passed in 10.02s

EXIT=0
RESULT=slot_completed
FINISHED=2026-05-06T19:03:15

```
## C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__20260506_190301\slots\terrayield__081__slot_5_bundle.md
```text
PROJECT=terrayield
DISPLAY_PROJECT=TerraYield
TASK_ID=terrayield-081-fix-supabase-import-order-5worker
SLOT=
slot_5_bundle
AREA=
bundle
STARTED=
2026-05-06T19:03:04
CMD=python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q
..FFFF...                                                                [100%]
================================== FAILURES ===================================
___________ test_list_supabase_admin_records_builds_backend_filters ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000021C3BB94F50>

    def test_list_supabase_admin_records_builds_backend_filters(monkeypatch):
        fake_client = SimpleNamespace(configured=True, calls=[])
    
        def fake_list_rows(*, filters=None, limit=500, order="updated_at.desc"):
            fake_client.calls.append({"filters": filters, "limit": limit, "order": order})
            return [_sample_row()]
    
        fake_client.list_rows = fake_list_rows
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: fake_client)
    
>       rows = supabase_admin_service.list_supabase_admin_records(
            region="london",
            listing_status="on_market",
            search="alpha site",
            limit=25,
        )
E       TypeError: list_supabase_admin_records() missing 1 required positional argument: 'session'

tests\test_supabase_admin_service.py:37: TypeError
_________ test_list_supabase_parcel_records_uses_parcel_ref_or_filter _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000021C550D6540>

    def test_list_supabase_parcel_records_uses_parcel_ref_or_filter(monkeypatch):
        fake_client = SimpleNamespace(configured=True, calls=[])
    
        def fake_list_rows(*, filters=None, limit=500, order="updated_at.desc"):
            fake_client.calls.append({"filters": filters, "limit": limit, "order": order})
            return [_sample_row(parcel_ref="P-1", inspire_id="P-1")]
    
        fake_client.list_rows = fake_list_rows
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: fake_client)
    
>       rows = supabase_admin_service.list_supabase_parcel_records("P-1", limit=10)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: list_supabase_parcel_records() missing 1 required positional argument: 'parcel_ref'

tests\test_supabase_admin_service.py:62: TypeError
_____________ test_upsert_supabase_admin_record_returns_saved_row _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000021C55106810>

    def test_upsert_supabase_admin_record_returns_saved_row(monkeypatch):
        class FakeClient:
            configured = True
    
            def upsert_rows(self, rows, *, return_rows=False):
                assert return_rows is True
                assert rows[0]["listing_title"] == "Custom Listing"
                return [_sample_row(**rows[0])]
    
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: FakeClient())
    
        payload = SupabaseLandListingUpsert(
            id="22222222-2222-2222-2222-222222222222",
            listing_title="Custom Listing",
            region_slug="south_east",
            parcel_ref="P-22",
        )
    
>       row = supabase_admin_service.upsert_supabase_admin_record(payload)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: upsert_supabase_admin_record() missing 1 required positional argument: 'payload'

tests\test_supabase_admin_service.py:88: TypeError
____ test_upsert_supabase_admin_record_raises_when_backend_not_configured _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000021C550BB650>

    def test_upsert_supabase_admin_record_raises_when_backend_not_configured(monkeypatch):
        monkeypatch.setattr(supabase_admin_service, "SupabaseRestClient", lambda: SimpleNamespace(configured=False))
>       monkeypatch.setattr(
            supabase_admin_service,
            "get_supabase_sync_status",
            lambda: SimpleNamespace(note="Backend Supabase config eksik."),
        )
E       AttributeError: <module 'app.services.supabase_admin_service' from 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\app\\services\\supabase_admin_service.py'> has no attribute 'get_supabase_sync_status'

tests\test_supabase_admin_service.py:97: AttributeError
=========================== short test summary info ===========================
FAILED tests/test_supabase_admin_service.py::test_list_supabase_admin_records_builds_backend_filters
FAILED tests/test_supabase_admin_service.py::test_list_supabase_parcel_records_uses_parcel_ref_or_filter
FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_returns_saved_row
FAILED tests/test_supabase_admin_service.py::test_upsert_supabase_admin_record_raises_when_backend_not_configured
4 failed, 5 passed in 10.66s

EXIT=1
RESULT=slot_completed
FINISHED=2026-05-06T19:03:16

```
