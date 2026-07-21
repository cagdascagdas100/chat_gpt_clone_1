#!/usr/bin/env python3
"""Deterministic network-free tests for direct Ofcom ZIP streaming."""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

MODULE_PATH = Path(__file__).with_name("017_stream_ofcom_zip_needed_postcodes.py")


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load(MODULE_PATH, "direct_zip_stream")

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
    values = {normalise_key(key): value for key, value in row.items()}
    for alias in aliases:
        key = normalise_key(alias)
        if key in values:
            return values[key]
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
    number = float(str(value).strip().replace("%", ""))
    if not 0 <= number <= 100:
        raise ValueError(f"outside range: {number}")
    return number


BASE = SimpleNamespace(
    FIELD_ALIASES=FIELD_ALIASES,
    first_present=first_present,
    has_alias=has_alias,
    normalise_postcode=normalise_postcode,
    parse_percentage=parse_percentage,
)


def csv_row(postcode: str, area: str, **overrides: str) -> dict[str, str]:
    spaced = postcode[:-3] + " " + postcode[-3:] if postcode else ""
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


def csv_bytes(rows: list[dict[str, str]], headers: list[str] | None = None) -> bytes:
    output = io.StringIO(newline="")
    fieldnames = headers or HEADERS
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def make_zip(path: Path, members: list[tuple[str, list[dict[str, str]], list[str] | None]]) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, rows, headers in members:
            archive.writestr(name, csv_bytes(rows, headers))
    return path


def valid_members() -> list[tuple[str, list[dict[str, str]], list[str] | None]]:
    return [
        ("folder/202601_fixed_postcode_coverage_r2_AA.csv", [csv_row("AA11AA", "AA"), csv_row("AA11AB", "AA")], None),
        ("folder/202601_fixed_postcode_coverage_r2_BB.csv", [csv_row("BB11AA", "BB"), csv_row("BB11AB", "BB")], None),
        ("folder/202601_fixed_postcode_coverage_r2_CC.csv", [csv_row("CC11AA", "CC"), csv_row("CC11AB", "CC")], None),
    ]


def expect_error(func: Callable[[], Any], text: str) -> None:
    try:
        func()
    except Exception as exc:
        if text not in str(exc):
            raise AssertionError(f"Expected {text!r}, got {type(exc).__name__}: {exc}") from exc
    else:
        raise AssertionError(f"Expected failure containing {text!r}")


def scan(path: Path, needed: set[str] | None = None, files: int = 3, rows: int = 6):
    return m.scan_ofcom_zip(
        path,
        needed or set(),
        BASE,
        expected_file_count=files,
        expected_total_rows=rows,
        minimum_zip_bytes=1,
    )


def test_valid_direct_stream() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        selected, files, stats = scan(path, {"AA11AA", "CC11AB", "ZZ99ZZ"})
        assert set(selected) == {"AA11AA", "CC11AB"}
        assert len(files) == 3
        assert stats["ofcom_postcodes_scanned"] == 6
        assert stats["needed_postcodes_not_found"] == 1
        assert stats["ofcom_csv_extracted_to_disk"] is False


def test_area_partition_stats() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        _, files, stats = scan(path, {"AA11AA"})
        assert stats["postcode_uniqueness_strategy"] == "AREA_PARTITIONED_EXACT_PER_MEMBER_SET"
        assert stats["postcode_area_member_count"] == 3
        assert stats["ofcom_unique_postcodes"] == 6
        assert stats["peak_member_unique_postcodes"] == 2


def test_member_unique_count_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        _, files, _ = scan(path)
        assert [item["unique_postcodes"] for item in files] == [2, 2, 2]
        assert all(item["unique_postcodes"] == item["rows"] for item in files)


def test_member_hash_crc_manifest() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        _, files, stats = scan(path, {"AA11AA"})
        assert all(len(item["sha256"]) == 64 and len(item["crc32"]) == 8 for item in files)
        assert stats["zip_member_stream_sha256_count"] == 3
        assert len(stats["ofcom_zip_sha256"]) == 64


def test_reject_non_zip_signature() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "bad.zip"; path.write_bytes(b"not-a-zip")
        expect_error(lambda: scan(path), "ZIP signature")


