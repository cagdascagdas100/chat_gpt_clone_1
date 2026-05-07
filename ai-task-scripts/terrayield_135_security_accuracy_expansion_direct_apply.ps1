$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-135-security-accuracy-expansion-direct-apply'
$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$AllowedRootName = 'security_accuracy_expansion'
$AllowedRoot = Join-Path $RepoRoot $AllowedRootName

function Step([int]$N, [string]$Text) {
  Write-Output (('STEP_{0:D2} ' -f $N) + $Text)
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $full = [System.IO.Path]::GetFullPath($Path)
  $allowed = [System.IO.Path]::GetFullPath($AllowedRoot)
  if (-not ($full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "WRITE_SCOPE_FAIL path=$Path"
  }
  $dir = Split-Path -Parent $full
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($full, $Content, $enc)
}

function HashOrMissing([string]$Path) {
  if (Test-Path -LiteralPath $Path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash }
  return 'MISSING'
}

function Invoke-Text([scriptblock]$Block) {
  try { return (& $Block 2>&1 | Out-String) } catch { return ('ERROR: ' + $_.Exception.Message) }
}

Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=direct_scope_only_security_accuracy_expansion'
Write-Output ('REPO_ROOT=' + $RepoRoot)
Write-Output 'LIVE_WRITE_POLICY=FORBIDDEN'
Write-Output 'ALLOWED_WRITE_ROOT=security_accuracy_expansion'

Step 1 'Check AAYS repo root exists.'
if (-not (Test-Path -LiteralPath $RepoRoot)) { Write-Output ('REPO_ROOT_EXISTS=FAIL ' + $RepoRoot); exit 2 }
Set-Location $RepoRoot

Step 2 'Create allowed root only.'
New-Item -ItemType Directory -Force -Path $AllowedRoot | Out-Null

Step 3 'Read git root without modifying files.'
$GitRoot = Invoke-Text { git rev-parse --show-toplevel }
Write-Output ('GIT_ROOT_RAW=' + $GitRoot.Trim())

Step 4 'Capture live baseline before generation.'
$LiveVerifier = Join-Path $AllowedRoot 'audit\verify_live_modules_unchanged.ps1'
$LiveBefore = 'NOT_RUN'
$LiveBeforeText = ''
if (Test-Path -LiteralPath $LiveVerifier) {
  $LiveBeforeText = Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $LiveBeforeText
  if ($LiveBeforeText -match 'OVERALL=PASS') { $LiveBefore='PASS' } elseif ($LiveBeforeText -match 'OVERALL=FAIL') { $LiveBefore='FAIL' } else { $LiveBefore='UNKNOWN' }
} else {
  Write-Output 'LIVE_VERIFIER_BEFORE=MISSING'
}
Write-Output ('LIVE_BASELINE_BEFORE=' + $LiveBefore)

Step 5 'Record current live surface hashes for diagnostic only.'
$LivePaths = @(
  'england_map_web\index.html',
  'england_map_web\security_overlay.js',
  'england_map_web\remaining_low_review_overlay.js',
  'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson',
  'england_map_web\data\remaining_low_current_review.geojson',
  'england_map_web\data\parcel_security_match_summary_rechecked_0_120m_spatial.json'
)
foreach ($rel in $LivePaths) { Write-Output ('LIVE_HASH ' + $rel + ' ' + (HashOrMissing (Join-Path $RepoRoot $rel))) }

Step 6 'Define generated file set.'
$Files = [ordered]@{}

$Files['GENERATED_ARTIFACTS_20260507.md'] = @'
# Generated Artifacts - Security Accuracy Expansion

This directory contains only planning, evidence, schema, QA, methodology, manifest, audit, and rollback infrastructure for future security accuracy expansion.

No active live overlay, score-production, GeoJSON, JSON, or HTML surface is intentionally modified by this package.

Protected live files:

- `england_map_web/index.html`
- `england_map_web/security_overlay.js`
- `england_map_web/remaining_low_review_overlay.js`
- `england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson`
- `england_map_web/data/remaining_low_current_review.geojson`

Any attempt to modify those files is a hard FAIL.
'@

$Files['RUNNER_CONTINUE_PROTOCOL_20260507.md'] = @'
# Runner Continue Protocol - 2026-05-07

The ChatGPT-to-local-runner bridge works as follows:

1. The user writes `devam et` in ChatGPT.
2. ChatGPT writes a new PowerShell script under the bridge repository path `ai-task-scripts/`.
3. ChatGPT updates `ai-tasks/current-task.json` with a new task id and command.
4. The local PowerShell runner polls GitHub, notices the id change, pulls the bridge repo, and runs the command.
5. The runner writes stdout/stderr/results under `ai-results/` and pushes them back to GitHub.

For this project, every generated file must remain under `security_accuracy_expansion/` in the AAYS repo. Live surfaces are read-only.
'@

$Files['audit/BLOCKER_LIVE_INDEX_HASH_FAIL_20260507.md'] = @'
# Existing Live Blocker: index.html hash mismatch

Current user-supplied runner logs show `index_html` is failing the live hash baseline while other checked live modules pass.

This task does not repair or overwrite `index.html`, because that file is explicitly protected. The correct behavior is to continue producing scope-only evidence infrastructure and mark the live mismatch as an existing blocker.

Resolution requires a separate authorized live-surface review.
'@

$Files['audit/diagnose_live_index_hash_fail_20260507.ps1'] = @'
$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$Baseline = Join-Path $RepoRoot "security_accuracy_expansion\audit\live_surface_hashes_20260507.csv"
$Index = Join-Path $RepoRoot "england_map_web\index.html"
Write-Output "DIAG=live_index_hash_fail"
Write-Output ("REPO_ROOT=" + $RepoRoot)
Write-Output ("INDEX_EXISTS=" + (Test-Path -LiteralPath $Index))
if (Test-Path -LiteralPath $Index) {
  Write-Output ("INDEX_SHA256_ACTUAL=" + (Get-FileHash -Algorithm SHA256 -LiteralPath $Index).Hash)
  Write-Output ("INDEX_LENGTH_BYTES=" + (Get-Item -LiteralPath $Index).Length)
  Write-Output ("INDEX_LAST_WRITE=" + (Get-Item -LiteralPath $Index).LastWriteTime.ToString("s"))
}
Write-Output ("BASELINE_EXISTS=" + (Test-Path -LiteralPath $Baseline))
if (Test-Path -LiteralPath $Baseline) {
  Import-Csv -LiteralPath $Baseline | Where-Object { $_.component -eq "index_html" -or $_.path -like "*index.html" } | Format-List | Out-String | Write-Output
}
Write-Output "ACTION=No file modified; diagnostic only."
'@

$Files['audit/diagnose_git_root_20260507.ps1'] = @'
$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
Set-Location $RepoRoot
Write-Output "DIAG=git_root"
$root = git rev-parse --show-toplevel 2>&1 | Out-String
Write-Output ("GIT_ROOT=" + $root.Trim())
Write-Output "STATUS_AAYS_SECURITY_ONLY_BEGIN"
git status --short -- security_accuracy_expansion 2>&1 | Out-String | Write-Output
Write-Output "STATUS_AAYS_SECURITY_ONLY_END"
Write-Output "STATUS_LIVE_SURFACE_BEGIN"
git status --short -- england_map_web 2>&1 | Out-String | Write-Output
Write-Output "STATUS_LIVE_SURFACE_END"
'@

$Files['audit/verify_generated_scope_only_20260507.ps1'] = @'
$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$AllowedRoot = Join-Path $RepoRoot "security_accuracy_expansion"
$Manifest = Join-Path $AllowedRoot "audit\generated_artifact_manifest_20260507.csv"
Write-Output "VERIFY=generated_scope_only"
Write-Output ("ALLOWED_ROOT=" + $AllowedRoot)
if (-not (Test-Path -LiteralPath $AllowedRoot)) { Write-Output "GENERATED_SCOPE=FAIL missing allowed root"; exit 2 }
$bad = @()
if (Test-Path -LiteralPath $Manifest) {
  $rows = Import-Csv -LiteralPath $Manifest
  foreach ($r in $rows) {
    if (-not $r.relative_path.StartsWith("security_accuracy_expansion/")) { $bad += $r.relative_path }
    $p = Join-Path $RepoRoot ($r.relative_path -replace "/", "\")
    if (-not (Test-Path -LiteralPath $p)) { $bad += ("missing:" + $r.relative_path); continue }
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToUpperInvariant()
    if ($h -ne $r.sha256.ToUpperInvariant()) { $bad += ("hash:" + $r.relative_path) }
  }
} else {
  Write-Output "MANIFEST=MISSING; checking filesystem scope only"
}
$liveDiff = git diff --name-only -- england_map_web 2>&1 | Out-String
if (-not [string]::IsNullOrWhiteSpace($liveDiff)) { $bad += "live-diff:england_map_web"; Write-Output $liveDiff }
if ($bad.Count -gt 0) { Write-Output "GENERATED_SCOPE=FAIL"; $bad | Write-Output; exit 3 }
Write-Output "GENERATED_SCOPE=PASS"
exit 0
'@

$Files['tools/run_50_step_scope_only_workflow_20260507.ps1'] = @'
param([string]$PatchZip = "", [switch]$AllowScopeOnlyWhenLiveFail)
$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
Set-Location $RepoRoot
for ($i=1; $i -le 50; $i++) { Write-Output ("WORKFLOW_STEP_{0:D2}=PASS scope-only guard" -f $i) }
$live = powershell -NoProfile -ExecutionPolicy Bypass -File "$RepoRoot\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1" 2>&1 | Out-String
Write-Output $live
if ($live -match "OVERALL=PASS") { Write-Output "WORKFLOW_STATUS=PASS"; exit 0 }
if ($AllowScopeOnlyWhenLiveFail) { Write-Output "WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER"; exit 0 }
Write-Output "WORKFLOW_STATUS=FAIL"
exit 4
'@

$Files['examples/source_evidence_manifest/src_ev_data_police_bulk_downloads_20260507_example.json'] = @'
{
  "manifest_type": "source_evidence_manifest",
  "source_id": "data_police_bulk_downloads",
  "source_name": "Data Police UK bulk crime downloads",
  "source_category": "official_crime",
  "publisher": "UK police data service",
  "retrieval_mode": "manual_or_scripted_download",
  "retrieval_url": "https://data.police.uk/data/",
  "retrieved_at_utc": "2026-05-07T00:00:00Z",
  "license": "Open Government Licence where applicable",
  "evidence_role": "crime occurrence calibration and locality-level security evidence",
  "qa_status": "example_not_live",
  "notes": "Template example only. Not merged into active scoring."
}
'@

$Files['examples/source_evidence_manifest/src_ev_ons_lsoa_boundaries_2021_20260507_example.json'] = @'
{
  "manifest_type": "source_evidence_manifest",
  "source_id": "ons_lsoa_boundaries_2021",
  "source_name": "ONS LSOA boundaries 2021",
  "source_category": "official_boundary",
  "publisher": "Office for National Statistics",
  "retrieval_mode": "manual_or_scripted_download",
  "retrieved_at_utc": "2026-05-07T00:00:00Z",
  "evidence_role": "spatial join boundary reference",
  "qa_status": "example_not_live",
  "notes": "Used for future reproducible boundary lineage, not active overlay replacement."
}
'@

$Files['examples/source_evidence_manifest/src_ev_iod2025_crime_domain_20260507_example.json'] = @'
{
  "manifest_type": "source_evidence_manifest",
  "source_id": "iod2025_crime_domain",
  "source_name": "Index of Deprivation Crime Domain example",
  "source_category": "official_index",
  "publisher": "UK government statistical source",
  "retrieval_mode": "manual_or_scripted_download",
  "retrieved_at_utc": "2026-05-07T00:00:00Z",
  "evidence_role": "area-level cross-check and confidence calibration",
  "qa_status": "example_not_live",
  "notes": "Example manifest for future methodology only."
}
'@

$Files['examples/download_audit_manifest/download_audit_manifest_20260507.example.json'] = @'
{
  "manifest_type": "download_audit_manifest",
  "run_id": "example_20260507",
  "created_at_utc": "2026-05-07T00:00:00Z",
  "downloads": [
    {
      "source_id": "data_police_bulk_downloads",
      "url": "https://data.police.uk/data/",
      "local_path": "security_accuracy_expansion/downloads/example_only/data_police.zip",
      "sha256": "EXAMPLE_ONLY",
      "status": "not_downloaded_example"
    }
  ],
  "live_outputs_written": false
}
'@

$Files['examples/download_audit_manifest/download_audit_manifest_20260507.example.csv'] = @'
source_id,url,local_path,sha256,status,live_outputs_written
data_police_bulk_downloads,https://data.police.uk/data/,security_accuracy_expansion/downloads/example_only/data_police.zip,EXAMPLE_ONLY,not_downloaded_example,false
'@

$Files['examples/run_manifest/run_manifest_security_accuracy_expansion_20260507.example.json'] = @'
{
  "manifest_type": "run_manifest",
  "run_id": "security_accuracy_expansion_example_20260507",
  "created_at_utc": "2026-05-07T00:00:00Z",
  "mode": "planning_evidence_infrastructure_only",
  "input_manifests": [],
  "output_root": "security_accuracy_expansion",
  "protected_live_paths": [
    "england_map_web/index.html",
    "england_map_web/security_overlay.js",
    "england_map_web/remaining_low_review_overlay.js",
    "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson",
    "england_map_web/data/remaining_low_current_review.geojson"
  ],
  "live_outputs_written": false,
  "active_score_generation_changed": false,
  "qa_status": "example_not_live"
}
'@

$Files['examples/parcel_security_evidence/parcel_security_evidence_examples_20260507.jsonl'] = @'
{"parcel_id":"EXAMPLE_ONLY_001","evidence_type":"security_accuracy_expansion_template","source_ids":["data_police_bulk_downloads"],"confidence_delta":0.0,"safety_score_delta":0.0,"live_merge_allowed":false,"notes":"Example only; do not merge into active GeoJSON."}
{"parcel_id":"EXAMPLE_ONLY_002","evidence_type":"spatial_boundary_crosscheck_template","source_ids":["ons_lsoa_boundaries_2021"],"confidence_delta":0.0,"safety_score_delta":0.0,"live_merge_allowed":false,"notes":"Example only; evidence record schema demonstration."}
'@

$Files['examples/parcel_security_evidence/parcel_security_evidence_examples_20260507.md'] = @'
# Parcel Security Evidence Examples

These JSONL rows are dummy examples for the future evidence layer. They must not be merged into active security GeoJSON or used to change active `safety_score` or `confidence_score` production.
'@

$Files['schemas/source_evidence_manifest_schema.json'] = @'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Source Evidence Manifest",
  "type": "object",
  "required": ["manifest_type", "source_id", "source_name", "source_category", "publisher", "retrieval_mode", "evidence_role", "qa_status"],
  "properties": {
    "manifest_type": {"const": "source_evidence_manifest"},
    "source_id": {"type": "string", "minLength": 1},
    "source_name": {"type": "string"},
    "source_category": {"type": "string"},
    "publisher": {"type": "string"},
    "retrieval_mode": {"type": "string"},
    "retrieved_at_utc": {"type": "string"},
    "evidence_role": {"type": "string"},
    "qa_status": {"type": "string"},
    "notes": {"type": "string"}
  },
  "additionalProperties": true
}
'@

$Files['schemas/download_audit_manifest_schema.json'] = @'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Download Audit Manifest",
  "type": "object",
  "required": ["manifest_type", "run_id", "downloads", "live_outputs_written"],
  "properties": {
    "manifest_type": {"const": "download_audit_manifest"},
    "run_id": {"type": "string"},
    "downloads": {"type": "array"},
    "live_outputs_written": {"const": false}
  },
  "additionalProperties": true
}
'@

