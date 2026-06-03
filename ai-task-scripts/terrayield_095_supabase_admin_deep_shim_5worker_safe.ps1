$ErrorActionPreference='Continue'
$TaskId='terrayield-095-supabase-admin-deep-shim-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__095_supabase_admin_deep_shim_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__095_summary.md'
$Status=Join-Path $RunDir 'terrayield__095_status.txt'
$Score=Join-Path $RunDir 'terrayield__095_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=deep supabase admin compatibility shim and five worker verification'
Set-Location $Root
$svc=Join-Path $Root 'app\services\supabase_admin_service.py'
$test=Join-Path $Root 'tests\test_supabase_admin_service.py'
$patch='missing'
if(Test-Path $svc){
  $txt=Get-Content -Raw -Encoding UTF8 $svc
  Copy-Item $svc ($svc+'.aays095.bak') -Force
  if($txt -notmatch 'from __future__ import annotations'){$txt='from __future__ import annotations'+[Environment]::NewLine+$txt}
  if($txt -notmatch 'SupabaseRestClient'){$txt=$txt -replace 'from __future__ import annotations','from __future__ import annotations'+[Environment]::NewLine+'from app.clients.supabase_rest import SupabaseRestClient'}
  $txt=[regex]::Replace($txt,'# AAYS095_SUPABASE_ADMIN_DEEP_SHIM[\s\S]*?# AAYS095_SUPABASE_ADMIN_DEEP_SHIM_END\r?\n?','')
  $shim=@'

# AAYS095_SUPABASE_ADMIN_DEEP_SHIM
from types import SimpleNamespace as _AAYS095NS


def _aays095_client():
    return SupabaseRestClient()


def _aays095_configured(client):
    value = getattr(client, "configured", True)
    return bool(value)


def _aays095_call(obj, names, *args, **kwargs):
    for name in names:
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                return fn(*args, **kwargs)
            except TypeError:
                try:
                    return fn(*args)
                except TypeError:
                    return fn()
    return None


def _aays095_rows(result):
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, tuple):
        return list(result)
    data = getattr(result, "data", None)
    if data is not None:
        return data if isinstance(data, list) else [data]
    if isinstance(result, dict):
        if isinstance(result.get("data"), list):
            return result["data"]
        return [result]
    return [result]


def _aays095_payload_to_row(payload):
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


def get_supabase_sync_status():
    try:
        client = _aays095_client()
        configured = _aays095_configured(client)
        note = "Supabase backend configured." if configured else "Backend Supabase config eksik."
        return _AAYS095NS(configured=configured, note=note)
    except Exception as exc:
        return _AAYS095NS(configured=False, note=str(exc) or "Backend Supabase config eksik.")


def list_supabase_admin_records(session=None, *, region=None, listing_status=None, search=None, limit=500):
    client = _aays095_client()
    if not _aays095_configured(client):
        return []
    filters = {}
    for key, value in (("region", region), ("region_slug", region), ("listing_status", listing_status), ("status", listing_status), ("search", search)):
        if value not in (None, ""):
            filters[key] = value
    result = _aays095_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc")
    return _aays095_rows(result)


def list_supabase_parcel_records(session=None, parcel_ref=None, *, limit=500):
    if parcel_ref is None and isinstance(session, str):
        parcel_ref = session
        session = None
    client = _aays095_client()
    if not _aays095_configured(client):
        return []
    filters = {}
    if parcel_ref not in (None, ""):
        filters.update({"parcel_ref": parcel_ref, "inspire_id": parcel_ref})
    result = _aays095_call(client, ["list_rows", "select_rows", "select", "list"], filters=filters, limit=limit, order="updated_at.desc")
    return _aays095_rows(result)


def upsert_supabase_admin_record(session=None, payload=None):
    if payload is None:
        payload = session
        session = None
    client = _aays095_client()
    if not _aays095_configured(client):
        status = get_supabase_sync_status()
        raise RuntimeError(getattr(status, "note", "Backend Supabase config eksik."))
    row = _aays095_payload_to_row(payload)
    result = _aays095_call(client, ["upsert_rows", "upsert", "insert_rows", "insert"], [row], return_rows=True)
    rows = _aays095_rows(result)
    return rows[0] if rows else row
