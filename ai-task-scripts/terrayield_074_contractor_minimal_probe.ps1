$ErrorActionPreference='Continue'
$TaskId='terrayield-074-contractor-minimal-probe'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,$LegalRoot,(Join-Path $LegalRoot 'reports') | Out-Null
function Info($p){ if(Test-Path $p){ $i=Get-Item $p; return @{path=$p; exists=$true; bytes=$i.Length} }; return @{path=$p; exists=$false; bytes=0} }
$script1=Join-Path $ProjectRoot 'scripts\contractor_collect_procurement_ocds.py'
$script2=Join-Path $ProjectRoot 'scripts\contractor_normalize_and_score.py'
$script3=Join-Path $ProjectRoot 'scripts\contractor_export_for_app.py'
$checks=@()
if((Test-Path $script1) -and (Test-Path $script2) -and (Test-Path $script3)){
  Push-Location $ProjectRoot
  $env:AAYS_LEGAL_ROOT=$LegalRoot
  $compileOut = & python -m py_compile $script1 $script2 $script3 2>&1
  $checks += @{name='compile'; exit=$LASTEXITCODE; output=($compileOut|Out-String)}
  $helpOut = & python $script1 --help 2>&1
  $checks += @{name='procurement_help'; exit=$LASTEXITCODE; output=($helpOut|Out-String)}
  Pop-Location
}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
if(-not $dbCreds){ '{"status":"blocked","reason":"missing_database_credential"}' | Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') }
$files=@(Info $script1,Info $script2,Info $script3,Info (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json'))
$progress=56
if(@($checks|Where-Object{$_.name -eq 'compile' -and $_.exit -eq 0}).Count -gt 0){$progress=58}
$a=@{task_id=$TaskId; status='completed'; generated_at=(Get-Date).ToString('s'); db_credentials_present=$dbCreds; checks=$checks; files=$files; plan_progress_percent=$progress; plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir ($TaskId+'.audit.json'))
Write-Output ('PLAN_PROGRESS_PERCENT='+$progress)
Write-Output ('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
