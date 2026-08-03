from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
)
EXPECTED_POSTCODE_FILE_COUNT = 121
EXPECTED_TOTAL_DATA_ROWS = 1_741_096
MINIMUM_ARCHIVE_BYTES = 1_000_000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalized(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def archive_provenance_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".provenance.json")


def _postcode_member_sets(archive: zipfile.ZipFile) -> tuple[list[str], list[str]]:
    names = archive.namelist()
    r2_files = sorted(
        name
        for name in names
        if "/postcode_files/" in "/" + name.replace("\\", "/")
        and Path(name).name.startswith("202601_fixed_postcode_coverage_r2_")
        and name.lower().endswith(".csv")
    )
    stale_r1_all_premises = sorted(
        name
        for name in names
        if "/postcode_files/" in "/" + name.replace("\\", "/")
        and Path(name).name.startswith("202601_fixed_postcode_coverage_r1_")
        and name.lower().endswith(".csv")
    )
    return r2_files, stale_r1_all_premises


def archive_has_expected_members(archive: zipfile.ZipFile) -> bool:
    r2_files, stale_r1_all_premises = _postcode_member_sets(archive)
    unique_basenames = {Path(name).name.casefold() for name in r2_files}
    return (
        len(r2_files) == EXPECTED_POSTCODE_FILE_COUNT
        and len(unique_basenames) == EXPECTED_POSTCODE_FILE_COUNT
        and not stale_r1_all_premises
    )


