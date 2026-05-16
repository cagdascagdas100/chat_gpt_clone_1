$ErrorActionPreference = "Stop"

$ExpectedBranch = "security-accuracy-expansion-20260508"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppRoot = Resolve-Path (Join-Path $ScriptDir "..\..\..")
$GitRoot = (git -C $AppRoot rev-parse --show-toplevel).Trim()
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $AppRoot "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_BLOCKERS.md"
$PytestOut = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PYTEST.txt"
$DiffCheckOut = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_DIFF_CHECK.txt"
$ImportProbeOut = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_IMPORT_PROBE.txt"
$PublishLog = Join-Path $EvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PUBLISH_LOG.txt"
$PatchPy = Join-Path $EvidenceDir "repair_apply_source_lineage.py"

$BlockerList = New-Object System.Collections.Generic.List[string]
function Add-Blocker([string]$Name) { if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) } }

$BackupDir = Join-Path $EvidenceDir ("repair_apply_source_lineage_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Set-Location $AppRoot
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()
if ($Branch -ne $ExpectedBranch) { Add-Blocker "BRANCH_MISMATCH:$Branch" }

$PatchCode = @'
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

app_root = pathlib.Path(r"__APP_ROOT__")
evidence_dir = pathlib.Path(r"__EVIDENCE_DIR__")
backup_dir = pathlib.Path(r"__BACKUP_DIR__")
import_probe_out = pathlib.Path(r"__IMPORT_PROBE_OUT__")

matcher = app_root / "app" / "etl" / "match" / "parcel_matcher.py"
test_file = app_root / "tests" / "test_parcel_matcher_source_confidence.py"
blockers: list[str] = []
changed: list[str] = []

new_function = '''def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
    source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
    record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
    source_name_hint = _first_populated_attr(record, ("source_name", "provider_name", "dataset_name"))
    source_record_id_hint = _first_populated_attr(record, ("source_record_id", "record_id", "site_id", "transaction_id", "id"))
    source_updated_at_hint = _first_populated_attr(record, ("source_updated_at", "updated_at", "last_updated_at", "fetched_at"))

    lineage_fields_present = [
        name
        for name, value in (
            ("source_name", source_name_hint),
            ("source_record_id", source_record_id_hint),
            ("parcel_ref", record_parcel_hint),
            ("source_updated_at", source_updated_at_hint),
        )
        if value is not None
    ]

    if source_url:
        source_lineage_status = "verified_source_url"
        source_lineage_missing_reason = None
    elif lineage_fields_present:
        source_lineage_status = "partial_lineage_no_source_url"
        source_lineage_missing_reason = "missing_source_url_high_confidence_withheld"
    else:
        source_lineage_status = "missing_source_lineage"
        source_lineage_missing_reason = "missing_source_url_high_confidence_withheld"

    has_geometry = False
    polygon_attr = config.get("polygon_attr")
    point_attr = config.get("point_attr")
    if polygon_attr and getattr(record, polygon_attr, None) is not None:
        has_geometry = True
    if point_attr and getattr(record, point_attr, None) is not None:
        has_geometry = True

    payload = {
        "source_url": source_url,
        "source_name": source_name_hint,
        "source_record_id": source_record_id_hint,
        "source_updated_at": source_updated_at_hint,
        "matched_parcel_id": candidate.parcel_id,
        "parcel_ref": record_parcel_hint,
        "parcel_specific_spatial_match": (
            candidate.match_method in _SPATIAL_MATCH_METHODS
            or candidate.overlap_ratio is not None
            or candidate.distance_m is not None
            or has_geometry
        ),
        "ambiguous_match": bool(candidate.requires_review),
    }

    source_confidence_fields = build_source_confidence_fields(payload)
    source_confidence_fields.update(
        {
            "source_lineage_status": source_lineage_status,
            "source_lineage_fields_present": tuple(lineage_fields_present),
            "source_lineage_missing_reason": source_lineage_missing_reason,
        }
    )
    return source_confidence_fields
'''

new_test = '''def test_parcel_matcher_reports_partial_lineage_without_source_url() -> None:
    record = SimpleNamespace(
        parcel_ref="17103798",
        source_name="hmlr_inspire",
        source_record_id="england:east-devon-district-council:17103798",
        source_updated_at="2026-04-30",
        site_geometry=None,
        point_geometry=None,
    )
    config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
    candidate = MatchCandidate(
        parcel_id=477,
        match_method="metadata_inspire_exact",
        match_score=99.8,
        requires_review=False,
    )

    fields = _build_match_source_confidence_fields(record, config, candidate)

    assert fields["source_lineage_status"] == "partial_lineage_no_source_url"
    assert fields["source_lineage_missing_reason"] == "missing_source_url_high_confidence_withheld"
    assert "source_name" in fields["source_lineage_fields_present"]
    assert "source_record_id" in fields["source_lineage_fields_present"]
    assert "parcel_ref" in fields["source_lineage_fields_present"]
    assert fields["source_confidence_needs_review"] is True
'''

def backup(path: pathlib.Path) -> None:
    rel = path.relative_to(app_root)
    dest = backup_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, dest)

