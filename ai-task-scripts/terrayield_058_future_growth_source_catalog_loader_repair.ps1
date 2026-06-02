$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-058-future-growth-source-catalog-loader-repair'
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null
$Errors = @()
try {
  $LoaderFile = Join-Path $Backend 'future_growth\source_catalog_loader.py'
  $TestFile = Join-Path $Backend 'future_growth\tests\test_source_catalog_loader.py'
  $ExampleFile = Join-Path $Backend 'future_growth\approved_sources.example.json'
  @'
"""Load approved source catalog metadata from reviewed external JSON."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Union
from future_growth.connectors.official_source import OfficialSourceDescriptor
from future_growth.source_catalog import ApprovedSourceCatalog, SourceApproval

def load_approved_source_catalog(path: Union[str, Path]) -> ApprovedSourceCatalog:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
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
    licensing_note = _required_text(item, "licensing_note")
    descriptor = OfficialSourceDescriptor(
        source_name=_required_text(item, "source_name"),
        source_url=_required_text(item, "source_url"),
        source_type=item.get("source_type", "official_or_structured"),
        licensing_note=licensing_note,
    )
    return SourceApproval(
        descriptor=descriptor,
        jurisdiction=_required_text(item, "jurisdiction"),
        coverage=_required_text(item, "coverage"),
        access_note=_required_text(item, "access_note"),
        licensing_note=licensing_note,
        evidence_policy=item.get("evidence_policy", "source_url_and_retrieved_at_required"),
    )

def _required_text(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value
'@ | Set-Content -Path $LoaderFile -Encoding UTF8
  @'
{
  "sources": []
}
'@ | Set-Content -Path $ExampleFile -Encoding UTF8
  @'
from __future__ import annotations
import json
import pytest
from future_growth.source_catalog_loader import load_approved_source_catalog

def test_loader_accepts_empty_reviewed_catalog(tmp_path):
    p = tmp_path / "approved_sources.json"
    p.write_text(json.dumps({"sources": []}), encoding="utf-8")
    catalog = load_approved_source_catalog(p)
    assert list(catalog.iter_approvals()) == []

def test_loader_requires_sources_list(tmp_path):
    p = tmp_path / "approved_sources.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(ValueError, match="sources list"):
        load_approved_source_catalog(p)

def test_loader_validates_required_source_url(tmp_path):
    p = tmp_path / "approved_sources.json"
    p.write_text(json.dumps({"sources": [{"source_name": "x"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="source_url"):
        load_approved_source_catalog(p)

def test_loader_accepts_reviewed_source_metadata_without_fetching(tmp_path):
    p = tmp_path / "approved_sources.json"
    p.write_text(json.dumps({"sources": [{"source_name": "unit_test_source_not_ingested", "source_url": "https://example.test/official-source", "source_type": "unit_test_fixture", "jurisdiction": "England", "coverage": "unit test coverage, not source data", "access_note": "unit test access note, not source data", "licensing_note": "unit test licensing note, not source data"}]}), encoding="utf-8")
    catalog = load_approved_source_catalog(p)
    approvals = list(catalog.iter_approvals())
    assert len(approvals) == 1
    assert approvals[0].descriptor.source_name == "unit_test_source_not_ingested"
'@ | Set-Content -Path $TestFile -Encoding UTF8
} catch { $Errors += $_.Exception.Message }
$SyntaxExitCode = 999; $PytestExitCode = 999; $SyntaxOutput = ''; $PytestOutput = ''
try {
  Push-Location $Backend
  $SyntaxOutput = (& python -m py_compile future_growth\source_catalog_loader.py future_growth\tests\test_source_catalog_loader.py 2>&1 | Out-String)
  $SyntaxExitCode = $LASTEXITCODE
  $PytestOutput = (& python -m pytest future_growth\tests\test_source_catalog_loader.py -q 2>&1 | Out-String)
  $PytestExitCode = $LASTEXITCODE
  Pop-Location
} catch { try { Pop-Location } catch {}; $Errors += $_.Exception.Message }
$Status = if (($Errors.Count -eq 0) -and ($SyntaxExitCode -eq 0) -and ($PytestExitCode -eq 0)) { 'completed' } else { 'failed' }
$Audit = [ordered]@{ task_id=$TaskId; status=$Status; generated_at=(Get-Date).ToString('s'); errors=$Errors; syntax_exit_code=$SyntaxExitCode; pytest_exit_code=$PytestExitCode; syntax_output=$SyntaxOutput; pytest_output=$PytestOutput; policy=[ordered]@{ fake_data_allowed=$false; hardcoded_demo_data_allowed=$false; no_data_fetch=$true } }
$AuditPath = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 8 | Set-Content -Path $AuditPath -Encoding UTF8
@("# Source Catalog Loader Repair", "", "Status: $Status", "", "Syntax exit code: $SyntaxExitCode", "Pytest exit code: $PytestExitCode", "", "No data fetch. No operational source rows.") | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination (Join-Path $QualityReportsDir "$TaskId.report.md") -Force
if ($Status -eq 'completed') { Write-Host 'SOURCE_CATALOG_LOADER_REPAIR_COMPLETE'; exit 0 }
Write-Host 'SOURCE_CATALOG_LOADER_REPAIR_FAILED'; exit 1
