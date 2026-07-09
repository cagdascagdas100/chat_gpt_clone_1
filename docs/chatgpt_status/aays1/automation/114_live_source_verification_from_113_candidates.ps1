$ErrorActionPreference = 'Continue'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$pageKey = 'aays1'
$taskId = 'aays1-114-live-source-verification-from-113-candidates-20260709'
$inputRel = 'docs/chatgpt_status/aays1/status/113_aays1_next_geometry_source_candidate_extraction_latest.json'
$statusRel = 'docs/chatgpt_status/aays1/status/114_aays1_live_source_verification_latest.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/114_aays1_live_source_verification_report.md'
$runnerOutRel = 'docs/chatgpt_status/aays1/runner_outputs/114_live_source_verification_from_113_candidates.json'

$statusPath = Join-Path $repoRoot $statusRel
$reportPath = Join-Path $repoRoot $reportRel
$runnerOutPath = Join-Path $repoRoot $runnerOutRel
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $reportPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $runnerOutPath) | Out-Null

function New-SafeResult([string]$statusText, [array]$items, [array]$blockers, [object]$gitSync) {
  $okItems = @($items | Where-Object { $_.live_source_accessible -eq $true })
  return [ordered]@{
    task_id = $taskId
    page_key = $pageKey
    status = $statusText
    checked_at = (Get-Date).ToString('o')
    repo_root = $repoRoot
    input_status_file = $inputRel
    candidates_checked = @($items).Count
    live_source_accessible_count = @($okItems).Count
    minimum_required_for_metric_increase = 10
    metric_increase_allowed = $false
    metric_increase_reason = 'This script verifies candidate live source accessibility only. Product metrics must not increase until downstream CSV/GeoJSON/product integration writes source-backed rows.'
    verification_results = $items
    blockers = $blockers
    git_sync = $gitSync
    single_runner_only = $true
    new_runner = $false
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
}

function Write-Report([object]$result) {
  $lines = @()
  $lines += '# AAYS1 114 - Live source verification from 113 candidates'
  $lines += ''
  $lines += ('Status: ' + $result.status)
  $lines += ''
  $lines += '## Counts'
  $lines += ''
  $lines += ('- Candidates checked: ' + $result.candidates_checked)
  $lines += ('- Live source accessible: ' + $result.live_source_accessible_count)
  $lines += '- Metric increase allowed: false'
  $lines += ''
  $lines += '## Safety'
  $lines += ''
  $lines += '- single_runner_only=true'
  $lines += '- new_runner=false'
  $lines += '- parallel_runner=false'
  $lines += '- final_ready=false'
  $lines += '- fake_data=false'
  $lines += '- db_write=false'
  $lines += '- migration=false'
  $lines += '- production_deploy=false'
  $lines += ''
  $lines += '## Blockers'
  $lines += ''
  foreach ($b in @($result.blockers)) { $lines += ('- ' + $b) }
  $lines += ''
  $lines += '## Notes'
  $lines += ''
  $lines += 'This task only tests whether the candidate source URLs from 113 are reachable and records evidence. It does not fabricate product rows or increase panel percentage without downstream integration evidence.'
  $lines | Set-Content -Encoding UTF8 $reportPath
}

$gitSync = [ordered]@{ attempted=$false; status='not_attempted'; exit_code=$null; stdout=@(); stderr=@() }
$items = @()
$blockers = @()

try {
  $inputPath = Join-Path $repoRoot $inputRel
  if (-not (Test-Path $inputPath)) {
    $blockers += '113_candidate_output_missing_on_local_runner_worktree'
    $result = New-SafeResult 'blocked_missing_113_input' $items $blockers $gitSync
    $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $statusPath
    $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $runnerOutPath
    Write-Report $result
  } else {
    $input = Get-Content -Raw -Encoding UTF8 $inputPath | ConvertFrom-Json
    $candidates = @($input.next_candidates)
    if ($candidates.Count -eq 0) { $blockers += '113_candidate_list_empty' }

    foreach ($c in $candidates) {
      $url = [string]$c.listing_url
      $row = [ordered]@{
        row_id = $c.row_id
        parcel_ref = $c.parcel_ref
        source_url = $url
        live_source_accessible = $false
        http_status = $null
        content_length = $null
        source_checked_at = (Get-Date).ToString('o')
        error = ''
      }
      if ([string]::IsNullOrWhiteSpace($url)) {
        $row.error = 'missing_source_url'
      } else {
        try {
          $resp = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing -TimeoutSec 20 -MaximumRedirection 5
          $row.http_status = [int]$resp.StatusCode
          $row.content_length = if ($null -ne $resp.Content) { [int]$resp.Content.Length } else { 0 }
          if (($row.http_status -ge 200) -and ($row.http_status -lt 400) -and ($row.content_length -gt 100)) {
            $row.live_source_accessible = $true
          } else {
            $row.error = 'source_response_not_sufficient_for_live_accessibility'
          }
        } catch {
          try {
            $statusCode = [int]$_.Exception.Response.StatusCode
            $row.http_status = $statusCode
          } catch {}
          $row.error = $_.Exception.Message
        }
      }
      $items += [pscustomobject]$row
    }

    $accessible = @($items | Where-Object { $_.live_source_accessible -eq $true }).Count
    if ($accessible -lt 10) { $blockers += 'fewer_than_10_live_sources_accessible_for_next_metric_step' }
    $blockers += 'downstream_product_csv_geojson_integration_required_before_metric_increase'

    $statusText = if ($accessible -gt 0) { 'live_source_accessibility_checked_pending_product_integration' } else { 'live_source_accessibility_checked_no_accessible_sources_yet' }
    $result = New-SafeResult $statusText $items $blockers $gitSync
    $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $statusPath
    $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $runnerOutPath
    Write-Report $result
  }

  try {
    Push-Location $repoRoot
    $gitSync.attempted = $true
    & git add -- $statusRel $reportRel $runnerOutRel 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
    $changes = & git status --porcelain -- $statusRel $reportRel $runnerOutRel
    $gitSync.changed_count = @($changes).Count
    if (@($changes).Count -gt 0) {
      & git commit -m 'aays1 sync 114 live source verification output' 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
      $commitExit = $LASTEXITCODE
      if ($commitExit -eq 0) {
        & git push 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
        $gitSync.exit_code = $LASTEXITCODE
        $gitSync.status = if ($LASTEXITCODE -eq 0) { 'pushed' } else { 'push_failed' }
      } else {
        $gitSync.exit_code = $commitExit
        $gitSync.status = 'commit_failed'
      }
    } else {
      $gitSync.exit_code = 0
      $gitSync.status = 'no_changes_to_push'
    }
  } catch {
    $gitSync.status = 'exception'
    $gitSync.stderr += $_.Exception.Message
  } finally {
    try { Pop-Location } catch {}
  }

  # Write final local copy with git sync details; commit it if it changed.
  $final = New-SafeResult $result.status $items $blockers $gitSync
  $final | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $statusPath
  $final | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $runnerOutPath
  Write-Report $final

  try {
    Push-Location $repoRoot
    & git add -- $statusRel $reportRel $runnerOutRel 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
    $changes2 = & git status --porcelain -- $statusRel $reportRel $runnerOutRel
    if (@($changes2).Count -gt 0) {
      & git commit -m 'aays1 sync 114 verification git status' 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ }
      if ($LASTEXITCODE -eq 0) { & git push 2>&1 | ForEach-Object { $gitSync.stdout += [string]$_ } }
    }
  } catch {
    $gitSync.stderr += $_.Exception.Message
  } finally {
    try { Pop-Location } catch {}
  }

  Write-Host "OUTPUT=$statusPath"
  exit 0
} catch {
  $blockers += ('script_exception: ' + $_.Exception.Message)
  $result = New-SafeResult 'script_exception' $items $blockers $gitSync
  $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $statusPath
  $result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $runnerOutPath
  Write-Report $result
  Write-Host "OUTPUT=$statusPath"
  exit 0
}
