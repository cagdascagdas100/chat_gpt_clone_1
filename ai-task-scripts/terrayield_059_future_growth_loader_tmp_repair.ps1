$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-059-future-growth-loader-tmp-repair'
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null
$Errors = @()
try {
  $SafeTmp = Join-Path $Backend '.tmp_pytest_aays1'
  New-Item -ItemType Directory -Force -Path $SafeTmp | Out-Null
  $env:TEMP = $SafeTmp
  $env:TMP = $SafeTmp
  $env:PYTEST_ADDOPTS = "--basetemp=$SafeTmp"

  $TestFile = Join-Path $Backend 'future_growth\tests\test_source_catalog_loader.py'
  @'
from __future__ import annotations
import json
from pathlib import Path
import pytest
from future_growth.source_catalog_loader import load_approved_source_catalog

TEST_TMP = Path(__file__).resolve().parents[2] / ".tmp_loader_tests"

def write_catalog(payload):
    TEST_TMP.mkdir(parents=True, exist_ok=True)
    p = TEST_TMP / "approved_sources.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p

def test_loader_accepts_empty_reviewed_catalog():
    catalog = load_approved_source_catalog(write_catalog({"sources": []}))
    assert list(catalog.iter_approvals()) == []

def test_loader_requires_sources_list():
    with pytest.raises(ValueError, match="sources list"):
        load_approved_source_catalog(write_catalog({}))

def test_loader_validates_required_source_url():
    with pytest.raises(ValueError, match="source_url"):
        load_approved_source_catalog(write_catalog({"sources": [{"source_name": "x"}]}))

def test_loader_accepts_reviewed_source_metadata_without_fetching():
    catalog = load_approved_source_catalog(write_catalog({"sources": [{"source_name": "unit_test_source_not_ingested", "source_url": "https://example.test/official-source", "source_type": "unit_test_fixture", "jurisdiction": "England", "coverage": "unit test coverage, not source data", "access_note": "unit test access note, not source data", "licensing_note": "unit test licensing note, not source data"}]}))
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
  $PytestOutput = (& python -m pytest future_growth\tests\test_source_catalog_loader.py -q --basetemp=.tmp_pytest_aays1 2>&1 | Out-String)
  $PytestExitCode = $LASTEXITCODE
  Pop-Location
} catch { try { Pop-Location } catch {}; $Errors += $_.Exception.Message }
$Status = if (($Errors.Count -eq 0) -and ($SyntaxExitCode -eq 0) -and ($PytestExitCode -eq 0)) { 'completed' } else { 'failed' }
$Audit = [ordered]@{ task_id=$TaskId; status=$Status; generated_at=(Get-Date).ToString('s'); errors=$Errors; syntax_exit_code=$SyntaxExitCode; pytest_exit_code=$PytestExitCode; syntax_output=$SyntaxOutput; pytest_output=$PytestOutput; policy=[ordered]@{ fake_data_allowed=$false; hardcoded_demo_data_allowed=$false; no_data_fetch=$true } }
$AuditPath = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$Audit | ConvertTo-Json -Depth 8 | Set-Content -Path $AuditPath -Encoding UTF8
@("# Loader Temp Repair", "", "Status: $Status", "", "Syntax exit code: $SyntaxExitCode", "Pytest exit code: $PytestExitCode", "", "No data fetch. No operational source rows.") | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination (Join-Path $QualityReportsDir "$TaskId.report.md") -Force
if ($Status -eq 'completed') { Write-Host 'LOADER_TMP_REPAIR_COMPLETE'; exit 0 }
Write-Host 'LOADER_TMP_REPAIR_FAILED'; exit 1
