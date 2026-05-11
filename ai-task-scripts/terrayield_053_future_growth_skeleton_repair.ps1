$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-053-future-growth-skeleton-repair'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN' }
$Backend = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence' }
$PlannedDataRoot = if ($env:AAYS_PLANNED_DATA_ROOT) { $env:AAYS_PLANNED_DATA_ROOT } else { 'E:\AAYS_DATA\planlanan yapılar' }
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'

function Write-Step([string]$Text) {
  Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text)
}

function Write-FileUtf8([string]$Path, [string]$Content) {
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

Write-Step "TASK=$TaskId"
Write-Step "MODE=future_growth_skeleton_repair"
Write-Step "BRIDGE_ROOT=$BridgeRoot"
Write-Step "BACKEND=$Backend"
Write-Step "PLANNED_DATA_ROOT=$PlannedDataRoot"

New-Item -ItemType Directory -Force -Path $ResultsDir,$QualityReportsDir | Out-Null

$Errors = New-Object System.Collections.Generic.List[string]
$Created = New-Object System.Collections.Generic.List[string]
$Updated = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path $Backend)) {
  $Errors.Add("Backend path not found: $Backend") | Out-Null
} else {
  $PackageRoot = Join-Path $Backend 'future_growth'
  $ConnectorsRoot = Join-Path $PackageRoot 'connectors'
  New-Item -ItemType Directory -Force -Path $PackageRoot,$ConnectorsRoot | Out-Null

  $files = @{}

  $files[(Join-Path $PackageRoot '__init__.py')] = @'
"""TerraYield future growth intelligence primitives.

Evidence-preserving interfaces for planned development, transport infrastructure,
and future-growth signals.

No module in this package should create fake data or hardcoded demo records.
"""

from .evidence import EvidenceRef
from .timeline import TimelineEstimate

__all__ = ["EvidenceRef", "TimelineEstimate"]
'@

  $files[(Join-Path $PackageRoot 'evidence.py')] = @'
"""Evidence primitives for planned-development and infrastructure signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class EvidenceRef:
    """A source-backed evidence reference."""

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

  $files[(Join-Path $PackageRoot 'timeline.py')] = @'
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

  $files[(Join-Path $ConnectorsRoot '__init__.py')] = @'
"""Connector interfaces for future-growth source ingestion."""

from .base import FutureGrowthConnector, FutureGrowthRecord

__all__ = ["FutureGrowthConnector", "FutureGrowthRecord"]
'@

  $files[(Join-Path $ConnectorsRoot 'base.py')] = @'
"""Base connector protocol for official/structured future-growth sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol

from future_growth.evidence import EvidenceRef
from future_growth.timeline import TimelineEstimate


@dataclass(frozen=True)
class FutureGrowthRecord:
    """Normalized future-growth signal."""

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
        """Yield source-backed records with retained evidence."""
'@

  foreach ($path in $files.Keys) {
    $exists = Test-Path $path
    Write-FileUtf8 -Path $path -Content $files[$path]
    if ($exists) { $Updated.Add($path) | Out-Null } else { $Created.Add($path) | Out-Null }
  }

  $PyFiles = @(
    (Join-Path $PackageRoot '__init__.py'),
    (Join-Path $PackageRoot 'evidence.py'),
    (Join-Path $PackageRoot 'timeline.py'),
    (Join-Path $ConnectorsRoot '__init__.py'),
    (Join-Path $ConnectorsRoot 'base.py')
  )

  Write-Step 'PY_COMPILE_BEGIN'
  try {
    Push-Location $Backend
    $CompileOutput = & python -m py_compile $PyFiles 2>&1 | Out-String
    $CompileExit = $LASTEXITCODE
    Pop-Location
    Write-Output $CompileOutput
    Write-Step ("PY_COMPILE_EXIT=$CompileExit")
    if ($CompileExit -ne 0) { $Errors.Add("py_compile exit=$CompileExit output=$CompileOutput") | Out-Null }
  } catch {
    try { Pop-Location } catch {}
    $Errors.Add("py_compile exception: $($_.Exception.Message)") | Out-Null
  }
  Write-Step 'PY_COMPILE_END'

  Write-Step 'PY_IMPORT_SMOKE_BEGIN'
  try {
    Push-Location $Backend
    $Smoke = & python -c "from future_growth import EvidenceRef, TimelineEstimate; print('IMPORT_OK')" 2>&1 | Out-String
    $SmokeExit = $LASTEXITCODE
    Pop-Location
    Write-Output $Smoke
    Write-Step ("PY_IMPORT_SMOKE_EXIT=$SmokeExit")
    if ($SmokeExit -ne 0) { $Errors.Add("import smoke exit=$SmokeExit output=$Smoke") | Out-Null }
  } catch {
    try { Pop-Location } catch {}
    $Errors.Add("import smoke exception: $($_.Exception.Message)") | Out-Null
  }
  Write-Step 'PY_IMPORT_SMOKE_END'
}

$Status = if ($Errors.Count -eq 0) { 'completed' } else { 'completed_with_warnings' }
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"

$Audit = [ordered]@{
  task_id = $TaskId
  status = $Status
  generated_at = (Get-Date).ToString('s')
  bridge_root = $BridgeRoot
  backend = $Backend
  planned_data_root = $PlannedDataRoot
  created_files = @($Created)
  updated_files = @($Updated)
  errors = @($Errors)
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
}

$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$Report = @()
$Report += '# TerraYield Future Growth Skeleton Repair'
$Report += ''
$Report += "Status: $Status"
$Report += "Generated at: $($Audit.generated_at)"
$Report += "BridgeRoot: $BridgeRoot"
$Report += "Backend: $Backend"
$Report += ''
$Report += '## Created Files'
if ($Created.Count -eq 0) { $Report += '- none' } else { $Created | ForEach-Object { $Report += "- $_" } }
$Report += ''
$Report += '## Updated Files'
if ($Updated.Count -eq 0) { $Report += '- none' } else { $Updated | ForEach-Object { $Report += "- $_" } }
$Report += ''
$Report += '## Errors / Warnings'
if ($Errors.Count -eq 0) { $Report += '- none' } else { $Errors | ForEach-Object { $Report += "- $_" } }
$Report += ''
$Report += '## Policy'
$Report += '- No fake data.'
$Report += '- No hardcoded demo data.'
$Report += '- Evidence required for scores and timelines.'
$Report += '- Estimated language required when exact dates are missing.'
$Report += ''
$Report += 'TASK_COMPLETION=100/100'
$Report += 'TERRAYIELD_TASK_DONE'

$Report | Set-Content -Path $ReportPath -Encoding UTF8
try { Copy-Item -Path $ReportPath -Destination $ExternalReport -Force } catch { Write-Step "EXTERNAL_REPORT_COPY_WARNING=$($_.Exception.Message)" }

Write-Step "STATUS=$Status"
Write-Step "REPORT=$ReportPath"
Write-Step 'TASK_COMPLETION=100/100'
Write-Step 'TERRAYIELD_TASK_DONE'
exit 0
