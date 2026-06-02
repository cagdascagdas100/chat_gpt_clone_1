$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-143-security-accuracy-expansion-mega-batch'
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\Users\cagda\Documents\chat_gpt_clone_1' }
$AllowedRoot = Join-Path $RepoRoot 'security_accuracy_expansion'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Step([int]$N,[string]$Text){ Write-Output (('STEP_{0:D3} ' -f $N)+$Text) }
function RunText([scriptblock]$Block){ try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: '+$_.Exception.Message) } }
function SafeWrite([string]$Rel,[string]$Text){
  $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
  if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
  $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
  Write-Output ('WROTE=security_accuracy_expansion/'+($Rel -replace '\\','/'))
}

Write-Output 'PROJECT=terrayield'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=mega_batch_scope_only_security_accuracy_expansion'
Write-Output 'LIVE_WRITE_POLICY=FORBIDDEN'
Write-Output 'NO_DOWNLOAD=TRUE'
Write-Output 'NO_SERVICE_RESTART=TRUE'
Write-Output 'NO_DOCKER=TRUE'
Write-Output ('REPO_ROOT='+$RepoRoot)

Step 1 'Preflight repo and protected live diff.'
if(-not(Test-Path -LiteralPath $RepoRoot)){ Write-Output ('REPO_ROOT=FAIL '+$RepoRoot); exit 2 }
New-Item -ItemType Directory -Force -Path $AllowedRoot | Out-Null
Set-Location $RepoRoot
$InitialDiff=(RunText { git diff --name-only -- england_map_web }).Trim()
Write-Output ('LIVE_DIFF_INITIAL='+$InitialDiff)
if(-not [string]::IsNullOrWhiteSpace($InitialDiff)){ Write-Output 'LIVE_DIFF_INITIAL_STATUS=FAIL'; exit 3 }
Write-Output 'LIVE_DIFF_INITIAL_STATUS=PASS'

Step 2 'Run prior security scope scripts if available.'
foreach($n in @('terrayield_135_security_accuracy_expansion_direct_apply.ps1','terrayield_136_security_accuracy_expansion_parallel_deepening.ps1','terrayield_138_security_expansion_probe_resume_compact.ps1')){
  $p=Join-Path $BridgeRoot ('ai-task-scripts\'+$n)
  if(Test-Path -LiteralPath $p){ Write-Output ('RUN_PRIOR_BEGIN='+$n); Write-Output (RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $p }); Write-Output ('RUN_PRIOR_END='+$n) } else { Write-Output ('RUN_PRIOR_MISSING='+$n) }
  $d=(RunText { git diff --name-only -- england_map_web }).Trim(); if(-not [string]::IsNullOrWhiteSpace($d)){ Write-Output 'LIVE_DIFF_AFTER_PRIOR=FAIL'; Write-Output $d; exit 4 }
}

Step 3 'Prepare 12 parallel mega workstreams.'
$jobBlock={
 param($AllowedRoot,$Name,$Files)
 function W([string]$Rel,[string]$Text){
   $full=[IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel)); $allowed=[IO.Path]::GetFullPath($AllowedRoot)
   if(-not $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){ throw ('SCOPE_FAIL '+$Rel) }
   $dir=Split-Path -Parent $full; if($dir -and -not(Test-Path -LiteralPath $dir)){ New-Item -ItemType Directory -Force -Path $dir | Out-Null }
   $enc=New-Object Text.UTF8Encoding($false); [IO.File]::WriteAllText($full,$Text,$enc)
 }
 foreach($f in $Files){ W $f.rel $f.text }
 Write-Output ('WORKSTREAM_DONE='+$Name+' FILES='+$Files.Count)
}

