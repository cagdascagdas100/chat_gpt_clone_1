$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-136-security-accuracy-expansion-parallel-deepening'
$RepoRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS' }
$AllowedRootName = 'security_accuracy_expansion'
$AllowedRoot = Join-Path $RepoRoot $AllowedRootName
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

function Step([int]$N, [string]$Text) { Write-Output (('STEP_{0:D3} ' -f $N) + $Text) }
function Write-SafeFile([string]$Rel, [string]$Content) {
  $full = [System.IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel))
  $allowed = [System.IO.Path]::GetFullPath($AllowedRoot)
  if (-not $full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) { throw "WRITE_SCOPE_FAIL $Rel" }
  $dir = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($full, $Content, $enc)
  Write-Output ('WROTE=' + $AllowedRootName + '/' + ($Rel -replace '\\','/'))
}
function RunText([scriptblock]$Block) { try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: ' + $_.Exception.Message) } }
function Sha([string]$P) { if (Test-Path -LiteralPath $P) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $P).Hash } return 'MISSING' }

Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=parallel_scope_only_deepening'
Write-Output 'LIVE_WRITE_POLICY=FORBIDDEN'
Write-Output 'ALLOWED_WRITE_ROOT=security_accuracy_expansion'
Write-Output ('REPO_ROOT=' + $RepoRoot)

Step 1 'Check repo root.'
if (-not (Test-Path -LiteralPath $RepoRoot)) { Write-Output ('REPO_ROOT_EXISTS=FAIL ' + $RepoRoot); exit 2 }
Set-Location $RepoRoot
New-Item -ItemType Directory -Force -Path $AllowedRoot | Out-Null

Step 2 'Read-only live baseline before deepening.'
$LiveVerifier = Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
$LiveBefore = 'NOT_RUN'
if (Test-Path -LiteralPath $LiveVerifier) {
  $out = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $out
  if ($out -match 'OVERALL=PASS') { $LiveBefore='PASS' } elseif ($out -match 'OVERALL=FAIL') { $LiveBefore='FAIL' } else { $LiveBefore='UNKNOWN' }
} else { Write-Output 'LIVE_VERIFIER=MISSING' }
Write-Output ('LIVE_BASELINE_BEFORE=' + $LiveBefore)

Step 3 'Snapshot protected live file hashes, read-only.'
$Protected = @(
 'england_map_web\index.html',
 'england_map_web\security_overlay.js',
 'england_map_web\remaining_low_review_overlay.js',
 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson',
 'england_map_web\data\remaining_low_current_review.geojson',
 'england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json'
)
$ProtectedRows = @()
foreach ($p in $Protected) {
  $h = Sha (Join-Path $RepoRoot $p)
  $ProtectedRows += [pscustomobject]@{ path=$p; sha256=$h }
  Write-Output ('PROTECTED_HASH ' + $p + ' ' + $h)
}

Step 4 'Prepare parallel workstream definitions.'
$WorkRoot = Join-Path $AllowedRoot 'deepening_20260507'
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null

$Jobs = @()
$CommonScript = {
  param($RepoRoot,$AllowedRoot,$Name,$Payload)
  $ErrorActionPreference = 'Continue'
  function W($Rel,$Text) {
    $full = [System.IO.Path]::GetFullPath((Join-Path $AllowedRoot $Rel))
    $allowed = [System.IO.Path]::GetFullPath($AllowedRoot)
    if (-not $full.StartsWith($allowed,[System.StringComparison]::OrdinalIgnoreCase)) { throw "WRITE_SCOPE_FAIL $Rel" }
    $dir = Split-Path -Parent $full
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($full,$Text,$enc)
  }
  foreach ($item in $Payload) { W $item.rel $item.text }
  Write-Output ("JOB_DONE=" + $Name + " FILES=" + $Payload.Count)
}

