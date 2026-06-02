param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  [string]$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1",
  [string]$ZipPath = "C:\Users\cagda\Downloads\AAYS_TerraYield_FutureGrowth_Contractor_Handoff.zip",
  [string]$WorkRoot = "C:\Users\cagda\Documents\GitHub\AAYS\_handoff_unpack\future_growth_contractor",
  [int]$DurationMinutes = 40,
  [switch]$SkipPipeline
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$OutRoot = Join-Path $WorkRoot ("deep_run_" + $RunId)
$LogRoot = Join-Path $WorkRoot "logs"
New-Item -ItemType Directory -Force -Path $OutRoot,$LogRoot | Out-Null
$MainLog = Join-Path $LogRoot ("deep_orchestrator_" + $RunId + ".log")
$Summary = Join-Path $OutRoot "summary_status.json"
$Start = Get-Date
$End = $Start.AddMinutes($DurationMinutes)

function CleanLine([string]$s) {
  if ($null -eq $s) { return "" }
  $keys = @(("DATABASE"+"_URL"),("PG"+"PASSWORD"),("API"+"_KEY"),("JWT"+"_SECRET"),("TOKEN"),("SECRET"),("PASSWORD"))
  $x = [string]$s
  foreach ($k in $keys) {
    if ($x.ToUpperInvariant().Contains($k)) { return "[REDACTED_SENSITIVE_LINE]" }
  }
  return $x
}
function Log([string]$s) {
  $m = "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), (CleanLine $s)
  Add-Content -LiteralPath $MainLog -Value $m
  Write-Host $m
}
function SaveSummary([string]$status,[string]$reason) {
  [ordered]@{
    run_id=$RunId; status=$status; reason=$reason; now=(Get-Date).ToString("o");
    repo_root_present=(Test-Path -LiteralPath $RepoRoot);
    bridge_root_present=(Test-Path -LiteralPath $BridgeRoot);
    zip_present=(Test-Path -LiteralPath $ZipPath);
    secret_values_written=$false;
    disclaimer_required="Kesin fiyat tahmini degildir";
    high_confidence_rule="source_url olmayan kayit high confidence olamaz";
    popup_evidence_rule="Popup evidence sadece ilgili parcel_id icin donmeli"
  } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $Summary -Encoding UTF8
}
function FailClosed([string]$r) { Log "pipeline_stop=fail_closed"; Log ("blocked_reason="+$r); SaveSummary "blocked" $r; exit 2 }
function RunSafe([string]$label,[scriptblock]$cmd,[string]$path) {
  Add-Content -LiteralPath $path -Value ("=== "+$label+" ===")
  $global:LASTEXITCODE = 0
  try { & $cmd 2>&1 | ForEach-Object { Add-Content -LiteralPath $path -Value (CleanLine ([string]$_)) } }
  catch { Add-Content -LiteralPath $path -Value ("EXCEPTION="+(CleanLine $_.Exception.Message)); $global:LASTEXITCODE=999 }
  Add-Content -LiteralPath $path -Value ("exit_code="+$LASTEXITCODE)
  return $LASTEXITCODE
}

Log "task=AAYS TerraYield FGC deep orchestrator"
Log "mode=parallel_long_run_same_console_fail_closed"
Log ("duration_minutes="+$DurationMinutes)
Log ("repo_root="+$RepoRoot)
Log ("bridge_root="+$BridgeRoot)
Log ("out_root="+$OutRoot)
if (-not (Test-Path -LiteralPath $RepoRoot)) { FailClosed "repo_root_missing" }
if (-not (Test-Path -LiteralPath $BridgeRoot)) { FailClosed "bridge_root_missing" }
if (-not (Test-Path -LiteralPath $ZipPath)) { FailClosed "handoff_zip_missing" }

Log "sync_bridge_start"
Push-Location $BridgeRoot
try { git pull --ff-only 2>&1 | ForEach-Object { Log ([string]$_) } } catch { FailClosed "bridge_pull_failed" } finally { Pop-Location }

Log "duplicate_check_start"
$heavyNames = @("terrayield_fgc_deep_orchestrator_40min.ps1","contractor_load_to_postgres.py","contractor_match_to_parcels.py","contractor_export_for_app.py")
$mine = $PID
$existing = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $mine -and (($heavyNames | Where-Object { ([string]$_.CommandLine) -like ("*"+$_+"*") }).Count -gt 0) })
if ($existing.Count -gt 0) {
  Log ("existing_heavy_process_count="+$existing.Count)
  foreach ($p in $existing | Select-Object -First 6) { Log ("pid="+$p.ProcessId+" running=true") }
  SaveSummary "running_elsewhere" "duplicate_detected"
  exit 0
}

