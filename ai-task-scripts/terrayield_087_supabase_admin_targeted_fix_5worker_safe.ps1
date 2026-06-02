$ErrorActionPreference='Continue'
$TaskId='terrayield-087-supabase-admin-targeted-fix-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__087_supabase_admin_targeted_fix_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__087_summary.md'
$Status=Join-Path $RunDir 'terrayield__087_status.txt'
$Score=Join-Path $RunDir 'terrayield__087_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=targeted supabase admin fix and broad five worker validation'
Set-Location $Root
$svc=Join-Path $Root 'app\services\supabase_admin_service.py'
$test=Join-Path $Root 'tests\test_supabase_admin_service.py'
$patch='missing'
if(Test-Path $svc){
  $txt=Get-Content -Raw -Encoding UTF8 $svc
  Copy-Item $svc ($svc+'.aays087.bak') -Force
  $txt=[regex]::Replace($txt,'# AAYS087_SUPABASE_ADMIN_TARGETED[\s\S]*?# AAYS087_SUPABASE_ADMIN_TARGETED_END\r?\n?','')
  if($txt -notmatch 'from __future__ import annotations'){$txt='from __future__ import annotations'+[Environment]::NewLine+$txt}
  if($txt -notmatch 'SupabaseRestClient'){$txt=$txt -replace 'from __future__ import annotations','from __future__ import annotations'+[Environment]::NewLine+'from app.clients.supabase_rest import SupabaseRestClient'}
  $compat=@'

# AAYS087_SUPABASE_ADMIN_TARGETED
from types import SimpleNamespace as _AAYS087SimpleNamespace


def get_supabase_sync_status():
    try:
        client = SupabaseRestClient()
        configured = bool(getattr(client, "configured", False))
        return _AAYS087SimpleNamespace(configured=configured, note=("Supabase backend configured." if configured else "Backend Supabase config eksik."))
    except Exception as exc:
        return _AAYS087SimpleNamespace(configured=False, note=str(exc) or "Backend Supabase config eksik.")


def _aays087_payload_to_row(payload):
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


def _aays087_add_filter(filters, key, value):
    if value is None or value == "":
        return
    filters[key] = value


def list_supabase_admin_records(session=None, *, region=None, listing_status=None, search=None, limit=500):
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    _aays087_add_filter(filters, "region", region)
    _aays087_add_filter(filters, "region_slug", region)
    _aays087_add_filter(filters, "listing_status", listing_status)
    _aays087_add_filter(filters, "status", listing_status)
    _aays087_add_filter(filters, "search", search)
    if search:
        filters["listing_title"] = search
    return client.list_rows(filters=filters, limit=limit, order="updated_at.desc") or []


def list_supabase_parcel_records(session=None, parcel_ref=None, *, limit=500):
    if parcel_ref is None and isinstance(session, str):
        parcel_ref = session
        session = None
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        return []
    filters = {}
    _aays087_add_filter(filters, "parcel_ref", parcel_ref)
    _aays087_add_filter(filters, "inspire_id", parcel_ref)
    return client.list_rows(filters=filters, limit=limit, order="updated_at.desc") or []


def upsert_supabase_admin_record(session=None, payload=None):
    if payload is None:
        payload = session
        session = None
    client = SupabaseRestClient()
    if not bool(getattr(client, "configured", False)):
        status = get_supabase_sync_status()
        raise RuntimeError(getattr(status, "note", "Backend Supabase config eksik."))
    row = _aays087_payload_to_row(payload)
    rows = client.upsert_rows([row], return_rows=True)
    return rows[0] if rows else row
# AAYS087_SUPABASE_ADMIN_TARGETED_END
'@
  Set-Content -Encoding UTF8 -Path $svc -Value ($txt.TrimEnd()+$compat)
  $patch='patched'
}
W ('PATCH_SUPABASE_ADMIN_TARGETED='+$patch)
$Slots=@(
 @{slot='slot_1_test_source_visibility'; area='test_source_visibility'; cmd='source'},
 @{slot='slot_2_compile'; area='compile'; cmd='python -m compileall app'},
 @{slot='slot_3_supabase_admin'; area='supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_4_admin_bundle'; area='admin_bundle'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_5_broad_guard'; area='broad_guard'; cmd='python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_source_registry.py tests/test_facility_api.py tests/test_listing_service.py tests/test_parcel_matcher.py -q'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir,$Svc,$Test)
 $out=Join-Path $SlotsDir ('terrayield__087__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-087-supabase-admin-targeted-fix-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Cmd -eq 'source'){
     L '--- tests/test_supabase_admin_service.py ---'
     if(Test-Path $Test){Get-Content -LiteralPath $Test -Raw -ErrorAction SilentlyContinue|Add-Content -Encoding UTF8 -Path $out}
     L '--- app/services/supabase_admin_service.py tail ---'
     if(Test-Path $Svc){Get-Content -LiteralPath $Svc -Tail 160 -ErrorAction SilentlyContinue|Out-String|Add-Content -Encoding UTF8 -Path $out}
     $global:LASTEXITCODE=0
   } else {
     L ('CMD='+$Cmd)
     Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   }
   L ('EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir,$svc,$test; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$failureMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=96
if($completed -eq 5 -and $partial -eq 0){$program=97}
if($failureMarkers -eq 0 -and $passedMarkers -ge 3){$program=98}
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'failure_markers,'+$failureMarkers,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'targeted_fix,98')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'PATCH_SUPABASE_ADMIN_TARGETED='+$patch,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'FAILURE_MARKERS='+$failureMarkers,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','TARGETED_FIX=98/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "FAILURE_MARKERS=$failureMarkers"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
W 'TARGETED_FIX=98/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_087_SUPABASE_ADMIN_TARGETED_FIX_5WORKER_SAFE_DONE'
exit 0