if not matcher.exists():
    blockers.append("MATCHER_NOT_FOUND")
else:
    text = matcher.read_text(encoding="utf-8-sig")
    pattern = re.compile(
        r'def _build_match_source_confidence_fields\(record: Any, config: dict\[str, Any\], candidate: "MatchCandidate"\) -> dict\[str, Any\]:\n.*?\n\n@dataclass',
        re.DOTALL,
    )
    replacement = new_function + "\n\n@dataclass"
    new_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        blockers.append("MATCHER_FUNCTION_REPLACE_FAILED")
    else:
        if new_text != text:
            backup(matcher)
            matcher.write_text(new_text, encoding="utf-8")
            changed.append("app/etl/match/parcel_matcher.py")

if not test_file.exists():
    blockers.append("TEST_FILE_NOT_FOUND")
else:
    text = test_file.read_text(encoding="utf-8-sig")
    if "test_parcel_matcher_reports_partial_lineage_without_source_url" not in text:
        text = text.rstrip() + "\n\n\n" + new_test
    else:
        # Replace existing partial-lineage test to keep it stable and trim EOF.
        pattern = re.compile(
            r'\n\ndef test_parcel_matcher_reports_partial_lineage_without_source_url\(\) -> None:\n.*?\n\s*assert fields\["source_confidence_needs_review"\] is True\s*',
            re.DOTALL,
        )
        text, count = pattern.subn("\n\n" + new_test, text, count=1)
        if count != 1:
            blockers.append("TEST_REPLACE_FAILED")
    text = text.rstrip() + "\n"
    backup(test_file)
    test_file.write_text(text, encoding="utf-8")
    changed.append("tests/test_parcel_matcher_source_confidence.py")

probe_cmd = [
    sys.executable,
    "-c",
    "import inspect; import app.etl.match.parcel_matcher as m; print(m.__file__); print('source_lineage_status' in inspect.getsource(m._build_match_source_confidence_fields)); print(inspect.getsource(m._build_match_source_confidence_fields))",
]
proc = subprocess.run(probe_cmd, cwd=str(app_root), text=True, capture_output=True, timeout=60)
import_probe_out.write_text(
    "EXIT_CODE=" + str(proc.returncode) + "\nSTDOUT\n" + proc.stdout + "\nSTDERR\n" + proc.stderr,
    encoding="utf-8",
)
if proc.returncode != 0:
    blockers.append("IMPORT_PROBE_FAILED")
elif "True" not in proc.stdout.splitlines()[1:2]:
    blockers.append("IMPORT_PROBE_SOURCE_LINEAGE_MISSING")

print("changed_files=" + "; ".join(changed))
print("blockers=" + "; ".join(blockers) if blockers else "blockers=none")
if blockers:
    raise SystemExit(10)
'@