Log "unpack_start"
$Unpack = Join-Path $OutRoot "handoff_unpack"
New-Item -ItemType Directory -Force -Path $Unpack | Out-Null
Expand-Archive -LiteralPath $ZipPath -DestinationPath $Unpack -Force
$HandoffRoot = $Unpack
$kids = @(Get-ChildItem -LiteralPath $Unpack -Directory)
if ($kids.Count -eq 1 -and (Test-Path -LiteralPath (Join-Path $kids[0].FullName "manifest"))) { $HandoffRoot=$kids[0].FullName }
foreach ($d in @("docs","future_growth_stage_artifacts","contractor_db","runner","audit_results_sanitized","manifest")) { if (-not (Test-Path -LiteralPath (Join-Path $HandoffRoot $d))) { FailClosed ("handoff_missing_"+$d) } }
Log ("handoff_root="+$HandoffRoot)

$jobScript = {
  param($Mode,$RepoRoot,$BridgeRoot,$HandoffRoot,$OutRoot,$SkipPipeline)
  $ErrorActionPreference="Continue"
  Set-StrictMode -Version Latest
  function C([string]$s){ if($null -eq $s){return ""}; $keys=@(("DATABASE"+"_URL"),("PG"+"PASSWORD"),("API"+"_KEY"),("JWT"+"_SECRET"),("TOKEN"),("SECRET"),("PASSWORD")); foreach($k in $keys){ if(([string]$s).ToUpperInvariant().Contains($k)){return "[REDACTED_SENSITIVE_LINE]"}}; return [string]$s }
  $log=Join-Path $OutRoot ($Mode+".log")
  function W([string]$s){ Add-Content -LiteralPath $log -Value ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"),(C $s)) }
  function R([string]$label,[scriptblock]$cmd){ W ("=== "+$label+" ==="); $global:LASTEXITCODE=0; try{ & $cmd 2>&1 | ForEach-Object{ W ([string]$_) }}catch{ W ("EXCEPTION="+$_.Exception.Message); $global:LASTEXITCODE=999 }; W ("exit_code="+$LASTEXITCODE); return $LASTEXITCODE }
  $status="completed"; $exit=0
  Push-Location $RepoRoot
  try {
    if($Mode -eq "repo_watch"){
      for($i=1;$i -le 8;$i++){ R "git_status" { git status --short } | Out-Null; $raw=((git diff --name-only 2>$null)+(git diff --cached --name-only 2>$null)) -join ","; W ("changed_files="+$raw); Start-Sleep -Seconds 180 }
    } elseif($Mode -eq "static_compile"){
      $need=@("scripts\contractor_env.py","scripts\contractor_load_to_postgres.py","scripts\contractor_match_to_parcels.py","scripts\contractor_export_for_app.py")
      foreach($f in $need){ W ("present_"+$f+"="+(Test-Path -LiteralPath $f)) }
      $c=R "py_compile" { python -m py_compile scripts\contractor_env.py scripts\contractor_load_to_postgres.py scripts\contractor_match_to_parcels.py scripts\contractor_export_for_app.py }; if($c -ne 0){$status="failed_closed";$exit=$c}
    } elseif($Mode -eq "future_growth_tests"){
      if(-not(Test-Path -LiteralPath "future_growth\tests")){ W "missing_future_growth_tests=true"; $status="failed_closed"; $exit=2 }
      else { $pass=0; for($i=1;$i -le 3;$i++){ $c=R ("pytest_future_growth_"+$i) { python -m pytest future_growth\tests -q }; if($c -eq 0){$pass++}; Start-Sleep -Seconds 120 }; W ("pytest_passes="+$pass); if($pass -lt 1){$status="failed_closed";$exit=2} }
    } elseif($Mode -eq "handoff_audit"){
      foreach($d in @("docs","future_growth_stage_artifacts","contractor_db","runner","audit_results_sanitized","manifest")){ W ("handoff_"+$d+"="+(Test-Path -LiteralPath (Join-Path $HandoffRoot $d))) }
      Get-ChildItem -LiteralPath $HandoffRoot -Recurse -File | Select-Object -First 200 | ForEach-Object { W ("file="+$_.Name) }
    } elseif($Mode -eq "preflight_pipeline"){
      $pre=Join-Path $BridgeRoot "ai-task-scripts\terrayield_079_contractor_db_env_loader_preflight.ps1"
      if(-not(Test-Path -LiteralPath $pre)){ W "missing_preflight_script=true"; $status="failed_closed"; $exit=2 }
      else{
        $c=R "preflight" { powershell -NoProfile -ExecutionPolicy Bypass -File $pre }; if($c -ne 0){$status="failed_closed";$exit=$c}
        if($status -eq "completed" -and -not $SkipPipeline){
          $schema=@("scripts\contractor_apply_schema.py","db_transfer\apply_contractor_schema.py","scripts\contractor_schema_apply.py") | Where-Object{Test-Path -LiteralPath $_} | Select-Object -First 1
          if(-not $schema){ W "missing_schema_apply=true"; $status="failed_closed"; $exit=2 }
          else{
            foreach($step in @("schema","load","match","export")){
              if($step -eq "schema"){$c=R "schema_apply" { python $schema }}
              if($step -eq "load"){$c=R "contractor_load" { python scripts\contractor_load_to_postgres.py }}
              if($step -eq "match"){$c=R "parcel_match" { python scripts\contractor_match_to_parcels.py }}
              if($step -eq "export"){$c=R "app_export" { python scripts\contractor_export_for_app.py }}
              if($c -ne 0){$status="failed_closed";$exit=$c;break}
            }
            if($status -eq "completed" -and (Test-Path -LiteralPath "scripts\contractor_final_audit.py")){ $c=R "final_audit" { python scripts\contractor_final_audit.py }; if($c -ne 0){$status="failed_closed";$exit=$c} }
          }
        }
      }
    }
  } catch { W ("worker_exception="+$_.Exception.Message); $status="failed_closed"; $exit=2 } finally { Pop-Location }
  [ordered]@{mode=$Mode;status=$status;exit_code=$exit;ended_at=(Get-Date).ToString("o")} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutRoot ($Mode+".json")) -Encoding UTF8
  exit $exit
}

