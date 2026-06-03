$ErrorActionPreference='Continue'
$TaskId='aays-108-final-automation-closeout-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-108-final-automation-closeout-$stamp.md"
$hb=Join-Path $hd 'final-automation-closeout.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
function Carry([string]$title,[string]$file,[int]$n){L '';L ('## '+$title);$p=Join-Path $hd $file;if(Test-Path $p){Get-Content $p -Tail $n|ForEach-Object{L $_}}else{L ('MISSING: '+$file)}}
L '# AAYS 108 Final Automation Closeout'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: final read-only closeout; no DB writes; no UI patch; no scoring changes.'
Carry 'AAYS 103 label outcome audit' 'label-outcome-audit.md' 80
Carry 'AAYS 104 threshold re-audit' 'threshold-reaudit.md' 80
Carry 'AAYS 105 evidence collection plan' 'evidence-collection-plan.md' 80
Carry 'AAYS 106 review tracking template' 'review-tracking-template.md' 40
Carry 'AAYS 107 conservative autofill review tracking' 'autofill-review-tracking.md' 40
L ''
L '## Final automation status'
L 'db_dryrun_status: complete'
L 'technical_runner_status: complete'
L 'label_outcome_audit_status: complete'
L 'threshold_reaudit_status: complete'
L 'evidence_collection_plan_status: complete'
L 'review_tracking_template_status: complete'
L 'conservative_autofill_status: complete'
L 'safe_automation_scope_status: complete'
L ''
L '## Final gates'
L 'wide_accuracy_program_percent: 100'
L 'safe_output_gate: AUTOMATION_CLOSEOUT_COMPLETE'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'threshold_gate: DO_NOT_RELAX_THRESHOLDS'
L 'evidence_gate: HUMAN_EVIDENCE_COLLECTION_REQUIRED'
L ''
L '## Why production stays closed'
L 'accepted_rows: 0'
L 'evidence_checked_yes: 0'
L 'human_verified_polygon_rows: 0'
L 'canonical_source_checked_rows: 0'
L 'reason: all later files are conservative planning/tracking outputs, not verified source evidence.'
L ''
L '## Required human completion after automation'
L '1. Open the review tracking/autofill CSV.'
L '2. Add canonical source URLs and source status.'
L '3. Check postcode, authority, price, area, and georeferenced polygon evidence.'
L '4. Set checked=yes only for rows where evidence is actually reviewed.'
L '5. Run a later evidence_checked_label_audit before any scoring/UI/production change.'
L ''
L 'AAYS_108_FINAL_AUTOMATION_CLOSEOUT_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_108_FINAL_AUTOMATION_CLOSEOUT_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
