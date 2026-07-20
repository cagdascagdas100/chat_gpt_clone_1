#!/usr/bin/env python3
"""Discover the canonical height_difference_3 shard export and prepare three queries.

Fail-closed behaviour:
- Does not infer row numbers from file order.
- Does not invent parcel IDs, coordinates, geometry, or elevation values.
- Writes a canonical shard export only when rows 61523..92283 are complete.
- Invokes the existing 004 query preparer only after strict validation passes.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

ROW_START = 61523
ROW_END = 92283
EXPECTED_COUNT = 30761
REQUIRED_KEYS = {
    "row_no",
    "parcel_id",
    "longitude",
    "latitude",
    "bng_easting",
    "bng_northing",
    "local_authority_name",
    "data_status",
}
OFFICIAL_ID_KEYS = {
    "parcel_registry_id",
    "hmlr_inspire_id",
    "national_cadastral_reference",
}
SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".geojson"}
DEFAULT_RELATIVE_CANDIDATES = (
    "outputs/england_program_parcel_matrix_20260629/canonical_rows.jsonl",
    "outputs/england_program_parcel_matrix_20260629/parcel_matrix.jsonl",
    "outputs/england_program_parcel_matrix_20260629/parcel_matrix.csv",
    "outputs/england_program_parcel_matrix_20260629/parcel_matrix.geojson",
    "outputs/england_program_parcel_matrix_20260629/chunks/manifest.json",
    "outputs/england_program_parcel_matrix_20260629/manifest.json",
    "england_map_web/data/program_layer_matrix/manifest.json",
    "england_map_web/data/program_layer_matrix/filter_indexes.json",
    "england_map_web/data/program_layer_matrix/parcel_matrix.jsonl",
    "england_map_web/data/aays_18_slots/height_difference_3/canonical_export/manifest.json",
)
DEFAULT_HTTP_CANDIDATES = (
    "http://127.0.0.1:8012/outputs/england_program_parcel_matrix_20260629/chunks/manifest.json",
    "http://127.0.0.1:8012/outputs/england_program_parcel_matrix_20260629/manifest.json",
    "http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/manifest.json",
    "http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/filter_indexes.json",
    "http://127.0.0.1:8012/england_map_web/data/aays_18_slots/height_difference_3/canonical_export/manifest.json",
)


@dataclass
class CandidateResult:
    source: str
    source_kind: str
    status: str
    size_bytes: int | None = None
    rows_seen: int = 0
    shard_rows_seen: int = 0
    complete_shard: bool = False
    required_keys_present: bool = False
    official_id_rows: int = 0
    error: str | None = None


def _iter_json_rows(payload: Any) -> Iterator[dict[str, Any]]:
    if isinstance(payload, list):
        for value in payload:
            if isinstance(value, dict):
                yield dict(value)
        return
    if not isinstance(payload, dict):
        return
    if isinstance(payload.get("rows"), list):
        for value in payload["rows"]:
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


def _load_rows(path: Path, max_file_bytes: int) -> list[dict[str, Any]]:
    size = path.stat().st_size
    if size > max_file_bytes:
        raise ValueError(f"file exceeds max size: {size} > {max_file_bytes}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix in {".json", ".geojson"}:
        return list(_iter_json_rows(json.loads(path.read_text(encoding="utf-8-sig"))))
    if suffix in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_no, line in enumerate(handle, start=1):
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


def _analyse_rows(
    source: str,
    source_kind: str,
    rows: list[dict[str, Any]],
    size: int | None,
) -> tuple[CandidateResult, list[dict[str, Any]]]:
    shard: list[dict[str, Any]] = []
    for row in rows:
        number = _row_no(row)
        if number is not None and ROW_START <= number <= ROW_END:
            copy = dict(row)
            copy["row_no"] = number
            shard.append(copy)
    numbers = [row["row_no"] for row in shard]
    unique_numbers = set(numbers)
    complete = (
        len(shard) == EXPECTED_COUNT
        and len(unique_numbers) == EXPECTED_COUNT
        and min(unique_numbers, default=-1) == ROW_START
        and max(unique_numbers, default=-1) == ROW_END
    )
    required = bool(shard) and all(REQUIRED_KEYS.issubset(row.keys()) for row in shard)
    official_rows = sum(
        any(str(row.get(key, "")).strip() for key in OFFICIAL_ID_KEYS)
        for row in shard
    )
    status = "COMPLETE_CANONICAL_SHARD" if complete and required else "PARTIAL_OR_NONCANONICAL"
    return (
        CandidateResult(
            source=source,
            source_kind=source_kind,
            status=status,
            size_bytes=size,
            rows_seen=len(rows),
            shard_rows_seen=len(shard),
            complete_shard=complete,
            required_keys_present=required,
            official_id_rows=official_rows,
        ),
        sorted(shard, key=lambda row: row["row_no"]),
    )


def _manifest_paths(path: Path, max_file_bytes: int) -> list[Path]:
    if path.suffix.lower() != ".json" or path.stat().st_size > max_file_bytes:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    values: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)
        elif isinstance(value, str) and Path(value).suffix.lower() in SUPPORTED_SUFFIXES:
            values.append(value)

    walk(payload)
    result = []
    for value in values:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        result.append(candidate.resolve())
    return result


def _bounded_walk(root: Path, max_depth: int, max_files: int) -> Iterator[Path]:
    root = root.resolve()
    emitted = 0
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        if depth >= max_depth:
            dirs[:] = []
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in {".git", "node_modules", ".venv", "venv", "__pycache__"}
        ]
        for name in files:
            path = current_path / name
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            lowered = name.lower()
            if not any(
                token in lowered
                for token in ("parcel", "matrix", "manifest", "index", "canonical", "chunk")
            ):
                continue
            yield path
            emitted += 1
            if emitted >= max_files:
                return


def _http_probe(url: str, timeout: int, max_bytes: int) -> tuple[CandidateResult, bytes | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TerraYield-AAYS/height_difference_3"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                return CandidateResult(url, "local_http", "TOO_LARGE", size_bytes=len(body)), None
            return CandidateResult(url, "local_http", "HTTP_READABLE", size_bytes=len(body)), body
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CandidateResult(
            url,
            "local_http",
            "UNAVAILABLE",
            error=f"{type(exc).__name__}: {exc}",
        ), None


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _root_candidates(cli_roots: Iterable[Path]) -> list[Path]:
    roots = [Path(value) for value in cli_roots]
    for key in ("AAYS_REPO_ROOT", "AAYS_BRIDGE_ROOT"):
        value = os.environ.get(key)
        if value:
            roots.append(Path(value))
    cwd = Path.cwd().resolve()
    if cwd != Path(cwd.anchor):
        roots.append(cwd)
    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            continue
        marker = str(resolved).casefold()
        if marker not in seen and resolved.exists() and resolved.is_dir():
            seen.add(marker)
            unique.append(resolved)
    return unique


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query-preparer", type=Path)
    parser.add_argument("--probe-local-http", action="store_true")
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Pass --no-network to the 004 query preparer.",
    )
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--max-depth", type=int, default=7)
    parser.add_argument("--max-files", type=int, default=250)
    parser.add_argument("--max-file-mb", type=int, default=256)
    parser.add_argument("--skip-recursive-scan", action="store_true")
    args = parser.parse_args(argv)

    max_file_bytes = args.max_file_mb * 1024 * 1024
    roots = _root_candidates(args.root)
    discovered: list[Path] = []
    for root in roots:
        for relative in DEFAULT_RELATIVE_CANDIDATES:
            candidate = (root / relative).resolve()
            if candidate.exists() and candidate.is_file():
                discovered.append(candidate)
        if not args.skip_recursive_scan:
            discovered.extend(_bounded_walk(root, args.max_depth, args.max_files))

    queue = list(dict.fromkeys(path.resolve() for path in discovered))
    seen_paths: set[Path] = set()
    results: list[CandidateResult] = []
    valid_source: Path | None = None
    valid_rows: list[dict[str, Any]] = []

    while queue:
        path = queue.pop(0)
        if path in seen_paths:
            continue
        seen_paths.add(path)
        if not path.exists() or not path.is_file():
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            results.append(CandidateResult(str(path), "local_file", "TOO_LARGE", size_bytes=size))
            continue
        try:
            rows = _load_rows(path, max_file_bytes)
            result, shard = _analyse_rows(str(path), "local_file", rows, size)
            results.append(result)
            if result.complete_shard and result.required_keys_present and result.official_id_rows >= 3:
                valid_source = path
                valid_rows = shard
                break
        except Exception as exc:
            results.append(
                CandidateResult(
                    str(path),
                    "local_file",
                    "NOT_ROW_SOURCE",
                    size_bytes=size,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
        queue.extend(
            candidate
            for candidate in _manifest_paths(path, max_file_bytes)
            if candidate not in seen_paths
        )

    if args.probe_local_http:
        for url in DEFAULT_HTTP_CANDIDATES:
            result, body = _http_probe(url, args.timeout, max_file_bytes)
            results.append(result)
            if body and url.lower().endswith((".json", ".geojson")):
                try:
                    rows = list(_iter_json_rows(json.loads(body.decode("utf-8-sig"))))
                    analysed, shard = _analyse_rows(url, "local_http", rows, len(body))
                    results.append(analysed)
                    if (
                        analysed.complete_shard
                        and analysed.required_keys_present
                        and analysed.official_id_rows >= 3
                    ):
                        valid_rows = shard
                        break
                except Exception as exc:
                    results.append(
                        CandidateResult(
                            url,
                            "local_http",
                            "HTTP_JSON_NOT_ROW_SOURCE",
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    )

    output_dir = args.output_dir.resolve()
    export_path = output_dir / "canonical_shard_61523_92283.jsonl"
    report = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "count": EXPECTED_COUNT},
        "roots_scanned": [str(root) for root in roots],
        "local_candidate_files_checked": len(seen_paths),
        "local_http_probe_enabled": args.probe_local_http,
        "candidate_results": [asdict(result) for result in results],
        "canonical_source_found": bool(valid_rows),
        "canonical_source_path": str(valid_source) if valid_source else None,
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

    if not valid_rows:
        report["status"] = "BLOCKED_CANONICAL_8012_EXPORT_NOT_DISCOVERED"
        report["next_step"] = "EXPOSE_CANONICAL_MATRIX_FILE_OR_8012_MANIFEST_THEN_RERUN"
        _write_json(output_dir / "discovery_report.json", report)
        print(json.dumps({"ok": False, "status": report["status"], "checked": len(results)}))
        return 2

    _write_jsonl(export_path, valid_rows)
    report["status"] = "CANONICAL_SHARD_EXPORTED"
    _write_json(output_dir / "discovery_report.json", report)

    preparer = args.query_preparer
    if preparer is None:
        preparer = Path(__file__).with_name("004_prepare_three_real_sample_queries.py")
    if not preparer.exists():
        raise FileNotFoundError(f"query preparer not found: {preparer}")
    query_output = output_dir / "first_three_queries"
    command = [
        sys.executable,
        str(preparer),
        "--input",
        str(export_path),
        "--output-dir",
        str(query_output),
        "--sample-size",
        "3",
    ]
    if args.no_network:
        command.append("--no-network")
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    _write_json(
        output_dir / "query_preparer_execution.json",
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        },
    )
    print(
        json.dumps(
            {
                "ok": completed.returncode == 0,
                "exported": len(valid_rows),
                "query_preparer_returncode": completed.returncode,
            }
        )
    )
    return completed.returncode


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
