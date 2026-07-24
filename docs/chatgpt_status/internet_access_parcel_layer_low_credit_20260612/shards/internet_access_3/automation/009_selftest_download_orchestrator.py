#!/usr/bin/env python3
"""Deterministic network-free tests for the slot-3 download orchestrator."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("008_download_validate_run_slot3.py")
spec = importlib.util.spec_from_file_location("slot3_orchestrator", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def make_zip(path: Path, *, r2_count: int = 3, r1_count: int = 0, duplicate_basename: bool = False) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for idx in range(r2_count):
            area = f"X{idx:02d}"
            name = f"postcode_files/202601_fixed_postcode_coverage_r2_{area}.csv"
            archive.writestr(name, "postcode,SFBB availability (% premises),UFBB (100Mbit/s) availability (% premises),UFBB availability (% premises),Gigabit availability (% premises)\n")
        if duplicate_basename:
            archive.writestr("other/202601_fixed_postcode_coverage_r2_X00.csv", "duplicate\n")
        for idx in range(r1_count):
            archive.writestr(f"postcode_files/202601_fixed_postcode_coverage_r1_Z{idx:02d}.csv", "bad\n")
        archive.writestr("postcode_res_files/202601_fixed_postcode_res_coverage_r1_X00.csv", "allowed residential r1\n")


def expect_error(fn, contains: str) -> None:
    try:
        fn()
    except mod.GateError as exc:
        assert contains in str(exc), (contains, str(exc))
    else:
        raise AssertionError(f"Expected GateError containing {contains!r}")


def main() -> int:
    passed = []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        valid = root / "valid.zip"
        make_zip(valid)
        metadata = mod.validate_zip_file(valid, min_bytes=0, expected_r2_count=3)
        assert metadata["r2_file_count"] == 3 and metadata["r1_file_count"] == 0
        passed.append("valid_r2_zip")

        r1 = root / "r1.zip"
        make_zip(r1, r1_count=1)
        expect_error(lambda: mod.validate_zip_file(r1, min_bytes=0, expected_r2_count=3), "r1")
        passed.append("reject_all_premises_r1")

        wrong = root / "wrong.zip"
        make_zip(wrong, r2_count=2)
        expect_error(lambda: mod.validate_zip_file(wrong, min_bytes=0, expected_r2_count=3), "Expected 3")
        passed.append("reject_wrong_r2_count")

        invalid = root / "invalid.zip"
        invalid.write_bytes(b"not-a-zip")
        expect_error(lambda: mod.validate_zip_file(invalid, min_bytes=0, expected_r2_count=3), "ZIP signature")
        passed.append("reject_invalid_signature")

        duplicate = root / "duplicate.zip"
        make_zip(duplicate, duplicate_basename=True)
        expect_error(lambda: mod.validate_zip_file(duplicate, min_bytes=0, expected_r2_count=4), "Duplicate")
        passed.append("reject_duplicate_basename")

        cache = root / "cache.zip"
        make_zip(cache)
        selection = mod.choose_existing_zip(None, cache, min_bytes=0, expected_r2_count=3)
        assert selection and selection[0] == "VALIDATED_CACHE"
        passed.append("validated_cache_selection")

        explicit = root / "explicit.zip"
        make_zip(explicit)
        selection = mod.choose_existing_zip(explicit, cache, min_bytes=0, expected_r2_count=3)
        assert selection and selection[0] == "EXPLICIT_OFFICIAL_ZIP"
        passed.append("explicit_zip_precedence")

        bad_explicit = root / "bad-explicit.zip"
        bad_explicit.write_bytes(b"bad")
        expect_error(lambda: mod.choose_existing_zip(bad_explicit, cache, min_bytes=0, expected_r2_count=3), "ZIP signature")
        passed.append("reject_bad_explicit_without_fallback")

        extract_dir = root / "extract"
        outputs = mod.extract_r2_files(valid, extract_dir, expected_r2_count=3)
        assert len(outputs) == 3 and all(path.is_file() for path in outputs)
        passed.append("safe_r2_only_extraction")

        diagnostics = mod.initial_diagnostics(root, root / "work", mod.OFFICIAL_ZIP_URL)
        truth = {k: diagnostics[k] for k in ["actual_business_data_rows_written", "scores_written", "fake_data", "db_write", "migration", "production_deploy", "final_ready"]}
        assert truth == {
            "actual_business_data_rows_written": 0,
            "scores_written": 0,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        passed.append("truth_flags")

    print(json.dumps({"passed": len(passed), "total": 10, "tests": passed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
