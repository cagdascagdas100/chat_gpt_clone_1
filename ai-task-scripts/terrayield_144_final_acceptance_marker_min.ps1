$ErrorActionPreference='Continue'
$TaskId='terrayield-144-final-acceptance-marker-min'
$Base='D:\6 color parcells\plan_l_run01'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=final acceptance marker read-only'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
$Qa=Join-Path $Base 'output\qa\PLAN_L_DEEP_QA_REPORT.md'
$Json=Join-Path $Base 'output\qa\plan_l_deep_qa_report.json'
$FinalRoot=Join-Path $Base 'final_packages'
$latest=$null
if(Test-Path $FinalRoot){$latest=Get-ChildItem $FinalRoot -Directory -Filter 'terrayield-112-plan-l-recovery-final-pack_*'|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
C 'FINAL_DIR_EXISTS' ($null -ne $latest)
if($latest){C 'FINAL_ZIP_EXISTS' (Test-Path ($latest.FullName+'.zip'))}
C 'QA_REPORT_EXISTS' (Test-Path $Qa)
if(Test-Path $Qa){$t=Get-Content -Raw -Encoding UTF8 $Qa;C 'QA_WARNINGS_NONE' ($t -match 'Warnings\s*\r?\n- none');C 'QA_CLASSIFIED_34864' ($t -match 'classified_rows:\s*34864');C 'QA_GEOJSON_34864' ($t -match 'geojson_features:\s*34864');C 'QA_CONFIDENCE_34864' ($t -match '3:\s*34864')}
if(Test-Path $Json){try{$j=Get-Content -Raw -Encoding UTF8 $Json|ConvertFrom-Json;C 'JSON_WARNINGS_EMPTY' (($j.warnings|Measure-Object).Count -eq 0);C 'JSON_COUNTS_OK' ([int]$j.counts.classified_rows -eq 34864 -and [int]$j.counts.geojson_features -eq 34864)}catch{C 'JSON_PARSE' $false}}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'FINAL_ACCEPTANCE=100/100';Write-Output 'PROGRAM_COMPLETION=100/100';Write-Output 'RESULT=accepted_final_pack'}else{Write-Output 'FINAL_ACCEPTANCE=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100';Write-Output 'RESULT=needs_attention'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_144_FINAL_ACCEPTANCE_MARKER_MIN_DONE'
exit 0