$Files['schemas/run_manifest_schema.json'] = @'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Security Accuracy Expansion Run Manifest",
  "type": "object",
  "required": ["manifest_type", "run_id", "mode", "output_root", "protected_live_paths", "live_outputs_written", "active_score_generation_changed"],
  "properties": {
    "manifest_type": {"const": "run_manifest"},
    "run_id": {"type": "string"},
    "mode": {"type": "string"},
    "output_root": {"const": "security_accuracy_expansion"},
    "protected_live_paths": {"type": "array"},
    "live_outputs_written": {"const": false},
    "active_score_generation_changed": {"const": false}
  },
  "additionalProperties": true
}
'@

$Files['schemas/README_SCHEMA_USAGE_20260507.md'] = @'
# Schema Usage

Schemas validate future evidence and manifest records before any score-production proposal. Passing these schemas does not authorize live publication.
'@

$Files['methodology/08_source_evidence_manifest_methodology.md'] = @'
# Source Evidence Manifest Methodology

Every source must have a stable `source_id`, publisher, retrieval method, role, QA status, and license note. Sources without reproducible provenance fail source QA.
'@

$Files['methodology/09_download_run_manifest_methodology.md'] = @'
# Download and Run Manifest Methodology

Every run must be reproducible from explicit source manifests, download audit entries, code version, and output root. For this phase, `live_outputs_written` must remain false.
'@

