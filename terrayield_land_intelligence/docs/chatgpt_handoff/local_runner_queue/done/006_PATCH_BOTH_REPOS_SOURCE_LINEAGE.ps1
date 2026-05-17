$ErrorActionPreference = "Continue"

$TaskName = "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE"
$ExpectedBranch = "security-accuracy-expansion-20260508"
$CorrectRepo = "C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence"
$MainRepo = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$EvidenceDir = Join-Path $CorrectRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
$MainEvidenceDir = Join-Path $MainRepo "docs\chatgpt_handoff\parcel_location_evidence_wave_20260516"
New-Item -ItemType Directory -Force -Path $EvidenceDir, $MainEvidenceDir | Out-Null

$Report = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_REPORT.txt"
$Blockers = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_BLOCKERS.md"
$PytestOut = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_PYTEST.txt"
$ImportProbeOut = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_IMPORT_PROBE.txt"
$DiffCheckOut = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_DIFF_CHECK.txt"
$PublishLog = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_PUBLISH_LOG.txt"
$PatchPy = Join-Path $EvidenceDir "006_patch_both_repos_source_lineage.py"
$BackupDir = Join-Path $EvidenceDir ("006_patch_both_repos_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$BlockerList = New-Object System.Collections.Generic.List[string]
function Add-Blocker([string]$Name) { if (-not $BlockerList.Contains($Name)) { $BlockerList.Add($Name) } }

Set-Location $CorrectRepo
$Branch = (git branch --show-current).Trim()
$HeadBefore = (git rev-parse --short=12 HEAD).Trim()
if ($Branch -ne $ExpectedBranch) { Add-Blocker "BRANCH_MISMATCH:$Branch" }

$PullOutput = git pull origin $ExpectedBranch 2>&1
$PullExit = $LASTEXITCODE
if ($PullExit -ne 0) { Add-Blocker "GIT_PULL_FAILED" }

$PatchCode = @'
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

correct_repo = pathlib.Path(r"__CORRECT_REPO__")
main_repo = pathlib.Path(r"__MAIN_REPO__")
evidence_dir = pathlib.Path(r"__EVIDENCE_DIR__")
backup_dir = pathlib.Path(r"__BACKUP_DIR__")
import_probe_out = pathlib.Path(r"__IMPORT_PROBE_OUT__")
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

def backup(path: pathlib.Path, root: pathlib.Path, label: str) -> None:
    rel = path.relative_to(root)
    dest = backup_dir / label / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, dest)

def patch_root(root: pathlib.Path, label: str, patch_test: bool) -> None:
    matcher = root / "app" / "etl" / "match" / "parcel_matcher.py"
    if not matcher.exists():
        blockers.append(f"{label}:MATCHER_NOT_FOUND")
    else:
        text = matcher.read_text(encoding="utf-8-sig")
        pattern = re.compile(
            r'def _build_match_source_confidence_fields\(record: Any, config: dict\[str, Any\], candidate: "MatchCandidate"\) -> dict\[str, Any\]:\n.*?\n\n@dataclass',
            re.DOTALL,
        )
        replacement = new_function + "\n\n@dataclass"
        new_text, count = pattern.subn(replacement, text, count=1)
        if count != 1:
            blockers.append(f"{label}:MATCHER_FUNCTION_REPLACE_FAILED")
        else:
            if new_text != text:
                backup(matcher, root, label)
                matcher.write_text(new_text, encoding="utf-8")
                changed.append(f"{label}:app/etl/match/parcel_matcher.py")

    if patch_test:
        test_file = root / "tests" / "test_parcel_matcher_source_confidence.py"
        if not test_file.exists():
            blockers.append(f"{label}:TEST_FILE_NOT_FOUND")
        else:
            text = test_file.read_text(encoding="utf-8-sig")
            if "test_parcel_matcher_reports_partial_lineage_without_source_url" not in text:
                text = text.rstrip() + "\n\n\n" + new_test
            else:
                pattern = re.compile(
                    r'\n\ndef test_parcel_matcher_reports_partial_lineage_without_source_url\(\) -> None:\n.*?\n\s*assert fields\["source_confidence_needs_review"\] is True\s*',
                    re.DOTALL,
                )
                text, count = pattern.subn("\n\n" + new_test, text, count=1)
                if count != 1:
                    blockers.append(f"{label}:TEST_REPLACE_FAILED")
            text = text.rstrip() + "\n"
            backup(test_file, root, label)
            test_file.write_text(text, encoding="utf-8")
            changed.append(f"{label}:tests/test_parcel_matcher_source_confidence.py")

