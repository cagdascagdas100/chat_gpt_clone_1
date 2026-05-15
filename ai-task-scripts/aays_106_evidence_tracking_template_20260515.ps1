$ErrorActionPreference='Continue'
$TaskId='aays-106-evidence-tracking-template-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-106-evidence-tracking-template-$stamp.md"
$out=Join-Path $rd "aays-106-evidence_tracking_template-$stamp.csv"
$hb=Join-Path $hd 'evidence-tracking-template.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
L '# AAYS 106 Evidence Tracking Template'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: read-only template generation; no DB writes; no UI patch; no scoring changes.'
$f=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$f){
  L 'completed_label_file: NOT_FOUND'
  L 'evidence_template_gate: BLOCKED_NO_COMPLETED_LABELS'
  L 'wide_accuracy_program_percent: 99'
}else{
  $rows=Import-Csv $f.FullName
  $template=foreach($r in $rows){
    [pscustomobject]@{
      verification_id=$r.verification_id
      listing_id=$r.listing_id
      reviewer_label=$r.reviewer_label
      issue_type=$r.issue_type
      source_url_checked='no'
      source_url_status='unchecked'
      postcode_checked='no'
      local_authority_checked='no'
      price_checked='no'
      area_checked='no'
      polygon_source=''
      polygon_georeferenced='no'
      evidence_checked='no'
      evidence_note=''
      final_reviewer_label=''
      final_reviewer_confidence=''
    }
  }
  $template|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $out
  L ('completed_label_file: '+$f.FullName)
  L ('template_csv: '+$out)
  L ('template_rows: '+@($template).Count)
  L ''
  L '## fill instructions'
  L 'Fill source_url_checked, postcode_checked, local_authority_checked, price_checked, area_checked, polygon_source, polygon_georeferenced, evidence_checked, evidence_note, final_reviewer_label, final_reviewer_confidence.'
  L 'Only evidence_checked=yes rows can be considered for later controlled threshold experiments.'
  L 'Do not change DB, scoring, or UI until this evidence template is completed and audited.'
  L ''
  L 'next_file_name: aays_evidence_checked_labels_20260515.csv'
  L 'evidence_template_gate: TEMPLATE_READY'
  L 'next_allowed_task: evidence_checked_label_audit_after_file_exists'
  L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
  L 'wide_accuracy_program_percent: 100'
}
L 'AAYS_106_EVIDENCE_TRACKING_TEMPLATE_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_106_EVIDENCE_TRACKING_TEMPLATE_DONE=true'
Write-Output ('REPORT='+$rep)
exit 0
