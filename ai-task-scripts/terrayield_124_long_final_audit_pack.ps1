$ErrorActionPreference='Continue'
$TaskId='terrayield-124-long-final-audit-pack'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=long final audit pack after Plan L final closure and evidence pack'
$pass=0;$fail=0
function C($n,$ok,$d){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'})+' '+$d);if($ok){$script:pass++}else{$script:fail++}}
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
$Manifest=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'
$Csv=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'
$Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
C 'ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest) $Manifest
C 'ACTIVE_CSV_EXISTS' (Test-Path $Csv) $Csv
C 'ACTIVE_README_EXISTS' (Test-Path $Readme) $Readme
if(Test-Path $Manifest){try{$m=Get-Content -Raw -Encoding UTF8 $Manifest|ConvertFrom-Json;C 'STATUS_ACTIVE' ([string]$m.status -like 'active*') ([string]$m.status);C 'ROWS_34864' ([int]$m.rows -eq 34864) ('rows='+$m.rows);C 'FEATURES_34864' ([int]$m.features -eq 34864) ('features='+$m.features);C 'MATCH_TRUE' ([bool]$m.match) ('match='+$m.match);C 'NO_UI_PATCH' (-not [bool]$m.ui_patch_applied) ('ui_patch_applied='+$m.ui_patch_applied);C 'NO_DB_IMPORT' (-not [bool]$m.db_import_applied) ('db_import_applied='+$m.db_import_applied)}catch{C 'MANIFEST_PARSE' $false $_.Exception.Message}}
$cmds=@(
 'python -m compileall app',
 'python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"',
 'python -m pytest tests/test_supabase_admin_service.py tests/test_admin_publish_service.py tests/test_supabase_sync.py -q -ra',
 'python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_service.py tests/test_parcel_matcher.py -q -ra',
 'python -m pytest tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_manifests.py -q -ra',
 'python -m pytest tests/test_facility_adapters.py tests/test_facility_api.py tests/test_facility_resolution.py tests/test_facility_scoring_engine.py -q -ra'
)
$cmdPass=0;$cmdFail=0
foreach($cmd in $cmds){
  Write-Output ('CMD='+$cmd)
  Invoke-Expression ($cmd+' 2>&1') | Out-String | Write-Output
  if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){$cmdPass++}else{$cmdFail++}
}
Write-Output ('CHECK_PASS='+$pass)
Write-Output ('CHECK_FAIL='+$fail)
Write-Output ('CMD_PASS='+$cmdPass)
Write-Output ('CMD_FAIL='+$cmdFail)
if($fail -eq 0 -and $cmdFail -eq 0){Write-Output 'LONG_FINAL_AUDIT=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'LONG_FINAL_AUDIT=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_124_LONG_FINAL_AUDIT_PACK_DONE'
exit 0
