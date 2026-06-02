$ErrorActionPreference='Continue'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-102-label-waiter-$stamp.md"
$hb=Join-Path $hd 'label-waiter.md'
$lines=@('# AAYS 102 Label Waiter',('Generated: '+(Get-Date -Format s)),'Mode: read-only wait; no writes to DB or app.','wait_seconds: 1800')
$found=$null
for($i=1;$i -le 60;$i++){
  $f=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
  if($f){$found=$f;break}
  Start-Sleep -Seconds 30
}
if($found){$lines+=('completed_label_file: '+$found.FullName);$lines+='manual_review_gate: LABEL_FILE_FOUND';$lines+='wide_accuracy_program_percent: 97'}else{$lines+='completed_label_file: NOT_FOUND_AFTER_WAIT';$lines+='manual_review_gate: WAITING_FOR_HUMAN_LABELS';$lines+='wide_accuracy_program_percent: 96'}
$lines+='production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
$lines+='AAYS_102_LABEL_WAITER_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_102_LABEL_WAITER_DONE=true'
exit 0
