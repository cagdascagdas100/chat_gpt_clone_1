#!/usr/bin/env python3
"""Deterministic network-free tests for the targeted Ofcom postcode join."""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

MODULE_PATH = Path(__file__).with_name("012_extract_slot3_ofcom_needed_postcodes.py")


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("targeted_join", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_module(MODULE_PATH)

FIELD_ALIASES = {
    "postcode": ["postcode"],
    "postcode_space": ["postcode_space"],
    "postcode_area": ["postcode area"],
    "sfbb": ["SFBB availability (% premises)"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)"],
    "unable30": ["% of premises unable to receive 30Mbit/s"],
    "unable_decent": ["% of premises unable to receive decent broadband from fixed or FWA"],
}
HEADERS = [aliases[0] for aliases in FIELD_ALIASES.values()]


def normalise_key(value: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def first_present(row: dict[str, Any], aliases: list[str]) -> Any:
    normalised = {normalise_key(k): v for k, v in row.items()}
    for alias in aliases:
        if normalise_key(alias) in normalised:
            return normalised[normalise_key(alias)]
    return None


def has_alias(headers: list[str], aliases: list[str]) -> bool:
    keys = {normalise_key(header) for header in headers}
    return any(normalise_key(alias) in keys for alias in aliases)


def normalise_postcode(value: Any) -> str | None:
    import re
    if value is None:
        return None
    result = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return result or None


def parse_percentage(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    number = float(str(value).replace("%", ""))
    if not 0 <= number <= 100:
        raise ValueError(f"outside range: {number}")
    return number


def row_number(row: dict[str, Any]) -> int | None:
    value = row.get("row_no") or row.get("canonical_row_no")
    return int(value) if value is not None else None


def parcel_id(row: dict[str, Any]) -> str | None:
    value = row.get("parcel_id") or row.get("canonical_program_parcel_id")
    return str(value) if value is not None else None


def parse_legacy_postcode(row: dict[str, Any]) -> str | None:
    return normalise_postcode(row.get("postcode"))


def identity_match(canonical: dict[str, Any], legacy: dict[str, Any]) -> tuple[bool, str]:
    if parcel_id(canonical) != parcel_id(legacy):
        return False, "PARCEL_ID_MISMATCH"
    if canonical.get("hmlr_inspire_id") and legacy.get("hmlr_inspire_id") and canonical["hmlr_inspire_id"] != legacy["hmlr_inspire_id"]:
        return False, "HMLR_INSPIRE_ID_MISMATCH"
    return True, "ROW_AND_OFFICIAL_ID_MATCH"


def build_rows(canonical_rows: list[dict[str, Any]], legacy_rows: dict[int, dict[str, Any]], coverage: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for canonical in canonical_rows:
        number = row_number(canonical)
        assert number is not None
        legacy = legacy_rows.get(number)
        postcode = parse_legacy_postcode(legacy or {})
        official = coverage.get(postcode or "")
        identity_ok, reason = identity_match(canonical, legacy) if legacy else (False, "NO_LEGACY_ROW")
        if legacy and postcode and identity_ok and official:
            status = "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW"
            confidence = 0.90
            level = "POSTCODE_PROXY"
        elif legacy and not identity_ok:
            status = "IDENTITY_CONFLICT_NO_DATA"
            confidence = 0.0
            level = "NO_DATA"
        elif legacy and postcode and not official:
            status = "POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA"
            confidence = 0.0
            level = "NO_DATA"
        else:
            status = "NO_VERIFIED_POSTCODE_NO_DATA"
            confidence = 0.0
            level = "NO_DATA"
        row = {
            "slot_id": "internet_access_3",
            "canonical_row_no": number,
            "canonical_program_parcel_id": parcel_id(canonical),
            "hmlr_row_id": canonical.get("hmlr_row_id"),
            "hmlr_inspire_id": canonical.get("hmlr_inspire_id"),
            "parcel_centroid_lon": canonical.get("hmlr_lon"),
            "parcel_centroid_lat": canonical.get("hmlr_lat"),
            "postcode": postcode,
            "identity_check": reason,
            "source_level": level,
            "internet_match_confidence": confidence,
            "internet_availability_quality_percent": None,
            "internet_quality_band": None,
            "calculation_version": None,
            "calculation_explanation": "Current Ofcom postcode fields retained individually; no parcel score emitted.",
            "status": status,
            "business_row_written": False,
        }
        if official and identity_ok:
            row.update(official)
        rows.append(row)
    return rows


BASE = SimpleNamespace(
    FIELD_ALIASES=FIELD_ALIASES,
    first_present=first_present,
    has_alias=has_alias,
    normalise_postcode=normalise_postcode,
    parse_percentage=parse_percentage,
    row_number=row_number,
    parcel_id=parcel_id,
    parse_legacy_postcode=parse_legacy_postcode,
    identity_match=identity_match,
    build_rows=build_rows,
)


def csv_row(postcode: str, area: str, **overrides: str) -> dict[str, str]:
    spaced = postcode[:-3] + " " + postcode[-3:]
    row = {
        "postcode": postcode,
        "postcode_space": spaced,
        "postcode area": area,
        "SFBB availability (% premises)": "98.0",
        "UFBB (100Mbit/s) availability (% premises)": "95.0",
        "UFBB availability (% premises)": "80.0",
        "Gigabit availability (% premises)": "75.0",
        "% of premises unable to receive 30Mbit/s": "2.0",
        "% of premises unable to receive decent broadband from fixed or FWA": "0.1",
    }
    row.update(overrides)
    return row


def write_csv(path: Path, rows: list[dict[str, str]], headers: list[str] | None = None) -> None:
    fieldnames = headers or HEADERS
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_valid_dir(root: Path) -> Path:
    directory = root / "postcode_files"
    directory.mkdir()
    write_csv(directory / "202601_fixed_postcode_coverage_r2_AA.csv", [csv_row("AA11AA", "AA"), csv_row("AA11AB", "AA")])
    write_csv(directory / "202601_fixed_postcode_coverage_r2_BB.csv", [csv_row("BB11AA", "BB"), csv_row("BB11AB", "BB")])
    write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("CC11AA", "CC"), csv_row("CC11AB", "CC")])
    return directory


def expect_error(func: Callable[[], Any], text: str) -> None:
    try:
        func()
    except Exception as exc:
        if text not in str(exc):
            raise AssertionError(f"Expected {text!r}, got {type(exc).__name__}: {exc}") from exc
    else:
        raise AssertionError(f"Expected failure containing {text!r}")


def test_valid_targeted_scan() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp))
        selected, files, stats = m.scan_ofcom_postcodes(directory, {"AA11AA", "CC11AB", "ZZ99ZZ"}, BASE, expected_file_count=3, expected_total_rows=6)
        assert set(selected) == {"AA11AA", "CC11AB"}
        assert len(files) == 3
        assert stats == {"ofcom_postcodes_scanned": 6, "ofcom_unique_postcodes": 6, "needed_postcodes": 3, "retained_postcodes": 2, "needed_postcodes_not_found": 1}


