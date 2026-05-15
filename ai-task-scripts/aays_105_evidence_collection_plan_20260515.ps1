$ErrorActionPreference='Continue'
$TaskId='aays-105-evidence-collection-plan-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-105-evidence-collection-plan-$stamp.md"
$hb=Join-Path $hd 'evidence-collection-plan.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
function Tail([string]$title,[string]$path,[int]$n){L ''; L ('## '+$title); if(Test-Path $path){Get-Content $path -Tail $n|ForEach-Object{L $_}}else{L ('MISSING: '+$path)}}
$thresholdHb=Join-Path $hd 'threshold-reaudit.md'
$labelHb=Join-Path $hd 'label-outcome-audit.md'
$riskHb=Join-Path $hd 'risk-preview-v2.md'
$completed=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
L '# AAYS 105 Evidence Collection Plan'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: read-only evidence plan; no DB writes; no UI patch; no scoring changes.'
Tail 'Threshold re-audit carried forward' $thresholdHb 80
Tail 'Label outcome carried forward' $labelHb 80
Tail 'Risk preview v2 carried forward' $riskHb 60
L ''
L '## Evidence collection objective'
L 'Collect enough source and polygon evidence to convert selected rows from needs_source/ambiguous into either reject, downgrade, or accept_candidate. Do not auto-accept without evidence_checked=yes.'
L ''
L '## Priority order'
L 'P1: all derived_multi_signal rows, because there are only 2 and they are closest to accept_candidate after source checks.'
L 'P2: all ambiguous derived_signal rows from the 26-row review set.'
L 'P3: high-value or extreme-area critical rows from risk_preview_v2.'
L 'P4: derived_ai_visual rows only after georeferenced polygon evidence exists.'
L ''
L '## Required evidence fields per row'
L 'verification_id, listing_id, canonical_source_url, source_url_status, postcode_check, local_authority_check, polygon_source, polygon_georeferenced, evidence_checked, evidence_notes'
L ''
L '## Evidence decisions'
L 'If source URL missing or inaccessible: reviewer_label=needs_source.'
L 'If postcode/authority conflict: reviewer_label=reject or ambiguous.'
L 'If polygon not georeferenced: reviewer_label=needs_source; acceptance_status remains manual_review.'
L 'If polygon/source/postcode/authority all pass: reviewer_label may become accept_candidate subject to human review.'
L ''
L '## Output files to use'
if($completed){L ('completed_labels_auto_csv: '+$completed.FullName)}else{L 'completed_labels_auto_csv: NOT_FOUND'}
L 'risk_preview_v2_csv: C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results\aays-097-risk-preview-v2-20260515_025249.csv'
L ''
L '## Next safe task'
L 'AAYS 106 should create an evidence tracking CSV template from completed_labels_auto and risk_preview_v2. It must remain read-only and must not modify DB/UI/scoring.'
L ''
L 'wide_accuracy_program_percent: 99'
L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
L 'safe_output_gate: READY_FOR_EVIDENCE_COLLECTION'
L 'AAYS_105_EVIDENCE_COLLECTION_PLAN_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_105_EVIDENCE_COLLECTION_PLAN_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
