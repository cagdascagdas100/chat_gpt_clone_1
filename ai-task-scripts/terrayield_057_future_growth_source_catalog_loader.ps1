$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-057-future-growth-source-catalog-loader'

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

  $LoaderFile = Join-Path $Backend 'future_growth\source_catalog_loader.py'
  $ExampleFile = Join-Path $Backend 'future_growth\approved_sources.example.json'
  $TestFile = Join-Path $Backend 'future_growth\tests\test_source_catalog_loader.py'

  Write-NewFileOnly -Path $LoaderFile -Content @'
"""Load approved source catalog metadata from reviewed external JSON.

The loader validates metadata only. It does not fetch source data and does not
create operational records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from future_growth.connectors.official_source import OfficialSourceDescriptor
from future_growth.source_catalog import ApprovedSourceCatalog, SourceApproval


def load_approved_source_catalog(path: str | Path) -> ApprovedSourceCatalog:
    """Load approved source descriptors from a reviewed JSON config file."""

    config_path = Path(path)
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("approved source catalog JSON must be an object")
    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        raise ValueError("approved source catalog must contain a sources list")

    approvals = tuple(_approval_from_payload(item) for item in raw_sources)
    return ApprovedSourceCatalog(approvals=approvals)


def _approval_from_payload(item: Any) -> SourceApproval:
    if not isinstance(item, dict):
        raise ValueError("each source approval must be an object")

    descriptor = OfficialSourceDescriptor(
        source_name=_required_text(item, "source_name"),
        source_url=_required_text(item, "source_url"),
        source_type=item.get("source_type", "official_or_structured"),
        licensing_note=item.get("licensing_note"),
    )

    return SourceApproval(
        descriptor=descriptor,
        jurisdiction=_required_text(item, "jurisdiction"),
        coverage=_required_text(item, "coverage"),
        access_note=_required_text(item, "access_note"),
        licensing_note=_required_text(item, "licensing_note"),
        evidence_policy=item.get("evidence_policy", "source_url_and_retrieved_at_required"),
    )


def _required_text(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value
'@

  Write-NewFileOnly -Path $ExampleFile -Content @'
{
  "sources": []
}
'@

  Write-NewFileOnly -Path $TestFile -Content @'
"""Tests for loading approved source catalog metadata."""

from __future__ import annotations

import json

import pytest

from future_growth.source_catalog_loader import load_approved_source_catalog


def test_loader_accepts_empty_reviewed_catalog(tmp_path) -> None:
    catalog_path = tmp_path / "approved_sources.json"
    catalog_path.write_text(json.dumps({"sources": []}), encoding="utf-8")

    catalog = load_approved_source_catalog(catalog_path)

    assert list(catalog.iter_approvals()) == []


def test_loader_requires_sources_list(tmp_path) -> None:
    catalog_path = tmp_path / "approved_sources.json"
    catalog_path.write_text(json.dumps({}), encoding="utf-8")

    with pytest.raises(ValueError, match="sources list"):
        load_approved_source_catalog(catalog_path)


def test_loader_validates_required_fields(tmp_path) -> None:
    catalog_path = tmp_path / "approved_sources.json"
    catalog_path.write_text(json.dumps({"sources": [{"source_name": "x"}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="source_url"):
        load_approved_source_catalog(catalog_path)
'@
} catch { Add-ErrorText $_.Exception.Message }

$SyntaxExitCode = $null
$SyntaxOutput = ''
$PytestExitCode = $null
$PytestOutput = ''
try {
  Push-Location $Backend
  $PyFiles = @(
    'future_growth\source_catalog_loader.py',
    'future_growth\tests\test_source_catalog_loader.py'
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
  scope = 'Create source catalog JSON loader and empty example config. No data fetch. No operational source rows.'
  backend = $Backend
  created_files = @($Created)
  skipped_existing_files = @($Skipped)
  errors = @($Errors)
  syntax_check = [ordered]@{ command='python -m py_compile source catalog loader and test'; exit_code=$SyntaxExitCode; output=$SyntaxOutput }
  test_check = [ordered]@{ command='python -m pytest future_growth/tests -q'; exit_code=$PytestExitCode; output=$PytestOutput }
  backend_git_status_after = [ordered]@{ exit_code=$BackendGitExitCode; output=$BackendGitStatus }
  policy = [ordered]@{
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Add concrete approved source metadata only after source list and licensing/access notes are reviewed.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Source Catalog Loader',
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
  '- Empty example config by default; no hardcoded operational source rows.',
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

if ($FinalStatus -eq 'completed') { Write-Host 'FUTURE_GROWTH_SOURCE_CATALOG_LOADER_COMPLETE'; exit 0 }
Write-Host 'FUTURE_GROWTH_SOURCE_CATALOG_LOADER_FAILED'
exit 1