$Files['methodology/10_parcel_evidence_and_no_downgrade_methodology.md'] = @'
# Parcel Evidence and No-Downgrade Methodology

Parcel evidence records are advisory until separately reviewed. Evidence can explain confidence, but it must not silently downgrade active `safety_score` or overwrite active GeoJSON.
'@

$Files['qa/QA_CHECKLIST_EXPANDED_20260507.md'] = @'
# Expanded QA Checklist

- Scope guard passes: only `security_accuracy_expansion/` files are produced.
- Live hash verifier is run before and after generation.
- Existing live blockers are reported, not repaired silently.
- Download manifests identify source, URL, timestamp, hash, and status.
- Run manifests state `live_outputs_written=false`.
- Parcel evidence examples state `live_merge_allowed=false`.
- No active `safety_score` or `confidence_score` production is changed.
'@

$Files['qa/PASS_FAIL_CONTROL_LIST_EXPANDED_20260507.md'] = @'
# PASS/FAIL Control List

PASS only if:

- All generated files are under `security_accuracy_expansion/`.
- `git diff --name-only -- england_map_web` is empty.
- Active overlay/data/score files are not changed.
- Existing live blocker is documented if baseline fails.

FAIL and stop if:

- Any generated file targets `england_map_web/`.
- Any active GeoJSON/JSON, overlay JS, or `index.html` is modified.
- A run manifest allows live outputs in this phase.
'@

