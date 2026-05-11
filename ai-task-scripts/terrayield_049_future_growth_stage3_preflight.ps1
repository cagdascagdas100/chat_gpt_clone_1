$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$Backend = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Frontend = "C:\Users\cagda\Documents\GitHub\AAYS\england_map_web"
$PlannedDataRoot = "E:\AAYS_DATA\planlanan yapılar"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$QualityReportsDir = Join-Path $PlannedDataRoot "10_quality_reports"
$TaskId = "terrayield-049-future-growth-stage3-preflight"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null

function Safe-TestPath($Path) {
  try { return Test-Path -Path $Path } catch { return $false }
}

function Safe-GitStatus($Path) {
  $status = "NOT_CHECKED"
  $exitCode = $null
  $output = ""

  if (-not (Safe-TestPath $Path)) {
    return [ordered]@{ status="PATH_NOT_FOUND"; exit_code=$null; output="" }
  }

  try {
    Push-Location $Path
    $raw = git status --short --untracked-files=no 2>&1
    $exitCode = $LASTEXITCODE
    Pop-Location

    if ($exitCode -eq 0) {
      if ($raw) {
        $status = "HAS_TRACKED_CHANGES"
        $output = ($raw -join "`n")
      } else {
        $status = "CLEAN"
        $output = "CLEAN"
      }
    } else {
      $status = "GIT_STATUS_FAILED_NON_BLOCKING"
      $output = ($raw -join "`n")
    }
  } catch {
    try { Pop-Location } catch {}
    $status = "GIT_STATUS_EXCEPTION_NON_BLOCKING"
    $output = $_.Exception.Message
  }

  return [ordered]@{ status=$status; exit_code=$exitCode; output=$output }
}

function Find-FilesSafe($Root, $Patterns, $Max = 80) {
  $found = New-Object System.Collections.Generic.List[object]

  if (-not (Safe-TestPath $Root)) {
    return @()
  }

  foreach ($pattern in $Patterns) {
    try {
      Get-ChildItem -Path $Root -Recurse -Force -File -Filter $pattern -ErrorAction SilentlyContinue |
        Select-Object -First $Max |
        ForEach-Object {
          if ($found.Count -lt $Max) {
            $found.Add([ordered]@{
              name = $_.Name
              path = $_.FullName
              length = $_.Length
              last_write_time = $_.LastWriteTime.ToString("s")
            })
          }
        }
    } catch {}
  }

  return @($found | Sort-Object path -Unique)
}

$SearchRoots = @($Backend, $Frontend, $PlannedDataRoot, $BridgeRoot)
$Stage1Files = New-Object System.Collections.Generic.List[object]
$Stage2Files = New-Object System.Collections.Generic.List[object]
$FutureGrowthFiles = New-Object System.Collections.Generic.List[object]

foreach ($root in $SearchRoots) {
  Find-FilesSafe -Root $root -Patterns @("FG_STAGE1_SOURCE_REGISTRY.csv", "*STAGE1*SOURCE*REGISTRY*.csv") -Max 30 | ForEach-Object { $Stage1Files.Add($_) }
  Find-FilesSafe -Root $root -Patterns @("FG_STAGE2_CONNECTOR_SPEC.md", "*STAGE2*CONNECTOR*SPEC*.md") -Max 30 | ForEach-Object { $Stage2Files.Add($_) }
  Find-FilesSafe -Root $root -Patterns @("*future*growth*", "*Future*Growth*", "*FG_STAGE*") -Max 80 | ForEach-Object { $FutureGrowthFiles.Add($_) }
}

$Audit = [ordered]@{
  task_id = $TaskId
  status = "completed"
  generated_at = (Get-Date).ToString("s")
  scope = "Read-only Stage3 preflight. No backend/frontend source changes."
  paths = [ordered]@{
    bridge_root_exists = Safe-TestPath $BridgeRoot
    backend_exists = Safe-TestPath $Backend
    frontend_exists = Safe-TestPath $Frontend
    planned_data_root_exists = Safe-TestPath $PlannedDataRoot
  }
  git_status = [ordered]@{
    backend = Safe-GitStatus $Backend
    frontend = Safe-GitStatus $Frontend
    bridge = Safe-GitStatus $BridgeRoot
  }
  stage_inputs = [ordered]@{
    stage1_registry_candidates = @($Stage1Files | Sort-Object path -Unique)
    stage2_connector_spec_candidates = @($Stage2Files | Sort-Object path -Unique)
    future_growth_related_candidates = @($FutureGrowthFiles | Sort-Object path -Unique | Select-Object -First 120)
  }
  readiness = [ordered]@{
    has_stage1_registry = ($Stage1Files.Count -gt 0)
    has_stage2_connector_spec = ($Stage2Files.Count -gt 0)
    ready_for_stage3_ingestion_skeleton = (($Stage1Files.Count -gt 0) -and ($Stage2Files.Count -gt 0))
    note = "Stage3 should remain read-only until source registry and connector spec are confirmed. No fake data is allowed."
  }
  policy = [ordered]@{
    no_repo_source_changes = $true
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = "If ready_for_stage3_ingestion_skeleton is true, create minimal backend connector interface and evidence-preserving ingestion skeleton. If false, repair Stage1/Stage2 outputs first."
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"

$Audit | ConvertTo-Json -Depth 12 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  "# TerraYield Future Growth Stage3 Preflight",
  "",
  "Generated at: $($Audit.generated_at)",
  "",
  "## Scope",
  "",
  "Read-only Stage3 preflight. No backend/frontend source code was modified.",
  "",
  "## Readiness",
  "",
  "- Has Stage1 registry: $($Audit.readiness.has_stage1_registry)",
  "- Has Stage2 connector spec: $($Audit.readiness.has_stage2_connector_spec)",
  "- Ready for Stage3 ingestion skeleton: $($Audit.readiness.ready_for_stage3_ingestion_skeleton)",
  "",
  "## Candidate Counts",
  "",
  "- Stage1 registry candidates: $($Stage1Files.Count)",
  "- Stage2 connector spec candidates: $($Stage2Files.Count)",
  "- Future-growth related candidates: $($FutureGrowthFiles.Count)",
  "",
  "## Git Status",
  "",
  "- Backend: $($Audit.git_status.backend.status)",
  "- Frontend: $($Audit.git_status.frontend.status)",
  "- Bridge: $($Audit.git_status.bridge.status)",
  "",
  "## Policy",
  "",
  "- No fake data.",
  "- No hardcoded demo data.",
  "- Official / structured source priority remains active.",
  "- Evidence is required for scores and timelines.",
  "- Use estimated language when exact dates are missing.",
  "",
  "## Recommended Next Step",
  "",
  $Audit.recommended_next_step
)

$ReportLines | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination $ExternalReport -Force

Write-Host "STAGE3_PREFLIGHT_COMPLETE"
exit 0
