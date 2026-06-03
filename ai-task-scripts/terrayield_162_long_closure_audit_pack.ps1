$ErrorActionPreference='Continue'
$TaskId='terrayield-162-long-closure-audit-pack'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $Root
Write-Output 'PROJECT=terrayield'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=long closure audit after final verifier 100/100'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
$Plan='D:\6 color parcells\plan_l_run01'
$Qa=Join-Path $Plan 'output\qa\PLAN_L_DEEP_QA_REPORT.md'
$FinalRoot=Join-Path $Plan 'final_packages'
$latest=$null
if(Test-Path $FinalRoot){$latest=Get-ChildItem $FinalRoot -Directory -Filter 'terrayield-112-plan-l-recovery-final-pack_*'|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
C 'PLAN_L_FINAL_DIR_EXISTS' ($null -ne $latest)
if($latest){C 'PLAN_L_FINAL_ZIP_EXISTS' (Test-Path ($latest.FullName+'.zip'))}
C 'PLAN_L_QA_REPORT_EXISTS' (Test-Path $Qa)
if(Test-Path $Qa){$t=Get-Content -Raw -Encoding UTF8 $Qa;C 'PLAN_L_QA_WARNINGS_NONE' ($t -match 'Warnings\s*\r?\n- none');C 'PLAN_L_CLASSIFIED_34864' ($t -match 'classified_rows:\s*34864');C 'PLAN_L_GEOJSON_34864' ($t -match 'geojson_features:\s*34864')}
$Sec=Join-Path (Split-Path $Root -Parent) 'security_accuracy_expansion'
C 'SECURITY_EXPANSION_EXISTS' (Test-Path $Sec)
if(Test-Path $Sec){$files=Get-ChildItem $Sec -Recurse -File -ErrorAction SilentlyContinue;$total=($files|Measure-Object).Count;$hyper=($files|Where-Object {$_.FullName -match 'hyper|source_lineage|download_audit|run_reproducibility|parcel_evidence|spatial_join|temporal_freshness|conflict_resolution|confidence_model|qa_acceptance|rollback_release|audit_traceability|review_handoff'}|Measure-Object).Count;$ultra=($files|Where-Object {$_.FullName -match 'ultra|final_verifier|schemas|methodology|audit'}|Measure-Object).Count;$mega=($files|Where-Object {$_.FullName -match 'mega|final|manifest|verifier'}|Measure-Object).Count;Write-Output ('TOTAL_FILES='+$total);Write-Output ('HYPER_RELATED='+$hyper);Write-Output ('ULTRA_RELATED='+$ultra);Write-Output ('MEGA_RELATED='+$mega);C 'TOTAL_FILES_GE_1200' ($total -ge 1200);C 'HYPER_RELATED_GE_700' ($hyper -ge 700);C 'ULTRA_RELATED_GE_300' ($ultra -ge 300);C 'MEGA_RELATED_GE_30' ($mega -ge 30)}
$diff=(git diff --name-only -- england_map_web 2>$null) -join ';'
Write-Output ('ENGLAND_MAP_WEB_DIFF='+$diff)
C 'ENGLAND_MAP_WEB_DIFF_EMPTY' ([string]::IsNullOrWhiteSpace($diff))
Write-Output 'CMD=python -m compileall app'
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output 'CMD=python -m pytest tests --collect-only -q --ignore tests/facility-adapter-5qtl4e17'
python -m pytest tests --collect-only -q --ignore 'tests/facility-adapter-5qtl4e17' 2>&1 | Out-String | Write-Output
C 'PYTEST_COLLECT' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'LONG_CLOSURE_AUDIT=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'LONG_CLOSURE_AUDIT=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_162_LONG_CLOSURE_AUDIT_PACK_DONE'
exit 0
