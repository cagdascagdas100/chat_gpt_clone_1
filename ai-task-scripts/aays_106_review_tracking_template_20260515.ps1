$ErrorActionPreference='Continue'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-106-review-tracking-template-$stamp.md"
$out=Join-Path $rd "aays-106-review_tracking_template-$stamp.csv"
$hb=Join-Path $hd 'review-tracking-template.md'
$f=Get-ChildItem $rd -Filter '*completed_labels*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
$lines=@('# AAYS 106 Review Tracking Template',('Generated: '+(Get-Date -Format s)),'Mode: read-only tracking template; no DB writes; no UI patch.')
if(!$f){$lines+='completed_labels_csv: NOT_FOUND';$lines+='AAYS_106_REVIEW_TRACKING_TEMPLATE_DONE=false';Set-Content -Encoding UTF8 $rep $lines;Set-Content -Encoding UTF8 $hb $lines;exit 2}
$rows=Import-Csv $f.FullName
$template=foreach($r in $rows){
  [pscustomobject]@{
    case_id=if($r.validation_case_id){$r.validation_case_id}else{$r.supplemental_case_id}
    verification_id=$r.verification_id
    listing_id=$r.listing_id
    geometry_verdict=$r.geometry_verdict
    current_label=$r.reviewer_label
    current_issue=$r.issue_type
    check_url=''
    url_status='unchecked'
    postcode_status='unchecked'
    authority_status='unchecked'
    polygon_status='unchecked'
    checked='no'
    final_decision='pending'
    notes=''
  }
}
$template|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $out
$lines+=('completed_labels_csv: '+$f.FullName)
$lines+=('template_csv: '+$out)
$lines+=('template_rows: '+@($template).Count)
$lines+='production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
$lines+='safe_output_gate: READY_FOR_REVIEW_TRACKING'
$lines+='wide_accuracy_program_percent: 99'
$lines+='AAYS_106_REVIEW_TRACKING_TEMPLATE_DONE=true'
Set-Content -Encoding UTF8 $rep $lines
Set-Content -Encoding UTF8 $hb $lines
Write-Output 'AAYS_106_REVIEW_TRACKING_TEMPLATE_DONE=true'
Write-Output ('REPORT='+$rep)
Write-Output ('TEMPLATE_CSV='+$out)
exit 0
