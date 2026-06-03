$ErrorActionPreference = "Continue"
$TaskId = "terrayield-110-plan-l-parallel-expansion"
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$Bridge = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$PlanBase = "D:\6 color parcells\plan_l_run01"
$ScriptDir = Join-Path $PlanBase "scripts"
$InputDir = Join-Path $PlanBase "input"
$OutputDir = Join-Path $PlanBase "output"
$LogDirPlan = Join-Path $PlanBase "logs"
$ResultDir = Join-Path $Bridge "ai-results"
$BeatDir = Join-Path $Bridge "ai-heartbeat"
$RunDir = Join-Path $Bridge (".aays_runs\" + $TaskId + "_" + $Run)
$SlotsDir = Join-Path $RunDir "slots"
New-Item -ItemType Directory -Force -Path $ResultDir,$BeatDir,$RunDir,$SlotsDir,$ScriptDir,$OutputDir,$LogDirPlan | Out-Null
$Summary = Join-Path $ResultDir ($TaskId + "-summary.md")
$Status = Join-Path $ResultDir ($TaskId + "-status.txt")
$Score = Join-Path $ResultDir ($TaskId + "-scorecard.csv")
function W([string]$x) { Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x }
function B([string]$s) { @("# AAYS Heartbeat", "TASK_ID=" + $TaskId, "STATUS=" + $s, "UPDATED=" + (Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $BeatDir ($TaskId + ".md")) }
function Slot([string]$name, [string]$result, [string[]]$lines) { @("# " + $name, "TASK_ID=" + $TaskId, "RESULT=" + $result, "UPDATED=" + (Get-Date -Format s), "") + $lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir ($name + ".md")) }
function Count-CsvRows([string]$p) { try { if(Test-Path $p) { return @((Import-Csv -LiteralPath $p)).Count } } catch { return -1 } return 0 }
B "starting"
W "# TerraYield 110 Plan L Parallel Expansion"
W "MODE=single_devam_multi_slot_parallel; writes_and_runs_plan_l; safe_local_only"
W ("BRIDGE=" + $Bridge)
W ("PLAN_BASE=" + $PlanBase)

$preJobs = @()
$preJobs += Start-Job -Name "pre_bridge_git" -ScriptBlock { param($Bridge,$SlotsDir,$TaskId) Set-Location $Bridge; $out = git status --short 2>&1 | Out-String; @("# pre_bridge_git","TASK_ID=$TaskId","RESULT=done","",$out) | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "pre_bridge_git.md") } -ArgumentList $Bridge,$SlotsDir,$TaskId
$preJobs += Start-Job -Name "pre_plan_paths" -ScriptBlock { param($PlanBase,$InputDir,$OutputDir,$SlotsDir,$TaskId) $lines=@("PlanBase="+$PlanBase,"InputExists="+(Test-Path $InputDir),"OutputExists="+(Test-Path $OutputDir)); @("# pre_plan_paths","TASK_ID=$TaskId","RESULT=done","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "pre_plan_paths.md") } -ArgumentList $PlanBase,$InputDir,$OutputDir,$SlotsDir,$TaskId
$preJobs += Start-Job -Name "pre_input_inventory" -ScriptBlock { param($InputDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @("london_parcels_geometry.geojson","market_3110.csv","voa_london.csv")){ $p=Join-Path $InputDir $n; if(Test-Path $p){$b=(Get-Item $p).Length}else{$b=0}; $lines += ($n + " exists=" + (Test-Path $p) + " bytes=" + $b) }; @("# pre_input_inventory","TASK_ID=$TaskId","RESULT=done","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "pre_input_inventory.md") } -ArgumentList $InputDir,$SlotsDir,$TaskId
Wait-Job $preJobs -Timeout 120 | Out-Null
Receive-Job $preJobs -ErrorAction SilentlyContinue | Out-Null
Remove-Job $preJobs -Force -ErrorAction SilentlyContinue
B "preflight_done"

$SourceScript = Join-Path $Bridge "ai-task-scripts\build_london_6color_plan_l.py"
$TargetScript = Join-Path $ScriptDir "build_london_6color.py"
if(Test-Path $TargetScript) { Copy-Item -Force $TargetScript (Join-Path $ScriptDir ("build_london_6color.backup_" + $Run + ".py")) }
if(Test-Path $SourceScript) {
  Copy-Item -Force $SourceScript $TargetScript
  Slot "slot_01_script_written" "completed" @("source=" + $SourceScript, "target=" + $TargetScript, "bytes=" + (Get-Item $TargetScript).Length)
} else {
  Slot "slot_01_script_written" "blocked" @("source_missing=" + $SourceScript)
}

B "running_plan_l_classifier"
$PythonExe = $null
foreach($candidate in @("python","py")) { $cmd = Get-Command $candidate -ErrorAction SilentlyContinue; if($cmd) { $PythonExe = $cmd.Source; break } }
$RunLog = Join-Path $RunDir "plan_l_python_run.log"
$RunExit = 900
if($null -eq $PythonExe) {
  "NO_PYTHON_FOUND" | Set-Content -Encoding UTF8 $RunLog
  Slot "slot_02_python_run" "blocked" @("python_exe=not_found")
} elseif(!(Test-Path $TargetScript)) {
  "TARGET_SCRIPT_MISSING" | Set-Content -Encoding UTF8 $RunLog
  Slot "slot_02_python_run" "blocked" @("target_script_missing=" + $TargetScript)
} else {
  try {
    if($PythonExe.ToLower().EndsWith("py.exe")) { & $PythonExe -3 $TargetScript 2>&1 | Tee-Object -FilePath $RunLog } else { & $PythonExe $TargetScript 2>&1 | Tee-Object -FilePath $RunLog }
    $RunExit = $LASTEXITCODE
  } catch {
    $RunExit = 901
    ("RUN_EXCEPTION=" + $_.Exception.Message) | Add-Content -Encoding UTF8 $RunLog
  }
  Slot "slot_02_python_run" $(if($RunExit -eq 0){"completed"}else{"blocked"}) @("python_exe=" + $PythonExe, "exit_code=" + $RunExit, "run_log=" + $RunLog)
}
B "post_run_parallel_qa"

$jobs = @()
$jobs += Start-Job -Name "slot_03_output_presence" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $names=@("london_6color.geojson","london_6color.csv","london_6color_summary.csv","london_6color_confidence_summary.csv"); $lines=@(); foreach($n in $names){ $p=Join-Path $OutputDir $n; if(Test-Path $p){$b=(Get-Item $p).Length}else{$b=0}; $lines += ($n + " exists=" + (Test-Path $p) + " bytes=" + $b) }; @("# slot_03_output_presence","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_03_output_presence.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_04_class_summary" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir "london_6color_summary.csv"; $lines=@(); if(Test-Path $p){ $rows=Import-Csv $p; foreach($r in $rows){ $lines += ($r.class + "=" + $r.count) } } else { $lines += "summary_missing" }; @("# slot_04_class_summary","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_04_class_summary.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_05_confidence_summary" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir "london_6color_confidence_summary.csv"; $lines=@(); if(Test-Path $p){ $rows=Import-Csv $p; foreach($r in $rows){ $lines += ("confidence_" + $r.confidence + "=" + $r.count) } } else { $lines += "confidence_summary_missing" }; @("# slot_05_confidence_summary","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_05_confidence_summary.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_06_csv_schema" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir "london_6color.csv"; $lines=@(); if(Test-Path $p){ $first=Get-Content -LiteralPath $p -Encoding UTF8 -TotalCount 1; $count=@(Import-Csv $p).Count; $lines += "rows="+$count; $lines += "header="+$first } else { $lines += "csv_missing" }; @("# slot_06_csv_schema","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_06_csv_schema.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_07_geojson_schema" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir "london_6color.geojson"; $lines=@(); if(Test-Path $p){ try{ $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; $lines += "features="+$j.features.Count; if($j.features.Count -gt 0){ $props=$j.features[0].properties.PSObject.Properties.Name -join ","; $lines += "sample_properties="+$props } }catch{ $lines += "geojson_parse_error="+$_.Exception.Message } } else { $lines += "geojson_missing" }; @("# slot_07_geojson_schema","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_07_geojson_schema.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_08_input_counts" -ScriptBlock { param($InputDir,$SlotsDir,$TaskId) $lines=@(); foreach($n in @("market_3110.csv","voa_london.csv")){ $p=Join-Path $InputDir $n; if(Test-Path $p){ try{ $lines += ($n + "_rows=" + @((Import-Csv $p)).Count) }catch{ $lines += ($n + "_rows=parse_error") } } else { $lines += ($n + "=missing_optional_or_required") } }; @("# slot_08_input_counts","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_08_input_counts.md") } -ArgumentList $InputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_09_mixed_policy" -ScriptBlock { param($OutputDir,$SlotsDir,$TaskId) $p=Join-Path $OutputDir "london_6color_summary.csv"; $mixed="unknown"; if(Test-Path $p){ $row=Import-Csv $p | Where-Object { $_.class -eq "Karma" } | Select-Object -First 1; if($row){ $mixed=$row.count } }; $lines=@("mixed_count="+$mixed,"policy=Karma only when residential and retail signals co-exist or explicit stacked-use phrase appears"); @("# slot_09_mixed_policy","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_09_mixed_policy.md") } -ArgumentList $OutputDir,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_10_log_tail" -ScriptBlock { param($LogDirPlan,$SlotsDir,$TaskId) $p=Join-Path $LogDirPlan "build.log"; $lines=@(); if(Test-Path $p){ $lines = Get-Content -Tail 80 -Encoding UTF8 $p } else { $lines += "build_log_missing" }; @("# slot_10_log_tail","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_10_log_tail.md") } -ArgumentList $LogDirPlan,$SlotsDir,$TaskId
$jobs += Start-Job -Name "slot_11_runner_artifacts" -ScriptBlock { param($RunDir,$SlotsDir,$TaskId,$RunLog) $lines=@("run_dir="+$RunDir,"run_log="+$RunLog); if(Test-Path $RunLog){ $lines += "run_log_bytes="+(Get-Item $RunLog).Length }; @("# slot_11_runner_artifacts","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_11_runner_artifacts.md") } -ArgumentList $RunDir,$SlotsDir,$TaskId,$RunLog
$jobs += Start-Job -Name "slot_12_next_actions" -ScriptBlock { param($SlotsDir,$TaskId) $lines=@("NEXT_ACTION=Read slot outputs and improve evidence joins if needed","NEXT_ACTION_2=If VOA has no parcel key, do not broad-match by borough","NEXT_COMMAND=devam et"); @("# slot_12_next_actions","TASK_ID=$TaskId","RESULT=completed","")+$lines | Set-Content -Encoding UTF8 (Join-Path $SlotsDir "slot_12_next_actions.md") } -ArgumentList $SlotsDir,$TaskId
Wait-Job $jobs -Timeout 900 | Out-Null
Receive-Job $jobs -ErrorAction SilentlyContinue | Out-Null
Remove-Job $jobs -Force -ErrorAction SilentlyContinue

$classSummary = Join-Path $OutputDir "london_6color_summary.csv"
$confSummary = Join-Path $OutputDir "london_6color_confidence_summary.csv"
$csvOut = Join-Path $OutputDir "london_6color.csv"
$geoOut = Join-Path $OutputDir "london_6color.geojson"
$rowsOut = Count-CsvRows $csvOut
$geoOk = Test-Path $geoOut
$summaryOk = Test-Path $classSummary
$confOk = Test-Path $confSummary
@("metric,value", "python_exit,$RunExit", "output_rows,$rowsOut", "geojson_exists,$geoOk", "summary_exists,$summaryOk", "confidence_summary_exists,$confOk", "parallel_slots,12") | Set-Content -Encoding UTF8 $Score
W "## Consolidated status"
W ("PYTHON_EXIT=" + $RunExit)
W ("OUTPUT_ROWS=" + $rowsOut)
W ("GEOJSON_EXISTS=" + $geoOk)
W ("SUMMARY_EXISTS=" + $summaryOk)
W ("CONFIDENCE_SUMMARY_EXISTS=" + $confOk)
if(Test-Path $classSummary) { W "## Class summary"; Get-Content -Encoding UTF8 $classSummary | ForEach-Object { W $_ } }
if(Test-Path $confSummary) { W "## Confidence summary"; Get-Content -Encoding UTF8 $confSummary | ForEach-Object { W $_ } }
$result = if($RunExit -eq 0 -and $geoOk -and $summaryOk -and $confOk){"completed_plan_l_parallel_expansion"}else{"needs_attention_plan_l_parallel_expansion"}
@(
  "TASK=" + $TaskId,
  "RESULT=" + $result,
  "PYTHON_EXIT=" + $RunExit,
  "OUTPUT_ROWS=" + $rowsOut,
  "RUN_DIR=" + $RunDir,
  "SLOTS_DIR=" + $SlotsDir,
  "SCRIPT_PATH=" + $TargetScript,
  "OUTPUT_GEOJSON=" + $geoOut,
  "OUTPUT_CSV=" + $csvOut,
  "SUMMARY=" + $classSummary,
  "CONFIDENCE_SUMMARY=" + $confSummary,
  "NEXT_COMMAND=devam et"
) | Set-Content -Encoding UTF8 $Status
B "finished"
W "NEXT_COMMAND=devam et"
exit 0
