#!/usr/bin/env python3
"""Run the bounded internet_access_3 Ofcom r2 review pipeline safely.

This orchestrator is intentionally review-only. It can use an explicitly supplied
official ZIP, a previously validated cache, or multiple network clients. DNS
failure is diagnostic rather than an unconditional stop because configured HTTP
proxies may still work. It never writes business data, scores, a database, or a
deployment target.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Callable

SLOT_ID = "internet_access_3"
OFFICIAL_ZIP_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
)
EXPECTED_CANONICAL_ROWS = 30_761
EXPECTED_R2_FILE_COUNT = 121
EXPECTED_OFCOM_POSTCODE_ROWS = 1_741_096
MIN_OFFICIAL_ZIP_BYTES = 30_000_000
R2_PATTERN = "202601_fixed_postcode_coverage_r2_*.csv"
R1_PATTERN = "202601_fixed_postcode_coverage_r1_*.csv"


class GateError(RuntimeError):
    """A verified safety or source gate failed."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def initial_diagnostics(repo_root: Path, work_root: Path, url: str) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "started_at": utc_now(),
        "official_zip_url": url,
        "repo_root": str(repo_root),
        "work_root": str(work_root),
        "dns_state": "NOT_CHECKED",
        "download_state": "NOT_STARTED",
        "download_attempts": [],
        "zip_source_mode": None,
        "zip_path": None,
        "zip_bytes": 0,
        "zip_sha256": None,
        "r2_file_count": 0,
        "r1_file_count": 0,
        "canonical_slice_rows": None,
        "candidate_manifest": None,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def save_diagnostics(path: Path, diagnostics: dict[str, Any], state: str, message: str) -> None:
    diagnostics["state"] = state
    diagnostics["message"] = message
    diagnostics["updated_at"] = utc_now()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _matching_members(names: list[str], pattern: str) -> list[str]:
    return [name for name in names if fnmatch.fnmatch(PurePosixPath(name).name, pattern)]


def validate_zip_file(
    path: Path,
    *,
    min_bytes: int = MIN_OFFICIAL_ZIP_BYTES,
    expected_r2_count: int = EXPECTED_R2_FILE_COUNT,
) -> dict[str, Any]:
    if not path.is_file():
        raise GateError(f"ZIP does not exist: {path}")
    size = path.stat().st_size
    if size < min_bytes:
        raise GateError(f"ZIP is unexpectedly small: {size} bytes; minimum={min_bytes}")
    with path.open("rb") as handle:
        if handle.read(2) != b"PK":
            raise GateError("File does not have a ZIP signature")

    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise GateError(f"ZIP CRC test failed: {bad_member}")
            names = [item.filename for item in archive.infolist() if not item.is_dir()]
    except zipfile.BadZipFile as exc:
        raise GateError(f"Invalid ZIP: {exc}") from exc

    r1 = _matching_members(names, R1_PATTERN)
    r2 = _matching_members(names, R2_PATTERN)
    r2_basenames = [PurePosixPath(name).name for name in r2]
    if r1:
        raise GateError(f"Superseded all-premises r1 postcode files found: {len(r1)}")
    if len(r2) != expected_r2_count:
        raise GateError(f"Expected {expected_r2_count} corrected r2 postcode files, found {len(r2)}")
    if len(set(r2_basenames)) != len(r2_basenames):
        raise GateError("Duplicate corrected r2 postcode basenames found")

    return {
        "path": str(path),
        "bytes": size,
        "sha256": sha256_file(path),
        "r1_file_count": len(r1),
        "r2_file_count": len(r2),
        "r2_members": sorted(r2),
    }