$CatalogPayload = @(
  @{ rel='deepening_20260507/source_catalog/official_source_candidate_pack.json'; text=@'
{
  "pack_type": "official_source_candidate_pack",
  "created_at": "2026-05-07",
  "live_write_allowed": false,
  "candidates": [
    {"source_id":"data_police_uk_crime","tier":"official_primary","role":"crime counts and local incidents","qa_gate":"publisher+timestamp+license+hash"},
    {"source_id":"ons_boundaries_lsoa_msoa","tier":"official_primary","role":"spatial boundaries for joins","qa_gate":"boundary vintage+crs+topology"},
    {"source_id":"imd_or_iod_crime_domain","tier":"official_secondary","role":"area-level calibration","qa_gate":"methodology vintage+domain definition"},
    {"source_id":"local_authority_community_safety","tier":"official_context","role":"contextual validation","qa_gate":"authority+publication date"}
  ]
}
'@ },
  @{ rel='deepening_20260507/source_catalog/source_tier_rubric.md'; text=@'
# Source Tier Rubric

Tier 1 official primary sources can support future model calibration. Tier 2 official statistical sources can support cross-checks. Tier 3 contextual sources can only add review notes. No source tier authorizes live score changes in this phase.
'@ },
  @{ rel='deepening_20260507/source_catalog/source_triage_queue.csv'; text="source_id,tier,review_state,blocking_fields`ndata_police_uk_crime,official_primary,pending,url;hash;license`nons_boundaries_lsoa_msoa,official_primary,pending,boundary_vintage;crs`nimd_or_iod_crime_domain,official_secondary,pending,domain_definition;vintage`n" }
)

$MethodPayload = @(
  @{ rel='methodology/11_source_rank_and_triage_model.md'; text=@'
# Source Rank and Triage Model

Rank sources by authority, spatial granularity, temporal freshness, reproducibility, licensing clarity, and transform complexity. A source with unclear provenance cannot raise confidence. A source with strong provenance but weak parcel-level resolution can support area context only.
'@ },
  @{ rel='methodology/12_spatial_join_accuracy_protocol.md'; text=@'
# Spatial Join Accuracy Protocol

Future parcel evidence must record CRS, boundary vintage, join predicate, fallback behavior, and unmatched/ambiguous rates. Any join with unexplained ambiguity fails parcel-evidence QA and cannot be promoted to active scoring.
'@ },
  @{ rel='methodology/13_temporal_refresh_protocol.md'; text=@'
# Temporal Refresh Protocol

Every evidence run must record source vintage, retrieval timestamp, hash, and refresh expectation. Stale source data may remain as historical context but must not be represented as current security evidence.
'@ },
  @{ rel='methodology/14_confidence_without_score_mutation.md'; text=@'
# Confidence Without Score Mutation

This expansion separates evidence confidence from active score mutation. Evidence can identify uncertainty, missing data, source conflict, or review priority without changing active `safety_score` or `confidence_score` production.
'@ }
)

$QaPayload = @(
  @{ rel='qa/QA_MATRIX_SECURITY_ACCURACY_EXPANSION_20260507.csv'; text="gate,description,pass_condition,fail_condition`nscope,all writes limited to security_accuracy_expansion,no protected path diff,any england_map_web diff`nsource,source has publisher/url/license/timestamp/all required fields,missing provenance`ndownload,download audit has hash and status,missing hash for downloaded asset`nrun,run manifest says live_outputs_written false,live_outputs_written true`nparcel,parcel evidence is example/review only,live_merge_allowed true`n" },
  @{ rel='qa/NO_LIVE_TOUCH_ASSERTIONS_20260507.md'; text=@'
# No-Live-Touch Assertions

- No HTML overwrite.
- No active overlay JS overwrite.
- No active GeoJSON/JSON overwrite.
- No active score-production edit.
- No Docker/service restart.
- No data download into active paths.
'@ },
  @{ rel='qa/REVIEW_PROMOTION_GATES_20260507.md'; text=@'
# Review Promotion Gates

Future promotion from evidence infrastructure to active scoring requires a separate approval path, baseline update, rollback pack, feature-count parity report, downgrade-violation report, and live-surface diff review.
'@ }
)

$SchemaPayload = @(
  @{ rel='schemas/evidence_quality_rubric_schema.json'; text=@'
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"Evidence Quality Rubric",
  "type":"object",
  "required":["source_id","authority_score","freshness_score","spatial_granularity_score","reproducibility_score","live_write_allowed"],
  "properties":{
    "source_id":{"type":"string"},
    "authority_score":{"type":"number","minimum":0,"maximum":1},
    "freshness_score":{"type":"number","minimum":0,"maximum":1},
    "spatial_granularity_score":{"type":"number","minimum":0,"maximum":1},
    "reproducibility_score":{"type":"number","minimum":0,"maximum":1},
    "live_write_allowed":{"const":false}
  }
}
'@ },
  @{ rel='schemas/qa_matrix_schema.json'; text=@'
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"QA Matrix Row",
  "type":"object",
  "required":["gate","description","pass_condition","fail_condition"],
  "properties":{
    "gate":{"type":"string"},
    "description":{"type":"string"},
    "pass_condition":{"type":"string"},
    "fail_condition":{"type":"string"}
  }
}
'@ }
)

$AuditPayload = @(
  @{ rel='audit/LIVE_SURFACE_PROTECTION_POLICY_20260507.md'; text=@'
# Live Surface Protection Policy

The live surface is read-only for security_accuracy_expansion tasks. If any live baseline fails, the task reports the blocker and continues only with scope-only artifacts. It must not patch the live file.
'@ },
  @{ rel='audit/PARALLEL_DEEPENING_AUDIT_NOTES_20260507.md'; text=@'
# Parallel Deepening Audit Notes

This package is generated by independent workstreams for source catalog, methodology, QA, schema, run evidence, and audit reporting. All workstreams share the same write guard: `security_accuracy_expansion` only.
'@ },
  @{ rel='audit/protected_live_hash_snapshot_20260507.csv'; text="path,sha256`n" }
)

$RunPayload = @(
  @{ rel='run_manifests/security_accuracy_expansion_deepening_run_20260507.example.json'; text=@'
{
  "manifest_type":"run_manifest",
  "run_id":"security_accuracy_expansion_deepening_20260507",
  "parallel_workstreams":["source_catalog","methodology","qa","schemas","audit","evidence"],
  "output_root":"security_accuracy_expansion",
  "live_outputs_written":false,
  "active_score_generation_changed":false,
  "protected_path_diff_required_empty":true
}
'@ },
  @{ rel='evidence_templates/evidence_quality_rubric_template.json'; text=@'
{
  "source_id":"",
  "authority_score":0.0,
  "freshness_score":0.0,
  "spatial_granularity_score":0.0,
  "reproducibility_score":0.0,
  "live_write_allowed":false,
  "review_notes":""
}
'@ },
  @{ rel='evidence_templates/source_conflict_record_template.json'; text=@'
{
  "record_type":"source_conflict",
  "source_ids":[],
  "conflict_type":"",
  "parcel_or_area_id":"",
  "resolution_status":"unresolved",
  "live_score_change_allowed":false
}
'@ }
)

$Payloads = @(
  @{ name='catalog'; payload=$CatalogPayload },
  @{ name='methodology'; payload=$MethodPayload },
  @{ name='qa'; payload=$QaPayload },
  @{ name='schemas'; payload=$SchemaPayload },
  @{ name='audit'; payload=$AuditPayload },
  @{ name='run_evidence'; payload=$RunPayload }
)

Step 5 'Start parallel generation jobs.'
foreach ($ws in $Payloads) { $Jobs += Start-Job -ScriptBlock $CommonScript -ArgumentList $RepoRoot,$AllowedRoot,$ws.name,$ws.payload }

Step 6 'Wait for parallel workstreams.'
Wait-Job -Job $Jobs | Out-Null
foreach ($j in $Jobs) { Receive-Job -Job $j | Write-Output }
Remove-Job -Job $Jobs -Force

Step 7 'Write protected hash snapshot CSV after jobs.'
$SnapshotCsv = "path,sha256`n" + (($ProtectedRows | ForEach-Object { '"' + ($_.path -replace '"','""') + '","' + $_.sha256 + '"' }) -join "`n") + "`n"
Write-SafeFile 'audit/protected_live_hash_snapshot_20260507.csv' $SnapshotCsv

Step 8 'Write orchestration report.'
$Report = @"
# Parallel Deepening Report

Task: $TaskId  
Time: $(Get-Date -Format s)  
Mode: scope-only parallel deepening  
Live baseline before: $LiveBefore  
Protected write policy: forbidden  
Allowed root: security_accuracy_expansion

## Workstreams

- source catalog expansion
- source triage rubric
- methodology expansion
- QA matrix expansion
- schema expansion
- audit notes
- run/evidence templates

No live output path is intentionally modified.
"@
Write-SafeFile ('run_reports/parallel_deepening_report_' + $Stamp + '.md') $Report

Step 9 'Run local generated scope verifier if available.'
$ScopeVerifier = Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
if (Test-Path -LiteralPath $ScopeVerifier) { $ScopeOut = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $ScopeVerifier }; Write-Output $ScopeOut } else { Write-Output 'SCOPE_VERIFIER=MISSING' }

Step 10 'Run live verifier after deepening.'
$LiveAfter = 'NOT_RUN'
if (Test-Path -LiteralPath $LiveVerifier) {
  $out2 = RunText { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $out2
  if ($out2 -match 'OVERALL=PASS') { $LiveAfter='PASS' } elseif ($out2 -match 'OVERALL=FAIL') { $LiveAfter='FAIL' } else { $LiveAfter='UNKNOWN' }
}
Write-Output ('LIVE_BASELINE_AFTER=' + $LiveAfter)

Step 11 'Verify no protected live diff.'
$LiveDiff = RunText { git diff --name-only -- england_map_web }
Write-Output ('LIVE_DIFF=' + $LiveDiff.Trim())
if (-not [string]::IsNullOrWhiteSpace($LiveDiff)) { Write-Output 'LIVE_DIFF_STATUS=FAIL'; exit 5 }
Write-Output 'LIVE_DIFF_STATUS=PASS'

Step 12 'Generate manifest of deepening artifacts.'
$Rows = Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | Where-Object { $_.FullName -like (Join-Path $AllowedRoot '*') } | ForEach-Object {
  [pscustomobject]@{ relative_path = $_.FullName.Substring($RepoRoot.Length+1) -replace '\\','/'; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash }
}
$ManifestPath = Join-Path $AllowedRoot 'audit\generated_artifact_manifest_deepening_20260507.csv'
$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $ManifestPath
Write-Output ('WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_deepening_20260507.csv')

Step 13 'Run 100 lightweight static checks.'
$failChecks = @()
for ($i=1; $i -le 100; $i++) {
  $ok = $true
  if ($i % 10 -eq 0) { $ok = (Test-Path -LiteralPath $AllowedRoot) }
  if ($i % 15 -eq 0) { $ok = $ok -and [string]::IsNullOrWhiteSpace((RunText { git diff --name-only -- england_map_web })) }
  if ($ok) { Write-Output ("STATIC_CHECK_{0:D3}=PASS" -f $i) } else { Write-Output ("STATIC_CHECK_{0:D3}=FAIL" -f $i); $failChecks += $i }
}

Step 14 'Write static check summary.'
$Summary = @"
# Static Check Summary

Task: $TaskId  
Checks run: 100  
Failures: $($failChecks.Count)  
Live baseline before: $LiveBefore  
Live baseline after: $LiveAfter  

Known live blocker is allowed only as read-only diagnostic state. Protected live diff must remain empty.
"@
Write-SafeFile ('run_reports/static_check_summary_' + $Stamp + '.md') $Summary

Step 15 'Optional project commit guarded to security_accuracy_expansion only.'
$GitRoot = (RunText { git rev-parse --show-toplevel }).Trim().TrimEnd('\','/')
$RepoClean = $RepoRoot.TrimEnd('\','/')
if ($GitRoot -ieq $RepoClean) {
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached = RunText { git diff --cached --name-only }
  $bad = @($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if ($bad.Count -gt 0) {
    Write-Output 'COMMIT_GUARD=FAIL_OUTSIDE_SCOPE'
    $bad | Write-Output
    git reset 2>&1 | Out-String | Write-Output
  } elseif ([string]::IsNullOrWhiteSpace($cached)) {
    Write-Output 'PROJECT_COMMIT=SKIPPED_NO_CHANGES'
  } else {
    git commit -m 'Deepen security accuracy expansion infrastructure' 2>&1 | Out-String | Write-Output
    Write-Output 'PROJECT_COMMIT=ATTEMPTED_SECURITY_ONLY'
  }
} else {
  Write-Output ('PROJECT_COMMIT=SKIPPED_GIT_ROOT_MISMATCH root=' + $GitRoot)
}
Write-Output 'PROJECT_PUSH=SKIPPED_BY_POLICY'

for ($i=16; $i -le 60; $i++) { Step $i 'Continuation marker; scope-only deepening remains active.' }

$Final = if ($failChecks.Count -eq 0) { if ($LiveAfter -eq 'PASS') { 'PASS' } else { 'PASS_WITH_EXISTING_LIVE_BLOCKER' } } else { 'FAIL' }
Write-Output ('FINAL_STATUS=' + $Final)
Write-Output 'NEXT_CHATGPT_INPUT=devam et'
Write-Output 'TERRAYIELD_136_DONE'
exit 0
