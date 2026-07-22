#!/usr/bin/env python3
"""Download three exact HMLR authority archives and revalidate seeded IDs.

The HMLR catalogue can establish an anonymous session through an initial redirect.
This bounded recovery performs a non-following bootstrap request, a session catalogue
read, and exact authority ZIP downloads carried in the reconciled seed manifest.
It never uses fuzzy authority, nearest polygon, centroid, or alternate parcel fill.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from pyproj import Transformer

SLOT_ID = "height_difference_2"
CATALOGUE_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
TARGET_ROWS = (30762, 46142, 61522)
MAX_DOWNLOAD_BYTES = 1_500_000_000
MAX_EXTRACTED_BYTES = 2_000_000_000
ALLOWED_FINAL_HOSTS = {
    "use-land-property-data.service.gov.uk",
    "datapub-prd-s3-bucket.s3.amazonaws.com",
}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _slug(value: str) -> str:
    return "-".join(part for part in value.casefold().replace("_", " ").split() if part) or "authority"


def _load_seeds(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    seeds = payload.get("candidate_seeds") if isinstance(payload, dict) else None
    if payload.get("status") != "THREE_EXACT_RECONCILED_CANDIDATE_SEEDS_READY_FOR_FRESH_HMLR_REVALIDATION":
        raise ValueError("reconciled candidate status is not ready")
    if not isinstance(seeds, list) or len(seeds) != 3:
        raise ValueError("exactly three reconciled candidate seeds required")
    rows = {int(row["row_no"]) for row in seeds if isinstance(row, dict)}
    if rows != set(TARGET_ROWS):
        raise ValueError(f"exact target row set mismatch: {sorted(rows)}")
    ids = [str(row.get("hmlr_inspire_id") or "").strip() for row in seeds]
    if any(not value for value in ids) or len(set(ids)) != 3:
        raise ValueError("three distinct HMLR seed IDs required")
    return [dict(row) for row in seeds]


def _starter_manifest(seeds: list[dict[str, Any]], seed_path: Path) -> dict[str, Any]:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
    candidates: list[dict[str, Any]] = []
    for seed in seeds:
        lon = float(seed["hmlr_lon"])
        lat = float(seed["hmlr_lat"])
        easting, northing = transformer.transform(lon, lat)
        if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
            raise ValueError(f"BNG point outside Great Britain for row {seed['row_no']}")
        candidates.append({
            "row_no": int(seed["row_no"]),
            "parcel_id": str(seed["parcel_id"]),
            "hmlr_row_id": seed.get("hmlr_row_id"),
            "hmlr_inspire_id": str(seed["hmlr_inspire_id"]),
            "local_authority_name": str(seed["london_authority"]),
            "longitude": lon,
            "latitude": lat,
            "bng_easting": round(easting, 3),
            "bng_northing": round(northing, 3),
            "hmlr_area_m2": float(seed["hmlr_area_m2"]),
            "identity_location_accuracy": "4/4",
            "candidate_seed_only": True,
            "parcel_polygon_present": False,
            "measurement_eligible": False,
            "legacy_point_topography_values_promoted": False,
            "fresh_official_gml_revalidation_required": True,
        })
    candidates.sort(key=lambda row: row["row_no"])
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "status": "READY_FOR_FRESH_HMLR_EXACT_ID_AND_POINT_INSIDE_REVALIDATION",
        "source_path": str(seed_path),
        "source_sha256": _sha256(seed_path),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "processing_crs": "EPSG:27700",
        "nearest_or_fuzzy_match_allowed": False,
        "final_ready": False,
        "fake_data": False,
    }


def _safe_extract(archive_path: Path, output_dir: Path) -> list[Path]:
    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"not a ZIP archive: {archive_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    extracted: list[Path] = []
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in {".gml", ".xml"}:
                continue
            source_name = Path(info.filename)
            if source_name.is_absolute() or ".." in source_name.parts:
                raise ValueError("unsafe HMLR archive member path")
            total += int(info.file_size)
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("HMLR extracted byte limit exceeded")
            destination = output_dir / source_name.name
            with archive.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=1024 * 1024)
            extracted.append(destination)
    if not extracted:
        raise ValueError("HMLR ZIP contains no GML/XML")
    return extracted


def _download(session: requests.Session, url: str, target: Path, timeout_seconds: int) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "use-land-property-data.service.gov.uk":
        raise ValueError(f"unapproved HMLR seed URL: {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with session.get(url, timeout=(30, timeout_seconds), stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        final_url = response.url
        final_host = (urlparse(final_url).hostname or "").casefold()
        if final_host not in ALLOWED_FINAL_HOSTS:
            raise ValueError(f"unapproved HMLR final host: {final_host}")
        with target.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("HMLR download byte limit exceeded")
                handle.write(chunk)
        content_type = response.headers.get("content-type", "")
    if total == 0:
        raise ValueError("empty HMLR download")
    return {
        "requested_url": url,
        "resolved_url": final_url,
        "resolved_host": final_host,
        "content_type": content_type,
        "size_bytes": total,
        "sha256": _sha256(target),
    }


def _run_matcher(matcher: Path, starter: Path, vector_root: Path, output: Path, timeout_seconds: int) -> dict[str, Any]:
    command = [
        sys.executable,
        str(matcher),
        "--starter-manifest",
        str(starter),
        "--vector-root",
        str(vector_root),
        "--max-files",
        "20",
        "--output",
        str(output),
    ]
    try:
        process = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            cwd=matcher.parent,
        )
        return {
            "command": command,
            "exit_code": process.returncode,
            "timed_out": False,
            "stdout": process.stdout[-12000:],
            "stderr": process.stderr[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": 124,
            "timed_out": True,
            "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
        }


def prepare(seed_manifest: Path, output_dir: Path, timeout_seconds: int, matcher_timeout_seconds: int) -> dict[str, Any]:
    seeds = _load_seeds(seed_manifest)
    output_dir.mkdir(parents=True, exist_ok=True)
    starter_path = output_dir / "starter_manifest.json"
    starter_payload = _starter_manifest(seeds, seed_manifest)
    _write(starter_path, starter_payload)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "TerraYield-AAYS-height_difference_2-F-host-reconciliation/6.0",
        "Accept": "text/html,application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
    })
    bootstrap = session.get(CATALOGUE_URL, timeout=(30, 90), allow_redirects=False)
    bootstrap_status = bootstrap.status_code
    bootstrap_location = bootstrap.headers.get("location")
    catalogue = session.get(CATALOGUE_URL + "?source=direct", timeout=(30, 90), allow_redirects=True)
    catalogue.raise_for_status()
    catalogue_sha256 = hashlib.sha256(catalogue.content).hexdigest()

    records: list[dict[str, Any]] = []
    vector_root = output_dir / "sources" / "hmlr"
    for seed in seeds:
        row_no = int(seed["row_no"])
        url = str(seed.get("hmlr_download_url") or "").strip()
        zip_name = str(seed.get("hmlr_zip_name") or "").strip()
        if not url or not zip_name or not url.endswith("/" + zip_name):
            raise ValueError(f"exact HMLR download URL/filename mismatch at row {row_no}")
        authority_dir = vector_root / _slug(str(seed["london_authority"]))
        zip_path = authority_dir / zip_name
        metadata = _download(session, url, zip_path, timeout_seconds)
        vectors = _safe_extract(zip_path, authority_dir / "extracted")
        records.append({
            "row_no": row_no,
            "authority": seed["london_authority"],
            "hmlr_inspire_id_seed": seed["hmlr_inspire_id"],
            "zip_name": zip_name,
            **metadata,
            "vectors": [
                {"path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)}
                for path in vectors
            ],
        })

    matcher = Path(__file__).resolve().parent / "010_match_hmlr_exact_polygons.py"
    if not matcher.is_file():
        raise FileNotFoundError(matcher)
    match_output = output_dir / "hmlr_exact_matches.json"
    matcher_result = _run_matcher(matcher, starter_path, vector_root, match_output, matcher_timeout_seconds)
    match_payload: dict[str, Any] | None = None
    if match_output.is_file():
        match_payload = json.loads(match_output.read_text(encoding="utf-8-sig"))
    matched_count = int((match_payload or {}).get("matched_candidate_count", 0))
    ready = matcher_result["exit_code"] == 0 and matched_count == 3
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "status": "THREE_HMLR_EXACT_POLYGONS_REVALIDATED" if ready else "BLOCKED_FRESH_HMLR_REVALIDATION",
        "catalogue_url": CATALOGUE_URL,
        "bootstrap_status": bootstrap_status,
        "bootstrap_location": bootstrap_location,
        "catalogue_resolved_url": catalogue.url,
        "catalogue_sha256": catalogue_sha256,
        "session_cookie_names": sorted(session.cookies.get_dict().keys()),
        "candidate_count": len(seeds),
        "prepared_authority_count": len(records),
        "records": records,
        "starter_manifest": str(starter_path),
        "hmlr_exact_matches": str(match_output),
        "matcher": matcher_result,
        "matched_candidate_count": matched_count,
        "matching_method": "FRESH_OFFICIAL_GML_EXACT_INSPIRE_ID_AND_POINT_INSIDE",
        "nearest_or_fuzzy_authority_match_used": False,
        "nearest_polygon_fill_used": False,
        "centroid_fallback_used": False,
        "measurement_values_written": 0,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--matcher-timeout", type=int, default=1800)
    args = parser.parse_args(argv)
    try:
        payload = prepare(args.seed_manifest, args.output_dir, args.timeout, args.matcher_timeout)
        code = 0 if payload["status"] == "THREE_HMLR_EXACT_POLYGONS_REVALIDATED" else 2
    except Exception as exc:
        payload = {
            "schema_version": 2,
            "slot_id": SLOT_ID,
            "status": "BLOCKED_FRESH_HMLR_REVALIDATION",
            "error": f"{type(exc).__name__}: {exc}",
            "matched_candidate_count": 0,
            "measurement_values_written": 0,
            "actual_business_rows_written": 0,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        code = 2
    _write(args.output_dir / "hmlr_polygon_preparation_execution.json", payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "matched": payload.get("matched_candidate_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