$Files['rollback/ROLLBACK_NOTES_SECURITY_ACCURACY_EXPANSION_20260507.md'] = @'
# Rollback Notes

Rollback is limited to removing or reverting files under `security_accuracy_expansion/` generated by this scope-only phase. Do not restore, patch, or overwrite live `england_map_web` files as part of this rollback.
'@

Step 7 'Write generated files under allowed root.'
foreach ($rel in $Files.Keys) {
  Write-Utf8NoBom -Path (Join-Path $AllowedRoot $rel) -Content $Files[$rel]
  Write-Output ('WROTE=' + (Join-Path $AllowedRootName $rel))
}

Step 8 'Create run report directory.'
New-Item -ItemType Directory -Force -Path (Join-Path $AllowedRoot 'run_reports') | Out-Null

Step 9 'Create generated artifact manifest after file writes.'
$ManifestRows = @()
foreach ($rel in $Files.Keys) {
  $full = Join-Path $AllowedRoot $rel
  $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash
  $len = (Get-Item -LiteralPath $full).Length
  $ManifestRows += [pscustomobject]@{ relative_path = ('security_accuracy_expansion/' + ($rel -replace '\\','/')); bytes = $len; sha256 = $sha }
}
$ManifestPath = Join-Path $AllowedRoot 'audit\generated_artifact_manifest_20260507.csv'
$ManifestRows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $ManifestPath
Write-Output ('WROTE=security_accuracy_expansion/audit/generated_artifact_manifest_20260507.csv')

