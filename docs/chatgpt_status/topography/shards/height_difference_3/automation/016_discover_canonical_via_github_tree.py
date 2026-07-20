#!/usr/bin/env python3
"""Discover a canonical height_difference_3 export through the GitHub REST tree.

This is a read-only, fail-closed fallback for the existing single shared runner.
It never infers row numbers from file order and never invents parcel identifiers,
coordinates, authorities, geometry, or measurements.
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

ROW_START = 61523
ROW_END = 92283
EXPECTED_COUNT = 30761
SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".geojson"}
PATH_TOKENS = ("parcel", "matrix", "manifest", "canonical", "registry", "chunk", "index")
BASE_REQUIRED = {"row_no", "parcel_id", "local_authority_name", "data_status"}
OFFICIAL_KEYS = {
    "parcel_registry_id",
    "hmlr_inspire_id",
    "national_cadastral_reference",
    "uprn",
}
COORDINATE_KEYS = ("bng_easting", "bng_northing")
WGS84_KEYS = ("longitude", "latitude")


@dataclass
class CandidateResult:
    path: str
    blob_sha: str | None
    status: str
    size_bytes: int | None = None
    rows_seen: int = 0
    shard_rows_seen: int = 0
    complete_shard: bool = False
    base_keys_present: bool = False
    source_backed_location_rows: int = 0
    official_identity_rows: int = 0
    error: str | None = None


def _request_json(url: str, token: str | None, timeout: int) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "TerraYield-AAYS/height_difference_3",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _iter_json_rows(payload: Any) -> Iterator[dict[str, Any]]:
    if isinstance(payload, list):
        for value in payload:
            if isinstance(value, dict):
                yield dict(value)
        return
    if not isinstance(payload, dict):
        return
    for key in ("rows", "records", "items", "parcels"):
        if isinstance(payload.get(key), list):
            for value in payload[key]:
                if isinstance(value, dict):
                    yield dict(value)
            return
    if isinstance(payload.get("features"), list):
        for feature in payload["features"]:
            if not isinstance(feature, dict):
                continue
            row = dict(feature.get("properties") or {})
            if feature.get("geometry") is not None:
                row["geometry_geojson_epsg4326"] = feature["geometry"]
            yield row


def _load_rows(data: bytes, suffix: str) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig")
    if suffix == ".csv":
        return [dict(row) for row in csv.DictReader(text.splitlines())]
    if suffix in {".json", ".geojson"}:
        return list(_iter_json_rows(json.loads(text)))
    if suffix in {".jsonl", ".ndjson"}:
        rows = []
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_no} is not an object")
            rows.append(dict(value))
        return rows
    raise ValueError(f"unsupported suffix: {suffix}")


def _row_no(row: dict[str, Any]) -> int | None:
    value = row.get("row_no")
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _truthy(row: dict[str, Any], key: str) -> bool:
    value = row.get(key)
    return value is not None and str(value).strip() != ""


def _location_backed(row: dict[str, Any]) -> bool:
    bng = all(_truthy(row, key) for key in COORDINATE_KEYS)
    wgs84 = all(_truthy(row, key) for key in WGS84_KEYS)
    uprn = _truthy(row, "uprn")
    geometry = any(
        _truthy(row, key)
        for key in ("geometry_wkt_epsg27700", "geometry_geojson_epsg27700", "geometry_geojson_epsg4326")
    )
    return bng or wgs84 or uprn or geometry


def _analyse(path: str, sha: str | None, rows: list[dict[str, Any]], size: int | None) -> tuple[CandidateResult, list[dict[str, Any]]]:
    shard = []
    for row in rows:
        number = _row_no(row)
        if number is not None and ROW_START <= number <= ROW_END:
            copy = dict(row)
            copy["row_no"] = number
            shard.append(copy)
    numbers = [row["row_no"] for row in shard]
    unique = set(numbers)
    complete = (
        len(shard) == EXPECTED_COUNT
        and len(unique) == EXPECTED_COUNT
        and min(unique, default=-1) == ROW_START
        and max(unique, default=-1) == ROW_END
    )
    base_ok = bool(shard) and all(BASE_REQUIRED.issubset(row.keys()) for row in shard)
    location_count = sum(_location_backed(row) for row in shard)
    identity_count = sum(any(_truthy(row, key) for key in OFFICIAL_KEYS) for row in shard)
    valid = complete and base_ok and location_count == EXPECTED_COUNT and identity_count >= 3
    return (
        CandidateResult(
            path=path,
            blob_sha=sha,
            status="COMPLETE_CANONICAL_SHARD" if valid else "PARTIAL_OR_NONCANONICAL",
            size_bytes=size,
            rows_seen=len(rows),
            shard_rows_seen=len(shard),
            complete_shard=complete,
            base_keys_present=base_ok,
            source_backed_location_rows=location_count,
            official_identity_rows=identity_count,
        ),
        sorted(shard, key=lambda row: row["row_no"]),
    )


def _manifest_refs(payload: Any) -> set[str]:
    refs: set[str] = set()
    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)
        elif isinstance(value, str):
            suffix = Path(urllib.parse.urlparse(value).path).suffix.lower()
            if suffix in SUPPORTED_SUFFIXES:
                refs.add(value.replace("\\", "/").lstrip("/"))
    walk(payload)
    return refs


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--ref", default="codex/aays-single-runner-v5-20260706")
    parser.add_argument("--api-base", default="https://api.github.com")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-candidate-files", type=int, default=120)
    parser.add_argument("--max-file-mb", type=int, default=256)
    args = parser.parse_args(argv)

    token = os.environ.get(args.token_env) or None
    repo = args.repository.strip("/")
    api = args.api_base.rstrip("/")
    encoded_ref = urllib.parse.quote(args.ref, safe="")
    commit_url = f"{api}/repos/{repo}/commits/{encoded_ref}"
    results: list[CandidateResult] = []
    tree_truncated = False
    files_considered = 0
    valid_rows: list[dict[str, Any]] = []
    valid_path = None
    valid_sha = None

    try:
        commit = _request_json(commit_url, token, args.timeout)
        tree_sha = commit["commit"]["tree"]["sha"]
        tree = _request_json(f"{api}/repos/{repo}/git/trees/{tree_sha}?recursive=1", token, args.timeout)
        tree_truncated = bool(tree.get("truncated"))
        blobs = {
            str(item["path"]).replace("\\", "/"): item
            for item in tree.get("tree", [])
            if item.get("type") == "blob"
        }
    except Exception as exc:
        report = {
            "schema_version": 1,
            "slot_id": "height_difference_3",
            "status": "BLOCKED_GITHUB_TREE_UNAVAILABLE",
            "error": f"{type(exc).__name__}: {exc}",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        _write_json(args.output_dir / "github_discovery_report.json", report)
        print(json.dumps({"ok": False, "status": report["status"]}))
        return 2

    prioritized = []
    for path, item in blobs.items():
        suffix = Path(path).suffix.lower()
        lower = path.casefold()
        if suffix not in SUPPORTED_SUFFIXES:
            continue
        if not any(token in lower for token in PATH_TOKENS):
            continue
        prioritized.append((path, item))
    prioritized.sort(key=lambda pair: (
        0 if "england_program_parcel_matrix_20260629" in pair[0].casefold() else 1,
        0 if "canonical" in pair[0].casefold() else 1,
        pair[0],
    ))

    queue = prioritized[: args.max_candidate_files]
    lookup = blobs
    seen: set[str] = set()
    max_bytes = args.max_file_mb * 1024 * 1024

    while queue and files_considered < args.max_candidate_files:
        path, item = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        files_considered += 1
        size = int(item.get("size") or 0)
        sha = item.get("sha")
        if size > max_bytes:
            results.append(CandidateResult(path, sha, "TOO_LARGE", size_bytes=size))
            continue
        try:
            blob = _request_json(f"{api}/repos/{repo}/git/blobs/{sha}", token, args.timeout)
            if blob.get("encoding") != "base64":
                raise ValueError("GitHub blob encoding is not base64")
            data = base64.b64decode(blob["content"], validate=False)
            suffix = Path(path).suffix.lower()
            rows = _load_rows(data, suffix)
            result, shard = _analyse(path, sha, rows, len(data))
            results.append(result)
            if result.status == "COMPLETE_CANONICAL_SHARD":
                valid_rows = shard
                valid_path = path
                valid_sha = sha
                break
            if suffix == ".json":
                try:
                    payload = json.loads(data.decode("utf-8-sig"))
                    parent = str(Path(path).parent).replace("\\", "/")
                    for ref in _manifest_refs(payload):
                        candidates = [ref, f"{parent}/{ref}" if parent not in {"", "."} else ref]
                        for candidate in candidates:
                            candidate = str(Path(candidate)).replace("\\", "/")
                            if candidate in lookup and candidate not in seen:
                                queue.append((candidate, lookup[candidate]))
                                break
                except Exception:
                    pass
        except Exception as exc:
            results.append(
                CandidateResult(
                    path=path,
                    blob_sha=sha,
                    status="NOT_ROW_SOURCE",
                    size_bytes=size,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    output_dir = args.output_dir.resolve()
    export_path = output_dir / "canonical_shard_61523_92283.jsonl"
    report = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "repository": repo,
        "ref": args.ref,
        "resolved_commit_sha": commit.get("sha"),
        "tree_sha": tree_sha,
        "tree_truncated": tree_truncated,
        "tree_blob_count": len(blobs),
        "candidate_files_prioritized": len(prioritized),
        "candidate_files_checked": files_considered,
        "candidate_results": [asdict(value) for value in results],
        "canonical_source_found": bool(valid_rows),
        "canonical_source_path": valid_path,
        "canonical_source_blob_sha": valid_sha,
        "canonical_rows_exported": len(valid_rows),
        "export_path": str(export_path) if valid_rows else None,
        "row_number_inference_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    if valid_rows:
        _write_jsonl(export_path, valid_rows)
        report["status"] = "GITHUB_CANONICAL_SHARD_EXPORTED"
        code = 0
    else:
        report["status"] = "BLOCKED_GITHUB_CANONICAL_EXPORT_NOT_DISCOVERED"
        report["next_step"] = "RUN_LOCAL_AND_8012_DISCOVERY_OR_EXPOSE_CANONICAL_EXPORT"
        code = 2
    _write_json(output_dir / "github_discovery_report.json", report)
    print(json.dumps({"ok": code == 0, "status": report["status"], "checked": files_considered}))
    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
