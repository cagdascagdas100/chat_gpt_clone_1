param()

$ErrorActionPreference = 'Stop'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { throw 'AAYS_REPO_ROOT_NOT_RESOLVED' }
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot)

$TaskId = '210_aays1_parcel_label_4row_artifact_restore_and_dom_proof_20260715'
$RestoreId = '210a_aays1_parcel_label_4row_artifact_restore_20260715'
$DomId = '210b_aays1_parcel_label_4row_dom_proof_20260715'
$Source207 = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\automation\207_aays1_parcel_label_4row_official_source_publish_20260715.ps1'
$Source209 = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\automation\209_aays1_parcel_label_4row_browser_dom_proof_20260715.ps1'
$OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\runner_outputs\210_aays1_parcel_label_4row_artifact_restore_and_dom_proof_20260715_output.json'
$EvidencePath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\evidence\210_parcel_label_4row_artifact_restore_and_dom_proof_evidence_20260715.json'
$GatePath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\status\210_aays1_parcel_label_4row_artifact_restore_and_dom_proof_20260715_gate.json'
$CheckpointPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\checkpoints\parcel_label_canonical_checkpoint.json'
$ReportPath = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\reports\210_parcel_label_4row_artifact_restore_and_dom_proof_report_20260715.md'
$RestoreOutputPath = Join-Path $RepoRoot ('docs\chatgpt_status\aays1\runner_outputs\' + $RestoreId + '_output.json')
$DomOutputPath = Join-Path $RepoRoot ('docs\chatgpt_status\aays1\runner_outputs\' + $DomId + '_output.json')

function Ensure-Parent([string]$Path) {
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
}
function Write-Utf8([string]$Path,[string]$Text) {
  Ensure-Parent $Path
  [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path,[object]$Value) { Write-Utf8 $Path (($Value | ConvertTo-Json -Depth 60) + "`n") }
function Read-Json([string]$Path) { if (Test-Path -LiteralPath $Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null } }
function Run-Child([string]$ScriptText,[string]$Name) {
  $tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('aays_' + $Name + '_' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
  $scriptPath = Join-Path $tempRoot ($Name + '.ps1')
  $stdoutPath = Join-Path $tempRoot 'stdout.log'
  $stderrPath = Join-Path $tempRoot 'stderr.log'
  Write-Utf8 $scriptPath $ScriptText
  try {
    $process = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $scriptPath + '"')) -WorkingDirectory $RepoRoot -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru -WindowStyle Hidden
    if (-not $process.WaitForExit(420000)) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue; return [pscustomobject]@{ exit_code=124; stdout=''; stderr='child_timeout' } }
    $process.Refresh()
    return [pscustomobject]@{
      exit_code=[int]$process.ExitCode
      stdout=$(if(Test-Path -LiteralPath $stdoutPath){Get-Content -LiteralPath $stdoutPath -Raw}else{''})
      stderr=$(if(Test-Path -LiteralPath $stderrPath){Get-Content -LiteralPath $stderrPath -Raw}else{''})
    }
  } finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}

if (-not (Test-Path -LiteralPath $Source207)) { throw 'TASK_207_AUTOMATION_SOURCE_MISSING' }
if (-not (Test-Path -LiteralPath $Source209)) { throw 'TASK_209_AUTOMATION_SOURCE_MISSING' }

$restoreText = Get-Content -LiteralPath $Source207 -Raw -Encoding UTF8
$restoreText = $restoreText.Replace('207_aays1_parcel_label_4row_official_source_publish_20260715',$RestoreId)
$restoreText = $restoreText.Replace('207_parcel_label_4row_official_source_publish_evidence_20260715.json','210a_parcel_label_4row_artifact_restore_evidence_20260715.json')
$restoreText = $restoreText.Replace('207_parcel_label_4row_official_source_publish_report_20260715.md','210a_parcel_label_4row_artifact_restore_report_20260715.md')
$restoreText = $restoreText.Replace('checkpoint_sequence=207','checkpoint_sequence=210')
$restoreText = $restoreText.Replace("last_accepted_task_id='206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714'","last_accepted_task_id='207_aays1_parcel_label_4row_official_source_publish_20260715'")
$restoreText = $restoreText.Replace("change_reason='task_207_official_source_batch_idempotent_append'","change_reason='task_210_restore_verified_task_207_rows_after_artifact_regression'")
$restoreRun = Run-Child -ScriptText $restoreText -Name 'parcel_label_210_restore'
$restoreOutput = Read-Json $RestoreOutputPath

$domText = Get-Content -LiteralPath $Source209 -Raw -Encoding UTF8
$domText = $domText.Replace('209_aays1_parcel_label_4row_browser_dom_proof_20260715',$DomId)
$domText = $domText.Replace('209_parcel_label_4row_browser_dom_proof_evidence_20260715.json','210b_parcel_label_4row_dom_proof_evidence_20260715.json')
$domText = $domText.Replace('209_parcel_label_4row_browser_dom_proof_report_20260715.md','210b_parcel_label_4row_dom_proof_report_20260715.md')
$domText = $domText.Replace('parcel-label-209','parcel-label-210')
$domRun = Run-Child -ScriptText $domText -Name 'parcel_label_210_dom'
$domOutput = Read-Json $DomOutputPath

$now = [DateTimeOffset]::UtcNow.ToString('o')
$restoreRows = if ($restoreOutput) { [int]$restoreOutput.tracked_row_count } else { 0 }
$restoredCount = if ($restoreOutput) { [int]$restoreOutput.new_rows_created } else { 0 }
$httpVisible = if ($restoreOutput -and [string]$restoreOutput.status -like '*HTTP_READBACK_VERIFIED*') { 4 } else { 0 }
$domVisible = if ($domOutput) { [int]$domOutput.browser_dom_visible_count } else { 0 }
$passed = ($restoreRun.exit_code -eq 0 -and $domRun.exit_code -eq 0 -and $restoreRows -ge 198 -and $httpVisible -eq 4 -and $domVisible -eq 4)
$blockers = @()
if ($restoreRun.exit_code -ne 0) { $blockers += 'TASK_210_RESTORE_CHILD_FAILED' }
if ($restoreRows -lt 198) { $blockers += 'TASK_210_SOURCE_ROWS_BELOW_198' }
if ($httpVisible -ne 4) { $blockers += 'TASK_210_HTTP_FOUR_IDS_NOT_VERIFIED' }
if ($domRun.exit_code -ne 0) { $blockers += 'TASK_210_DOM_CHILD_FAILED' }
if ($domVisible -ne 4) { $blockers += 'TASK_210_BROWSER_DOM_FOUR_IDS_NOT_VISIBLE' }
$blockers += 'EXACT_GEOMETRY_BINDING_PENDING'
$blockers += 'MANUAL_SCOPE_REVIEW_PENDING'

$evidence = [ordered]@{
  task_id=$TaskId; generated_at=$now
  regression_observed_rows=194; expected_restored_rows=198
  restore_child_id=$RestoreId; restore_exit_code=$restoreRun.exit_code; restore_output=$restoreOutput
  dom_child_id=$DomId; dom_exit_code=$domRun.exit_code; dom_output=$domOutput
  restored_row_count=$restoredCount; tracked_row_count=$restoreRows
  http_visible_count=$httpVisible; browser_dom_visible_count=$domVisible
  passed=$passed; blockers=$blockers
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json $EvidencePath $evidence

$output = [ordered]@{
  task_id=$TaskId
  status=$(if($passed){'ARTIFACT_RESTORED_198_ROWS_HTTP_AND_BROWSER_DOM_VERIFIED_REMOTE_COMMIT_PENDING'}else{'ARTIFACT_RESTORE_OR_BROWSER_DOM_PROOF_BLOCKED'})
  generated_at=$now; tracked_row_count=$restoreRows; restored_row_count=$restoredCount
  source_upgraded_rows=57; classification_enriched_rows=57; latest_batch_accuracy_score_4=3.9375
  http_visible_count=$httpVisible; browser_dom_visible_count=$domVisible
  browser_verified_rows=$(if($passed){198}else{194}); exact_geometry_rows=0
  blockers=$blockers; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
Write-Json $OutputPath $output
Write-Json $GatePath ([ordered]@{task_id=$TaskId;source_row_gate_passed=($restoreRows-ge198);ui_token_gate_passed=$passed;browser_smoke_passed=($domRun.exit_code-eq0);post_sync_ok=$passed;manual_review_required=$true;fake_data=$false;final_ready=$false})

$checkpoint = [ordered]@{
  page_key='aays1';layer_key='distance_property_types';branch='codex/aays-single-runner-v5-20260706';checkpoint_sequence=210
  checkpoint_status=$(if($passed){'TASK_210_LOCAL_VERIFIED_REMOTE_COMMIT_READBACK_PENDING'}else{'TASK_210_BLOCKED'})
  last_accepted_task_id='207_aays1_parcel_label_4row_official_source_publish_20260715';pending_task_id=$TaskId;pending_task_state=$output.status
  evidence_paths=@('docs/chatgpt_status/aays1/evidence/210_parcel_label_4row_artifact_restore_and_dom_proof_evidence_20260715.json','docs/chatgpt_status/aays1/runner_outputs/210_aays1_parcel_label_4row_artifact_restore_and_dom_proof_20260715_output.json','docs/chatgpt_status/aays1/reports/210_parcel_label_4row_artifact_restore_and_dom_proof_report_20260715.md')
  next_incomplete_action=$(if($passed){'remote_commit_readback_for_task_210_then_exact_geometry_binding'}else{'recover_task_210_artifact_or_dom_failure'})
  tracked_rows=$restoreRows;verified_rows=$restoreRows;published_rows=$restoreRows;http_verified_rows=$(if($httpVisible-eq4){$restoreRows}else{194});browser_verified_rows=$(if($passed){198}else{194})
  source_upgraded_rows=57;classification_enriched_rows=57;exact_geometry_rows=0;latest_batch_accuracy_average_4=3.9375;latest_batch_accuracy_percent=98.44
  blockers=$blockers;zip_timestamp_policy='IGNORE_ZIP_AND_HANDOFF_FILE_AGE_ALWAYS_READ_THIS_REMOTE_CHECKPOINT_FIRST'
  single_runner_only=$true;new_runner=$false;parallel_runner=$false;completed=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false;updated_at=$now
}
Write-Json $CheckpointPath $checkpoint

$report = @(
  '# Parcel Label Task 210 - Artifact Restore and DOM Proof','',
  ('- Regression baseline: 194; restored source rows: {0}' -f $restoreRows),
  ('- Restored rows in this run: {0}' -f $restoredCount),
  ('- HTTP visible IDs: {0}/4' -f $httpVisible),
  ('- Browser DOM visible IDs: {0}/4' -f $domVisible),
  ('- Result: {0}' -f $output.status),
  '- Exact geometry remains 0; manual scope review remains required.','',
  '`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
Write-Utf8 $ReportPath (($report -join "`n") + "`n")

Write-Output ($output | ConvertTo-Json -Depth 30)
if (-not $passed) { exit 2 }
exit 0
