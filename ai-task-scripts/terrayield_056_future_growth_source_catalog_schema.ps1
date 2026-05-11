$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-056-future-growth-source-catalog-schema'

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

  $CatalogFile = Join-Path $Backend 'future_growth\source_catalog.py'
  $TestFile = Join-Path $Backend 'future_growth\tests\test_source_catalog.py'

  Write-NewFileOnly -Path $CatalogFile -Content @'
"""Approved source catalog schema for future-growth intelligence.

This module defines source-catalog mechanics only. It does not contain approved
operational source rows. Source rows should be added only after legal/access and
evidence requirements are confirmed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from future_growth.connectors.official_source import OfficialSourceDescriptor


@dataclass(frozen=True)
class SourceApproval:
    """Approval metadata required before a source can be used for ingestion."""

    descriptor: OfficialSourceDescriptor
    jurisdiction: str
    coverage: str
    access_note: str
    licensing_note: str
    evidence_policy: str = "source_url_and_retrieved_at_required"

    def __post_init__(self) -> None:
        for field_name in ("jurisdiction", "coverage", "access_note", "licensing_note"):
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"{field_name} is required")
        if self.evidence_policy != "source_url_and_retrieved_at_required":
            raise ValueError("unsupported evidence_policy")


@dataclass(frozen=True)
class ApprovedSourceCatalog:
    """Immutable collection of source approvals."""

    approvals: Tuple[SourceApproval, ...]

    def __post_init__(self) -> None:
        names = [approval.descriptor.source_name for approval in self.approvals]
        if len(names) != len(set(names)):
            raise ValueError("approved source names must be unique")

    def iter_approvals(self) -> Iterable[SourceApproval]:
        return iter(self.approvals)

    def require_non_empty(self) -> "ApprovedSourceCatalog":
        if not self.approvals:
            raise ValueError("approved source catalog is empty")
        return self


EMPTY_APPROVED_SOURCE_CATALOG = ApprovedSourceCatalog(approvals=())


def get_empty_approved_source_catalog() -> ApprovedSourceCatalog:
    """Return an intentionally empty approved-source catalog."""

    return EMPTY_APPROVED_SOURCE_CATALOG
'@

  Write-NewFileOnly -Path $TestFile -Content @'
"""Tests for approved source catalog safeguards."""

from __future__ import annotations

import pytest

from future_growth.connectors.official_source import OfficialSourceDescriptor
from future_growth.source_catalog import (
    ApprovedSourceCatalog,
    SourceApproval,
    get_empty_approved_source_catalog,
)


def unit_test_descriptor(name: str = "unit_test_source_not_ingested") -> OfficialSourceDescriptor:
    return OfficialSourceDescriptor(
        source_name=name,
        source_url=f"https://example.test/{name}",
        source_type="unit_test_fixture",
    )


def test_empty_catalog_is_default_and_rejects_ingestion_use() -> None:
    catalog = get_empty_approved_source_catalog()
    assert list(catalog.iter_approvals()) == []
    with pytest.raises(ValueError, match="empty"):
        catalog.require_non_empty()


def test_source_approval_requires_access_and_licensing_notes() -> None:
    with pytest.raises(ValueError, match="access_note"):
        SourceApproval(
            descriptor=unit_test_descriptor(),
            jurisdiction="England",
            coverage="unit test coverage, not source data",
            access_note="",
            licensing_note="unit test licence note, not source data",
        )


def test_catalog_rejects_duplicate_approved_source_names() -> None:
    approval_a = SourceApproval(
        descriptor=unit_test_descriptor(),
        jurisdiction="England",
        coverage="unit test coverage, not source data",
        access_note="unit test access note, not source data",
        licensing_note="unit test licence note, not source data",
    )
    approval_b = SourceApproval(
        descriptor=unit_test_descriptor(),
        jurisdiction="England",
        coverage="unit test coverage, not source data",
        access_note="unit test access note, not source data",
        licensing_note="unit test licence note, not source data",
    )

    with pytest.raises(ValueError, match="unique"):
        ApprovedSourceCatalog(approvals=(approval_a, approval_b))
'@
} catch { Add-ErrorText $_.Exception.Message }

$SyntaxExitCode = $null
$SyntaxOutput = ''
$PytestExitCode = $null
$PytestOutput = ''
try {
  Push-Location $Backend
  $PyFiles = @(
    'future_growth\source_catalog.py',
    'future_growth\tests\test_source_catalog.py'
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
  scope = 'Create approved-source catalog schema without operational source rows. No fake data.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{ command='python -m py_compile source catalog and test'; exit_code=$SyntaxExitCode; output=$SyntaxOutput }
  test_check = [ordered]@{ command='python -m pytest future_growth/tests -q'; exit_code=$PytestExitCode; output=$PytestOutput }
  backend_git_status_after = [ordered]@{ exit_code=$BackendGitExitCode; output=$BackendGitStatus }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Add a source approval import path from external reviewed config, still without fetching data.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Source Catalog Schema',
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
  '- Empty catalog by default; no hardcoded operational source rows.',
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

if ($FinalStatus -eq 'completed') { Write-Host 'FUTURE_GROWTH_SOURCE_CATALOG_SCHEMA_COMPLETE'; exit 0 }
Write-Host 'FUTURE_GROWTH_SOURCE_CATALOG_SCHEMA_FAILED'
exit 1