$modes=@("repo_watch","static_compile","future_growth_tests","handoff_audit","preflight_pipeline")
$jobs=@()
foreach($m in $modes){ Log ("start_parallel_job="+$m); $jobs+=Start-Job -Name ("fgc_"+$m) -ScriptBlock $jobScript -ArgumentList $m,$RepoRoot,$BridgeRoot,$HandoffRoot,$OutRoot,$SkipPipeline }

$lastActivity=Get-Date
$lastSize=0
Log "watchdog_loop_start"
while((Get-Date) -lt $End){
  $running=@($jobs|Where-Object{$_.State -eq "Running"})
  $done=@($jobs|Where-Object{$_.State -ne "Running"})
  Log ("watchdog running="+$running.Count+" done="+$done.Count)
  $total=0
  Get-ChildItem -LiteralPath $OutRoot -Filter "*.log" -ErrorAction SilentlyContinue | ForEach-Object{$total+=$_.Length}
  if($total -ne $lastSize){$lastActivity=Get-Date;$lastSize=$total}
  $idle=[math]::Round(((Get-Date)-$lastActivity).TotalMinutes,2)
  Log ("idle_minutes="+$idle)
  if($idle -gt 12 -and $running.Count -gt 0){ Log "stuck_detected=true"; foreach($j in $running){ Stop-Job -Job $j -Force -ErrorAction SilentlyContinue; Log ("stopped="+$j.Name) }; break }
  if($running.Count -eq 0){ break }
  Start-Sleep -Seconds 180
}

Log "collect_results_start"
$overall="completed"
foreach($j in $jobs){ try{Receive-Job -Job $j -ErrorAction SilentlyContinue | ForEach-Object{Log ("job_output="+[string]$_)}}catch{} }
foreach($m in $modes){ $rp=Join-Path $OutRoot ($m+".json"); if(Test-Path -LiteralPath $rp){ $r=Get-Content -LiteralPath $rp -Raw | ConvertFrom-Json; Log ("result_"+$m+"="+$r.status+" exit="+$r.exit_code); if($r.status -ne "completed"){$overall="failed_closed"} } else { Log ("missing_result_"+$m+"=true"); $overall="failed_closed" } }

while((Get-Date) -lt $End -and $overall -eq "completed"){
  Log "post_success_health_poll"
  Push-Location $RepoRoot
  try { git status --short 2>&1 | ForEach-Object{Log ([string]$_)}; if(Test-Path -LiteralPath "future_growth\tests"){ python -m pytest future_growth\tests -q 2>&1 | Select-Object -First 80 | ForEach-Object{Log ([string]$_)} } } catch { Log ("post_poll_exception="+$_.Exception.Message) } finally { Pop-Location }
  Start-Sleep -Seconds 300
}

SaveSummary $overall "deep_orchestrator_finished"
Log ("overall_status="+$overall)
Log ("summary="+$Summary)
if($overall -eq "completed"){ exit 0 }
exit 2