def test_reject_r1_member() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members() + [("202601_fixed_postcode_coverage_r1_DD.csv", [csv_row("DD11AA", "DD")], None)]
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "r1 postcode members")


def test_reject_file_count() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        expect_error(lambda: scan(path, files=4), "Expected 4")


def test_reject_duplicate_member_basename() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members() + [("other/202601_fixed_postcode_coverage_r2_AA.csv", [csv_row("AA11AC", "AA")], None)]
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path, files=4, rows=7), "Duplicate corrected r2 member basenames")


def test_reject_total_rows() -> None:
    with tempfile.TemporaryDirectory() as temp:
        path = make_zip(Path(temp) / "official.zip", valid_members())
        expect_error(lambda: scan(path, rows=7), "Expected 7")


def test_reject_duplicate_postcode_within_area() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members()
        members[0] = (members[0][0], [csv_row("AA11AA", "AA"), csv_row("AA11AA", "AA")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "Duplicate Ofcom postcode within AA")


def test_reject_duplicate_normalised_area_members() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = [
            ("folder/202601_fixed_postcode_coverage_r2_AA.csv", [csv_row("AA11AA", "AA")], None),
            ("other/202601_fixed_postcode_coverage_r2_aa.csv", [csv_row("AA11AB", "AA")], None),
            ("folder/202601_fixed_postcode_coverage_r2_BB.csv", [csv_row("BB11AA", "BB")], None),
        ]
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path, files=3, rows=3), "Duplicate corrected r2 postcode areas")


def test_cross_area_duplicate_cannot_bypass_partition() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members()
        members[2] = (members[2][0], [csv_row("AA11AA", "CC"), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "Postcode area mismatch")


def test_reject_missing_field() -> None:
    with tempfile.TemporaryDirectory() as temp:
        headers = [header for header in HEADERS if header != "Gigabit availability (% premises)"]
        members = valid_members()
        members[2] = (members[2][0], [{k: v for k, v in csv_row("CC11AA", "CC").items() if k in headers}], headers)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path, rows=5), "missing strict fields")


def test_reject_blank_postcode() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members(); members[2] = (members[2][0], [csv_row("", "CC"), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "Blank required field postcode")


def test_reject_postcode_space_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members(); members[2] = (members[2][0], [csv_row("CC11AA", "CC", postcode_space="CC9 9ZZ"), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "postcode/postcode_space mismatch")


def test_reject_postcode_area_field_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members(); members[2] = (members[2][0], [csv_row("CC11AA", "DD"), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "Postcode area mismatch")


def test_reject_filename_area_mismatch() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members(); members[2] = ("folder/202601_fixed_postcode_coverage_r2_DD.csv", [csv_row("CC11AA", "CC"), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "Postcode area mismatch")


def test_reject_percentage_range() -> None:
    with tempfile.TemporaryDirectory() as temp:
        members = valid_members(); members[2] = (members[2][0], [csv_row("CC11AA", "CC", **{"Gigabit availability (% premises)": "101"}), csv_row("CC11AB", "CC")], None)
        path = make_zip(Path(temp) / "official.zip", members)
        expect_error(lambda: scan(path), "outside range")


TESTS = [
    test_valid_direct_stream,
    test_area_partition_stats,
    test_member_unique_count_manifest,
    test_member_hash_crc_manifest,
    test_reject_non_zip_signature,
    test_reject_r1_member,
    test_reject_file_count,
    test_reject_duplicate_member_basename,
    test_reject_total_rows,
    test_reject_duplicate_postcode_within_area,
    test_reject_duplicate_normalised_area_members,
    test_cross_area_duplicate_cannot_bypass_partition,
    test_reject_missing_field,
    test_reject_blank_postcode,
    test_reject_postcode_space_mismatch,
    test_reject_postcode_area_field_mismatch,
    test_reject_filename_area_mismatch,
    test_reject_percentage_range,
]


def main() -> int:
    results: list[dict[str, str]] = []
    for test in TESTS:
        test()
        results.append({"test": test.__name__, "state": "PASS"})
    print(json.dumps({"passed": len(results), "total": len(TESTS), "results": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