$PatchCode = $PatchCode.Replace("__APP_ROOT__", ($AppRoot.Path -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__EVIDENCE_DIR__", ($EvidenceDir -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__BACKUP_DIR__", ($BackupDir -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__IMPORT_PROBE_OUT__", ($ImportProbeOut -replace "\\", "\\"))
Set-Content -LiteralPath $PatchPy -Value $PatchCode -Encoding UTF8

$PatchExit = $null
if ($BlockerList.Count -eq 0) {
  $PatchOutput = python $PatchPy 2>&1
  $PatchExit = $LASTEXITCODE
  if ($PatchExit -ne 0) { Add-Blocker "PATCH_OR_IMPORT_PROBE_FAILED" }
}

$DiffCheckExit = $null
if ($BlockerList.Count -eq 0) {
  $DiffCheckText = git diff --check -- "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1
  $DiffCheckExit = $LASTEXITCODE
  @("diff_check_exit_code=$DiffCheckExit", "", $DiffCheckText) | Set-Content -LiteralPath $DiffCheckOut -Encoding UTF8
  if ($DiffCheckExit -ne 0) { Add-Blocker "DIFF_CHECK_FAILED" }
}

$PytestExit = $null
if ($BlockerList.Count -eq 0) {
  $PytestOutput = python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q 2>&1
  $PytestExit = $LASTEXITCODE
  @(
    "pytest_exit_code=$PytestExit",
    "cmd=python -m pytest tests/test_parcel_matcher_source_confidence.py tests/test_source_confidence_integration.py tests/test_source_confidence_rules.py -q",
    "",
    $PytestOutput
  ) | Set-Content -LiteralPath $PytestOut -Encoding UTF8
  if ($PytestExit -ne 0) { Add-Blocker "TARGETED_PYTEST_FAILED" }
}

$CommitStatus = "not_attempted"
$PushStatus = "not_attempted"
$CommitHash = ""

if ($BlockerList.Count -eq 0) {
  git add "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1 | Tee-Object -FilePath $PublishLog
  $CachedFiles = git diff --cached --name-only
  if (-not $CachedFiles) {
    $CommitStatus = "nothing_to_commit"
  } else {
    git commit -m "Apply source lineage guard to parcel matcher" 2>&1 | Tee-Object -FilePath $PublishLog -Append
    if ($LASTEXITCODE -eq 0) {
      $CommitStatus = "committed"
      $CommitHash = (git rev-parse --short=12 HEAD).Trim()
      git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
      if ($LASTEXITCODE -eq 0) { $PushStatus = "pushed" } else { $PushStatus = "push_failed"; Add-Blocker "GIT_PUSH_FAILED" }
    } else {
      $CommitStatus = "commit_failed"
      Add-Blocker "GIT_COMMIT_FAILED"
    }
  }
}

$HeadAfter = (git rev-parse --short=12 HEAD).Trim()
$Final = if ($BlockerList.Count -eq 0) { "SOURCE_LINEAGE_APPLICATION_REPAIR_READY" } else { "BLOCKED" }
$Next = if ($Final -eq "SOURCE_LINEAGE_APPLICATION_REPAIR_READY") { "run_api_smoke_and_sync_main_repo" } else { $BlockerList[0] }

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task=REPAIR_APPLY_SOURCE_LINEAGE_APPLICATION",
  "app_root=$AppRoot",
  "git_root=$GitRoot",
  "main_repo=$MainRepo",
  "branch=$Branch",
  "head_before=$HeadBefore",
  "head_after=$HeadAfter",
  "backup_dir=$BackupDir",
  "patch_exit_code=$PatchExit",
  "diff_check_exit_code=$DiffCheckExit",
  "pytest_exit_code=$PytestExit",
  "import_probe_output=$ImportProbeOut",
  "pytest_output=$PytestOut",
  "diff_check_output=$DiffCheckOut",
  "commit_status=$CommitStatus",
  "commit_hash=$CommitHash",
  "push_status=$PushStatus",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# Repair Apply Source Lineage Blockers", "")
if ($BlockerList.Count -eq 0) { $BlockerLines += "- none" } else { foreach ($b in $BlockerList) { $BlockerLines += "- $b" } }
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_BLOCKERS.md") -Force
Copy-Item -LiteralPath $PytestOut -Destination (Join-Path $MainEvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_PYTEST.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $ImportProbeOut -Destination (Join-Path $MainEvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_IMPORT_PROBE.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $DiffCheckOut -Destination (Join-Path $MainEvidenceDir "REPAIR_APPLY_SOURCE_LINEAGE_DIFF_CHECK.txt") -Force -ErrorAction SilentlyContinue

Get-Content $Report
Write-Host ""
Get-Content $Blockers
