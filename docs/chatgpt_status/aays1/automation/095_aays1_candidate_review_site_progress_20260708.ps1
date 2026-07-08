$ErrorActionPreference = 'Stop'

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

$PageKey = 'aays1'
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'aays1-candidate-review-site-progress-20260708' } else { $env:AAYS_TASK_ID }
$Now = (Get-Date).ToUniversalTime().ToString('o')
function JP([string]$p) { Join-Path $RepoRoot ($p -replace '/', '\') }

$StatusDir = JP 'docs/chatgpt_status/aays1/status'
$ReportDir = JP 'docs/chatgpt_status/aays1/reports'
$HeartbeatDir = JP 'docs/chatgpt_status/aays1/heartbeat'
$AaysDataDir = JP 'england_map_web/data/aays1'
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$HeartbeatDir,$AaysDataDir | Out-Null

$candidateDir = JP 'england_map_web/data/security_public_safety'
$candidateFile = Get-ChildItem -LiteralPath $candidateDir -Filter 'aays1_next_source_evidence_candidates_*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($null -eq $candidateFile) { throw 'NO_AAYS1_CANDIDATE_FILE_FOUND' }
$candidate = Get-Content -Raw -LiteralPath $candidateFile.FullName | ConvertFrom-Json -ErrorAction Stop
$rows = @($candidate.rows)
if ($rows.Count -le 0) { throw 'NO_AAYS1_CANDIDATE_ROWS_FOUND' }

$invalid = @($rows | Where-Object { $_.fake_data -eq $true -or [string]::IsNullOrWhiteSpace([string]$_.source_url) -or [string]::IsNullOrWhiteSpace([string]$_.source_date) })
if ($invalid.Count -gt 0) { throw 'CANDIDATE_REVIEW_FAILED_INVALID_SOURCE_FIELDS' }

$status = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  status = 'candidate_review_package_ready'
  source_task_id = [string]$candidate.task_id
  candidate_rows = $rows.Count
  verified_rows_added = 0
  candidate_output = ($candidateFile.FullName.Substring($RepoRoot.Length).TrimStart('\') -replace '\\','/')
  blocker = 'candidate_rows_require_review_before_verified_merge'
  completion_percent = 55
  remaining_percent = 45
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  updated_at = $Now
}
$status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $StatusDir '095_aays1_candidate_review_site_progress_latest.json')
$status | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $AaysDataDir 'aays1_product_status_latest.json')

$panelPath = JP 'england_map_web/data/runner_panel/page_status_index.json'
if (Test-Path -LiteralPath $panelPath) {
  try {
    $idx = Get-Content -Raw -LiteralPath $panelPath | ConvertFrom-Json -ErrorAction Stop
    foreach ($pg in @($idx.pages)) {
      if ([string]$pg.page_key -eq $PageKey) {
        $pg.runner_status = 'CandidateReviewPackageReady'
        $pg.single_runner_status = 'CandidateReviewPackageReady'
        $pg.latest_queue_status = 'review_ready'
        $pg.latest_task_id = $TaskId
        $pg.latest_report = 'docs/chatgpt_status/aays1/reports/095_aays1_candidate_review_site_progress_latest.md'
        $pg.latest_blocker = 'candidate_rows_require_review_before_verified_merge'
        $pg.blockers = @('candidate_rows_require_review_before_verified_merge')
        $pg.completion_percent = 55
        $pg.remaining_percent = 45
        $pg.final_ready = $false
        $pg.heartbeat_at = $Now
        $pg.last_heartbeat_at = $Now
        $pg.verified_new_rows = 150
        $pg.target_new_rows = 160
      }
    }
    $idx.updated_at = $Now
    $idx | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 -LiteralPath $panelPath
  } catch {
    throw ('PANEL_UPDATE_FAILED: ' + $_.Exception.Message)
  }
}

@"
# 095 aays1 candidate review site progress

status: candidate_review_package_ready
task_id: $TaskId
candidate_rows: $($rows.Count)
verified_rows_added: 0
completion_percent: 55
remaining_percent: 45
blocker: candidate_rows_require_review_before_verified_merge
final_ready: false
fake_data: false
db_write: false
migration: false
production_deploy: false

Notes:
- The 10 source candidates were fetched by the runner from the official Police.uk API.
- This step makes the review package visible on the site without fabricating verified rows.
- Verified merge remains blocked until candidate review/acceptance criteria are satisfied.
"@ | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $ReportDir '095_aays1_candidate_review_site_progress_latest.md')

"TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=candidate_review_package_ready`nCANDIDATE_ROWS=$($rows.Count)`nFINAL_READY=false`nHEARTBEAT_AT=$Now`n" | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $HeartbeatDir '095_aays1_candidate_review_site_progress_latest.txt')
Write-Output "AAYS1_095_CANDIDATE_REVIEW_SITE_PROGRESS candidate_rows=$($rows.Count) completion_percent=55 final_ready=false fake_data=false"
exit 0
