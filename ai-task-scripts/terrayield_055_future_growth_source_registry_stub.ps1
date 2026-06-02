$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-055-future-growth-source-registry-stub'

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

  $RegistryFile = Join-Path $Backend 'future_growth\source_registry.py'
  $TestFile = Join-Path $Backend 'future_growth\tests\test_source_registry.py'

  Write-NewFileOnly -Path $RegistryFile -Content @'
"""Source descriptor registry for future-growth intelligence.

This module defines registry mechanics only. It must not contain operational
source rows until each source is explicitly approved with licensing/access notes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from future_growth.connectors.official_source import OfficialSourceDescriptor


@dataclass(frozen=True)
class SourceRegistry:
    """Immutable collection of approved source descriptors."""

    sources: Tuple[OfficialSourceDescriptor, ...]

    def __post_init__(self) -> None:
        names = [source.source_name for source in self.sources]
        if len(names) != len(set(names)):
            raise ValueError("source names must be unique")

    def iter_sources(self) -> Iterable[OfficialSourceDescriptor]:
        return iter(self.sources)

    def require_non_empty(self) -> "SourceRegistry":
        if not self.sources:
            raise ValueError("source registry is empty; approve official sources before ingestion")
        return self


EMPTY_SOURCE_REGISTRY = SourceRegistry(sources=())


def get_empty_source_registry() -> SourceRegistry:
    """Return an intentionally empty registry.

    The empty default prevents accidental fake or hardcoded operational source
    usage. Approved official/structured sources should be loaded explicitly in a
    later step.
    """

    return EMPTY_SOURCE_REGISTRY
'@

  Write-NewFileOnly -Path $TestFile -Content @'
"""Tests for future-growth source registry safeguards."""

from __future__ import annotations

import pytest

from future_growth.connectors.official_source import OfficialSourceDescriptor
from future_growth.source_registry import SourceRegistry, get_empty_source_registry


def test_empty_registry_is_intentionally_empty() -> None:
    registry = get_empty_source_registry()
    assert list(registry.iter_sources()) == []


def test_empty_registry_rejects_ingestion_use_without_sources() -> None:
    with pytest.raises(ValueError, match="empty"):
        get_empty_source_registry().require_non_empty()


def test_registry_rejects_duplicate_source_names() -> None:
    source_a = OfficialSourceDescriptor(
        source_name="unit_test_source_not_ingested",
        source_url="https://example.test/a",
        source_type="unit_test_fixture",
    )
    source_b = OfficialSourceDescriptor(
        source_name="unit_test_source_not_ingested",
        source_url="https://example.test/b",
        source_type="unit_test_fixture",
    )

    with pytest.raises(ValueError, match="unique"):
        SourceRegistry(sources=(source_a, source_b))
'@
} catch { Add-ErrorText $_.Exception.Message }

$SyntaxExitCode = $null
$SyntaxOutput = ''
$PytestExitCode = $null
$PytestOutput = ''
try {
  Push-Location $Backend
  $PyFiles = @(
    'future_growth\source_registry.py',
    'future_growth\tests\test_source_registry.py'
  ) | Where-Object { Test-Path -Path $_ }
  $SyntaxRaw = & python -m py_compile $PyFiles 2>&1
  $SyntaxExitCode = $LASTEXITCODE
  $SyntaxOutput = ($SyntaxRaw | Out-String)
  $PytestRaw = & python -m pytest future_growth\tests -q 2>&1
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
  scope = 'Create source registry mechanics without operational source rows. No fake data.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{ command='python -m py_compile source registry and test'; exit_code=$SyntaxExitCode; output=$SyntaxOutput }
  test_check = [ordered]@{ command='python -m pytest future_growth/tests -q'; exit_code=$PytestExitCode; output=$PytestOutput }
  backend_git_status_after = [ordered]@{ exit_code=$BackendGitExitCode; output=$BackendGitStatus }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Add approved official/structured source metadata file after confirming source list and licensing/access notes.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Source Registry Stub',
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
  '- Empty registry by default; no hardcoded operational source rows.',
  '- No fake operational data.',
  '- Evidence required for scores and timelines.',
  '- Use estimated language when exact dates are missing.',
  '',
  '## Recommended Next Step',
  '',
  $Audit.recommended_next_step
)
$ReportLines | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination $ExternalReport -Force

if ($FinalStatus -eq 'completed') { Write-Host 'FUTURE_GROWTH_SOURCE_REGISTRY_STUB_COMPLETE'; exit 0 }
Write-Host 'FUTURE_GROWTH_SOURCE_REGISTRY_STUB_FAILED'
exit 1