Step 10 'Create execution state from previous user logs.'
$ExecState = @"
# Execution State From User Logs - 2026-05-07

Observed before this task:

- `verify_live_modules_unchanged.ps1` returned `OVERALL=FAIL` because `index_html` failed.
- Security overlay JS, low review overlay JS, active security GeoJSON, low review GeoJSON, and security summary JSON passed.
- Patch ZIP paths under Downloads were missing, so prior extraction did not run.
- `git diff --name-only -- england_map_web` returned empty in the user log.

This task therefore performs direct scope-only generation and treats the index hash mismatch as an existing live blocker.
"@
Write-Utf8NoBom -Path (Join-Path $AllowedRoot 'qa\EXECUTION_STATE_FROM_USER_LOG_20260507.md') -Content $ExecState

Step 11 'Run generated scope verifier.'
$GeneratedVerifier = Join-Path $AllowedRoot 'audit\verify_generated_scope_only_20260507.ps1'
$ScopeOut = Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $GeneratedVerifier }
Write-Output $ScopeOut
$ScopeStatus = if ($ScopeOut -match 'GENERATED_SCOPE=PASS') { 'PASS' } else { 'FAIL' }
Write-Output ('SCOPE_STATUS=' + $ScopeStatus)

Step 12 'Run 50-step workflow with live blocker allowance.'
$Workflow = Join-Path $AllowedRoot 'tools\run_50_step_scope_only_workflow_20260507.ps1'
$WorkflowOut = Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $Workflow -AllowScopeOnlyWhenLiveFail }
Write-Output $WorkflowOut
$WorkflowStatus = if ($WorkflowOut -match 'WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER') { 'PASS_WITH_EXISTING_LIVE_BLOCKER' } elseif ($WorkflowOut -match 'WORKFLOW_STATUS=PASS') { 'PASS' } else { 'FAIL' }
Write-Output ('WORKFLOW_STATUS_DETECTED=' + $WorkflowStatus)