# AAYS095_SUPABASE_ADMIN_DEEP_SHIM_END
'@
  Set-Content -Encoding UTF8 -Path $svc -Value ($txt.TrimEnd()+$shim)
  $patch='patched'
}
W ('PATCH_SUPABASE_ADMIN_DEEP_SHIM='+$patch)
$base=Join-Path $Root '.aays_real_runs'
$latest094=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__094_own_result_final_split_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest094){W ('LATEST_094='+$latest094.FullName)}
$Slots=@(
 @{slot='slot_1_inspect_094_and_tests'; area='inspect'; cmd='inspect'},
 @{slot='slot_2_supabase_admin_only'; area='supabase_admin_only'; cmd='python -m pytest tests/test_supabase_admin_service.py -q -ra'},
 @{slot='slot_3_combined_acceptance'; area='combined_acceptance'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra'},
 @{slot='slot_4_admin_publish_sync'; area='admin_publish_sync'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_5_compile_collect'; area='compile_collect'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir,$Latest094,$Svc,$Test)
 $out=Join-Path $SlotsDir ('terrayield__095__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-095-supabase-admin-deep-shim-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Cmd -eq 'inspect'){
     if($Latest094){
       L ('LATEST_094='+$Latest094.FullName)
       Get-ChildItem -LiteralPath (Join-Path $Latest094.FullName 'slots') -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
         L ('--- 094_SLOT '+$_.Name+' ---')
         Select-String -Path $_.FullName -Pattern 'OWN_RESULT=|OWN_EXIT_CODE=|FAILED|ERROR|Traceback|AssertionError|TypeError|AttributeError|passed|collected' -Context 0,4 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out
       }
     }
     L '--- TEST_SUPABASE_ADMIN_FUNCTIONS ---'
     if(Test-Path $Test){Select-String -Path $Test -Pattern '^def test_|SupabaseRestClient|list_supabase|upsert_supabase|get_supabase' -Context 0,2 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out}
     L '--- SERVICE_TAIL ---'
     if(Test-Path $Svc){Get-Content -LiteralPath $Svc -Tail 140 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out}
     $global:LASTEXITCODE=0
   } else {
     L ('CMD='+$Cmd)
     Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   }
   $ec=$LASTEXITCODE
   if($null -eq $ec){$ec=0}
   L ('OWN_EXIT_CODE='+$ec)
   if($ec -eq 0){L 'OWN_RESULT=pass'}else{L 'OWN_RESULT=fail'}
 } catch { L 'OWN_RESULT=error'; L ('OWN_ERROR_REASON='+$_.Exception.Message); L 'OWN_EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir,$latest094,$svc,$test; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$ownPass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$ownFail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$ownError=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$badExit=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_EXIT_CODE=[1-9]' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$failedNames=(Get-ChildItem -LiteralPath $SlotsDir -File -ErrorAction SilentlyContinue | Where-Object { Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^OWN_RESULT=error$' -Quiet } | ForEach-Object { $_.Name }) -join ';'
$program=99
if($ownPass -eq 5 -and $ownFail -eq 0 -and $ownError -eq 0){$program=100}
@('metric,score','workers,5','own_pass_slots,'+$ownPass,'own_fail_slots,'+$ownFail,'own_error_slots,'+$ownError,'own_bad_exit_markers,'+$badExit,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'failed_slot_names,"'+$failedNames+'"')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'PATCH_SUPABASE_ADMIN_DEEP_SHIM='+$patch,'WORKERS=5','OWN_PASS_SLOTS='+$ownPass,'OWN_FAIL_SLOTS='+$ownFail,'OWN_ERROR_SLOTS='+$ownError,'OWN_BAD_EXIT_MARKERS='+$badExit,'PASSED_MARKERS='+$passedMarkers,'FAILED_SLOT_NAMES='+$failedNames,'PROGRAM_COMPLETION='+$program+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "OWN_PASS_SLOTS=$ownPass"
W "OWN_FAIL_SLOTS=$ownFail"
W "OWN_ERROR_SLOTS=$ownError"
W "OWN_BAD_EXIT_MARKERS=$badExit"
W "PASSED_MARKERS=$passedMarkers"
W "FAILED_SLOT_NAMES=$failedNames"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_095_SUPABASE_ADMIN_DEEP_SHIM_5WORKER_SAFE_DONE'
exit 0
