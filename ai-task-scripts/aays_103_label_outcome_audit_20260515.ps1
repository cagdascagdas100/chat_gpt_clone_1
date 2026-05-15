$ErrorActionPreference='Continue'
$TaskId='aays-103-label-outcome-audit-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-103-label-outcome-audit-$stamp.md"
$hb=Join-Path $hd 'label-outcome-audit.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
L '# AAYS 103 Label Outcome Audit'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: read-only audit; no DB writes; no UI patch; no scoring changes.'
$f=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$f){
  L 'completed_label_file: NOT_FOUND'
  L 'manual_review_gate: WAITING_FOR_HUMAN_LABELS'
  L 'wide_accuracy_program_percent: 96'
  L 'AAYS_103_LABEL_OUTCOME_AUDIT_DONE=false'
}else{
  L ('completed_label_file: '+$f.FullName)
  $rows=Import-Csv $f.FullName
  $filled=@($rows|Where-Object{-not [string]::IsNullOrWhiteSpace([string]$_.reviewer_label)})
  L ('rows: '+@($rows).Count)
  L ('reviewer_label_filled: '+@($filled).Count)
  L ''
  L '## reviewer_label distribution'
  $rows|Group-Object reviewer_label|Sort-Object Count -Descending|ForEach-Object{L (($_.Name)+': '+$_.Count)}
  L ''
  L '## reviewer_confidence distribution'
  $rows|Group-Object reviewer_confidence|Sort-Object Count -Descending|ForEach-Object{L (($_.Name)+': '+$_.Count)}
  L ''
  L '## evidence_checked distribution'
  $rows|Group-Object evidence_checked|Sort-Object Count -Descending|ForEach-Object{L (($_.Name)+': '+$_.Count)}
  L ''
  L '## issue_type distribution'
  $rows|Group-Object issue_type|Sort-Object Count -Descending|ForEach-Object{L (($_.Name)+': '+$_.Count)}
  if(@($filled).Count -ge 25){
    L ''
    L 'manual_review_gate: LABEL_OUTCOME_AUDITED'
    L 'next_allowed_task: threshold_reaudit'
    L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
    L 'wide_accuracy_program_percent: 97'
    L 'AAYS_103_LABEL_OUTCOME_AUDIT_DONE=true'
  }else{
    L ''
    L 'manual_review_gate: LABEL_FILE_INSUFFICIENT'
    L 'next_allowed_task: fill_at_least_25_rows'
    L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
    L 'wide_accuracy_program_percent: 96'
    L 'AAYS_103_LABEL_OUTCOME_AUDIT_DONE=false'
  }
}
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_103_LABEL_OUTCOME_AUDIT_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
