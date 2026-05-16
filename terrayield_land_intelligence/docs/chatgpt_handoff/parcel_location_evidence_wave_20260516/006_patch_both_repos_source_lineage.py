from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

correct_repo = pathlib.Path(r"C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\.tmp_widescope_final_qa_20260515\\terrayield_land_intelligence")
main_repo = pathlib.Path(r"C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\terrayield_land_intelligence")
evidence_dir = pathlib.Path(r"C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\.tmp_widescope_final_qa_20260515\\terrayield_land_intelligence\\docs\\chatgpt_handoff\\parcel_location_evidence_wave_20260516")
backup_dir = pathlib.Path(r"C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\.tmp_widescope_final_qa_20260515\\terrayield_land_intelligence\\docs\\chatgpt_handoff\\parcel_location_evidence_wave_20260516\\006_patch_both_repos_backup_20260517_013204")
import_probe_out = pathlib.Path(r"C:\\Users\\cagda\\Documents\\GitHub\\AAYS\\.tmp_widescope_final_qa_20260515\\terrayield_land_intelligence\\docs\\chatgpt_handoff\\parcel_location_evidence_wave_20260516\\006_PATCH_BOTH_REPOS_SOURCE_LINEAGE_IMPORT_PROBE.txt")
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
