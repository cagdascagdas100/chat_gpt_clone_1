$ErrorActionPreference='Continue'
$TaskId='contractor-002-clean2-bridge-recovery-20260520'
$Bridge2='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Bridge1='C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ResultDir=Join-Path $Bridge2 'ai-results'
$ProgressDir=Join-Path $Bridge2 'ai-progress'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir | Out-Null
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
$Json=Join-Path $ResultDir ($TaskId+'.result.json')
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
function W($p,$m){Add-Content -LiteralPath $p -Encoding UTF8 -Value $m}
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# Contractor 002 CLEAN2 Bridge Recovery'
Set-Content -LiteralPath $Progress -Encoding UTF8 -Value '# Contractor 002 Recovery Progress'
$expected=@('contractor-002-long-watchdog-foundation-20260519.result.json','contractor-002-long-watchdog-foundation-20260519.report.md')
$copied=@();$seen=@();$warnings=@()
for($cycle=1;$cycle -le 8;$cycle++){
  W $Progress "cycle=$cycle utc=$((Get-Date).ToUniversalTime().ToString('o'))"
  W $Report "## cycle_$cycle"
  foreach($name in $expected){
    $src=Join-Path (Join-Path $Bridge1 'ai-results') $name
    $dst=Join-Path $ResultDir $name
    if(Test-Path $src -PathType Leaf){
      Copy-Item -LiteralPath $src -Destination $dst -Force
      $hash=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLower()
      $copied += $dst
      W $Report "copied=$dst sha256=$hash"
    } else {
      W $Report "missing_in_clean=$src"
    }
    if(Test-Path $dst -PathType Leaf){
      $seen += $dst
      W $Report "present_in_clean2=$dst"
    }
  }
  if($cycle -lt 8){Start-Sleep -Seconds 240}
}
$status=if(@($seen|Select-Object -Unique).Count -gt 0){'completed_outputs_found_or_copied'}else{'completed_no_outputs_found'}
if($status -eq 'completed_no_outputs_found'){$warnings += 'Contractor 002 outputs not found in CLEAN or CLEAN2 result folders. Likely runner bridge mismatch or task not executed.'}
$result=[ordered]@{task_id=$TaskId;status=$status;generated_at_utc=(Get-Date).ToUniversalTime().ToString('o');bridge_clean=$Bridge1;bridge_clean2=$Bridge2;copied=@($copied|Select-Object -Unique);seen=@($seen|Select-Object -Unique);warnings=$warnings;next_task=if($status -eq 'completed_no_outputs_found'){'Requeue contractor task on CLEAN2 or start correct runner bridge'}else{'Inspect copied contractor result and proceed to dry-run planning'}}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $Json -Encoding UTF8
W $Report "STATUS=$status"
W $Report "json=$Json"
W $Report "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W $Progress "done status=$status"
Write-Host "CONTRACTOR_002_BRIDGE_RECOVERY_DONE status=$status"
exit 0
