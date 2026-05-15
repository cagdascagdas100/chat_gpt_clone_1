$ErrorActionPreference='Continue'
$TaskId='aays-104-threshold-reaudit-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-104-threshold-reaudit-$stamp.md"
$hb=Join-Path $hd 'threshold-reaudit.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
L '# AAYS 104 Threshold Re-audit'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: read-only re-audit; no DB writes; no UI patch; no scoring changes.'
$f=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$f){
  L 'completed_label_file: NOT_FOUND'
  L 'threshold_gate: BLOCKED_NO_LABELS'
  L 'wide_accuracy_program_percent: 97'
}else{
  L ('completed_label_file: '+$f.FullName)
  $rows=Import-Csv $f.FullName
  $filled=@($rows|Where-Object{-not [string]::IsNullOrWhiteSpace([string]$_.reviewer_label)})
  $accept=@($rows|Where-Object{$_.reviewer_label -eq 'accept'})
  $downgrade=@($rows|Where-Object{$_.reviewer_label -eq 'downgrade'})
  $reject=@($rows|Where-Object{$_.reviewer_label -eq 'reject'})
  $needs=@($rows|Where-Object{$_.reviewer_label -eq 'needs_source'})
  $amb=@($rows|Where-Object{$_.reviewer_label -eq 'ambiguous'})
  $evidenceYes=@($rows|Where-Object{$_.evidence_checked -eq 'yes'})
  L ('rows: '+@($rows).Count)
  L ('reviewer_label_filled: '+@($filled).Count)
  L ('accept: '+@($accept).Count)
  L ('downgrade: '+@($downgrade).Count)
  L ('reject: '+@($reject).Count)
  L ('needs_source: '+@($needs).Count)
  L ('ambiguous: '+@($amb).Count)
  L ('evidence_checked_yes: '+@($evidenceYes).Count)
  L ''
  L '## threshold decision'
  if(@($accept).Count -eq 0 -and @($evidenceYes).Count -eq 0){
    L 'threshold_gate: DO_NOT_RELAX_THRESHOLDS'
    L 'reason: no accepted rows and no checked evidence in completed label file'
    L 'recommended_policy: keep all rows manual_review / needs_source until evidence is checked'
    L 'next_allowed_task: evidence_collection_plan'
    L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
    L 'wide_accuracy_program_percent: 98'
  }else{
    L 'threshold_gate: PARTIAL_REVIEW_REQUIRED'
    L 'reason: accepted/evidence rows exist but production scoring still needs manual review'
    L 'next_allowed_task: controlled_threshold_experiment'
    L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
    L 'wide_accuracy_program_percent: 98'
  }
}
L 'AAYS_104_THRESHOLD_REAUDIT_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_104_THRESHOLD_REAUDIT_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