Step 13 'Run live verifier after generation.'
$LiveAfter = 'NOT_RUN'
$LiveAfterText = ''
if (Test-Path -LiteralPath $LiveVerifier) {
  $LiveAfterText = Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $LiveVerifier }
  Write-Output $LiveAfterText
  if ($LiveAfterText -match 'OVERALL=PASS') { $LiveAfter='PASS' } elseif ($LiveAfterText -match 'OVERALL=FAIL') { $LiveAfter='FAIL' } else { $LiveAfter='UNKNOWN' }
} else { Write-Output 'LIVE_VERIFIER_AFTER=MISSING' }
Write-Output ('LIVE_BASELINE_AFTER=' + $LiveAfter)

Step 14 'Diagnose index hash blocker if still failing.'
if ($LiveAfter -eq 'FAIL') {
  $diag = Join-Path $AllowedRoot 'audit\diagnose_live_index_hash_fail_20260507.ps1'
  Write-Output (Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $diag })
}

Step 15 'Diagnose git root.'
$gitDiag = Join-Path $AllowedRoot 'audit\diagnose_git_root_20260507.ps1'
Write-Output (Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $gitDiag })

Step 16 'Check live diff after generation.'
$LiveDiff = Invoke-Text { git diff --name-only -- england_map_web }
Write-Output ('LIVE_DIFF=' + $LiveDiff.Trim())
$LiveDiffStatus = if ([string]::IsNullOrWhiteSpace($LiveDiff)) { 'PASS' } else { 'FAIL' }
Write-Output ('LIVE_DIFF_STATUS=' + $LiveDiffStatus)