def test_reject_r1() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r1_AA.csv", [csv_row("AA11AC", "AA")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "r1 files")


def test_reject_file_count() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=4, expected_total_rows=6), "Expected 4")


def test_reject_total_rows() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=7), "Expected 7")


def test_reject_duplicate_postcode() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("AA11AA", "CC"), csv_row("CC11AB", "CC")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "Duplicate Ofcom postcode")


def test_reject_missing_required_field() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); headers = [h for h in HEADERS if h != "Gigabit availability (% premises)"]
        write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [{k: v for k, v in csv_row("CC11AA", "CC").items() if k in headers}], headers)
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=5), "missing strict fields")


def test_reject_blank_postcode() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("", "CC"), csv_row("CC11AB", "CC")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "Blank required field postcode")


def test_reject_postcode_space_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("CC11AA", "CC", postcode_space="CC9 9ZZ"), csv_row("CC11AB", "CC")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "postcode/postcode_space mismatch")


def test_reject_postcode_area_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("CC11AA", "DD"), csv_row("CC11AB", "CC")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "Postcode area mismatch")


def test_reject_percentage_out_of_range() -> None:
    with tempfile.TemporaryDirectory() as temp:
        directory = make_valid_dir(Path(temp)); write_csv(directory / "202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("CC11AA", "CC", **{"Gigabit availability (% premises)": "101"}), csv_row("CC11AB", "CC")])
        expect_error(lambda: m.scan_ofcom_postcodes(directory, set(), BASE, expected_file_count=3, expected_total_rows=6), "outside range")


def test_status_partition_and_samples() -> None:
    canonical = [{"row_no": 61523, "parcel_id": "parcel_61523", "hmlr_inspire_id": "A"}, {"row_no": 61524, "parcel_id": "parcel_61524", "hmlr_inspire_id": "B"}, {"row_no": 61525, "parcel_id": "parcel_61525", "hmlr_inspire_id": "C"}, {"row_no": 61526, "parcel_id": "parcel_61526", "hmlr_inspire_id": "D"}]
    legacy = {61523: {"row_no": 61523, "parcel_id": "parcel_61523", "hmlr_inspire_id": "A", "postcode": "AA11AA"}, 61524: {"row_no": 61524, "parcel_id": "WRONG", "hmlr_inspire_id": "B", "postcode": "AA11AB"}, 61525: {"row_no": 61525, "parcel_id": "parcel_61525", "hmlr_inspire_id": "C", "postcode": "ZZ99ZZ"}}
    rows = BASE.build_rows(canonical, legacy, {"AA11AA": {"postcode": "AA11AA", "gigabit_available_pct": 75.0}})
    assert [row["status"] for row in rows] == list(m.STATUS_ORDER)
    assert [row["status"] for row in m.choose_samples(rows)] == list(m.STATUS_ORDER)


def test_truth_flags() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); canonical_path = root / "canonical.json"; legacy_path = root / "legacy.json"
        canonical_path.write_text("{}", encoding="utf-8"); legacy_path.write_text("{}", encoding="utf-8")
        canonical = [{"row_no": number, "parcel_id": f"parcel_{number}"} for number in range(61523, 92284)]
        rows, manifest = m.build_manifest(canonical_path, legacy_path, canonical, {}, {}, [], {"ofcom_postcodes_scanned": 6, "ofcom_unique_postcodes": 6, "needed_postcodes": 0, "retained_postcodes": 0, "needed_postcodes_not_found": 0}, BASE)
        assert len(rows) == 30761
        assert manifest["actual_business_data_rows_written"] == 0 and manifest["scores_written"] == 0
        assert manifest["fake_data"] is False and manifest["db_write"] is False and manifest["migration"] is False and manifest["production_deploy"] is False and manifest["final_ready"] is False


TESTS = [test_valid_targeted_scan, test_reject_r1, test_reject_file_count, test_reject_total_rows, test_reject_duplicate_postcode, test_reject_missing_required_field, test_reject_blank_postcode, test_reject_postcode_space_mismatch, test_reject_postcode_area_mismatch, test_reject_percentage_out_of_range, test_status_partition_and_samples, test_truth_flags]


def main() -> int:
    results: list[dict[str, str]] = []
    for test in TESTS:
        test(); results.append({"test": test.__name__, "state": "PASS"})
    print(json.dumps({"passed": len(results), "total": len(TESTS), "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