def choose_existing_zip(
    explicit_zip: Path | None,
    cache_zip: Path,
    *,
    min_bytes: int = MIN_OFFICIAL_ZIP_BYTES,
    expected_r2_count: int = EXPECTED_R2_FILE_COUNT,
) -> tuple[str, Path, dict[str, Any]] | None:
    candidates: list[tuple[str, Path]] = []
    if explicit_zip is not None:
        candidates.append(("EXPLICIT_OFFICIAL_ZIP", explicit_zip))
    candidates.append(("VALIDATED_CACHE", cache_zip))

    errors: list[str] = []
    for mode, path in candidates:
        if not path.is_file():
            continue
        try:
            metadata = validate_zip_file(
                path, min_bytes=min_bytes, expected_r2_count=expected_r2_count
            )
            return mode, path, metadata
        except GateError as exc:
            errors.append(f"{mode}: {exc}")
            if mode == "EXPLICIT_OFFICIAL_ZIP":
                raise
    if errors:
        return None
    return None


def diagnose_dns(host: str) -> dict[str, Any]:
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443)})
        return {"state": "PASS", "addresses": addresses}
    except OSError as exc:
        return {"state": "FAIL_NON_FATAL", "error": str(exc)}


def download_with_urllib(url: str, target: Path, timeout: int) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-internet_access_3-verifier/4", "Accept": "application/zip,*/*"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler())
    with opener.open(request, timeout=timeout) as response, target.open("wb") as output:
        shutil.copyfileobj(response, output, length=1024 * 1024)


def download_with_curl(url: str, target: Path, timeout: int) -> None:
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if not executable:
        raise FileNotFoundError("curl/curl.exe is not available")
    subprocess.run(
        [
            executable,
            "--fail",
            "--location",
            "--retry",
            "3",
            "--retry-all-errors",
            "--connect-timeout",
            "30",
            "--max-time",
            str(timeout),
            "--user-agent",
            "AAYS-internet_access_3-verifier/4",
            "--output",
            str(target),
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def download_with_powershell(url: str, target: Path, timeout: int) -> None:
    executable = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
    if not executable:
        raise FileNotFoundError("PowerShell is not available")
    escaped_url = url.replace("'", "''")
    escaped_target = str(target).replace("'", "''")
    command = (
        "$ProgressPreference='SilentlyContinue';"
        "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;"
        f"Invoke-WebRequest -UseBasicParsing -TimeoutSec {timeout} "
        f"-MaximumRedirection 8 -Headers @{{'User-Agent'='AAYS-internet_access_3-verifier/4'}} "
        f"-Uri '{escaped_url}' -OutFile '{escaped_target}'"
    )
    subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", command], check=True)


def download_and_validate(
    url: str,
    cache_zip: Path,
    diagnostics: dict[str, Any],
    *,
    retries: int,
    timeout: int,
    min_bytes: int = MIN_OFFICIAL_ZIP_BYTES,
    expected_r2_count: int = EXPECTED_R2_FILE_COUNT,
    clients: list[tuple[str, Callable[[str, Path, int], None]]] | None = None,
) -> dict[str, Any]:
    cache_zip.parent.mkdir(parents=True, exist_ok=True)
    partial = cache_zip.with_suffix(cache_zip.suffix + ".part")
    clients = clients or [
        ("PYTHON_URLLIB_PROXY_AWARE", download_with_urllib),
        ("CURL", download_with_curl),
        ("POWERSHELL_IWR", download_with_powershell),
    ]

    for round_no in range(1, retries + 1):
        for client_name, client in clients:
            if partial.exists():
                partial.unlink()
            attempt = {
                "round": round_no,
                "client": client_name,
                "started_at": utc_now(),
                "state": "STARTED",
            }
            try:
                client(url, partial, timeout)
                metadata = validate_zip_file(
                    partial, min_bytes=min_bytes, expected_r2_count=expected_r2_count
                )
                os.replace(partial, cache_zip)
                metadata = validate_zip_file(
                    cache_zip, min_bytes=min_bytes, expected_r2_count=expected_r2_count
                )
                attempt.update({"state": "PASS", "bytes": metadata["bytes"]})
                diagnostics["download_attempts"].append(attempt)
                return metadata
            except Exception as exc:
                attempt.update({"state": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
                diagnostics["download_attempts"].append(attempt)
                if partial.exists():
                    partial.unlink()
        if round_no < retries:
            time.sleep(min(30, 2**round_no))
    raise GateError(f"Official ZIP download failed after {retries} rounds and {len(clients)} clients")


def extract_r2_files(zip_path: Path, target_dir: Path, *, expected_r2_count: int = EXPECTED_R2_FILE_COUNT) -> list[Path]:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        members = [
            item for item in archive.infolist()
            if not item.is_dir() and fnmatch.fnmatch(PurePosixPath(item.filename).name, R2_PATTERN)
        ]
        if len(members) != expected_r2_count:
            raise GateError(f"Expected {expected_r2_count} r2 members at extraction, found {len(members)}")
        seen: set[str] = set()
        for member in members:
            basename = PurePosixPath(member.filename).name
            if basename in seen:
                raise GateError(f"Duplicate r2 basename during extraction: {basename}")
            seen.add(basename)
            destination = target_dir / basename
            with archive.open(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            output_paths.append(destination)
    return sorted(output_paths)


def run_checked(command: list[str], diagnostics: dict[str, Any], stage: str) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    diagnostics.setdefault("stages", []).append(
        {
            "stage": stage,
            "command": command,
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        }
    )
    if completed.returncode != 0:
        raise GateError(f"{stage} failed with exit code {completed.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--ofcom-zip", type=Path, help="Explicit already-downloaded official ZIP")
    parser.add_argument("--ofcom-url", default=OFFICIAL_ZIP_URL)
    parser.add_argument("--download-retries", type=int, default=4)
    parser.add_argument("--download-timeout-seconds", type=int, default=600)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    work_root = (args.work_root or (repo_root / "outputs/internet_access_3_verified_run")).resolve()
    automation_root = repo_root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/automation"
    canonical_source = repo_root / "england_map_web/data/program_layer_matrix/security.geojson"
    legacy_source = repo_root / "england_map_web/data/program_layer_matrix/internet.geojson"
    stage_root = work_root / "stage"
    cache_zip = stage_root / "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
    extract_root = work_root / "ofcom_extract/postcode_files"
    slice_root = work_root / "slot_inputs"
    output_root = work_root / "candidate_outputs"
    diagnostics_path = work_root / "internet_access_3_network_and_execution_diagnostics_latest.json"
    diagnostics = initial_diagnostics(repo_root, work_root, args.ofcom_url)
    stage_root.mkdir(parents=True, exist_ok=True)
    slice_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        for required in (canonical_source, legacy_source, automation_root / "002_extract_slot3_ofcom_2026_candidates.py", automation_root / "005_stream_extract_slot3_inputs.py"):
            if not required.exists():
                raise GateError(f"Required source or automation missing: {required}")

        host = urllib.request.urlparse(args.ofcom_url).hostname or "www.ofcom.org.uk"
        dns = diagnose_dns(host)
        diagnostics["dns_state"] = dns["state"]
        diagnostics["dns_detail"] = dns

        selected = choose_existing_zip(args.ofcom_zip, cache_zip)
        if selected:
            mode, zip_path, zip_metadata = selected
            diagnostics["zip_source_mode"] = mode
            diagnostics["download_state"] = "NOT_REQUIRED_VALIDATED_EXISTING_ZIP"
        else:
            zip_metadata = download_and_validate(
                args.ofcom_url,
                cache_zip,
                diagnostics,
                retries=args.download_retries,
                timeout=args.download_timeout_seconds,
            )
            zip_path = cache_zip
            diagnostics["zip_source_mode"] = "VALIDATED_NETWORK_DOWNLOAD"
            diagnostics["download_state"] = "PASS"

        diagnostics.update(
            {
                "zip_path": str(zip_path),
                "zip_bytes": zip_metadata["bytes"],
                "zip_sha256": zip_metadata["sha256"],
                "r1_file_count": zip_metadata["r1_file_count"],
                "r2_file_count": zip_metadata["r2_file_count"],
            }
        )
        extracted = extract_r2_files(zip_path, extract_root)
        diagnostics["extracted_r2_files"] = len(extracted)

        run_checked([sys.executable, str(automation_root / "003_selftest_slot3_extractor.py")], diagnostics, "IDENTITY_EXTRACTOR_SELFTEST")
        run_checked([sys.executable, str(automation_root / "006_selftest_stream_extract_slot3_inputs.py")], diagnostics, "STREAMING_SLICER_SELFTEST")
        run_checked(
            [
                sys.executable,
                str(automation_root / "005_stream_extract_slot3_inputs.py"),
                "--canonical",
                str(canonical_source),
                "--legacy-internet",
                str(legacy_source),
                "--output-dir",
                str(slice_root),
            ],
            diagnostics,
            "EXACT_SLOT3_STREAM_SLICE",
        )
        slice_manifest_path = slice_root / "internet_access_3_stream_slice_manifest_latest.json"
        slice_manifest = json.loads(slice_manifest_path.read_text(encoding="utf-8"))
        canonical_rows = int(slice_manifest["canonical"]["rows"])
        if canonical_rows != EXPECTED_CANONICAL_ROWS:
            raise GateError(f"Canonical slice row count mismatch: {canonical_rows}")
        diagnostics["canonical_slice_rows"] = canonical_rows
        diagnostics["canonical_slice_sha256"] = slice_manifest["canonical"]["output_sha256"]
        diagnostics["legacy_slice_rows"] = int(slice_manifest["legacy_internet"]["rows"])
        diagnostics["legacy_slice_sha256"] = slice_manifest["legacy_internet"]["output_sha256"]
        diagnostics["canonical_first_rows"] = slice_manifest["canonical"]["first_rows"]

        run_checked(
            [
                sys.executable,
                str(automation_root / "002_extract_slot3_ofcom_2026_candidates.py"),
                "--canonical",
                str(slice_root / "internet_access_3_canonical_slice_latest.geojson"),
                "--legacy-internet-geojson",
                str(slice_root / "internet_access_3_legacy_slice_latest.geojson"),
                "--ofcom-postcode-dir",
                str(extract_root),
                "--output-dir",
                str(output_root),
            ],
            diagnostics,
            "REVIEW_ONLY_R2_JOIN",
        )
        candidate_manifest_path = output_root / "internet_access_3_candidate_manifest_latest.json"
        candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
        if int(candidate_manifest["canonical_rows"]) != EXPECTED_CANONICAL_ROWS:
            raise GateError("Candidate manifest canonical row count mismatch")
        matched = int(candidate_manifest["current_r2_postcode_proxy_rows"])
        no_data = int(candidate_manifest["no_data_rows"])
        if matched + no_data != EXPECTED_CANONICAL_ROWS:
            raise GateError(f"Candidate partition mismatch: matched={matched}, no_data={no_data}")
        if int(candidate_manifest.get("actual_business_data_rows_written", -1)) != 0:
            raise GateError("Review-only extractor reported business writes")

        diagnostics["candidate_manifest"] = str(candidate_manifest_path)
        diagnostics["current_r2_postcode_proxy_rows"] = matched
        diagnostics["identity_conflict_rows"] = int(candidate_manifest["identity_conflict_rows"])
        diagnostics["no_data_rows"] = no_data
        diagnostics["samples"] = candidate_manifest.get("samples", [])
        save_diagnostics(
            diagnostics_path,
            diagnostics,
            "COMPLETE_REVIEW_OUTPUT_READY",
            "Official ZIP, hashes, exact bounded slice and review-only counts completed. No migration or business write occurred.",
        )
        print(json.dumps({k: v for k, v in diagnostics.items() if k not in {"download_attempts", "stages", "samples"}}, sort_keys=True))
        return 0
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        save_diagnostics(
            diagnostics_path,
            diagnostics,
            "BLOCKED_EXECUTION",
            "Execution stopped at a verified gate. No migration or business write occurred.",
        )
        print(diagnostics["error"], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