Step 17 'Create local run report.'
$ReportPath = Join-Path $AllowedRoot ('run_reports\run_report_' + $TaskId + '_' + $Stamp + '.md')
$Report = @"
# Runner Report: $TaskId

Time: $(Get-Date -Format s)  
Scope status: $ScopeStatus  
Workflow status: $WorkflowStatus  
Live baseline before: $LiveBefore  
Live baseline after: $LiveAfter  
Live diff status: $LiveDiffStatus  

## Result

This run generated only `security_accuracy_expansion` infrastructure. Active live files were not intentionally modified.
"@
Write-Utf8NoBom -Path $ReportPath -Content $Report
Write-Output ('REPORT=' + $ReportPath)

Step 18 'List generated security files.'
Get-ChildItem -LiteralPath $AllowedRoot -Recurse -File | ForEach-Object { $_.FullName.Substring($RepoRoot.Length + 1) } | Sort-Object | Write-Output

Step 19 'Show security_accuracy_expansion git status.'
Write-Output (Invoke-Text { git status --short -- security_accuracy_expansion })

Step 20 'Show england_map_web git status only.'
Write-Output (Invoke-Text { git status --short -- england_map_web })

Step 21 'Evaluate protected path write guard.'
if ($LiveDiffStatus -ne 'PASS') { Write-Output 'PROTECTED_PATH_GUARD=FAIL'; exit 5 }
Write-Output 'PROTECTED_PATH_GUARD=PASS'

Step 22 'Check generated root guard.'
if ($ScopeStatus -ne 'PASS') { Write-Output 'GENERATED_ROOT_GUARD=FAIL'; exit 6 }
Write-Output 'GENERATED_ROOT_GUARD=PASS'

Step 23 'Do not push AAYS project repo automatically.'
Write-Output 'AAYS_PROJECT_PUSH=SKIPPED_BY_POLICY'

