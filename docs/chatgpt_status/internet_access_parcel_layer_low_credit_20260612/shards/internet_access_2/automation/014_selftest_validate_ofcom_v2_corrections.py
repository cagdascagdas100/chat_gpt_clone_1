#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("013_validate_ofcom_v2_corrections.py")
spec = importlib.util.spec_from_file_location("validator", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import validator")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

HEADERS = [
    "postcode", "postcode_space", "postcode area",
    "SFBB availability (% premises)", "UFBB (100Mbit/s) availability (% premises)",
    "UFBB availability (% premises)", "Gigabit availability (% premises)",
    "% of premises unable to receive 30Mbit/s",
    "% of premises unable to receive decent broadband from fixed or FWA",
]

def row(postcode: str, area: str, gigabit: str = "90") -> dict[str, str]:
    spaced = postcode[:-3] + " " + postcode[-3:]
    return {"postcode":postcode,"postcode_space":spaced,"postcode area":area,"SFBB availability (% premises)":"100","UFBB (100Mbit/s) availability (% premises)":"95","UFBB availability (% premises)":"92","Gigabit availability (% premises)":gigabit,"% of premises unable to receive 30Mbit/s":"0","% of premises unable to receive decent broadband from fixed or FWA":"0"}

def write(path: Path, rows: list[dict[str,str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader(); writer.writerows(rows)

def expect_fail(name: str, fn, text: str, passed: list[str]) -> None:
    try: fn()
    except ValueError as exc:
        if text not in str(exc): raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else: raise AssertionError(name)

passed: list[str] = []
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    areas = {"CV":"CV11AA","CW":"CW11AA","ME":"ME11AA","MK":"MK11AA"}
    for area, postcode in areas.items(): write(root / f"202601_fixed_postcode_coverage_r2_{area}.csv", [row(postcode, area)])
    report = module.validate(root, expected_files=4, expected_rows=4)
    checks = {
        "valid_status": report["status"] == "PASS_OFFICIAL_V2_R2_CORRECTION_VALIDATED",
        "exact_file_count": report["file_count"] == 4,
        "exact_row_count": report["row_count"] == 4,
        "unique_postcodes": report["unique_postcode_count"] == 4,
        "cw_cv_distinct": report["cw_sha256"] != report["cv_sha256"],
        "mk_me_distinct": report["mk_sha256"] != report["me_sha256"],
        "no_business_write": report["actual_business_data_rows_written"] == 0,
        "not_final": report["final_ready"] is False,
    }
    for name, ok in checks.items():
        if not ok: raise AssertionError(name)
        passed.append(name)

    r1 = root / "202601_fixed_postcode_coverage_r1_CV.csv"; r1.write_text("postcode\nCV11AA\n", encoding="utf-8")
    expect_fail("r1_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Superseded r1", passed); r1.unlink()
    cv = root / "202601_fixed_postcode_coverage_r2_CV.csv"; cw = root / "202601_fixed_postcode_coverage_r2_CW.csv"; original_cw = cw.read_bytes(); cw.write_bytes(cv.read_bytes())
    expect_fail("cw_cv_duplicate_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "CW file is still", passed); cw.write_bytes(original_cw)
    me = root / "202601_fixed_postcode_coverage_r2_ME.csv"; mk = root / "202601_fixed_postcode_coverage_r2_MK.csv"; original_mk = mk.read_bytes(); mk.write_bytes(me.read_bytes())
    expect_fail("mk_me_duplicate_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "MK file is still", passed); mk.write_bytes(original_mk)
    bad = root / "202601_fixed_postcode_coverage_r2_CW.csv"; write(bad, [row("BAD", "CW")])
    expect_fail("invalid_postcode_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Invalid UK postcode", passed); write(bad, [row("CW11AA", "CW")])
    write(bad, [dict(row("CW11AA", "CW"), postcode_space="CW9 9ZZ")])
    expect_fail("postcode_space_mismatch_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "postcode/postcode_space mismatch", passed); write(bad, [row("CW11AA", "CW")])
    write(bad, [dict(row("CW11AA", "CW"), **{"postcode area":"CV"})])
    expect_fail("postcode_area_mismatch_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Postcode area mismatch", passed); write(bad, [row("CW11AA", "CW")])
    write(bad, [row("CW11AA", "CW", "nan")])
    expect_fail("nan_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Non-finite percentage", passed); write(bad, [row("CW11AA", "CW")])
    write(bad, [row("CW11AA", "CW", "101")])
    expect_fail("percent_101_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "outside 0-100", passed); write(bad, [row("CW11AA", "CW")])
    write(bad, [row("CV11AA", "CW")])
    expect_fail("duplicate_postcode_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Postcode area mismatch", passed); write(bad, [row("CW11AA", "CW")])
    missing = root / "202601_fixed_postcode_coverage_r2_MK.csv"; missing.unlink()
    expect_fail("file_count_rejected", lambda: module.validate(root, expected_files=4, expected_rows=4), "Expected 4", passed)

print({"status":"PASS","tests_passed":len(passed),"tests_total":18,"test_names":passed,"business_rows_written":0})
