[CmdletBinding()]
param([string]$RepoRoot)
$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel).Trim() }
$taskId = '174_aays1_parcel_label_matrix_visibility_source_paths_codex_fix_20260711'
function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Read-Json([string]$Path) { if (Test-Path -LiteralPath $Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } }
function Ensure-Dir([string]$Path) { if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Json([string]$Path,[object]$Value) { Ensure-Dir (Split-Path -Parent $Path); $tmp=$Path+'.tmp.'+$PID; [IO.File]::WriteAllText($tmp,(($Value|ConvertTo-Json -Depth 60)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $tmp -Destination $Path -Force }
function Rel([string]$Path) { ([IO.Path]::GetFullPath($Path).Substring([IO.Path]::GetFullPath($RepoRoot).TrimEnd('\').Length).TrimStart('\') -replace '\\','/') }
function Hash-File([string]$Path) { if(Test-Path -LiteralPath $Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null} }
function Get-Value([object]$Object,[string]$Name,[object]$Default=$null){$p=$Object.PSObject.Properties[$Name];if($p -and $null-ne $p.Value){$p.Value}else{$Default}}
function Set-Value([object]$Object,[string]$Name,[object]$Value){$Object|Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force}
$allRowsRel='england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel='england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel='england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel='england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$indexRel='england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$rejectedRel='docs/chatgpt_status/aays1/evidence/174_parcel_label_rejected_inputs_latest.json'
$outputRel='docs/chatgpt_status/aays1/runner_outputs/174_aays1_parcel_label_matrix_visibility_source_paths_fix_output.json'
$proofRel='docs/chatgpt_status/aays1/runner_outputs/174_aays1_parcel_label_matrix_visibility_source_paths_browser_proof.json'
$statusOutRel='docs/chatgpt_status/aays1/status/174_aays1_parcel_label_matrix_visibility_source_paths_fix_status.json'
$reportRel='docs/chatgpt_status/aays1/reports/174_aays1_parcel_label_matrix_visibility_source_paths_fix_completion_report.md'
$builder=Join-Path $RepoRoot 'docs/chatgpt_status/aays1/automation/169_parcel_label_backlog_visibility_orchestrator_20260711.ps1'
if(-not(Test-Path -LiteralPath $builder)){throw 'TASK_169_BUILDER_MISSING'}
& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $RepoRoot
if($LASTEXITCODE -ne 0){throw ('TASK_169_BUILDER_EXIT_'+$LASTEXITCODE)}
$allRowsPath=Join-Path $RepoRoot ($allRowsRel-replace'/','\')
$doc=Read-Json $allRowsPath
$unique=[ordered]@{}; $duplicateIds=@()
foreach($row in @($doc.rows)){$id=[string](Get-Value $row 'parcel_id' '');if(-not$id){continue};if($unique.Contains($id)){$duplicateIds+=$id;continue};$unique[$id]=$row}
$rows=@($unique.Values);$generated=Now-Utc;$indexRows=@();$new=0;$upgraded=0;$enriched=0;$missing=0;$present=0
foreach($row in $rows){
  $change='EXISTING_TRACKED'
  if((Get-Value $row 'new_this_run' $false)-eq $true -or (Get-Value $row 'is_new_in_latest_batch' $false)-eq $true){$change='NEW_ROW';$new++}
  elseif([string](Get-Value $row 'batch_id' '')-match '171|enrichment'){$change='ADDRESS_GEOMETRY_ENRICHED';$enriched++}
  elseif([string](Get-Value $row 'candidate_status' '')-match 'UPGRADED|SOURCE_REACHABLE'){$change='SOURCE_UPGRADED';$upgraded++}
  Set-Value $row 'change_kind' $change; Set-Value $row 'artifact_index_path' $indexRel
  $artifacts=@()
  foreach($field in @('payload_path','queue_task_path','source_path','local_source_path','downloaded_source_path','report_path','evidence_path','runner_output_path')){
    $value=[string](Get-Value $row $field '')
    $state='MISSING';$href=$null
    if($value -and $value -notmatch 'not_available|not_downloaded|missing|remote_source_'){
      $candidate=Join-Path $RepoRoot ($value-replace'/','\')
      if(Test-Path -LiteralPath $candidate){$state='LOCAL_PRESENT';$present++;$href='/'+$value}else{$missing++}
    }else{$missing++}
    $artifacts+=[ordered]@{field=$field;path=if($value){$value}else{'MISSING'};state=$state;browser_href=$href}
  }
  $indexRows+=[ordered]@{parcel_id=[string]$row.parcel_id;change_kind=$change;candidate_status=[string](Get-Value $row 'candidate_status' 'pending');geometry_status=[string](Get-Value $row 'geometry_status' 'NOT_BOUND');artifacts=$artifacts}
}
Set-Value $doc 'rows' $rows;Set-Value $doc 'row_count' $rows.Count;Set-Value $doc 'visible_row_count' $rows.Count;Set-Value $doc 'unique_parcel_count' $rows.Count;Set-Value $doc 'new_row_count' $new;Set-Value $doc 'source_upgraded_count' $upgraded;Set-Value $doc 'address_geometry_enriched_count' $enriched;Set-Value $doc 'row_artifact_index_path' $indexRel;Set-Value $doc 'updated_at' $generated;Set-Value $doc 'final_ready' $false;Set-Value $doc 'fake_data' $false
Write-Json $allRowsPath $doc
$inputRoot=Join-Path $RepoRoot 'docs/chatgpt_status/aays1/inputs';$rejected=@()
Get-ChildItem -LiteralPath $inputRoot -File -Filter '*.json' -ErrorAction SilentlyContinue|ForEach-Object{
  $inputFile=$_.FullName
  $inputRel=Rel $inputFile
  try{
    $j=Read-Json $inputFile
    $features=@(if($j.features){$j.features}elseif($j.rows){$j.rows}elseif($j.parcels){$j.parcels}else{@()})
    foreach($f in $features){if(-not [string](Get-Value $f 'parcel_id' '')){$rejected+=[ordered]@{input_path=$inputRel;reason='MISSING_PARCEL_ID'}}}
  }catch{$rejected+=[ordered]@{input_path=$inputRel;reason='JSON_PARSE_FAILED';error=$_.Exception.Message}}
}
Write-Json (Join-Path $RepoRoot ($rejectedRel-replace'/','\')) ([ordered]@{generated_at=$generated;rejected_count=$rejected.Count;duplicate_ids=@($duplicateIds|Select-Object -Unique);rejected=$rejected;final_ready=$false;fake_data=$false})
Write-Json (Join-Path $RepoRoot ($indexRel-replace'/','\')) ([ordered]@{task_id=$taskId;generated_at=$generated;unique_parcel_count=$rows.Count;local_present_artifact_count=$present;missing_artifact_count=$missing;rows=$indexRows;final_ready=$false;fake_data=$false})
$status=Read-Json (Join-Path $RepoRoot ($statusRel-replace'/','\'));if($null-eq$status){$status=[pscustomobject]@{}}
Set-Value $status 'latest_task_id' $taskId;Set-Value $status 'tracked_row_count' $rows.Count;Set-Value $status 'visible_row_count' $rows.Count;Set-Value $status 'unique_parcel_count' $rows.Count;Set-Value $status 'new_row_count' $new;Set-Value $status 'source_upgraded_count' $upgraded;Set-Value $status 'address_geometry_enriched_count' $enriched;Set-Value $status 'local_present_artifact_count' $present;Set-Value $status 'missing_artifact_count' $missing;Set-Value $status 'bulk_blocker' $(if($missing-gt0){'ROW_ARTIFACT_PATHS_MISSING_OR_NOT_BROWSER_SERVED'}else{'BROWSER_AND_REMOTE_READBACK_PENDING'});Set-Value $status 'updated_at' $generated;Set-Value $status 'final_ready' $false;Set-Value $status 'fake_data' $false
Write-Json (Join-Path $RepoRoot ($statusRel-replace'/','\')) $status
if($env:AAYS_CONTROLLER_REPO_ROOT){$publisher=Join-Path $RepoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';$publishArg=(@($allRowsRel,$statusRel,$changesRel,$manifestRel,$indexRel)-join'|');& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $RepoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishArg -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){throw'PARCEL_LABEL_174_LIVE_CONTROLLER_PUBLISH_BLOCKED'}}
$artifactSha=Hash-File $allRowsPath
$proof=[ordered]@{task_id=$taskId;checked_at=$generated;local_data_parse_ok=$true;unique_row_count=$rows.Count;artifact_sha=$artifactSha;http_status=$null;browser_row_count=$null;browser_match=$false;blockers=@('BROWSER_HTTP_PROOF_PENDING_AFTER_PUBLISH');final_ready=$false;fake_data=$false}
try{$r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json';$served=$r.Content|ConvertFrom-Json;$proof.http_status=[int]$r.StatusCode;$proof.browser_row_count=@($served.rows).Count;$proof.browser_match=($proof.http_status-eq200-and$proof.browser_row_count-eq$rows.Count);if($proof.browser_match){$proof.blockers=@()}}catch{$proof.blockers=@('BROWSER_HTTP_PROOF_FAILED:'+$_.Exception.Message)}
Write-Json (Join-Path $RepoRoot ($proofRel-replace'/','\')) $proof
$output=[ordered]@{task_id=$taskId;status=if($proof.browser_match){'COMPLETED_VISIBLE_NOT_FINAL'}else{'LOCAL_BUILD_COMPLETE_BROWSER_PUBLISH_PENDING'};generated_at=$generated;unique_parcel_count=$rows.Count;new_row_count=$new;source_upgraded_count=$upgraded;address_geometry_enriched_count=$enriched;rejected_input_count=$rejected.Count;row_artifact_index_path=$indexRel;artifact_sha=$artifactSha;browser_match=$proof.browser_match;blockers=@($proof.blockers);final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
Write-Json (Join-Path $RepoRoot ($outputRel-replace'/','\')) $output;Write-Json (Join-Path $RepoRoot ($statusOutRel-replace'/','\')) $output
$report=@('# Parcel Label Task 174','',('- Status: '+$output.status),('- Unique parcels: '+$rows.Count),('- New: '+$new),('- Source upgraded: '+$upgraded),('- Address/geometry enriched: '+$enriched),('- Rejected inputs: '+$rejected.Count),('- Artifact SHA-256: '+$artifactSha),('- Browser match: '+$proof.browser_match),('- Blockers: '+(@($proof.blockers)-join'; ')),'- final_ready=false','- fake_data=false')-join"`n"
[IO.File]::WriteAllText((Join-Path $RepoRoot ($reportRel-replace'/','\')),$report,[Text.UTF8Encoding]::new($false))
$output|ConvertTo-Json -Depth 30
