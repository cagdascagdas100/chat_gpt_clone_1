$ErrorActionPreference = 'Continue'

$ProjectName = 'AAYS_LAYER_PERF_BACKEND_READ_PATH_FIX'
$TaskId = 'aays-layer-perf-backend-read-path-fix-20260606'
$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$BaseUrl = 'http://127.0.0.1:8010'
$OutDir = Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606'
$RunnerOut = Join-Path $RepoRoot 'docs\chatgpt_status\runner_outputs'
$Latest = Join-Path $RunnerOut 'aays-layer-perf-backend-read-path-fix-latest.txt'

function New-Dir($p){ if(-not(Test-Path -LiteralPath $p)){ New-Item -ItemType Directory -Path $p -Force | Out-Null } }
function Write-Txt($p,$t){ New-Dir (Split-Path -Parent $p); Set-Content -LiteralPath $p -Value $t -Encoding UTF8 }

function Measure-One($name,$url,$runs,$timeout,$target){
  $rows=@();
  for($i=1;$i -le $runs;$i++){
    $sw=[Diagnostics.Stopwatch]::StartNew(); $status='ERR'; $bytes=0; $err=''
    try{
      $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec $timeout -Method GET
      $sw.Stop(); $status=[string][int]$r.StatusCode
      if($null -ne $r.RawContentStream){$bytes=[int64]$r.RawContentStream.Length}elseif($null -ne $r.Content){$bytes=[Text.Encoding]::UTF8.GetByteCount([string]$r.Content)}
    }catch{ $sw.Stop(); if($_.Exception.Message -match 'timeout|timed out'){$status='TIMEOUT'}; $err=$_.Exception.Message }
    $rows += [pscustomobject]@{run=$i;status=$status;ms=[math]::Round($sw.Elapsed.TotalMilliseconds,1);bytes=$bytes;error=$err}
  }
  $ok=@($rows|Where-Object{$_.status -match '^[23]\d\d$'}|Sort-Object ms); $p95='NA'
  if($ok.Count -gt 0){$idx=[math]::Ceiling(.95*$ok.Count)-1; if($idx -lt 0){$idx=0}; if($idx -ge $ok.Count){$idx=$ok.Count-1}; $p95=$ok[$idx].ms}
  $pass=($p95 -ne 'NA' -and [double]$p95 -le $target)
  $txt=@("[$name]","url=$url","target_ms=$target","p95_ms=$p95",('status='+$(if($pass){'PASS'}else{'FAIL'})))
  foreach($x in $rows){$txt += "run=$($x.run) status=$($x.status) ms=$($x.ms) bytes=$($x.bytes) error=$($x.error)"}
  return [pscustomobject]@{name=$name;pass=$pass;p95=$p95;text=($txt -join "`r`n")}
}

New-Dir $OutDir; New-Dir $RunnerOut
$RunnerReport=Join-Path $OutDir 'RUNNER_STATE_AND_QUEUE_REPORT.txt'
$BackendReport=Join-Path $OutDir 'BACKEND_READ_PATH_FIX_REPORT.txt'
$FrontendReport=Join-Path $OutDir 'FRONTEND_LAZY_LOAD_AND_PMTILES_REPORT.txt'
$PerfReport=Join-Path $OutDir 'POST_FIX_PERF_SMOKE.txt'
$ValidationReport=Join-Path $OutDir 'CHANGED_FILES_AND_VALIDATION.txt'

$rp=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{($_.CommandLine -like '*portable_queue_runner.ps1*') -or ($_.CommandLine -like '*Kalife*') -or ($_.CommandLine -like '*ai-queue*')})
$runnerCount=$rp.Count
$runnerStatus=if($runnerCount -eq 1){'one_runner_available'}elseif($runnerCount -eq 0){'no_runner_detected'}else{'multiple_runners_detected_blocked'}
Write-Txt $RunnerReport ((@("timestamp=$(Get-Date -Format s)","project_name=$ProjectName","task_id=$TaskId","runner_count=$runnerCount","status=$runnerStatus") + ($rp|ForEach-Object{"runner_pid=$($_.ProcessId) command=$($_.CommandLine)"}) + @('safety_flags=db_write_false,deploy_false,migration_false,ddl_false,fake_data_false,secret_print_false')) -join "`r`n")

