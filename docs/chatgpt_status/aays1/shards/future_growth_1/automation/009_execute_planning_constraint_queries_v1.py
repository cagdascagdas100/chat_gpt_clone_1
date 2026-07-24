#!/usr/bin/env python3
"""Execute and evidence Planning Data coordinate queries for future_growth_1.

Fail-closed network runner helper. It never promotes a parcel, creates a score,
or treats an empty response as proof that no planning constraint exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

ALLOWED_DATASETS = {
    "brownfield-land",
    "conservation-area",
    "listed-building",
    "green-belt",
    "flood-risk-zone",
    "article-4-direction-area",
    "tree-preservation-zone",
}
REQUIRED_FIELDS = {
    "entity", "dataset", "reference", "name", "start-date", "end-date",
    "geometry", "point", "quality",
}
EXPECTED_HOST = "www.planning.data.gov.uk"


class ContractError(RuntimeError):
    pass


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _normalise_float(value: Any) -> str:
    try:
        return format(float(value), ".10g")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"invalid coordinate: {value!r}") from exc


def validate_request_contract(row: dict[str, Any]) -> dict[str, Any]:
    row_no = row.get("row_no")
    if not isinstance(row_no, int) or row_no < 1:
        raise ContractError("row_no must be a positive integer")
    if row.get("parcel_id") != f"parcel_{row_no}":
        raise ContractError(f"row {row_no}: parcel_id mismatch")
    if not row.get("hmlr_inspire_id"):
        raise ContractError(f"row {row_no}: missing HMLR INSPIRE id")

    url = row.get("request_url")
    if not isinstance(url, str) or not url:
        raise ContractError(f"row {row_no}: request_url missing")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != EXPECTED_HOST or parsed.path != "/entity.json":
        raise ContractError(f"row {row_no}: unexpected endpoint")
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

    datasets = set(query.get("dataset", []))
    if datasets != ALLOWED_DATASETS:
        raise ContractError(f"row {row_no}: dataset contract mismatch")
    fields = set(query.get("field", []))
    if fields != REQUIRED_FIELDS:
        raise ContractError(f"row {row_no}: field contract mismatch")
    if query.get("period") != ["current"]:
        raise ContractError(f"row {row_no}: period must be current")
    try:
        limit = int(query.get("limit", [""])[0])
    except ValueError as exc:
        raise ContractError(f"row {row_no}: invalid limit") from exc
    if limit < 1 or limit > 100:
        raise ContractError(f"row {row_no}: limit outside 1..100")

    expected_lon = _normalise_float(row.get("longitude"))
    expected_lat = _normalise_float(row.get("latitude"))
    got_lon = _normalise_float(query.get("longitude", [None])[0])
    got_lat = _normalise_float(query.get("latitude", [None])[0])
    if got_lon != expected_lon or got_lat != expected_lat:
        raise ContractError(f"row {row_no}: coordinate contract mismatch")

    return {
        "row_no": row_no,
        "request_url": url,
        "datasets": sorted(datasets),
        "fields": sorted(fields),
        "limit": limit,
        "longitude": float(row["longitude"]),
        "latitude": float(row["latitude"]),
    }


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = manifest.get("rows")
    if not isinstance(rows, list) or len(rows) != 19:
        raise ContractError("manifest must contain exactly 19 rows")
    checked = [validate_request_contract(row) for row in rows]
    row_nos = [row["row_no"] for row in checked]
    if row_nos != list(range(1, 20)):
        raise ContractError("manifest rows must be ordered 1..19")
    hmlr_ids = [str(row.get("hmlr_inspire_id")) for row in rows]
    if len(set(hmlr_ids)) != 19:
        raise ContractError("HMLR INSPIRE ids must be unique")
    return checked


def _default_fetch(url: str, timeout: float, user_agent: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": user_agent},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), dict(exc.headers.items()) if exc.headers else {}, exc.read()


def validate_response_bytes(row_no: int, status: int, headers: dict[str, str], body: bytes) -> dict[str, Any]:
    if status != 200:
        raise ContractError(f"row {row_no}: HTTP {status}")
    content_type = next((v for k, v in headers.items() if k.lower() == "content-type"), "")
    if "json" not in content_type.lower():
        raise ContractError(f"row {row_no}: non-JSON content type")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"row {row_no}: invalid JSON response") from exc
    entities = payload.get("entities") if isinstance(payload, dict) else None
    if not isinstance(entities, list):
        raise ContractError(f"row {row_no}: entities must be a list")
    if len(entities) > 100:
        raise ContractError(f"row {row_no}: entity count exceeds request limit")
    entity_ids: set[int] = set()
    for entity in entities:
        if not isinstance(entity, dict):
            raise ContractError(f"row {row_no}: entity must be an object")
        entity_id = entity.get("entity")
        dataset = entity.get("dataset")
        if not isinstance(entity_id, int) or entity_id in entity_ids:
            raise ContractError(f"row {row_no}: duplicate or invalid entity id")
        entity_ids.add(entity_id)
        if dataset not in ALLOWED_DATASETS:
            raise ContractError(f"row {row_no}: unexpected dataset {dataset!r}")
        if entity.get("end-date") not in (None, ""):
            raise ContractError(f"row {row_no}: historical entity in current response")
    return {
        "entity_count": len(entities),
        "response_sha256": hashlib.sha256(body).hexdigest(),
        "zero_result_semantics": "NO_DATA_COVERAGE_NOT_PROOF" if not entities else None,
    }


def execute(
    manifest_path: Path,
    output_dir: Path,
    *,
    delay_seconds: float = 1.0,
    timeout_seconds: float = 45.0,
    retries: int = 3,
    user_agent: str = "TerraYield-AAYS/future-growth-1 evidence runner",
    dry_run: bool = False,
    fetcher: Callable[[str, float, str], tuple[int, dict[str, str], bytes]] = _default_fetch,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    checked = validate_manifest(manifest)
    plan = {
        "schema_version": 1,
        "slot_id": "future_growth_1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "request_count": len(checked),
        "dataset_screens": len(checked) * len(ALLOWED_DATASETS),
        "dry_run": dry_run,
        "network_requests_executed": 0,
        "rows_completed": 0,
        "entities_read": 0,
        "rows": [],
        "promotion_eligible_rows": 0,
        "scores_emitted": 0,
        "final_ready": False,
    }
    if dry_run:
        plan["rows"] = [
            {"row_no": row["row_no"], "state": "VALIDATED_PENDING_NETWORK", "request_url": row["request_url"]}
            for row in checked
        ]
        return plan

    output_dir.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(checked):
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                status, headers, body = fetcher(row["request_url"], timeout_seconds, user_agent)
                result = validate_response_bytes(row["row_no"], status, headers, body)
                break
            except Exception as exc:
                last_error = exc
                if attempt == retries:
                    raise ContractError(f"row {row['row_no']}: exhausted retries: {exc}") from exc
                sleeper(min(2 ** (attempt - 1), 8))
        else:
            raise ContractError(str(last_error))

        response_path = output_dir / f"row_{row['row_no']:05d}.json"
        _atomic_write(response_path, body)
        evidence = {
            "row_no": row["row_no"],
            "request_url": row["request_url"],
            "response_path": str(response_path),
            "response_sha256": result["response_sha256"],
            "entity_count": result["entity_count"],
            "zero_result_semantics": result["zero_result_semantics"],
            "promotion_eligible": False,
            "score": None,
        }
        plan["rows"].append(evidence)
        plan["network_requests_executed"] += 1
        plan["rows_completed"] += 1
        plan["entities_read"] += result["entity_count"]
        if index + 1 < len(checked) and delay_seconds > 0:
            sleeper(delay_seconds)

    evidence_bytes = (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _atomic_write(output_dir / "execution_evidence_manifest.json", evidence_bytes)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = execute(
            args.manifest,
            args.output_dir,
            delay_seconds=args.delay_seconds,
            timeout_seconds=args.timeout_seconds,
            retries=args.retries,
            dry_run=args.dry_run,
        )
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({
        "result": "PASS",
        "dry_run": result["dry_run"],
        "requests": result["request_count"],
        "executed": result["network_requests_executed"],
        "entities": result["entities_read"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
