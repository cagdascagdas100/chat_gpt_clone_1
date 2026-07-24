#!/usr/bin/env python3
"""Static, network-free wiring tests for direct-ZIP slot-3 orchestration."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from typing import Any

ROOT = Path(__file__).parent


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_targeted_command_uses_direct_zip_017() -> None:
    module = load(ROOT / "014_run_slot3_targeted_pipeline.py", "pipeline014")
    command = module.build_targeted_command(Path("A"), Path("S"), Path("official.zip"), Path("O"))
    assert any(value.endswith("017_stream_ofcom_zip_needed_postcodes.py") for value in command)
    assert "--canonical" in command and "--ofcom-zip" in command
    assert "--ofcom-postcode-dir" not in command


def test_pipeline_required_set_complete() -> None:
    module = load(ROOT / "014_run_slot3_targeted_pipeline.py", "pipeline014_required")
    required = set(module.REQUIRED_AUTOMATION)
    assert {
        "002_extract_slot3_ofcom_2026_candidates.py",
        "008_download_validate_run_slot3.py",
        "012_extract_slot3_ofcom_needed_postcodes.py",
        "013_selftest_targeted_postcode_join.py",
        "016_selftest_targeted_pipeline_wiring.py",
        "017_stream_ofcom_zip_needed_postcodes.py",
        "018_selftest_direct_zip_stream_join.py",
    } <= required


def test_pipeline_does_not_extract_csv_members() -> None:
    source = (ROOT / "014_run_slot3_targeted_pipeline.py").read_text(encoding="utf-8")
    assert "extract_r2_files(" not in source
    assert '"ofcom_csv_extracted_to_disk"] = False' in source
    assert "DIRECT_ZIP_STREAM" in source


def test_exact_entrypoint_targets_014() -> None:
    module = load(ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py", "entry015")
    with tempfile.TemporaryDirectory() as temp:
        command = module.build_child_command(Path(temp), Path(temp) / "work", None, None, 4, 600)
    assert any(value.endswith("014_run_slot3_targeted_pipeline.py") for value in command)
    assert "--download-retries" in command and "--download-timeout-seconds" in command


def test_exact_copy_set_contains_direct_zip_layer() -> None:
    module = load(ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py", "entry015_required")
    required = set(module.REQUIRED_AUTOMATION)
    assert "014_run_slot3_targeted_pipeline.py" in required
    assert "016_selftest_targeted_pipeline_wiring.py" in required
    assert "017_stream_ofcom_zip_needed_postcodes.py" in required
    assert "018_selftest_direct_zip_stream_join.py" in required


def test_exact_truth_boundary() -> None:
    source = (ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py").read_text(encoding="utf-8")
    for literal in (
        '"actual_business_data_rows_written": 0',
        '"scores_written": 0',
        '"fake_data": False',
        '"db_write": False',
        '"migration": False',
        '"production_deploy": False',
        '"final_ready": False',
        '"ofcom_csv_extracted_to_disk": False',
    ):
        assert literal in source


def test_direct_zip_uses_area_partitioned_exact_uniqueness() -> None:
    source = (ROOT / "017_stream_ofcom_zip_needed_postcodes.py").read_text(encoding="utf-8")
    assert "seen_in_member: set[str]" in source
    assert "AREA_PARTITIONED_EXACT_PER_MEMBER_SET" in source
    assert "seen_postcodes: set[str]" not in source


def test_direct_zip_rejects_duplicate_normalised_areas() -> None:
    source = (ROOT / "017_stream_ofcom_zip_needed_postcodes.py").read_text(encoding="utf-8")
    assert "Duplicate corrected r2 postcode areas found" in source
    assert "normalised_areas" in source


TESTS = [
    test_targeted_command_uses_direct_zip_017,
    test_pipeline_required_set_complete,
    test_pipeline_does_not_extract_csv_members,
    test_exact_entrypoint_targets_014,
    test_exact_copy_set_contains_direct_zip_layer,
    test_exact_truth_boundary,
    test_direct_zip_uses_area_partitioned_exact_uniqueness,
    test_direct_zip_rejects_duplicate_normalised_areas,
]


def main() -> int:
    results = []
    for test in TESTS:
        test()
        results.append({"test": test.__name__, "state": "PASS"})
    print(json.dumps({"passed": len(results), "total": len(TESTS), "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
