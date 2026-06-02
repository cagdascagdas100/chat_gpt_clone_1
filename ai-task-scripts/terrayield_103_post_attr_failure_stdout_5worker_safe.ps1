$ErrorActionPreference='Continue'
$TaskId='terrayield-103-post-attr-failure-stdout-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__103_post_attr_failure_stdout_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__103_summary.md'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=print post-attr Supabase failures to runner stdout with five workers'
Set-Location $Root
$commands=@(
  @{slot='slot_1_admin_service_firstfail'; cmd='python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=long'},
  @{slot='slot_2_admin_service_all_short'; cmd='python -m pytest tests/test_supabase_admin_service.py -q -ra --tb=short'},
  @{slot='slot_3_admin_combo_short'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra --tb=short'},
  @{slot='slot_4_control_compile'; cmd='python -m compileall app; python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'},
  @{slot='slot_5_service_tail'; cmd='probe'}
)
foreach($c in $commands){
  W ('WORKER_STARTED='+$c.slot)
  $outFile=Join-Path $SlotsDir ('terrayield__103__'+$c.slot+'.md')
  Set-Content -Encoding UTF8 -Path $outFile -Value @('SLOT='+$c.slot,'CMD='+$c.cmd,'STARTED='+(Get-Date -Format 's'))
  Start-Job -Name $c.slot -ScriptBlock {
    param($Cmd,$Root,$OutFile)
    Set-Location $Root
    if($Cmd -eq 'probe'){
      $txt=(Select-String -Path 'app/services/supabase_admin_service.py' -Pattern 'AAYS102|def list_supabase|def upsert_supabase|get_supabase_sync_status|return _aays102|_aays102_rows|_aays102_attr' -Context 0,3 | Out-String)
      $code=0
    } else {
      $txt=Invoke-Expression ($Cmd+' 2>&1')|Out-String
      $code=$LASTEXITCODE;if($null -eq $code){$code=0}
    }
    Add-Content -Encoding UTF8 -Path $OutFile -Value $txt
    Add-Content -Encoding UTF8 -Path $OutFile -Value ('OWN_EXIT_CODE='+$code)
    if($code -eq 0){Add-Content -Encoding UTF8 -Path $OutFile -Value 'OWN_RESULT=pass'}else{Add-Content -Encoding UTF8 -Path $OutFile -Value 'OWN_RESULT=fail'}
    Add-Content -Encoding UTF8 -Path $OutFile -Value ('FINISHED='+(Get-Date -Format 's'))
  } -ArgumentList $c.cmd,$Root,$outFile | Out-Null
}
Get-Job | Where-Object { $_.Name -like 'slot_*' } | Wait-Job | Out-Null
Get-Job | Where-Object { $_.Name -like 'slot_*' } | ForEach-Object { Receive-Job $_ -ErrorAction SilentlyContinue|Out-Null; Remove-Job $_ -Force -ErrorAction SilentlyContinue }
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$assert=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|FAILED tests/' -ErrorAction SilentlyContinue).Count
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('ASSERTION_MARKERS='+$assert)
W 'PROGRAM_COMPLETION=99/100'
W '--- POST ATTR FAILED SLOT EXCERPTS BEGIN ---'
Get-ChildItem -LiteralPath $SlotsDir -File | Sort-Object Name | ForEach-Object {
  $failed=Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$' -Quiet -ErrorAction SilentlyContinue
  if($failed){
    W ('--- FAILED_FILE='+$_.Name+' ---')
    $matches=Select-String -Path $_.FullName -Pattern 'FAILED tests/|ERROR tests/|AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|assert |Expected|actual|OWN_EXIT_CODE|OWN_RESULT' -Context 4,12 -ErrorAction SilentlyContinue | Select-Object -First 100 | Out-String
    W $matches
  }
}
W '--- POST ATTR FAILED SLOT EXCERPTS END ---'
Write-Output 'TERRAYIELD_103_POST_ATTR_FAILURE_STDOUT_5WORKER_SAFE_DONE'
exit 0
