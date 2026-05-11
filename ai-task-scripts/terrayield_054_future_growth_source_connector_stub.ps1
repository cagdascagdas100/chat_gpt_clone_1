$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-054-future-growth-source-connector-stub'

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

  $ConnectorFile = Join-Path $Backend 'future_growth\connectors\official_source.py'
  $TestFile = Join-Path $Backend 'future_growth\tests\test_official_source_connector.py'

  Write-NewFileOnly -Path $ConnectorFile -Content @'
"""Official/structured source connector primitives.

This module defines source metadata and connector safeguards only. It must not
embed fake records, hardcoded demo source rows, or operational scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional

from future_growth.connectors.base import FutureGrowthConnector, FutureGrowthRecord
from future_growth.evidence import EvidenceRef


@dataclass(frozen=True)
class OfficialSourceDescriptor:
    """Metadata for an official or structured source endpoint/document."""

    source_name: str
    source_url: str
    source_type: str = "official_or_structured"
    licensing_note: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise ValueError("source_name is required")
        if not self.source_url.strip():
            raise ValueError("source_url is required")
        if not self.source_url.lower().startswith(("http://", "https://")):
            raise ValueError("source_url must be an http(s) URL")
        if not self.source_type.strip():
            raise ValueError("source_type is required")

    def evidence(self, summary: str) -> EvidenceRef:
        """Create an evidence reference for metadata-level observations."""

        return EvidenceRef(
            source_name=self.source_name,
            source_url=self.source_url,
            source_type=self.source_type,
            evidence_summary=summary,
            retrieved_at=datetime.now(timezone.utc),
        )


class OfficialStructuredSourceConnector(FutureGrowthConnector):
    """Base class for official/structured future-growth connectors.

    Subclasses implement fetch() against real source endpoints/documents.
    This base class intentionally returns no records to avoid fake data.
    """

    def __init__(self, descriptor: OfficialSourceDescriptor) -> None:
        self.descriptor = descriptor
        self.source_name = descriptor.source_name

    def fetch(self) -> Iterable[FutureGrowthRecord]:
        """Return no records in the abstract base implementation.

        Real connectors must override this method and preserve source evidence
        and estimated-vs-exact timeline language for every emitted record.
        """

        return ()
'@

  Write-NewFileOnly -Path $TestFile -Content @'
"""Tests for official/structured source connector safeguards."""

from __future__ import annotations

import pytest

from future_growth.connectors.official_source import (
    OfficialSourceDescriptor,
    OfficialStructuredSourceConnector,
)


def test_descriptor_requires_http_url() -> None:
    with pytest.raises(ValueError, match="http"):
        OfficialSourceDescriptor(
            source_name="unit_test_source_not_ingested",
            source_url="not-a-url",
        )


def test_descriptor_creates_timezone_aware_evidence() -> None:
    descriptor = OfficialSourceDescriptor(
        source_name="unit_test_source_not_ingested",
        source_url="https://example.test/source",
        source_type="unit_test_fixture",
    )

    evidence = descriptor.evidence("unit test metadata observation, not source data")

    assert evidence.source_name == "unit_test_source_not_ingested"
    assert evidence.source_url == "https://example.test/source"
    assert evidence.retrieved_at.tzinfo is not None


def test_base_connector_returns_no_fake_records() -> None:
    descriptor = OfficialSourceDescriptor(
        source_name="unit_test_source_not_ingested",
        source_url="https://example.test/source",
        source_type="unit_test_fixture",
    )

    connector = OfficialStructuredSourceConnector(descriptor)

    assert connector.source_name == "unit_test_source_not_ingested"
    assert list(connector.fetch()) == []
'@
} catch { Add-ErrorText $_.Exception.Message }

$SyntaxExitCode = $null
$SyntaxOutput = ''
$PytestExitCode = $null
$PytestOutput = ''
try {
  Push-Location $Backend
  $PyFiles = @(
    'future_growth\connectors\official_source.py',
    'future_growth\tests\test_official_source_connector.py'
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
  scope = 'Create official/structured source connector stub. No real ingestion and no fake data.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{ command='python -m py_compile official_source connector and test'; exit_code=$SyntaxExitCode; output=$SyntaxOutput }
  test_check = [ordered]@{ command='python -m pytest future_growth/tests -q'; exit_code=$PytestExitCode; output=$PytestOutput }
  backend_git_status_after = [ordered]@{ exit_code=$BackendGitExitCode; output=$BackendGitStatus }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Add a concrete source descriptor registry for official/structured sources without fetching or hardcoding operational records.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Official Source Connector Stub',
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
  '- No fake operational data.',
  '- No hardcoded demo data.',
  '- Base connector returns no records by design.',
  '- Evidence required for scores and timelines.',
  '- Use estimated language when exact dates are missing.',
  '',
  '## Recommended Next Step',
  '',
  $Audit.recommended_next_step
)
$ReportLines | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination $ExternalReport -Force

if ($FinalStatus -eq 'completed') { Write-Host 'FUTURE_GROWTH_SOURCE_CONNECTOR_STUB_COMPLETE'; exit 0 }
Write-Host 'FUTURE_GROWTH_SOURCE_CONNECTOR_STUB_FAILED'
exit 1
