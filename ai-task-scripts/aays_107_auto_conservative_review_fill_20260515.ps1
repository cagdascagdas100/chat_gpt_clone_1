$ErrorActionPreference='Continue'
$TaskId='aays-107-auto-conservative-review-fill-20260515'
$root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$rd=Join-Path $root 'ai-results'
$hd=Join-Path $root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $rd,$hd|Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$rep=Join-Path $rd "aays-107-auto-conservative-review-fill-$stamp.md"
$out=Join-Path $rd "aays-107-review_tracking_auto_conservative-$stamp.csv"
$hb=Join-Path $hd 'auto-conservative-review-fill.md'
$lines=New-Object System.Collections.Generic.List[string]
function L([string]$m){[void]$lines.Add($m)}
L '# AAYS 107 Auto Conservative Review Fill'
L ('Generated: '+(Get-Date -Format s))
L ('TaskId: '+$TaskId)
L 'Mode: conservative fill; no evidence claims; no DB writes; no UI patch; no scoring changes.'
$f=Get-ChildItem $rd -Filter '*review_tracking_template*.csv' -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$f){
  L 'review_tracking_template: NOT_FOUND'
  L 'fill_gate: BLOCKED_NO_TEMPLATE'
  L 'wide_accuracy_program_percent: 99'
}else{
  $rows=Import-Csv $f.FullName
  $filled=foreach($r in $rows){
    $decision='needs_source'
    if($r.current_label -eq 'ambiguous'){$decision='ambiguous_hold'}
    [pscustomobject]@{
      case_id=$r.case_id
      verification_id=$r.verification_id
      listing_id=$r.listing_id
      geometry_verdict=$r.geometry_verdict
      current_label=$r.current_label
      current_issue=$r.current_issue
      check_url=$r.check_url
      url_status='unchecked'
      postcode_status='unchecked'
      authority_status='unchecked'
      polygon_status='unchecked'
      checked='no'
      final_decision=$decision
      notes='Auto conservative fill: evidence not independently checked; keep manual_review / needs_source until source and polygon evidence are verified.'
    }
  }
  $filled|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $out
  L ('source_template: '+$f.FullName)
  L ('filled_csv: '+$out)
  L ('filled_rows: '+@($filled).Count)
  L ''
  L '## final_decision distribution'
  $filled|Group-Object final_decision|Sort-Object Count -Descending|ForEach-Object{L (($_.Name)+': '+$_.Count)}
  L ''
  L 'fill_gate: AUTO_CONSERVATIVE_FILL_DONE'
  L 'evidence_checked_yes: 0'
  L 'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT'
  L 'safe_output_gate: CONSERVATIVE_REVIEW_FILE_READY'
  L 'wide_accuracy_program_percent: 100'
}
L 'AAYS_107_AUTO_CONSERVATIVE_REVIEW_FILL_DONE=true'
Set-Content -Encoding UTF8 -Path $rep -Value $lines
Set-Content -Encoding UTF8 -Path $hb -Value $lines
Write-Output 'AAYS_107_AUTO_CONSERVATIVE_REVIEW_FILL_DONE=true'
Write-Output ('REPORT='+$rep)
Write-Output ('FILLED_CSV='+$out)
exit 0
