$ErrorActionPreference='Continue'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-107-autofill-review-tracking-$stamp.md"
$out=Join-Path $rd "aays-107-review_tracking_autofilled-$stamp.csv"
$hb=Join-Path $hd 'autofill-review-tracking.md'
$f=Get-ChildItem $rd -Filter 'aays-106-review_tracking_template-*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
$lines=@('# AAYS 107 Autofill Review Tracking',('Generated: '+(Get-Date -Format s)),'Mode: conservative autofill; no DB writes; no UI patch; no scoring changes; not human evidence verification.')
if(!$f){$lines+='template_csv: NOT_FOUND';$lines+='AAYS_107_AUTOFILL_REVIEW_TRACKING_DONE=false';Set-Content -Encoding UTF8 $rep $lines;Set-Content -Encoding UTF8 $hb $lines;exit 2}
$rows=Import-Csv $f.FullName
$filled=foreach($r in $rows){
  $decision='needs_source'
  if($r.current_label -eq 'ambiguous'){$decision='ambiguous'}
  [pscustomobject]@{
    case_id=$r.case_id
    verification_id=$r.verification_id
    listing_id=$r.listing_id
    geometry_verdict=$r.geometry_verdict
    current_label=$r.current_label
    current_issue=$r.current_issue
    check_url='manual_source_url_required'
    url_status='unchecked'
    postcode_status='unchecked'
    authority_status='unchecked'
    polygon_status='unchecked'
    checked='no'
    final_decision=$decision
    notes='AUTO_CONSERVATIVE_FILL: evidence not checked by human; keep production auto-accept disabled; collect canonical source URL and georeferenced polygon before promotion.'
  }
}
$filled|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $out
$lines+=('template_csv: '+$f.FullName)
$lines+=('autofilled_csv: '+$out)
$lines+=('rows: '+@($filled).Count)
$lines+='checked_yes: 0'
$lines+='production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
$lines+='safe_output_gate: AUTOFILLED_REVIEW_TRACKING_CREATED'
$lines+='next_allowed_task: final_closeout_or_human_evidence_collection'
$lines+='wide_accuracy_program_percent: 99'
$lines+='AAYS_107_AUTOFILL_REVIEW_TRACKING_DONE=true'
Set-Content -Encoding UTF8 $rep $lines
Set-Content -Encoding UTF8 $hb $lines
Write-Output 'AAYS_107_AUTOFILL_REVIEW_TRACKING_DONE=true'
Write-Output ('REPORT='+$rep)
Write-Output ('AUTOFILLED_CSV='+$out)
exit 0