patch_root(correct_repo, "correct_repo", True)
patch_root(main_repo, "main_repo", True)

probe_cmd = [
    sys.executable,
    "-c",
    "import inspect; import app.etl.match.parcel_matcher as m; print(m.__file__); print('source_lineage_status' in inspect.getsource(m._build_match_source_confidence_fields)); print(inspect.getsource(m._build_match_source_confidence_fields))",
]
proc = subprocess.run(probe_cmd, cwd=str(correct_repo), text=True, capture_output=True, timeout=60)
import_probe_out.write_text(
    "EXIT_CODE=" + str(proc.returncode) + "\nSTDOUT\n" + proc.stdout + "\nSTDERR\n" + proc.stderr,
    encoding="utf-8",
)
if proc.returncode != 0:
    blockers.append("IMPORT_PROBE_FAILED")
elif len(proc.stdout.splitlines()) < 2 or proc.stdout.splitlines()[1].strip() != "True":
    blockers.append("IMPORT_PROBE_SOURCE_LINEAGE_MISSING")

print("changed_files=" + "; ".join(changed))
print("blockers=" + ("; ".join(blockers) if blockers else "none"))
if blockers:
    raise SystemExit(10)
'@

$PatchCode = $PatchCode.Replace("__CORRECT_REPO__", ($CorrectRepo -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__MAIN_REPO__", ($MainRepo -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__EVIDENCE_DIR__", ($EvidenceDir -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__BACKUP_DIR__", ($BackupDir -replace "\\", "\\"))
$PatchCode = $PatchCode.Replace("__IMPORT_PROBE_OUT__", ($ImportProbeOut -replace "\\", "\\"))
Set-Content -LiteralPath $PatchPy -Value $PatchCode -Encoding UTF8

$PatchOutput = python $PatchPy 2>&1
$PatchExit = $LASTEXITCODE
$PatchStdout = Join-Path $EvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_PATCH_STDOUT.txt"
$PatchOutput | Set-Content -LiteralPath $PatchStdout -Encoding UTF8
if ($PatchExit -ne 0) { Add-Blocker "PATCH_OR_IMPORT_PROBE_FAILED" }

$DiffCheckExit = $null
if ($BlockerList.Count -eq 0) {
  Set-Location $CorrectRepo
  $DiffCheckText = git diff --check -- "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" 2>&1
  $DiffCheckExit = $LASTEXITCODE
  @("diff_check_exit_code=$DiffCheckExit", "", $DiffCheckText) | Set-Content -LiteralPath $DiffCheckOut -Encoding UTF8
  if ($DiffCheckExit -ne 0) { Add-Blocker "DIFF_CHECK_FAILED" }
}

$PytestExit = $null
if ($BlockerList.Count -eq 0) {
  Set-Location $CorrectRepo
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
  Set-Location $CorrectRepo
  git add "app/etl/match/parcel_matcher.py" "tests/test_parcel_matcher_source_confidence.py" `
    "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516" 2>&1 | Tee-Object -FilePath $PublishLog
  $Cached = git diff --cached --name-only
  if ($Cached) {
    git commit -m "Apply source lineage guard across local worktrees" 2>&1 | Tee-Object -FilePath $PublishLog -Append
    if ($LASTEXITCODE -eq 0) {
      $CommitStatus = "committed"
      $CommitHash = (git rev-parse --short=12 HEAD).Trim()
      git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
      if ($LASTEXITCODE -eq 0) { $PushStatus = "pushed" } else { $PushStatus = "push_failed"; Add-Blocker "GIT_PUSH_FAILED" }
    } else {
      $CommitStatus = "commit_failed"
      Add-Blocker "GIT_COMMIT_FAILED"
    }
  } else {
    $CommitStatus = "nothing_to_commit"
  }
}

Set-Location $CorrectRepo
$HeadAfter = (git rev-parse --short=12 HEAD).Trim()
$Final = if ($BlockerList.Count -eq 0) { "PATCH_BOTH_REPOS_SOURCE_LINEAGE_READY" } else { "BLOCKED" }
$Next = if ($Final -eq "PATCH_BOTH_REPOS_SOURCE_LINEAGE_READY") { "queue_api_smoke_and_final_sync" } else { $BlockerList[0] }

@(
  "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
  "task=$TaskName",
  "correct_repo=$CorrectRepo",
  "main_repo=$MainRepo",
  "branch=$Branch",
  "head_before=$HeadBefore",
  "head_after=$HeadAfter",
  "git_pull_exit_code=$PullExit",
  "patch_exit_code=$PatchExit",
  "patch_stdout=$PatchStdout",
  "import_probe_output=$ImportProbeOut",
  "diff_check_exit_code=$DiffCheckExit",
  "diff_check_output=$DiffCheckOut",
  "pytest_exit_code=$PytestExit",
  "pytest_output=$PytestOut",
  "commit_status=$CommitStatus",
  "commit_hash=$CommitHash",
  "push_status=$PushStatus",
  "backup_dir=$BackupDir",
  "publish_log=$PublishLog",
  "db_write=none",
  "ddl=none",
  "migration_apply=none",
  "prod_deploy=none",
  "secret_values_printed=false",
  "final_classification=$Final",
  "next_single_action=$Next"
) | Set-Content -LiteralPath $Report -Encoding UTF8

$BlockerLines = @("# 006 Patch Both Repos Source Lineage Blockers", "")
if ($BlockerList.Count -eq 0) { $BlockerLines += "- none" } else { foreach ($b in $BlockerList) { $BlockerLines += "- $b" } }
$BlockerLines | Set-Content -LiteralPath $Blockers -Encoding UTF8

Copy-Item -LiteralPath $Report -Destination (Join-Path $MainEvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_REPORT.txt") -Force
Copy-Item -LiteralPath $Blockers -Destination (Join-Path $MainEvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_BLOCKERS.md") -Force
Copy-Item -LiteralPath $PytestOut -Destination (Join-Path $MainEvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_PYTEST.txt") -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $ImportProbeOut -Destination (Join-Path $MainEvidenceDir "006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_IMPORT_PROBE.txt") -Force -ErrorAction SilentlyContinue

# Always publish reports, including failures.
Set-Location $CorrectRepo
git add "docs/chatgpt_handoff/parcel_location_evidence_wave_20260516" `
  "docs/chatgpt_handoff/local_runner_queue/done" `
  "docs/chatgpt_handoff/local_runner_queue/failed" `
  "docs/chatgpt_handoff/local_runner_queue/outputs" 2>&1 | Tee-Object -FilePath $PublishLog -Append
$CachedReports = git diff --cached --name-only
if ($CachedReports -and $CommitStatus -ne "committed") {
  git commit -m "Publish dual-repo source lineage runner reports" 2>&1 | Tee-Object -FilePath $PublishLog -Append
  if ($LASTEXITCODE -eq 0) {
    git push origin $Branch 2>&1 | Tee-Object -FilePath $PublishLog -Append
  }
}

Get-Content $Report
Write-Host ""
Get-Content $Blockers
