#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SLOT_ID = "future_growth_2"
CONTINUATION_KEY = "5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
EXPECTED_TARGETS = {30762: 17, 46142: 20, 61522: 33}
ALLOWED_HOSTS = {"services.arcgis.com"}
TERMS_URL = "https://www.esri.com/en-us/legal/terms/full-master-agreement"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def build_plan(manifest: dict) -> list[dict]:
    if manifest.get("slot_id") != SLOT_ID:
        raise ValueError("manifest slot_id mismatch")
    if manifest.get("continuation_key") != CONTINUATION_KEY:
        raise ValueError("manifest continuation_key mismatch")

    rows = manifest.get("rows")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("manifest must contain exactly three target rows")

    row_map = {int(row["row_no"]): row for row in rows}
    if set(row_map) != set(EXPECTED_TARGETS):
        raise ValueError("manifest target rows mismatch")

    plan: list[dict] = []
    for row_no in sorted(EXPECTED_TARGETS):
        row = row_map[row_no]
        layer_id = EXPECTED_TARGETS[row_no]
        layer_map = {int(layer[0]): str(layer[1]) for layer in row.get("layers", [])}
        if layer_id not in layer_map:
            raise ValueError(f"required layer {layer_id} absent for row {row_no}")
        service = str(row["service"]).rstrip("/")
        parsed = urlparse(service)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"unapproved service URL for row {row_no}")
        url = f"{service}/{layer_id}?f=pjson"
        plan.append(
            {
                "row_no": row_no,
                "parcel_id": str(row["parcel_id"]),
                "lpa": str(row["lpa"]),
                "layer_id": layer_id,
                "layer_name_expected": layer_map[layer_id],
                "source_url": url,
            }
        )
    return plan


def normalize_metadata(data: dict) -> dict:
    advanced = data.get("advancedQueryCapabilities") or {}
    return {
        "name": data.get("name"),
        "type": data.get("type"),
        "object_id_field": data.get("objectIdField"),
        "max_record_count": data.get("maxRecordCount"),
        "supports_pagination": advanced.get("supportsPagination"),
        "supports_order_by": advanced.get("supportsOrderBy"),
        "spatial_reference_wkid": (data.get("extent") or {}).get("spatialReference", {}).get("wkid"),
    }


def validate_metadata(meta: dict) -> None:
    if meta.get("type") not in {"Feature Layer", "Table"}:
        raise ValueError("unexpected ArcGIS layer type")
    if not isinstance(meta.get("object_id_field"), str) or not meta["object_id_field"]:
        raise ValueError("objectIdField missing")
    if not isinstance(meta.get("max_record_count"), int) or meta["max_record_count"] <= 0:
        raise ValueError("maxRecordCount invalid")
    if meta.get("supports_pagination") is not True:
        raise ValueError("supportsPagination is not true")
    if meta.get("supports_order_by") is not True:
        raise ValueError("supportsOrderBy is not true")


def fetch_one(item: dict, timeout_seconds: int) -> dict:
    request = Request(item["source_url"], headers={"User-Agent": "AAYS-future-growth-2/1.0"})
    fetched_at = utc_now()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
            status = int(getattr(response, "status", 200))
        parsed = json.loads(raw.decode("utf-8"))
        meta = normalize_metadata(parsed)
        validate_metadata(meta)
        return {
            **item,
            "fetched_at_utc": fetched_at,
            "http_status": status,
            "byte_count": len(raw),
            "raw_sha256": sha256_bytes(raw),
            "raw_body": raw.decode("utf-8"),
            "metadata": meta,
            "supports_fields": [
                "name",
                "type",
                "objectIdField",
                "maxRecordCount",
                "advancedQueryCapabilities.supportsPagination",
                "advancedQueryCapabilities.supportsOrderBy",
                "extent.spatialReference.wkid",
            ],
            "license_or_terms_url": TERMS_URL,
            "data_status": "VERIFIED_METADATA",
            "error": None,
        }
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            **item,
            "fetched_at_utc": fetched_at,
            "http_status": getattr(exc, "code", None),
            "byte_count": 0,
            "raw_sha256": sha256_bytes(b""),
            "raw_body": "",
            "metadata": None,
            "supports_fields": [],
            "license_or_terms_url": TERMS_URL,
            "data_status": "NO_DATA",
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.timeout_seconds < 1 or args.timeout_seconds > 120:
        raise ValueError("timeout must be between 1 and 120 seconds")

    manifest = load_json(args.manifest)
    plan = build_plan(manifest)

    if args.self_test:
        payload = {
            "schema_version": 3,
            "slot_id": SLOT_ID,
            "continuation_key": CONTINUATION_KEY,
            "state": "SELF_TEST_PASS",
            "generated_at": utc_now(),
            "completed_count": 3,
            "target_count": 3,
            "request_plan": plan,
            "network_executed": False,
            "fake_data": False,
        }
        atomic_write_json(args.output, payload)
        print(json.dumps({"self_test": "PASS", "planned_requests": len(plan)}, separators=(",", ":")))
        return 0

    results = [fetch_one(item, args.timeout_seconds) for item in plan]
    completed = sum(result["data_status"] == "VERIFIED_METADATA" for result in results)
    payload = {
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "continuation_key": CONTINUATION_KEY,
        "state": "PUBLISHED" if completed == 3 else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED" if completed == 3 else "BLOCKED",
        "generated_at": utc_now(),
        "completed_count": completed,
        "target_count": 3,
        "progress_percent": round(completed * 100.0 / 3.0, 6),
        "results": results,
        "large_raw_files_written": False,
        "fake_data": False,
    }
    atomic_write_json(args.output, payload)
    print(json.dumps({"completed_count": completed, "target_count": 3, "output": str(args.output)}, separators=(",", ":")))
    return 0 if completed == 3 else 2


if __name__ == "__main__":
    raise SystemExit(main())
