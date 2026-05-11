$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-052-future-growth-skeleton-repair'

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null

$Created = New-Object System.Collections.Generic.List[string]
$Skipped = New-Object System.Collections.Generic.List[string]
$Errors = New-Object System.Collections.Generic.List[string]

function Add-ErrorText {
  param([string]$Message)
  if ($Message) { [void]$Errors.Add($Message) }
}

function Write-NewFileOnly {
  param(
    [string]$Path,
    [string]$Content
  )
  try {
    if (Test-Path -Path $Path) {
      [void]$Skipped.Add($Path)
      return
    }
    $Parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    [void]$Created.Add($Path)
  } catch {
    Add-ErrorText $_.Exception.Message
  }
}

try {
  if (-not (Test-Path -Path $Backend)) { throw "Backend path not found: $Backend" }

  $PackageRoot = Join-Path $Backend 'future_growth'
  $ConnectorsRoot = Join-Path $PackageRoot 'connectors'
  New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
  New-Item -ItemType Directory -Force -Path $ConnectorsRoot | Out-Null

  Write-NewFileOnly -Path (Join-Path $PackageRoot '__init__.py') -Content @'
"""TerraYield future growth intelligence primitives.

No module in this package should create fake data or hardcoded demo records.
"""

from .evidence import EvidenceRef
from .timeline import TimelineEstimate

__all__ = ["EvidenceRef", "TimelineEstimate"]
'@

  Write-NewFileOnly -Path (Join-Path $PackageRoot 'evidence.py') -Content @'
"""Evidence primitives for planned-development and infrastructure signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class EvidenceRef:
    """A source-backed evidence reference required for scores and timelines."""

    source_name: str
    evidence_summary: str
    retrieved_at: datetime
    source_url: Optional[str] = None
    source_type: str = "official_or_structured"

    def __post_init__(self) -> None:
        if not self.source_name.strip():
            raise ValueError("source_name is required for evidence")
        if not self.evidence_summary.strip():
            raise ValueError("evidence_summary is required for evidence")
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")
        if self.source_url is not None and not self.source_url.strip():
            raise ValueError("source_url must be non-empty when provided")

    @classmethod
    def now_utc(
        cls,
        *,
        source_name: str,
        evidence_summary: str,
        source_url: Optional[str] = None,
        source_type: str = "official_or_structured",
    ) -> "EvidenceRef":
        return cls(
            source_name=source_name,
            evidence_summary=evidence_summary,
            retrieved_at=datetime.now(timezone.utc),
            source_url=source_url,
            source_type=source_type,
        )
'@

  Write-NewFileOnly -Path (Join-Path $PackageRoot 'timeline.py') -Content @'
"""Timeline primitives that preserve exact-vs-estimated language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .evidence import EvidenceRef


@dataclass(frozen=True)
class TimelineEstimate:
    """Evidence-backed delivery or planning timeline."""

    label: str
    evidence: EvidenceRef
    is_estimated: bool = True
    year: Optional[int] = None
    quarter: Optional[int] = None
    date_text: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label is required for timeline")
        if self.quarter is not None and self.quarter not in (1, 2, 3, 4):
            raise ValueError("quarter must be 1, 2, 3, or 4")
        if self.year is not None and self.year < 1900:
            raise ValueError("year is not plausible")
        if self.is_estimated and "estimated" not in self.label.lower():
            raise ValueError("estimated timelines must include estimated language in label")
'@

  Write-NewFileOnly -Path (Join-Path $ConnectorsRoot '__init__.py') -Content @'
"""Connector interfaces for future-growth source ingestion."""

from .base import FutureGrowthConnector, FutureGrowthRecord

__all__ = ["FutureGrowthConnector", "FutureGrowthRecord"]
'@

  Write-NewFileOnly -Path (Join-Path $ConnectorsRoot 'base.py') -Content @'
"""Base connector protocol for official/structured future-growth sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from future_growth.evidence import EvidenceRef
from future_growth.timeline import TimelineEstimate


@dataclass(frozen=True)
class FutureGrowthRecord:
    """Normalized future-growth signal. It must be backed by evidence."""

    external_id: str
    title: str
    category: str
    evidence: EvidenceRef
    timeline: TimelineEstimate

    def __post_init__(self) -> None:
        if not self.external_id.strip():
            raise ValueError("external_id is required")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.category.strip():
            raise ValueError("category is required")


class FutureGrowthConnector(Protocol):
    """Protocol for source-backed future-growth connectors."""

    source_name: str

    def fetch(self) -> Iterable[FutureGrowthRecord]:
        """Yield source-backed records without fake or hardcoded demo data."""
'@
} catch {
  Add-ErrorText $_.Exception.Message
}

$PyFiles = @(
  (Join-Path $Backend 'future_growth\__init__.py'),
  (Join-Path $Backend 'future_growth\evidence.py'),
  (Join-Path $Backend 'future_growth\timeline.py'),
  (Join-Path $Backend 'future_growth\connectors\__init__.py'),
  (Join-Path $Backend 'future_growth\connectors\base.py')
)

$SyntaxExitCode = $null
$SyntaxOutput = ''
try {
  Push-Location $Backend
  $ExistingPyFiles = @($PyFiles | Where-Object { Test-Path -Path $_ })
  if ($ExistingPyFiles.Count -gt 0) {
    $SyntaxRaw = & python -m py_compile $ExistingPyFiles 2>&1
    $SyntaxExitCode = $LASTEXITCODE
    $SyntaxOutput = ($SyntaxRaw | Out-String)
  } else {
    $SyntaxExitCode = 998
    $SyntaxOutput = 'No future_growth Python files existed for compile check.'
  }
  Pop-Location
} catch {
  try { Pop-Location } catch {}
  $SyntaxExitCode = 999
  $SyntaxOutput = $_.Exception.Message
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
  } else {
    $BackendGitStatus = 'GIT_STATUS_FAILED_NON_BLOCKING'
  }
} catch {
  try { Pop-Location } catch {}
  $BackendGitStatus = 'GIT_STATUS_EXCEPTION_NON_BLOCKING'
  Add-ErrorText $_.Exception.Message
}

$FinalStatus = if (($Errors.Count -eq 0) -and ($SyntaxExitCode -eq 0)) { 'completed' } else { 'failed' }

$Audit = [ordered]@{
  task_id = $TaskId
  status = $FinalStatus
  generated_at = (Get-Date).ToString('s')
  scope = 'Repair/create isolated future_growth backend package skeleton. No API/database wiring. No fake data.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{
    command = 'python -m py_compile future_growth files'
    exit_code = $SyntaxExitCode
    output = $SyntaxOutput
  }
  backend_git_status_after = [ordered]@{
    exit_code = $BackendGitExitCode
    output = $BackendGitStatus
  }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Add minimal tests for EvidenceRef and TimelineEstimate validation before API/database wiring.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Skeleton Repair',
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
  '## Errors',
  '',
  ($Errors | ForEach-Object { "- $_" }),
  '',
  '## Syntax Check',
  '',
  "- Exit code: $SyntaxExitCode",
  '',
  '## Policy',
  '',
  '- No fake data.',
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

if ($FinalStatus -eq 'completed') {
  Write-Host 'FUTURE_GROWTH_SKELETON_REPAIR_COMPLETE'
  exit 0
}

Write-Host 'FUTURE_GROWTH_SKELETON_REPAIR_FAILED'
exit 1
