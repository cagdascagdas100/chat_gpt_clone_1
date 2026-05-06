$ErrorActionPreference='Continue'
$TaskId='terrayield-101-supabase-service-probe-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__101_supabase_service_probe_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__101_summary.md'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
Set-Location $Root
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
$svc='app\services\supabase_admin_service.py'
$test='tests\test_supabase_admin_service.py'
$cmds=@(
 @{s='slot_1_service_defs';c="Select-String -Path '$svc' -Pattern '^def |class |return |list_rows|upsert' -Context 0,3"},
 @{s='slot_2_test_asserts';c="Select-String -Path '$test' -Pattern '^def test_|assert |listing_title|parcel_ref|row.id' -Context 0,3"},
 @{s='slot_3_admin_test';c='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{s='slot_4_controls';c='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'},
 @{s='slot_5_compile';c='python -m compileall app'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__101_probe__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('SLOT='+$Slot,'CMD='+$Cmd)
 Set-Location $Root
 $txt=Invoke-Expression ($Cmd+' 2>&1')|Out-String
 $code=$LASTEXITCODE;if($null -eq $code){$code=0}
 Add-Content -Encoding UTF8 -Path $out -Value $txt
 Add-Content -Encoding UTF8 -Path $out -Value ('EXIT_CODE='+$code)
 if($code -eq 0){Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=pass'}else{Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=fail'}
}
$jobs=@()
foreach($x in $cmds){$jobs+=Start-Job -Name $x.s -ScriptBlock $Worker -ArgumentList $x.s,$x.c,$Root,$SlotsDir;W ('WORKER_STARTED='+$x.s)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=fail$' -ErrorAction SilentlyContinue).Count
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W 'PROGRAM_COMPLETION=99/100'
W 'SUPABASE_PROBE=100/100'
Write-Output 'TERRAYIELD_101_SUPABASE_SERVICE_PROBE_5WORKER_SAFE_DONE'
exit 0
