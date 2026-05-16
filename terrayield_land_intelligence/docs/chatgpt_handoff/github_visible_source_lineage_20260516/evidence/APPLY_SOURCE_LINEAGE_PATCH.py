from __future__ import annotations

import difflib
import pathlib
import shutil
import subprocess
from datetime import datetime, timezone

repo = pathlib.Path(r"C:\Users\cagda\Documents\GitHub\AAYS\.tmp_widescope_final_qa_20260515\terrayield_land_intelligence")
out_dir = pathlib.Path(r"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\docs\chatgpt_handoff\parcel_location_evidence_wave_20260516")
out_dir.mkdir(parents=True, exist_ok=True)

report_path = out_dir / "SOURCE_LINEAGE_PATCH_REPORT.txt"
blockers_path = out_dir / "SOURCE_LINEAGE_PATCH_BLOCKERS.md"
diff_path = out_dir / "SOURCE_LINEAGE_PATCH_DIFF.patch"
pytest_path = out_dir / "SOURCE_LINEAGE_PATCH_PYTEST.txt"

backup_dir = out_dir / ("source_lineage_patch_backup_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup_dir.mkdir(parents=True, exist_ok=True)

blockers: list[str] = []
changed_files: list[str] = []
diff_chunks: list[str] = []

def read(rel: str) -> str:
    return (repo / rel).read_text(encoding="utf-8")

def write(rel: str, text: str) -> None:
    path = repo / rel
    backup_path = backup_dir / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, backup_path)
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(text, encoding="utf-8")
    changed_files.append(rel)
    diff_chunks.extend(
        difflib.unified_diff(
            old.splitlines(),
            text.splitlines(),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            lineterm="",
        )
    )

def patch_parcel_matcher() -> None:
    rel = "app/etl/match/parcel_matcher.py"
    path = repo / rel
    if not path.exists():
        blockers.append("PARCEL_MATCHER_NOT_FOUND")
        return

    text = read(rel)

    if "source_lineage_status" in text and "missing_source_url_high_confidence_withheld" in text:
        return

    anchor = '    source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)\n    record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))\n'
    replacement = '''    source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
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
'''

    if anchor not in text:
        blockers.append("PARCEL_MATCHER_ANCHOR_NOT_FOUND")
        return

    text = text.replace(anchor, replacement, 1)

    payload_anchor = '''    payload = {
        "source_url": source_url,
        "matched_parcel_id": candidate.parcel_id,
        "parcel_ref": record_parcel_hint,
'''
    payload_replacement = '''    payload = {
        "source_url": source_url,
        "source_name": source_name_hint,
        "source_record_id": source_record_id_hint,
        "source_updated_at": source_updated_at_hint,
        "matched_parcel_id": candidate.parcel_id,
        "parcel_ref": record_parcel_hint,
'''

    if payload_anchor not in text:
        blockers.append("PARCEL_MATCHER_PAYLOAD_ANCHOR_NOT_FOUND")
        return

    text = text.replace(payload_anchor, payload_replacement, 1)

    return_anchor = "    return build_source_confidence_fields(payload)\n"
    return_replacement = '''    source_confidence_fields = build_source_confidence_fields(payload)
    source_confidence_fields.update(
        {
            "source_lineage_status": source_lineage_status,
            "source_lineage_fields_present": tuple(lineage_fields_present),
            "source_lineage_missing_reason": source_lineage_missing_reason,
        }
    )
    return source_confidence_fields
'''

    if return_anchor not in text:
        blockers.append("PARCEL_MATCHER_RETURN_ANCHOR_NOT_FOUND")
        return

    text = text.replace(return_anchor, return_replacement, 1)
    write(rel, text)

def patch_test() -> None:
    rel = "tests/test_parcel_matcher_source_confidence.py"
    path = repo / rel
    if not path.exists():
        blockers.append("PARCEL_MATCHER_TEST_NOT_FOUND")
        return

    text = read(rel)
    test_name = "test_parcel_matcher_reports_partial_lineage_without_source_url"
    if test_name in text:
        return

    addition = '''

def test_parcel_matcher_reports_partial_lineage_without_source_url() -> None:
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
    text = text.rstrip() + addition + "\n"
    write(rel, text)

patch_parcel_matcher()
patch_test()

diff_path.write_text("\n".join(diff_chunks) + ("\n" if diff_chunks else ""), encoding="utf-8")

pytest_exit = None
pytest_cmd = [
    "python",
    "-m",
    "pytest",
    "tests/test_parcel_matcher_source_confidence.py",
    "tests/test_source_confidence_integration.py",
    "tests/test_source_confidence_rules.py",
    "-q",
]
try:
    proc = subprocess.run(
        pytest_cmd,
        cwd=str(repo),
        text=True,
        capture_output=True,
        timeout=120,
    )
    pytest_exit = proc.returncode
    pytest_path.write_text(
        "CMD=" + " ".join(pytest_cmd) + "\n"
        + "EXIT_CODE=" + str(proc.returncode) + "\n\n"
        + "STDOUT\n"
        + proc.stdout
        + "\nSTDERR\n"
        + proc.stderr,
        encoding="utf-8",
    )
except Exception as exc:
    blockers.append("PYTEST_EXECUTION_ERROR")
    pytest_path.write_text(f"PYTEST_EXECUTION_ERROR={exc!r}\n", encoding="utf-8")

if blockers:
    final = "BLOCKED"
elif pytest_exit == 0:
    final = "SOURCE_LINEAGE_PATCH_READY"
else:
    final = "BLOCKED"
    blockers.append("TARGETED_PYTEST_FAILED")

report_lines = [
    f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
    "task=SOURCE_LINEAGE_PATCH",
    f"repo={repo}",
    f"changed_files={'; '.join(changed_files) if changed_files else 'none'}",
    f"backup_dir={backup_dir}",
    f"diff_file={diff_path}",
    f"pytest_file={pytest_path}",
    "db_write=none",
    "ddl=none",
    "migration_apply=none",
    "prod_deploy=none",
    "secret_values_printed=false",
    f"pytest_exit_code={pytest_exit}",
    f"final_classification={final}",
    f"next_single_action={'send_patch_outputs_to_chatgpt' if final == 'SOURCE_LINEAGE_PATCH_READY' else blockers[0]}",
]
report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

blocker_lines = ["# Source Lineage Patch Blockers", ""]
if blockers:
    blocker_lines.extend(f"- {item}" for item in blockers)
else:
    blocker_lines.append("- none")
blockers_path.write_text("\n".join(blocker_lines) + "\n", encoding="utf-8")

print(report_path.read_text(encoding="utf-8"))
print(blockers_path.read_text(encoding="utf-8"))
print(f"PYTEST_OUTPUT={pytest_path}")
print(f"DIFF_OUTPUT={diff_path}")