$AppJs=Join-Path $RepoRoot 'england_map_web\app.js'
$val=@("timestamp=$(Get-Date -Format s)","project_name=$ProjectName","task_id=$TaskId")
if(Test-Path -LiteralPath $AppJs){
  $app=Get-Content -LiteralPath $AppJs -Raw -Encoding UTF8
  $val+='app_js_exists=PASS'
  $val+=('runtime_guard_present='+$(if($app.Contains('AAYS_LAYER_RUNTIME_GUARD_V1_START')){'PASS'}else{'FAIL'}))
  foreach($tok in @('/map/parcels','/map/listings','/map/sales-history/combined','/api/contractor/parcel','/cost/building-types/options','/cost/estimate/preview')){$val+=('contains_'+($tok -replace '[^a-zA-Z0-9]','_')+'='+$(if($app.Contains($tok)){'PASS'}else{'FAIL'}))}
  $node=Get-Command node -ErrorAction SilentlyContinue; if($node){$nodeOut=& node --check $AppJs 2>&1; $val+=('node_check='+$(if($LASTEXITCODE -eq 0){'PASS'}else{'FAIL '+$nodeOut}))}else{$val+='node_check=SKIP_NODE_NOT_FOUND'}
}else{$val+='app_js_exists=FAIL'}

$perf=@()
$perf+=Measure-One 'health' "$BaseUrl/health" 5 8 200
$perf+=Measure-One 'parcels_limit_200' "$BaseUrl/map/parcels?limit=200" 5 12 700
$perf+=Measure-One 'listings_limit_200' "$BaseUrl/map/listings?limit=200" 5 12 1200
$perf+=Measure-One 'sales_history_combined_limit_200' "$BaseUrl/map/sales-history/combined?limit=200" 5 12 1300
$perf+=Measure-One 'internet_access_limit_200' "$BaseUrl/map/internet-access?limit=200" 5 8 500
Write-Txt $PerfReport (($perf|ForEach-Object{$_.text}) -join "`r`n`r`n")

$allPerfPass=(($perf|Where-Object{-not $_.pass}).Count -eq 0)
$criticalPass=(($val -join "`n") -match 'app_js_exists=PASS' -and ($val -join "`n") -match 'runtime_guard_present=PASS')
if($runnerCount -gt 1){$status='blocked';$progress=65;$exact='multiple runner processes detected';$next='use only one canonical runner'}elseif(-not $criticalPass){$status='blocked';$progress=65;$exact='critical static validation failed';$next='fix static validation'}elseif($allPerfPass){$status='done';$progress=72;$exact='endpoint smoke passed';$next='run browser UI confirmation'}else{$status='blocked';$progress=65;$exact='endpoint performance still fails or runtime not ready';$next='apply safe backend read-path and frontend lazy-load fixes'}

Write-Txt $BackendReport "timestamp=$(Get-Date -Format s)`r`nproject_name=$ProjectName`r`ntask_id=$TaskId`r`nstatus=diagnosis_completed_no_db_change`r`nexact_blocker=$exact`r`ndb_write=false`r`nmigration=false`r`nddl=false`r`ndeploy=false"
Write-Txt $FrontendReport "timestamp=$(Get-Date -Format s)`r`nproject_name=$ProjectName`r`ntask_id=$TaskId`r`nstatus=diagnosis_completed`r`npmtiles_guard_expected=true`r`nlazy_load_required_for=listings,sales_history_combined"
$val += @("status=$status","exact_blocker=$exact","next_action=$next","completion_percent=$progress","changed_files=none_by_this_diagnostic_script","db_write=false","deploy=false","migration=false","ddl=false","secret_values_printed=false")
Write-Txt $ValidationReport ($val -join "`r`n")
Write-Txt $Latest "timestamp=$(Get-Date -Format s)`r`nproject_name=$ProjectName`r`ntask_id=$TaskId`r`nrunner_count=$runnerCount`r`noutput_files=$OutDir`r`nstatus=$status`r`nexact_blocker=$exact`r`nnext_action=$next`r`nwait_minutes=0`r`noverall_progress_percent=$progress`r`nsafety_flags=db_write_false,deploy_false,migration_false,ddl_false,fake_data_false,secret_print_false"

try{ Push-Location $RepoRoot; $git=Get-Command git -ErrorAction SilentlyContinue; if($git){ & git add 'docs/chatgpt_status/AAYS_LAYER_PERF_BACKEND_AUTO_FIX_20260606' 'docs/chatgpt_status/runner_outputs/aays-layer-perf-backend-read-path-fix-latest.txt'; & git commit -m 'add AAYS backend read path diagnostic reports'; & git push }; Pop-Location }catch{ Write-Txt (Join-Path $OutDir 'git_sync_blocker.txt') ('git_sync_blocker='+$_.Exception.Message) }
Get-Content -LiteralPath $Latest
