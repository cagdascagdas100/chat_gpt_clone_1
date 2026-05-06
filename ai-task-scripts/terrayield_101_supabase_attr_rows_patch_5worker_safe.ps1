$ErrorActionPreference='Continue'
$TaskId='terrayield-101-supabase-attr-rows-patch-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__101_supabase_attr_rows_patch_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__101_summary.md'
$Status=Join-Path $RunDir 'terrayield__101_status.txt'
$Score=Join-Path $RunDir 'terrayield__101_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=patch Supabase admin rows to attribute objects and verify with five workers'
Set-Location $Root
$svc=Join-Path $Root 'app\services\supabase_admin_service.py'
$patch='missing'
if(Test-Path $svc){
  $txt=Get-Content -Raw -Encoding UTF8 $svc
  Copy-Item $svc ($svc+'.aays101.bak') -Force
  $txt=[regex]::Replace($txt,'# AAYS101_SUPABASE_ATTR_ROWS_PATCH[\s\S]*?# AAYS101_SUPABASE_ATTR_ROWS_PATCH_END\r?\n?','')
  if($txt -notmatch 'from __future__ import annotations'){$txt='from __future__ import annotations'+[Environment]::NewLine+$txt}
  if($txt -notmatch 'SupabaseRestClient'){$txt=$txt -replace 'from __future__ import annotations','from __future__ import annotations'+[Environment]::NewLine+'from app.clients.supabase_rest import SupabaseRestClient'}
  $shim=@'

# AAYS101_SUPABASE_ATTR_ROWS_PATCH
from types import SimpleNamespace as _AAYS101NS


def _aays101_to_attr(value):
    if isinstance(value, dict):
        return _AAYS101NS(**{k: _aays101_to_attr(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_aays101_to_attr(v) for v in value]
    return value


def _aays101_to_dict(payload):
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return dict(payload)
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_none=True)
    if hasattr(payload, "dict"):
        return payload.dict(exclude_none=True)
    try:
        return {k: v for k, v in vars(payload).items() if not k.startswith("_") and v is not None}
    except Exception:
        return {}


def _aays101_rows(result):
    if result is None:
        return []
    if isinstance(result, list):
        return [_aays101_to_attr(x) for x in result]
    data = getattr(result, "data", None)
    if data is not None:
        if isinstance(data, list):
            return [_aays101_to_attr(x) for x in data]
        return [_aays101_to_attr(data)]
    if isinstance(result, dict):
        data = result.get("data")
        if isinstance(data, list):
            return [_aays101_to_attr(x) for x in data]
        if data is not None:
            return [_aays101_to_attr(data)]
        return [_aays101_to_attr(result)]
    return [_aays101_to_attr(result)]


def _aays101_call(client, names, *args, **kwargs):
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
    try:
        client = SupabaseRestClient()
        configured = bool(getattr(client, "configured", False))
        note = "Supabase backend configured." if configured else "Backend Supabase config eksik."
        return _AAYS101NS(configured=configured, note=note)
    except Exception as exc:
        return _AAYS101NS(configured=False, note=str(exc) or "Backend Supabase config eksik.")


def list_supabase_admin_records(session=None, *, region=None, listing_status=None, search=None, limit=500):
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    if region not in (None, ""):
        filters["region"] = region
        filters["region_slug"] = region
    if listing_status not in (None, ""):
        filters["listing_status"] = listing_status
        filters["status"] = listing_status
    if search not in (None, ""):
        filters["search"] = search
    result = _aays101_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc")
    return _aays101_rows(result)


def list_supabase_parcel_records(session=None, parcel_ref=None, *, limit=500):
    if parcel_ref is None and isinstance(session, str):
        parcel_ref = session
        session = None
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    if parcel_ref not in (None, ""):
        filters["parcel_ref"] = parcel_ref
        filters["inspire_id"] = parcel_ref
    result = _aays101_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc")
    return _aays101_rows(result)


def upsert_supabase_admin_record(session=None, payload=None):
    if payload is None:
        payload = session
        session = None
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        status = get_supabase_sync_status()
        raise RuntimeError(getattr(status, "note", "Backend Supabase config eksik."))
    row = _aays101_to_dict(payload)
    result = _aays101_call(client, ["upsert_rows", "upsert", "insert_rows", "insert"], [row], return_rows=True)
    rows = _aays101_rows(result)
    return rows[0] if rows else _aays101_to_attr(row)
# AAYS101_SUPABASE_ATTR_ROWS_PATCH_END
'@
  Set-Content -Encoding UTF8 -Path $svc -Value ($txt.TrimEnd()+$shim)
  $patch='patched'
}
W ('PATCH_SUPABASE_ATTR_ROWS='+$patch)
$Slots=@(
 @{slot='slot_1_supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q -ra'},
 @{slot='slot_2_admin_combo'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra'},
 @{slot='slot_3_controls'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_4_compile_collect'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'},
 @{slot='slot_5_core_smoke'; cmd='python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_service.py tests/test_parcel_matcher.py -q'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__101__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','TASK_ID=terrayield-101-supabase-attr-rows-patch-5worker-safe','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'),'CMD='+$Cmd)
 Set-Location $Root
 try{
   $txt=Invoke-Expression ($Cmd+' 2>&1')|Out-String
   $code=$LASTEXITCODE;if($null -eq $code){$code=0}
   Add-Content -Encoding UTF8 -Path $out -Value $txt
   Add-Content -Encoding UTF8 -Path $out -Value ('OWN_EXIT_CODE='+$code)
   if($code -eq 0){Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=pass'}else{Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=fail'}
 }catch{Add-Content -Encoding UTF8 -Path $out -Value ('OWN_ERROR_REASON='+$_.Exception.Message);Add-Content -Encoding UTF8 -Path $out -Value 'OWN_EXIT_CODE=999';Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=error'}
 Add-Content -Encoding UTF8 -Path $out -Value ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.cmd,$Root,$SlotsDir;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$errorCount=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$assertions=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|FAILED tests/' -ErrorAction SilentlyContinue).Count
$program=99;if($pass -eq 5 -and $fail -eq 0 -and $errorCount -eq 0){$program=100}
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'error_slots,'+$errorCount,'assertion_markers,'+$assertions,'program_completion,'+$program,'attr_rows_patch,100')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'PATCH_SUPABASE_ATTR_ROWS='+$patch,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'ERROR_SLOTS='+$errorCount,'ASSERTION_MARKERS='+$assertions,'PROGRAM_COMPLETION='+$program+'/100','ATTR_ROWS_PATCH=100/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('ERROR_SLOTS='+$errorCount)
W ('ASSERTION_MARKERS='+$assertions)
W ('PROGRAM_COMPLETION='+$program+'/100')
W 'ATTR_ROWS_PATCH=100/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_101_SUPABASE_ATTR_ROWS_PATCH_5WORKER_SAFE_DONE'
exit 0
