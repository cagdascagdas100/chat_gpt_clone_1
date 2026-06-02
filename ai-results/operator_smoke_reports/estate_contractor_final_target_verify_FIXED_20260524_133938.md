# Estate / Contractor Final Target Verify

generated=2026-05-24T13:40:00
DB_WRITE=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false
FULL_TEST_SUITE=false
DB_IMPORT=false
MIGRATION=false
DEPLOY=false

## Pass Fail
| check | pass |
|---|---:|
| estate_agents_api pytest | False |
| contractor_api pytest | False |
| JS syntax check | True |
| final targeted verification | False |

## estate_agents_api output
EEEEE                                                                    [100%]
=================================== ERRORS ====================================
_ ERROR at setup of test_estate_agents_by_parcel_returns_only_matching_and_sorted _

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_estate_agents_by_parcel_returns_only_matching_and_sorted>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
____ ERROR at setup of test_estate_agents_by_unknown_parcel_returns_empty _____

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_estate_agents_by_unknown_parcel_returns_empty>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
_ ERROR at setup of test_estate_agents_dry_run_validate_exposes_no_write_flags _

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_estate_agents_dry_run_validate_exposes_no_write_flags>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
____ ERROR at setup of test_contractor_contacts_uses_estate_agent_dataset _____

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_contacts_uses_estate_agent_dataset>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
_ ERROR at setup of test_contractor_contacts_unknown_parcel_returns_empty_no_fallback _

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_contacts_unknown_parcel_returns_empty_no_fallback>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
=========================== short test summary info ===========================
ERROR tests/test_estate_agents_api.py::test_estate_agents_by_parcel_returns_only_matching_and_sorted
ERROR tests/test_estate_agents_api.py::test_estate_agents_by_unknown_parcel_returns_empty
ERROR tests/test_estate_agents_api.py::test_estate_agents_dry_run_validate_exposes_no_write_flags
ERROR tests/test_estate_agents_api.py::test_contractor_contacts_uses_estate_agent_dataset
ERROR tests/test_estate_agents_api.py::test_contractor_contacts_unknown_parcel_returns_empty_no_fallback

## contractor_api output
EEEEEEE                                                                  [100%]
=================================== ERRORS ====================================
_____________ ERROR at setup of test_contractor_status_completed ______________

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_status_completed>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
_______ ERROR at setup of test_contractor_export_contractors_pagination _______

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_export_contractors_pagination>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
________ ERROR at setup of test_contractor_export_parcel_match_filter _________

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_export_parcel_match_filter>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
___________ ERROR at setup of test_contractor_parcel_match_preview ____________

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_parcel_match_preview>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
__ ERROR at setup of test_contractor_parcel_contacts_filters_do_not_contact ___

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_parcel_contacts_filters_do_not_contact>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
______ ERROR at setup of test_contractor_parcel_contacts_include_blocked ______

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_parcel_contacts_include_blocked>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
_ ERROR at setup of test_contractor_parcel_contacts_filters_by_structure_type _

fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
request = <SubRequest 'tmp_path' for <Function test_contractor_parcel_contacts_filters_by_structure_type>>

    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
        asyncio_mode = _get_asyncio_mode(request.config)
        if not _is_asyncio_fixture_function(fixturedef.func):
            if asyncio_mode == Mode.STRICT:
                # Ignore async fixtures without explicit asyncio mark in strict mode
                # This applies to pytest_trio fixtures, for example
>               return (yield)
                        ^^^^^
E               PermissionError: [WinError 5] Eri■im engellendi: 'C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence\\data\\tmp\\pytest-of-cagda'

..\..\..\..\AppData\Roaming\Python\Python312\site-packages\pytest_asyncio\plugin.py:728: PermissionError
=========================== short test summary info ===========================
ERROR tests/test_contractor_api.py::test_contractor_status_completed - Permis...
ERROR tests/test_contractor_api.py::test_contractor_export_contractors_pagination
ERROR tests/test_contractor_api.py::test_contractor_export_parcel_match_filter
ERROR tests/test_contractor_api.py::test_contractor_parcel_match_preview - Pe...
ERROR tests/test_contractor_api.py::test_contractor_parcel_contacts_filters_do_not_contact
ERROR tests/test_contractor_api.py::test_contractor_parcel_contacts_include_blocked
ERROR tests/test_contractor_api.py::test_contractor_parcel_contacts_filters_by_structure_type

## node output


## API smoke, service may be closed
summary:
SERVICE_DOWN_OR_EMPTY

by_parcel:
SERVICE_DOWN_OR_EMPTY

by_group:
SERVICE_DOWN_OR_EMPTY

## Production Gate
- No DB import performed.
- No migration performed.
- No production deploy performed.
- Explicit approval required for DB import or production rollout.