def archive_is_structurally_valid(path: Path) -> bool:
    try:
        if (
            not path.is_file()
            or path.stat().st_size < MINIMUM_ARCHIVE_BYTES
            or not zipfile.is_zipfile(path)
        ):
            return False
        with zipfile.ZipFile(path) as archive:
            if not archive.namelist():
                return False
            if archive.testzip() is not None:
                return False
            return archive_has_expected_members(archive)
    except (OSError, EOFError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return False


def archive_provenance_matches(path: Path, source_url: str) -> bool:
    sidecar = archive_provenance_path(path)
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        expected_sha = str(payload.get("archive_sha256", ""))
        expected_size = int(payload.get("archive_size_bytes", -1))
        return (
            payload.get("schema_version") == 1
            and payload.get("source_url") == source_url
            and expected_size == path.stat().st_size
            and len(expected_sha) == 64
            and expected_sha == sha256_file(path)
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def archive_is_reusable(path: Path, source_url: str) -> bool:
    return archive_is_structurally_valid(path) and archive_provenance_matches(path, source_url)


def write_archive_provenance(path: Path, source_url: str) -> dict:
    payload = {
        "schema_version": 1,
        "source_url": source_url,
        "archive_size_bytes": path.stat().st_size,
        "archive_sha256": sha256_file(path),
        "validated_at": utc_now(),
        "validation": {
            "minimum_size": True,
            "non_empty_zip": True,
            "member_crc": True,
            "corrected_r2_postcode_member_count": EXPECTED_POSTCODE_FILE_COUNT,
            "stale_r1_all_premises_member_count": 0,
        },
    }
    atomic_json(archive_provenance_path(path), payload)
    return payload


def remove_archive_and_provenance(path: Path) -> None:
    path.unlink(missing_ok=True)
    archive_provenance_path(path).unlink(missing_ok=True)


def download(url: str, destination: Path, timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        temporary = destination.with_suffix(destination.suffix + f".part.{attempt}")
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "AAYS-TerraYield-internet-access-audit/1.0",
                    "Accept": "application/zip, application/octet-stream;q=0.9, */*;q=0.1",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as out:
                if int(getattr(response, "status", 200)) != 200:
                    raise RuntimeError(f"HTTP_STATUS_{getattr(response, 'status', 'UNKNOWN')}")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                out.flush()
                os.fsync(out.fileno())
            if not archive_is_structurally_valid(temporary):
                raise RuntimeError("DOWNLOAD_ARCHIVE_INTEGRITY_OR_STRUCTURE_FAILED")
            os.replace(temporary, destination)
            write_archive_provenance(destination, url)
            if not archive_is_reusable(destination, url):
                raise RuntimeError("DOWNLOAD_ARCHIVE_PROVENANCE_FAILED")
            return
        except Exception as exc:
            last_error = exc
            temporary.unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"DOWNLOAD_FAILED: {last_error}")


def ensure_archive(url: str, destination: Path, timeout: int) -> str:
    if archive_is_reusable(destination, url):
        return "REUSED_VALIDATED_SOURCE_BOUND_CACHE"
    remove_archive_and_provenance(destination)
    download(url, destination, timeout)
    if not archive_is_reusable(destination, url):
        remove_archive_and_provenance(destination)
        raise RuntimeError("DOWNLOADED_ARCHIVE_FAILED_SOURCE_BOUND_VALIDATION")
    return "DOWNLOADED_AND_SOURCE_BOUND_VALIDATED"


def choose_column(headers: list[str], aliases: tuple[str, ...]) -> str | None:
    by_key = {normalized(header): header for header in headers}
    for alias in aliases:
        found = by_key.get(normalized(alias))
        if found:
            return found
    return None


def audit_zip(zip_path: Path, count_rows: bool) -> dict:
    required_aliases = {
        "postcode": ("postcode",),
        "postcode_space": ("postcode_space", "postcode space"),
        "sfbb_30mbps_pct": (
            "SFBB availability (% premises)",
            "SFBB availability percent premises",
        ),
        "ufbb_100mbps_pct": (
            "UFBB (100Mbit/s) availability (% premises)",
            "UFBB 100Mbit/s availability percent premises",
        ),
        "gigabit_pct": (
            "Gigabit availability (% premises)",
            "Gigabit availability percent premises",
        ),
        "decent_unavailable_pct": (
            "% of premises unable to receive decent broadband from fixed or FWA",
            "percent of premises unable to receive decent broadband from fixed or FWA",
        ),
    }
    with zipfile.ZipFile(zip_path) as archive:
        r2_files, stale_r1_all_premises = _postcode_member_sets(archive)
        headers_by_file: dict[str, list[str]] = {}
        mapped_columns: dict[str, dict[str, str | None]] = {}
        row_count = 0
        for name in r2_files:
            with archive.open(name, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                reader = csv.reader(text)
                headers = next(reader, [])
                headers_by_file[Path(name).name] = headers
                mapped_columns[Path(name).name] = {
                    key: choose_column(headers, aliases)
                    for key, aliases in required_aliases.items()
                }
                if count_rows:
                    row_count += sum(1 for _ in reader)

    missing_by_file = {
        name: [key for key, value in columns.items() if value is None]
        for name, columns in mapped_columns.items()
        if any(value is None for value in columns.values())
    }
    postcode_areas = sorted(
        Path(name).stem.removeprefix("202601_fixed_postcode_coverage_r2_")
        for name in r2_files
    )
    checks = {
        "zip_is_readable": True,
        "corrected_r2_postcode_files_present": len(r2_files) == EXPECTED_POSTCODE_FILE_COUNT,
        "stale_r1_all_premises_files_absent": len(stale_r1_all_premises) == 0,
        "postcode_areas_unique": len(postcode_areas) == len(set(postcode_areas)),
        "required_columns_present_in_every_file": not missing_by_file and bool(r2_files),
        "official_row_count_matches": (not count_rows) or row_count == EXPECTED_TOTAL_DATA_ROWS,
    }
    return {
        "checks": checks,
        "postcode_file_count": len(r2_files),
        "postcode_areas": postcode_areas,
        "stale_r1_all_premises_file_count": len(stale_r1_all_premises),
        "data_row_count": row_count if count_rows else None,
        "expected_data_row_count": EXPECTED_TOTAL_DATA_ROWS,
        "missing_columns_by_file": missing_by_file,
        "sample_headers": next(iter(headers_by_file.values()), []),
        "sample_column_mapping": next(iter(mapped_columns.values()), {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--count-rows", action="store_true")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    cache_dir = args.cache_dir or root / "runtime" / "internet_access_1" / "source_cache"
    zip_path = cache_dir / "ofcom_connected_nations_spring_2026_fixed_coverage.zip"
    started_at = utc_now()
    report: dict = {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "stage": "OFCom_2026_POSTCODE_SCHEMA_AUDIT",
        "source_url": args.url,
        "source_snapshot_date": "2026-01",
        "source_correction_version": "v2-2026-07-07",
        "started_at": started_at,
        "fake_data": False,
        "final_ready": False,
    }
    try:
        report["archive_cache_action"] = ensure_archive(args.url, zip_path, args.timeout)
        report["archive_size_bytes"] = zip_path.stat().st_size
        report["archive_sha256"] = sha256_file(zip_path)
        report["archive_source_provenance_verified"] = archive_provenance_matches(zip_path, args.url)
        report.update(audit_zip(zip_path, args.count_rows))
        report["checks"]["archive_source_provenance_matches"] = report[
            "archive_source_provenance_verified"
        ]
        report["status"] = "PASS" if all(report["checks"].values()) else "BLOCKED"
        report["blockers"] = [key for key, passed in report["checks"].items() if not passed]
    except Exception as exc:
        report.update(
            status="BLOCKED",
            blockers=["OFCom_SOURCE_DOWNLOAD_OR_SCHEMA_AUDIT_FAILED"],
            error=str(exc),
        )
    report["finished_at"] = utc_now()
    atomic_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
