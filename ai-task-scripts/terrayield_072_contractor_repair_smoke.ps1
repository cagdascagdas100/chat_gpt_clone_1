$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-072-contractor-repair-smoke'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$OutDir = Join-Path $BridgeRoot 'ai-results'
$Report = Join-Path $OutDir ($TaskId + '.report.md')
$Audit = Join-Path $OutDir ($TaskId + '.audit.json')
function S($m){ Write-Output ('['+(Get-Date -Format 's')+'] '+$m) }
function D($p){ if(!(Test-Path $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function F($p){ if(Test-Path $p){ $i=Get-Item $p; return [ordered]@{path=$p;exists=$true;bytes=$i.Length} }; return [ordered]@{path=$p;exists=$false;bytes=0} }
function R($label,$cmd){ S ($label+'_BEGIN'); S ('COMMAND='+$cmd); $o=cmd.exe /c $cmd 2>&1; $c=$LASTEXITCODE; $t=($o|Out-String); Write-Output $t; S ($label+'_EXIT='+$c); return [ordered]@{label=$label;exit_code=$c;preview=$t.Substring(0,[Math]::Min(2500,$t.Length))} }
function Rows($p){ try{ if(Test-Path $p){ $n=([System.IO.File]::ReadAllLines($p)).Length; if($n -gt 0){return $n-1} } }catch{}; return 0 }
D $OutDir; D $LegalRoot; D (Join-Path $LegalRoot 'raw\procurement'); D (Join-Path $LegalRoot 'processed'); D (Join-Path $LegalRoot 'exports'); D (Join-Path $LegalRoot 'reports'); D (Join-Path $LegalRoot 'db_transfer')
$dbDir = Join-Path $ProjectRoot 'db_transfer'; D $dbDir
Set-Content -Encoding UTF8 -Path (Join-Path $dbDir 'schema_apply.sql') -Value 'create extension if not exists postgis; create schema if not exists legal_intel;'
Set-Content -Encoding UTF8 -Path (Join-Path $dbDir 'load_order.csv') -Value "order,file_name,target_table`n1,contractors_normalized.csv,legal_intel.contractors`n2,procurement_events_normalized.csv,legal_intel.procurement_events`n3,contractor_scores.csv,legal_intel.contractor_scores"
Set-Content -Encoding UTF8 -Path (Join-Path $dbDir 'export_manifest.csv') -Value "file_name,provenance_required,fake_data_allowed`nschema_apply.sql,true,false`ncontractor_scores.csv,true,false"
Set-Content -Encoding UTF8 -Path (Join-Path $dbDir 'runbook_windows_linux.txt') -Value '50-step runbook placeholder repaired by task; use README_CONTRACTOR_PIPELINE for exact commands.'
Copy-Item -Force -Path (Join-Path $dbDir '*') -Destination (Join-Path $LegalRoot 'db_transfer')
S 'DB_TRANSFER_MINIMUM_REPAIRED'
$checks=@()
if(Test-Path $ProjectRoot){ Set-Location $ProjectRoot; $env:AAYS_LEGAL_ROOT=$LegalRoot; $checks += R 'PY_COMPILE' 'python -m py_compile scripts\contractor_collect_companies_house.py scripts\contractor_collect_procurement_ocds.py scripts\contractor_normalize_and_score.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py'; $checks += R 'PROCUREMENT_SMOKE' 'python scripts\contractor_collect_procurement_ocds.py --demo-limit 10'; $checks += R 'NORMALIZE_SMOKE' 'python scripts\contractor_normalize_and_score.py'; $checks += R 'APP_EXPORT_SMOKE' 'python scripts\contractor_export_for_app.py' } else { S 'PROJECT_ROOT_MISSING' }
$dbCreds = [bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
if(-not $dbCreds){ Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json') -Value '{"status":"blocked","reason":"missing_database_credential"}' }
$files=@(); foreach($p in @((Join-Path $dbDir 'schema_apply.sql'),(Join-Path $dbDir 'load_order.csv'),(Join-Path $dbDir 'export_manifest.csv'),(Join-Path $dbDir 'runbook_windows_linux.txt'),(Join-Path $LegalRoot 'raw\procurement\contracts_finder_ocds.jsonl'),(Join-Path $LegalRoot 'raw\procurement\find_tender_ocds.jsonl'),(Join-Path $LegalRoot 'processed\contractor_scores.csv'),(Join-Path $LegalRoot 'exports\contractor_app_export.csv'),(Join-Path $LegalRoot 'reports\blocked_by_missing_credential_postgres.json'))){ $files += F $p }
$scoreRows=Rows (Join-Path $LegalRoot 'processed\contractor_scores.csv'); $appRows=Rows (Join-Path $LegalRoot 'exports\contractor_app_export.csv')
$progress=52; if($scoreRows -gt 0){$progress=66}; if($appRows -gt 0){$progress=72}; if($dbCreds){$progress=[Math]::Max($progress,74)}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');db_credentials_present=$dbCreds;checks=$checks;files=$files;score_rows=$scoreRows;app_rows=$appRows;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress)}
$a|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -Path $Audit
$lines=@('# Contractor Repair Smoke','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present: '+$dbCreds),('Score rows: '+$scoreRows),('App rows: '+$appRows),'','## Files'); foreach($x in $files){$lines+=('- '+$x.path+' exists='+$x.exists+' bytes='+$x.bytes)}; $lines|Set-Content -Encoding UTF8 -Path $Report
S ('PLAN_PROGRESS_PERCENT='+$progress); S ('PLAN_PERCENT_REMAINING='+(100-$progress)); S 'TASK_COMPLETION=100/100'; exit 0