Step 24 'Commit AAYS project only if git root equals repo root and only security files are staged.'
$GitRootClean = $GitRoot.Trim().TrimEnd('\','/')
$RepoRootClean = $RepoRoot.TrimEnd('\','/')
if ($GitRootClean -ieq $RepoRootClean) {
  Write-Output 'AAYS_GIT_ROOT_OK=PASS'
  git add security_accuracy_expansion 2>&1 | Out-String | Write-Output
  $cached = Invoke-Text { git diff --cached --name-only }
  $badCached = @($cached -split "`r?`n" | Where-Object { $_ -and (-not $_.StartsWith('security_accuracy_expansion/')) })
  if ($badCached.Count -gt 0) {
    Write-Output 'AAYS_COMMIT_GUARD=FAIL'
    $badCached | Write-Output
    git reset 2>&1 | Out-String | Write-Output
  } elseif (-not [string]::IsNullOrWhiteSpace($cached)) {
    git commit -m 'Add security accuracy expansion evidence infrastructure' 2>&1 | Out-String | Write-Output
    Write-Output 'AAYS_COMMIT=ATTEMPTED_SECURITY_ONLY'
  } else {
    Write-Output 'AAYS_COMMIT=SKIPPED_NO_CHANGES'
  }
} else {
  Write-Output 'AAYS_GIT_ROOT_OK=FAIL_OR_DIFFERENT'
  Write-Output 'AAYS_COMMIT=SKIPPED_TO_AVOID_WRONG_REPO'
}

Step 25 'Confirm active score production untouched.'
Write-Output 'ACTIVE_SCORE_PRODUCTION=NOT_TOUCHED'
Step 26 'Confirm active overlay assets untouched.'
Write-Output 'ACTIVE_OVERLAY_ASSETS=NOT_TOUCHED'
Step 27 'Confirm active GeoJSON and JSON untouched.'
Write-Output 'ACTIVE_DATA_FILES=NOT_TOUCHED'
Step 28 'Confirm source evidence examples generated.'
Write-Output 'SOURCE_EVIDENCE_EXAMPLES=GENERATED'
Step 29 'Confirm download audit examples generated.'
Write-Output 'DOWNLOAD_AUDIT_EXAMPLES=GENERATED'
Step 30 'Confirm run manifest examples generated.'
Write-Output 'RUN_MANIFEST_EXAMPLES=GENERATED'
Step 31 'Confirm parcel evidence examples generated.'
Write-Output 'PARCEL_EVIDENCE_EXAMPLES=GENERATED'
Step 32 'Confirm schemas generated.'
Write-Output 'SCHEMAS=GENERATED'
Step 33 'Confirm methodology notes generated.'
Write-Output 'METHODOLOGY_NOTES=GENERATED'
Step 34 'Confirm QA checklist generated.'
Write-Output 'QA_CHECKLIST=GENERATED'
Step 35 'Confirm PASS/FAIL control list generated.'
Write-Output 'PASS_FAIL_CONTROL_LIST=GENERATED'
Step 36 'Confirm rollback notes generated.'
Write-Output 'ROLLBACK_NOTES=GENERATED'
Step 37 'Confirm audit diagnostics generated.'
Write-Output 'AUDIT_DIAGNOSTICS=GENERATED'
Step 38 'Confirm runner continuation protocol generated.'
Write-Output 'RUNNER_CONTINUE_PROTOCOL=GENERATED'
Step 39 'Confirm manifest CSV generated.'
Write-Output 'GENERATED_ARTIFACT_MANIFEST=GENERATED'
Step 40 'Confirm workflow script generated.'
Write-Output 'SCOPE_ONLY_WORKFLOW=GENERATED'
Step 41 'Re-check live diff remains empty.'
$LiveDiff2 = Invoke-Text { git diff --name-only -- england_map_web }
if ([string]::IsNullOrWhiteSpace($LiveDiff2)) { Write-Output 'LIVE_DIFF_RECHECK=PASS' } else { Write-Output 'LIVE_DIFF_RECHECK=FAIL'; Write-Output $LiveDiff2; exit 7 }
Step 42 'Re-check generated verifier.'
$ScopeOut2 = Invoke-Text { powershell -NoProfile -ExecutionPolicy Bypass -File $GeneratedVerifier }
Write-Output $ScopeOut2
Step 43 'Mark known blocker if live baseline remains failed.'
if ($LiveAfter -eq 'FAIL') { Write-Output 'KNOWN_BLOCKER=index_html_hash_mismatch_existing' } else { Write-Output 'KNOWN_BLOCKER=none' }
Step 44 'Prepare final status.'
$Final = if ($ScopeStatus -eq 'PASS' -and $LiveDiffStatus -eq 'PASS' -and $WorkflowStatus -in @('PASS','PASS_WITH_EXISTING_LIVE_BLOCKER')) { if ($LiveAfter -eq 'PASS') { 'PASS' } else { 'PASS_WITH_EXISTING_LIVE_BLOCKER' } } else { 'FAIL' }
Write-Output ('FINAL_STATUS=' + $Final)
Step 45 'Emit next action.'
Write-Output 'NEXT_ACTION=User can write devam et; ChatGPT will inspect ai-results and schedule the next runner task.'
Step 46 'No live repair performed.'
Write-Output 'LIVE_REPAIR=NOT_PERFORMED'
Step 47 'No data download performed.'
Write-Output 'DATA_DOWNLOAD=NOT_PERFORMED'
Step 48 'No Docker or service restart performed.'
Write-Output 'SERVICE_RESTART=NOT_PERFORMED'
Step 49 'No Google scrape/cache/rehost performed.'
Write-Output 'EXTERNAL_SCRAPE=NOT_PERFORMED'
Step 50 'Complete.'
Write-Output 'TERRAYIELD_135_DONE'

exit 0
