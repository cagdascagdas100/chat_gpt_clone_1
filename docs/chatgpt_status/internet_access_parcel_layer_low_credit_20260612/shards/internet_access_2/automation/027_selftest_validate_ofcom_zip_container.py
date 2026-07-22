#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path(__file__).with_name("026_validate_ofcom_zip_container.py")
spec = importlib.util.spec_from_file_location("zip_guard", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import ZIP guard")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.EXPECTED_R2_COUNT = 4

passed: list[str] = []


def check(name: str, value: bool) -> None:
    if not value:
        raise AssertionError(name)
    passed.append(name)


def expect_fail(name: str, fn, text: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if text not in str(exc):
            raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else:
        raise AssertionError(name)


def fake(name: str, *, flag_bits: int = 0, external_attr: int = 0,
         compress_type: int = zipfile.ZIP_DEFLATED, file_size: int = 10,
         compress_size: int = 5):
    return SimpleNamespace(
        filename=name, flag_bits=flag_bits, external_attr=external_attr,
        compress_type=compress_type, file_size=file_size, compress_size=compress_size,
        is_dir=lambda: name.endswith("/"),
    )


def valid_infos():
    return [fake(f"root/postcode_files/202601_fixed_postcode_coverage_r2_{area}.csv") for area in ("AA", "AB", "AC", "AD")]


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    zip_path = root / "official.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for area in ("AA", "AB", "AC", "AD"):
            archive.writestr(f"root/postcode_files/202601_fixed_postcode_coverage_r2_{area}.csv", "postcode,value\nAA1 1AA,1\n")
    out = root / "audit.json"
    result = module.audit(zip_path, out)
    check("valid_archive_status", result["status"] == "PASS_SAFE_OFFICIAL_ZIP_CONTAINER_REVIEW_ONLY")
    check("exact_r2_count", result["r2_postcode_file_count"] == 4)
    check("sha256_recorded", len(result["zip_sha256"]) == 64)
    check("audit_written", out.is_file())
    check("review_only_boundary", result["actual_business_data_rows_written"] == 0 and result["final_ready"] is False)

expect_fail("traversal_rejected", lambda: module.validate_entries(valid_infos() + [fake("../evil.csv")]), "unsafe path segments")
expect_fail("absolute_path_rejected", lambda: module.validate_entries(valid_infos() + [fake("/evil.csv")]), "absolute")
expect_fail("drive_path_rejected", lambda: module.validate_entries(valid_infos() + [fake("C:/evil.csv")]), "drive")
expect_fail("duplicate_casefold_path_rejected", lambda: module.validate_entries(valid_infos() + [fake("ROOT/POSTCODE_FILES/202601_FIXED_POSTCODE_COVERAGE_R2_AA.CSV")]), "duplicated")
expect_fail("encrypted_entry_rejected", lambda: module.validate_entries(valid_infos() + [fake("x.csv", flag_bits=1)]), "Encrypted")
expect_fail("symlink_entry_rejected", lambda: module.validate_entries(valid_infos() + [fake("link", external_attr=(0o120777 << 16))]), "Symlink")
expect_fail("unsupported_compression_rejected", lambda: module.validate_entries(valid_infos() + [fake("x.csv", compress_type=zipfile.ZIP_BZIP2)]), "Unsupported")
expect_fail("internal_r1_rejected", lambda: module.validate_entries(valid_infos() + [fake("root/postcode_files/202601_fixed_postcode_coverage_r1_ZZ.csv")]), "r1")
bad_parent = [fake(f"root/wrong/202601_fixed_postcode_coverage_r2_{area}.csv") for area in ("AA", "AB", "AC", "AD")]
expect_fail("wrong_parent_rejected", lambda: module.validate_entries(bad_parent), "outside postcode_files")
missing = [fake(f"root/postcode_files/202601_fixed_postcode_coverage_r2_{area}.csv") for area in ("AA", "AB", "AC")]
expect_fail("missing_exact_r2_count_rejected", lambda: module.validate_entries(missing), "Expected 4")
empty = valid_infos()
empty[0].file_size = 0
expect_fail("empty_file_rejected", lambda: module.validate_entries(empty), "empty")
expect_fail("control_character_path_rejected", lambda: module.validate_entries(valid_infos() + [fake("bad\nname.csv")]), "control-character")
dupe_area = [
    fake("a/postcode_files/202601_fixed_postcode_coverage_r2_AA.csv"),
    fake("b/postcode_files/202601_fixed_postcode_coverage_r2_AA.csv"),
    fake("c/postcode_files/202601_fixed_postcode_coverage_r2_AB.csv"),
    fake("d/postcode_files/202601_fixed_postcode_coverage_r2_AC.csv"),
]
expect_fail("duplicate_area_rejected", lambda: module.validate_entries(dupe_area), "area identifiers")

print(json.dumps({
    "status": "PASS",
    "tests_passed": len(passed),
    "tests_total": 18,
    "test_names": passed,
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}, sort_keys=True))
