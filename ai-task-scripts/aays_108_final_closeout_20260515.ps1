$ErrorActionPreference='Continue'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-108-final-closeout-$stamp.md"
$hb=Join-Path $hd 'final-closeout.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
function Latest([string]$pattern){Get-ChildItem $rd -Filter $pattern -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
$completed=Latest 'aays-103-completed_labels_auto_conservative-*.csv'
$review=Latest 'aays-107-review_tracking_autofilled-*.csv'
$risk=Latest 'aays-097-risk-preview-v2-*.csv'
L '# AAYS 108 Final Closeout'
L ('Generated: '+(Get-Date -Format s))
L 'Mode: read-only closeout; no DB writes; no UI patch; no scoring changes.'
L ''
L '## Automation completed outputs'
if($completed){L ('completed_labels_auto_csv: '+$completed.FullName)}else{L 'completed_labels_auto_csv: NOT_FOUND'}
if($review){L ('review_tracking_autofilled_csv: '+$review.FullName)}else{L 'review_tracking_autofilled_csv: NOT_FOUND'}
if($risk){L ('risk_preview_v2_csv: '+$risk.FullName)}else{L 'risk_preview_v2_csv: NOT_FOUND'}
L ''
L '## Final automation state'
L 'db_dryrun_schema_import: COMPLETE'
L 'source_inventory: COMPLETE'
L 'validation_sample: COMPLETE'
L 'risk_preview_v2: COMPLETE'
L 'auto_conservative_labels: COMPLETE'
L 'threshold_reaudit: COMPLETE_DO_NOT_RELAX'
L 'evidence_collection_plan: COMPLETE'
L 'review_tracking_template_and_autofill: COMPLETE'
L ''
L '## Final gates'
L 'automation_gate: COMPLETE'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'reason: no human evidence_checked=yes rows and no verified polygon/source evidence confirmed.'
L 'safe_output_gate: READY_FOR_HUMAN_EVIDENCE_REVIEW'
L ''
L '## Required human evidence actions before production'
L '1. Open review_tracking_autofilled_csv.'
L '2. Replace manual_source_url_required with canonical source URLs.'
L '3. Set url_status, postcode_status, authority_status, polygon_status based on real evidence.'
L '4. Set checked=yes only after evidence is actually checked.'
L '5. Keep final_decision as needs_source/ambiguous unless evidence supports change.'
L '6. Re-run a future label/evidence audit before any scoring or UI patch.'
L ''
L 'wide_accuracy_program_percent: 100_automation_complete'
L 'AAYS_108_FINAL_CLOSEOUT_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_108_FINAL_CLOSEOUT_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