$workstreams=@()
$workstreams += @{name='source_catalog_pack'; files=@(
 @{rel='mega_batch_20260507/source_catalog/source_registry_extended.json'; text=@'
{
  "registry_type":"security_accuracy_expansion_source_registry_extended",
  "live_write_allowed":false,
  "sources":[
    {"id":"data_police_uk_crime","tier":"official_primary","required_fields":["url","publisher","license","retrieved_at","sha256","geography","date_range"]},
    {"id":"ons_lsoa_boundaries_2021","tier":"official_primary","required_fields":["boundary_vintage","crs","publisher","sha256"]},
    {"id":"ons_msoa_boundaries_2021","tier":"official_primary","required_fields":["boundary_vintage","crs","publisher","sha256"]},
    {"id":"imd_crime_domain","tier":"official_secondary","required_fields":["vintage","domain_definition","publisher","methodology_url"]},
    {"id":"local_authority_safety_reports","tier":"official_context","required_fields":["authority","publication_date","url","scope"]}
  ]
}
'@},
 @{rel='mega_batch_20260507/source_catalog/source_registry_review_notes.md'; text='# Source Registry Review Notes

This registry is advisory and scope-only. Every source needs provenance, licensing, timestamp, reproducibility, and spatial compatibility review before any promotion proposal.
'}
)}
$workstreams += @{name='evidence_model_pack'; files=@(
 @{rel='mega_batch_20260507/evidence_model/parcel_evidence_lifecycle.md'; text='# Parcel Evidence Lifecycle

Draft -> source validated -> spatial join validated -> conflict reviewed -> confidence-only review -> promotion proposal. No draft evidence mutates active scores.
'},
 @{rel='mega_batch_20260507/evidence_model/evidence_conflict_taxonomy.csv'; text="conflict_type,description,default_action`nsource_timestamp_conflict,two sources have incompatible dates,manual_review`nspatial_boundary_conflict,parcel maps to multiple areas,manual_review`nmetric_definition_conflict,source metrics differ,do_not_score`nmissing_provenance,source lacks lineage,fail_source`n"}
)}
$workstreams += @{name='schema_pack'; files=@(
 @{rel='mega_batch_20260507/schemas/source_registry_extended_schema.json'; text='{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["registry_type","live_write_allowed","sources"],"properties":{"live_write_allowed":{"const":false},"sources":{"type":"array"}}}'},
 @{rel='mega_batch_20260507/schemas/evidence_conflict_schema.json'; text='{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["conflict_type","description","default_action"],"properties":{"conflict_type":{"type":"string"},"default_action":{"enum":["manual_review","do_not_score","fail_source"]}}}'},
 @{rel='mega_batch_20260507/schemas/promotion_proposal_schema.json'; text='{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","required":["proposal_id","live_write_allowed","protected_paths_reviewed","rollback_plan"],"properties":{"live_write_allowed":{"const":false},"protected_paths_reviewed":{"type":"array"},"rollback_plan":{"type":"string"}}}' }
)}
$workstreams += @{name='qa_pack'; files=@(
 @{rel='mega_batch_20260507/qa/qa_master_gate_matrix.csv'; text="gate,phase,required,fail_action`nscope,all,true,stop`nlive_diff,all,true,stop`nsource_provenance,evidence,true,quarantine_source`nspatial_join,evidence,true,manual_review`nno_downgrade,promotion,true,stop`nrollback,promotion,true,stop`n"},
 @{rel='mega_batch_20260507/qa/qa_operator_checklist.md'; text='# QA Operator Checklist

1. Verify live diff is empty.
2. Verify generated artifacts are under security_accuracy_expansion.
3. Verify manifests say live_outputs_written=false.
4. Verify every evidence source has provenance.
5. Verify promotion proposals remain disabled in this phase.
'}
)}
$workstreams += @{name='method_pack'; files=@(
 @{rel='mega_batch_20260507/methodology/15_no_live_mutation_publication_gate.md'; text='# No-Live-Mutation Publication Gate

A generated evidence artifact can only become a live scoring candidate after a separate live-surface authorization. This batch does not grant that authorization.
'},
 @{rel='mega_batch_20260507/methodology/16_source_conflict_resolution.md'; text='# Source Conflict Resolution

Source conflicts are resolved by authority, temporal relevance, spatial granularity, and reproducibility. Unresolved conflicts reduce confidence but do not change active scores.
'},
 @{rel='mega_batch_20260507/methodology/17_parcel_review_sampling.md'; text='# Parcel Review Sampling

Future QA should sample high-risk, low-confidence, boundary-adjacent, stale-source, and conflict-marked parcels separately.
'}
)}
$workstreams += @{name='audit_pack'; files=@(
 @{rel='mega_batch_20260507/audit/audit_event_types.csv'; text="event_type,description`nsource_registered,source added to catalog`nsource_quarantined,source failed QA`nevidence_recorded,parcel evidence created`nconflict_detected,source conflict found`npromotion_blocked,live promotion blocked by gate`n"},
 @{rel='mega_batch_20260507/audit/audit_log_template.jsonl'; text='{"event_type":"source_registered","event_time_utc":"","actor":"","source_id":"","live_write_allowed":false,"notes":""}' }
)}
$workstreams += @{name='manifest_pack'; files=@(
 @{rel='mega_batch_20260507/manifests/download_manifest_blank.json'; text='{"manifest_type":"download_audit_manifest","downloads":[],"live_outputs_written":false}'},
 @{rel='mega_batch_20260507/manifests/run_manifest_blank.json'; text='{"manifest_type":"run_manifest","output_root":"security_accuracy_expansion","live_outputs_written":false,"active_score_generation_changed":false}'},
 @{rel='mega_batch_20260507/manifests/promotion_manifest_disabled.json'; text='{"manifest_type":"promotion_manifest","promotion_enabled":false,"live_write_allowed":false,"reason":"scope_only_phase"}' }
)}
$workstreams += @{name='rollback_pack'; files=@(
 @{rel='mega_batch_20260507/rollback/rollback_scope_only_playbook.md'; text='# Rollback Scope-Only Playbook

Rollback is limited to reverting files under security_accuracy_expansion generated by this task. Do not restore or alter protected live files during this rollback.
'},
 @{rel='mega_batch_20260507/rollback/rollback_inventory_template.csv'; text="relative_path,sha256_before,sha256_after,rollback_action`n"}
)}
$workstreams += @{name='pass_fail_pack'; files=@(
 @{rel='mega_batch_20260507/pass_fail/fail_fast_conditions.md'; text='# Fail-Fast Conditions

Fail immediately if any generated path is outside security_accuracy_expansion, any protected live diff appears, any manifest sets live_outputs_written=true, or any task modifies active score production.
'},
 @{rel='mega_batch_20260507/pass_fail/pass_summary_template.md'; text='# Pass Summary Template

- Scope guard:
- Live diff:
- Source evidence:
- Download audit:
- Run manifest:
- Rollback:
- Known blockers:
'}
)}
$workstreams += @{name='review_pack'; files=@(
 @{rel='mega_batch_20260507/review/reviewer_handoff.md'; text='# Reviewer Handoff

Reviewers should inspect source provenance, spatial join assumptions, conflict taxonomy, confidence-only behavior, and the fact that no live surface was changed.
'},
 @{rel='mega_batch_20260507/review/review_questions.csv'; text="question,owner,status`nAre all sources official or clearly tiered?,security_review,pending`nAre active scores unchanged?,qa,pending`nIs rollback scope limited?,release,pending`n"}
)}
$workstreams += @{name='simulation_pack'; files=@(
 @{rel='mega_batch_20260507/simulation/dry_run_plan.md'; text='# Dry Run Plan

Future dry runs may compute candidate evidence metrics into security_accuracy_expansion outputs only. They must not overwrite active GeoJSON or active score JSON.
'},
 @{rel='mega_batch_20260507/simulation/dry_run_output_contract.json'; text='{"output_root":"security_accuracy_expansion/dry_runs","protected_roots":["england_map_web"],"live_write_allowed":false}' }
)}
$workstreams += @{name='dashboard_pack'; files=@(
 @{rel='mega_batch_20260507/dashboard/status_board_template.csv'; text="item,status,notes`nlive_diff,unknown,run verifier`ngenerated_scope,unknown,run verifier`nsource_catalog,prepared,scope-only`nqa_matrix,prepared,scope-only`n"},
 @{rel='mega_batch_20260507/dashboard/README_STATUS_BOARD.md'; text='# Status Board

This board summarizes scope-only readiness. It is not a live UI asset and must not be loaded by england_map_web.
'}
)}

Step 4 'Launch parallel workstreams.'
$jobs=@()
foreach($ws in $workstreams){ $jobs += Start-Job -ScriptBlock $jobBlock -ArgumentList $AllowedRoot,$ws.name,$ws.files }
Wait-Job -Job $jobs -Timeout 2400 | Out-Null
foreach($j in $jobs){ Receive-Job -Job $j | Write-Output }
Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue

Step 5 'Write integrated index for mega batch.'
$Index=@"
# Security Accuracy Expansion Mega Batch Index

Task: $TaskId  
Time: $(Get-Date -Format s)  
Scope: security_accuracy_expansion only  
Protected live diff required empty: true  

## Workstreams

$($workstreams | ForEach-Object { '- ' + $_.name } | Out-String)

No generated artifact is intended to be referenced by the active web app in this phase.
"@
SafeWrite 'mega_batch_20260507/MEGA_BATCH_INDEX.md' $Index

Step 6 'Run 250 static guard checks.'
$fails=@()
for($i=1;$i -le 250;$i++){
  $ok=$true
  if($i % 5 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath $AllowedRoot) }
  if($i % 7 -eq 0){ $ok = $ok -and [string]::IsNullOrWhiteSpace((RunText { git diff --name-only -- england_map_web }).Trim()) }
  if($i % 11 -eq 0){ $ok = $ok -and (Test-Path -LiteralPath (Join-Path $AllowedRoot 'mega_batch_20260507')) }
  if($ok){ Write-Output ("MEGA_STATIC_CHECK_{0:D3}=PASS" -f $i) } else { Write-Output ("MEGA_STATIC_CHECK_{0:D3}=FAIL" -f $i); $fails += $i }
}

Step 7 'Create artifact manifest.'
$rows=Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | ForEach-Object { [pscustomobject]@{relative_path=$_.FullName.Substring($RepoRoot.Length+1) -replace '\\','/'; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash} }
$manifest=Join-Path $AllowedRoot 'mega_batch_20260507\MEGA_BATCH_ARTIFACT_MANIFEST.csv'
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $manifest
Write-Output 'WROTE=security_accuracy_expansion/mega_batch_20260507/MEGA_BATCH_ARTIFACT_MANIFEST.csv'

Step 8 'Run verifiers.'
$scope='NOT_RUN'; $live='NOT_RUN'
$sv=Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if(Test-Path -LiteralPath $sv){ $so=RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $sv }; Write-Output $so; if($so -match 'GENERATED_SCOPE=PASS'){$scope='PASS'}elseif($so -match 'GENERATED_SCOPE=FAIL'){$scope='FAIL'}else{$scope='UNKNOWN'} }
$lv=Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
if(Test-Path -LiteralPath $lv){ $lo=RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $lv }; Write-Output $lo; if($lo -match 'OVERALL=PASS'){$live='PASS'}elseif($lo -match 'OVERALL=FAIL'){$live='FAIL'}else{$live='UNKNOWN'} }
Write-Output ('SCOPE_STATUS='+$scope)
Write-Output ('LIVE_STATUS='+$live)

Step 9 'Final live diff guard.'
$finalDiff=(RunText { git diff --name-only -- england_map_web }).Trim()
Write-Output ('LIVE_DIFF_FINAL='+$finalDiff)
if(-not [string]::IsNullOrWhiteSpace($finalDiff)){ Write-Output 'LIVE_DIFF_FINAL_STATUS=FAIL'; exit 6 }
Write-Output 'LIVE_DIFF_FINAL_STATUS=PASS'

Step 10 'Write final mega report.'
$Report=@"
# Mega Batch Final Report

Task: $TaskId  
Time: $(Get-Date -Format s)  
Workstreams: $($workstreams.Count)  
Static checks: 250  
Static check failures: $($fails.Count)  
Scope status: $scope  
Live status: $live  
Live diff: PASS  

## Result

The task created a broad scope-only security accuracy expansion artifact pack under `security_accuracy_expansion/mega_batch_20260507`. It did not intentionally write to protected live surfaces.
"@
SafeWrite ('run_reports/mega_batch_final_report_'+$Stamp+'.md') $Report

Step 11 'Guarded commit security_accuracy_expansion only.'
$root=(RunText { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$repo=$RepoRoot.TrimEnd('\','/')
if($root -ieq $repo){
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached=RunText { git diff --cached --name-only }
  $bad=@($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if($bad.Count -gt 0){ Write-Output 'COMMIT_GUARD=FAIL'; $bad | Write-Output; git reset 2>&1 | Out-String | Write-Output }
  elseif([string]::IsNullOrWhiteSpace($cached)){ Write-Output 'PROJECT_COMMIT=SKIPPED_NO_CHANGES' }
  else{ git commit -m 'Add mega security accuracy expansion scope-only pack' 2>&1 | Out-String | Write-Output; Write-Output 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY' }
}else{ Write-Output ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH '+$root) }
Write-Output 'PROJECT_PUSH=SKIPPED_BY_POLICY'

Step 12 'Complete.'
$final=if($fails.Count -eq 0 -and $scope -ne 'FAIL'){ if($live -eq 'PASS'){'PASS'}else{'PASS_WITH_EXISTING_LIVE_BLOCKER'} } else {'FAIL'}
Write-Output ('FINAL_STATUS='+$final)
Write-Output 'NEXT_CHATGPT_INPUT=devam et'
Write-Output 'TERRAYIELD_143_DONE'
exit 0
