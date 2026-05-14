$ErrorActionPreference = 'Stop'
$TaskId = 'aays-053-auto-clean-cluster-db-dryrun-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportPath = Join-Path $ResultDir "aays-053-auto-clean-cluster-db-dryrun-$Stamp.md"
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
function AddR([string]$m){ $m | Add-Content -Encoding UTF8 $ReportPath }
function RunNative([string]$label,[string]$exe,[string[]]$args){
  Write-Host $label -ForegroundColor Cyan
  AddR ''; AddR "## $label"
  $out = & $exe @args 2>&1
  $code = $LASTEXITCODE
  if($out){ $out | Tee-Object -FilePath $ReportPath -Append }
  AddR "EXIT_CODE: $code"
  if($code -ne 0){ throw "$label failed exit=$code" }
  return $out
}
function TestPortFree([int]$Port){
  try { $c = New-Object System.Net.Sockets.TcpClient; $iar=$c.BeginConnect('127.0.0.1',$Port,$null,$null); $ok=$iar.AsyncWaitHandle.WaitOne(300,$false); if($ok){$c.EndConnect($iar);$c.Close(); return $false}; $c.Close(); return $true } catch { return $true }
}
$PgBinCandidates = @('C:\Program Files\PostgreSQL\18\bin','C:\Program Files\PostgreSQL\17\bin','C:\Program Files\PostgreSQL\16\bin','C:\Program Files\PostgreSQL\15\bin')
$PgBin = $PgBinCandidates | Where-Object { Test-Path (Join-Path $_ 'psql.exe') } | Select-Object -First 1
if(-not $PgBin){ throw 'PostgreSQL bin not found' }
$Psql = Join-Path $PgBin 'psql.exe'
$Initdb = Join-Path $PgBin 'initdb.exe'
$PgCtl = Join-Path $PgBin 'pg_ctl.exe'
$Createdb = Join-Path $PgBin 'createdb.exe'
foreach($t in @($Psql,$Initdb,$PgCtl,$Createdb)){ if(!(Test-Path $t)){ throw "Missing tool: $t" } }
$Port = 5434
foreach($p in 5434..5460){ if(TestPortFree $p){ $Port=$p; break } }
$ClusterDir = "E:\AAYS_DATA\postgresql18_aays_auto_cluster_$Stamp"
$LogDir = 'E:\AAYS_DATA\postgresql18_aays_logs'
$LogFile = Join-Path $LogDir "postgresql-aays-auto-$Stamp.log"
New-Item -ItemType Directory -Force -Path $ClusterDir,$LogDir | Out-Null
$OutDir = 'E:\AAYS_DATA\land_sales\final_outputs'
$Schema = Join-Path $OutDir 'DB_SCHEMA_APPLY.sql'
$Csv = Join-Path $OutDir 'stg_land_sales_50step_db_ready.csv'
$CsvPg = $Csv -replace '\\','/'
foreach($f in @($Schema,$Csv)){ if(!(Test-Path $f)){ throw "Missing file: $f" } }
"# AAYS 053 Auto Clean Cluster DB Dry-run" | Set-Content -Encoding UTF8 $ReportPath
AddR "Generated: $(Get-Date -Format s)"
AddR 'mode: auto_clean_isolated_cluster_trust_local_only'
AddR "pg_host: 127.0.0.1"
AddR "pg_port: $Port"
AddR "cluster_dir: $ClusterDir"
AddR "log_file: $LogFile"
AddR 'no_secret_required: true'
RunNative '01 initdb trust locale C' $Initdb @('-D',$ClusterDir,'-U','postgres','--encoding=UTF8','--locale=C','--auth=trust')
RunNative '02 start cluster local only' $PgCtl @('-D',$ClusterDir,'-l',$LogFile,'-o',"-p $Port -h 127.0.0.1",'start')
Start-Sleep -Seconds 5
RunNative '03 psql version' $Psql @('--version')
RunNative '04 connection test' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','postgres','-v','ON_ERROR_STOP=1','-c','SELECT current_database(), current_user, version();')
RunNative '05 create database aays' $Createdb @('-h','127.0.0.1','-p',"$Port",'-U','postgres','aays')
RunNative '06 apply schema' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-f',$Schema)
RunNative '07 truncate staging' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-c','TRUNCATE aays_land_sales.stg_land_sales_3110;')
$copy = "\copy aays_land_sales.stg_land_sales_3110 FROM '$CsvPg' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')"
RunNative '08 import csv' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-c',$copy)
RunNative '09 count staging rows' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-c','SELECT COUNT(*) AS staging_rows FROM aays_land_sales.stg_land_sales_3110;')
RunNative '10 count verified polygon non-empty' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-c',"SELECT COUNT(*) AS verified_polygon_non_empty FROM aays_land_sales.stg_land_sales_3110 WHERE NULLIF(TRIM(verified_polygon_geojson), '') IS NOT NULL;")
RunNative '11 geometry verdict distribution' $Psql @('-h','127.0.0.1','-p',"$Port",'-U','postgres','-d','aays','-v','ON_ERROR_STOP=1','-c','SELECT geometry_verdict, COUNT(*) FROM aays_land_sales.stg_land_sales_3110 GROUP BY geometry_verdict ORDER BY COUNT(*) DESC;')
AddR ''; AddR 'plan_progress_percent: 90'; AddR 'AAYS_053_AUTO_CLEAN_CLUSTER_DB_DRYRUN_DONE=true'
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 aays_053_auto_clean_cluster_db_dryrun_done progress=90'),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 $HeartbeatPath
Write-Host "TERRAYIELD_TASK_DONE report=$ReportPath port=$Port"
exit 0
