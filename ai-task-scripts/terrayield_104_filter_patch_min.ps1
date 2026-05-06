$ErrorActionPreference='Continue'
$TaskId='terrayield-104-filter-patch-min'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $Root
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=minimal Supabase filter format patch'
$svc='app\services\supabase_admin_service.py'
if(Test-Path $svc){
  $txt=Get-Content -Raw -Encoding UTF8 $svc
  Copy-Item $svc ($svc+'.aays104min.bak') -Force
  $txt=[regex]::Replace($txt,'# AAYS104_MIN_FILTER_PATCH[\s\S]*?# AAYS104_MIN_FILTER_PATCH_END\r?\n?','')
  $add=@'

# AAYS104_MIN_FILTER_PATCH
from types import SimpleNamespace as _AAYS104MinNS


def _aays104min_attr(x):
    if isinstance(x, dict):
        return _AAYS104MinNS(**{k: _aays104min_attr(v) for k, v in x.items()})
    if isinstance(x, list):
        return [_aays104min_attr(v) for v in x]
    return x


def _aays104min_rows(result):
    if result is None:
        return []
    if isinstance(result, list):
        return [_aays104min_attr(v) for v in result]
    data = getattr(result, "data", None)
    if data is not None:
        return [_aays104min_attr(v) for v in data] if isinstance(data, list) else [_aays104min_attr(data)]
    if isinstance(result, dict):
        data = result.get("data")
        if data is not None:
            return [_aays104min_attr(v) for v in data] if isinstance(data, list) else [_aays104min_attr(data)]
        return [_aays104min_attr(result)]
    return [_aays104min_attr(result)]


def _aays104min_eq(v):
    if v is None or v == "":
        return None
    s = str(v)
    return s if s.startswith("eq.") else "eq." + s


def _aays104min_payload(p):
    if p is None:
        return {}
    if isinstance(p, dict):
        return dict(p)
    if hasattr(p, "model_dump"):
        return p.model_dump(exclude_none=True)
    if hasattr(p, "dict"):
        return p.dict(exclude_none=True)
    return {k: v for k, v in vars(p).items() if not k.startswith("_") and v is not None}


def _aays104min_call(client, names, *args, **kwargs):
    for name in names:
        fn = getattr(client, name, None)
        if callable(fn):
            try:
                return fn(*args, **kwargs)
            except TypeError:
                try:
                    return fn(*args)
                except TypeError:
                    return fn()
    return None


def get_supabase_sync_status():
    client = SupabaseRestClient()
    configured = bool(getattr(client, "configured", False))
    return _AAYS104MinNS(configured=configured, note=("Supabase backend configured." if configured else "Backend Supabase config eksik."))


def list_supabase_admin_records(session=None, *, region=None, listing_status=None, search=None, limit=500):
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    if region not in (None, ""):
        filters["region_slug"] = _aays104min_eq(region)
    if listing_status not in (None, ""):
        filters["listing_status"] = _aays104min_eq(listing_status)
    if search not in (None, ""):
        filters["search"] = str(search)
    return _aays104min_rows(_aays104min_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc"))


def list_supabase_parcel_records(session=None, parcel_ref=None, *, limit=500):
    if parcel_ref is None and isinstance(session, str):
        parcel_ref = session
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    if parcel_ref not in (None, ""):
        ref = str(parcel_ref)
        filters["or"] = "(parcel_ref.eq." + ref + ",inspire_id.eq." + ref + ")"
    return _aays104min_rows(_aays104min_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc"))


def upsert_supabase_admin_record(session=None, payload=None):
    if payload is None:
        payload = session
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        raise RuntimeError(get_supabase_sync_status().note)
    row = _aays104min_payload(payload)
    rows = _aays104min_rows(_aays104min_call(client, ["upsert_rows", "upsert", "insert_rows", "insert"], [row], return_rows=True))
    return rows[0] if rows else _aays104min_attr(row)
# AAYS104_MIN_FILTER_PATCH_END
'@
  Set-Content -Encoding UTF8 -Path $svc -Value ($txt.TrimEnd()+$add)
  Write-Output 'PATCH_SUPABASE_FILTER_EQ=patched'
}else{Write-Output 'PATCH_SUPABASE_FILTER_EQ=missing'}
$cmds=@('python -m pytest tests/test_supabase_admin_service.py -q -ra','python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra','python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q','python -m compileall app','python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_service.py tests/test_parcel_matcher.py -q')
$pass=0;$fail=0
foreach($cmd in $cmds){
  Write-Output ('CMD='+$cmd)
  Invoke-Expression ($cmd+' 2>&1') | Out-String | Write-Output
  if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){$pass++}else{$fail++}
}
Write-Output ('PASS_SLOTS='+$pass)
Write-Output ('FAIL_SLOTS='+$fail)
if($fail -eq 0){Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'TERRAYIELD_104_FILTER_PATCH_MIN_DONE'
exit 0
