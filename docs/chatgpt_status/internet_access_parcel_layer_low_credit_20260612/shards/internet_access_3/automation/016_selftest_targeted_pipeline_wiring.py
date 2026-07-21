#!/usr/bin/env python3
"""Static, network-free wiring tests for targeted slot-3 orchestration."""
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


def test_targeted_command_uses_012() -> None:
    module = load(ROOT / "014_run_slot3_targeted_pipeline.py", "pipeline014")
    command = module.build_targeted_command(Path("A"), Path("S"), Path("E"), Path("O"))
    assert any(value.endswith("012_extract_slot3_ofcom_needed_postcodes.py") for value in command)
    assert "--canonical" in command and "--ofcom-postcode-dir" in command


def test_pipeline_required_set_complete() -> None:
    module = load(ROOT / "014_run_slot3_targeted_pipeline.py", "pipeline014_required")
    required = set(module.REQUIRED_AUTOMATION)
    assert {"002_extract_slot3_ofcom_2026_candidates.py", "008_download_validate_run_slot3.py", "012_extract_slot3_ofcom_needed_postcodes.py", "013_selftest_targeted_postcode_join.py"} <= required


def test_exact_entrypoint_targets_014() -> None:
    module = load(ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py", "entry015")
    with tempfile.TemporaryDirectory() as temp:
        command = module.build_child_command(Path(temp), Path(temp) / "work", None, None, 4, 600)
    assert any(value.endswith("014_run_slot3_targeted_pipeline.py") for value in command)
    assert "--download-retries" in command and "--download-timeout-seconds" in command


def test_exact_copy_set_and_truth_boundary() -> None:
    module = load(ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py", "entry015_required")
    required = set(module.REQUIRED_AUTOMATION)
    assert "012_extract_slot3_ofcom_needed_postcodes.py" in required
    assert "013_selftest_targeted_postcode_join.py" in required
    assert "014_run_slot3_targeted_pipeline.py" in required
    source = (ROOT / "015_materialize_exact_blobs_and_run_targeted_slot3.py").read_text(encoding="utf-8")
    for literal in ('"actual_business_data_rows_written": 0', '"scores_written": 0', '"fake_data": False', '"db_write": False', '"migration": False', '"production_deploy": False', '"final_ready": False'):
        assert literal in source


TESTS = [test_targeted_command_uses_012, test_pipeline_required_set_complete, test_exact_entrypoint_targets_014, test_exact_copy_set_and_truth_boundary]


def main() -> int:
    results = []
    for test in TESTS:
        test(); results.append({"test": test.__name__, "state": "PASS"})
    print(json.dumps({"passed": len(results), "total": len(TESTS), "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
