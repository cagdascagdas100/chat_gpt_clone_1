$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-053-future-growth-tests-create'

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null

$Created = New-Object System.Collections.Generic.List[string]
$Skipped = New-Object System.Collections.Generic.List[string]
$Errors = New-Object System.Collections.Generic.List[string]

function Add-ErrorText { param([string]$Message) if ($Message) { [void]$Errors.Add($Message) } }
function Write-NewFileOnly {
  param([string]$Path, [string]$Content)
  try {
    if (Test-Path -Path $Path) { [void]$Skipped.Add($Path); return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path) | Out-Null
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    [void]$Created.Add($Path)
  } catch { Add-ErrorText $_.Exception.Message }
}

try {
  if (-not (Test-Path -Path $Backend)) { throw "Backend path not found: $Backend" }

  $TestsRoot = Join-Path $Backend 'future_growth\tests'
  $TestFile = Join-Path $TestsRoot 'test_primitives.py'

  Write-NewFileOnly -Path (Join-Path $TestsRoot '__init__.py') -Content @'
"""Tests for future_growth primitives."""
'@

  Write-NewFileOnly -Path $TestFile -Content @'
"""Validation tests for future_growth primitives.

These tests use unit-test fixtures only. They are not ingested source data,
not demo records, and not operational evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from future_growth.evidence import EvidenceRef
from future_growth.timeline import TimelineEstimate


def unit_test_evidence() -> EvidenceRef:
    return EvidenceRef(
        source_name="unit_test_source_not_ingested",
        evidence_summary="unit test evidence summary, not source data",
        retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source_url=None,
        source_type="unit_test_fixture",
    )


def test_evidence_requires_source_name() -> None:
    with pytest.raises(ValueError, match="source_name"):
        EvidenceRef(
            source_name="",
            evidence_summary="unit test evidence summary, not source data",
            retrieved_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_evidence_requires_timezone_aware_retrieved_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        EvidenceRef(
            source_name="unit_test_source_not_ingested",
            evidence_summary="unit test evidence summary, not source data",
            retrieved_at=datetime(2026, 1, 1),
        )


def test_estimated_timeline_requires_estimated_language() -> None:
    with pytest.raises(ValueError, match="estimated language"):
        TimelineEstimate(
            label="planned delivery date unknown",
            evidence=unit_test_evidence(),
            is_estimated=True,
            year=2030,
        )


def test_estimated_timeline_accepts_estimated_language() -> None:
    timeline = TimelineEstimate(
        label="estimated delivery around 2030",
        evidence=unit_test_evidence(),
        is_estimated=True,
        year=2030,
    )
    assert timeline.year == 2030
    assert timeline.evidence.source_type == "unit_test_fixture"


def test_timeline_rejects_invalid_quarter() -> None:
    with pytest.raises(ValueError, match="quarter"):
        TimelineEstimate(
            label="estimated delivery in invalid quarter",
            evidence=unit_test_evidence(),
            is_estimated=True,
            year=2030,
            quarter=5,
        )
'@
} catch { Add-ErrorText $_.Exception.Message }

$SyntaxExitCode = $null
$SyntaxOutput = ''
$PytestExitCode = $null
$PytestOutput = ''
try {
  Push-Location $Backend
  $PyFiles = @(
    'future_growth\__init__.py',
    'future_growth\evidence.py',
    'future_growth\timeline.py',
    'future_growth\connectors\__init__.py',
    'future_growth\connectors\base.py',
    'future_growth\tests\test_primitives.py'
  ) | Where-Object { Test-Path -Path $_ }
  $SyntaxRaw = & python -m py_compile $PyFiles 2>&1
  $SyntaxExitCode = $LASTEXITCODE
  $SyntaxOutput = ($SyntaxRaw | Out-String)
  $PytestRaw = & python -m pytest future_growth\tests\test_primitives.py -q 2>&1
  $PytestExitCode = $LASTEXITCODE
  $PytestOutput = ($PytestRaw | Out-String)
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  if ($null -eq $SyntaxExitCode) { $SyntaxExitCode = 999 }
  if ($null -eq $PytestExitCode) { $PytestExitCode = 999 }
  Add-ErrorText $_.Exception.Message
}

$BackendGitStatus = 'NOT_CHECKED'
$BackendGitExitCode = $null
try {
  Push-Location $Backend
  $GitRaw = git status --short --untracked-files=all 2>&1
  $BackendGitExitCode = $LASTEXITCODE
  Pop-Location
  if ($BackendGitExitCode -eq 0) {
    if ($GitRaw) { $BackendGitStatus = ($GitRaw -join "`n") } else { $BackendGitStatus = 'CLEAN' }
  } else { $BackendGitStatus = 'GIT_STATUS_FAILED_NON_BLOCKING' }
} catch {
  try { Pop-Location } catch {}
  Add-ErrorText $_.Exception.Message
  $BackendGitStatus = 'GIT_STATUS_EXCEPTION_NON_BLOCKING'
}

$FinalStatus = if (($Errors.Count -eq 0) -and ($SyntaxExitCode -eq 0) -and ($PytestExitCode -eq 0)) { 'completed' } else { 'failed' }

$Audit = [ordered]@{
  task_id = $TaskId
  status = $FinalStatus
  generated_at = (Get-Date).ToString('s')
  scope = 'Create minimal validation tests for future_growth primitives. No API/database wiring. No ingested fake data.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{ command='python -m py_compile future_growth files and tests'; exit_code=$SyntaxExitCode; output=$SyntaxOutput }
  test_check = [ordered]@{ command='python -m pytest future_growth/tests/test_primitives.py -q'; exit_code=$PytestExitCode; output=$PytestOutput }
  backend_git_status_after = [ordered]@{ exit_code=$BackendGitExitCode; output=$BackendGitStatus }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Commit/review skeleton and tests, then add first official/structured source connector stub without ingesting fake data.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Tests Create',
  '',
  "Generated at: $($Audit.generated_at)",
  '',
  '## Status',
  '',
  $FinalStatus,
  '',
  '## Created Files',
  '',
  ($Created | ForEach-Object { "- $_" }),
  '',
  '## Skipped Existing Files',
  '',
  ($Skipped | ForEach-Object { "- $_" }),
  '',
  '## Syntax Check',
  '',
  "- Exit code: $SyntaxExitCode",
  '',
  '## Test Check',
  '',
  "- Exit code: $PytestExitCode",
  '',
  '## Policy',
  '',
  '- Unit-test fixtures are not ingested source data.',
  '- No fake operational data.',
  '- No hardcoded demo data.',
  '- Evidence required for scores and timelines.',
  '- Use estimated language when exact dates are missing.',
  '',
  '## Recommended Next Step',
  '',
  $Audit.recommended_next_step
)
$ReportLines | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination $ExternalReport -Force

if ($FinalStatus -eq 'completed') { Write-Host 'FUTURE_GROWTH_TESTS_CREATE_COMPLETE'; exit 0 }
Write-Host 'FUTURE_GROWTH_TESTS_CREATE_FAILED'
exit 1
