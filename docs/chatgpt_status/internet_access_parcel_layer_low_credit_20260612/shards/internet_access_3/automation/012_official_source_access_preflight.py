#!/usr/bin/env python3
"""Lightweight official-source access checks for internet_access_3."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/006_official_source_access_preflight_registry_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/010_official_source_access_preflight_latest.json")
    p.add_argument("--timeout", type=int, default=60)
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def probe(source: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        source["url"],
        headers={
            "User-Agent": "TerraYield-AAYS-internet-access-3/2.0",
            "Accept": "*/*",
            "Range": "bytes=0-65535",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(65536)
            status = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
            final_url = response.geturl()
    except Exception as exc:
        return {"id": source["id"], "passed": False, "error_type": type(exc).__name__, "error": str(exc)}
    text = body.decode("utf-8", errors="ignore").lower()
    missing = [value for value in source.get("required_signatures", []) if value.lower() not in text]
    expected = [value.lower() for value in source.get("expected_content_types", [])]
    type_ok = not expected or any(value in content_type.lower() for value in expected)
    return {
        "id": source["id"],
        "passed": status in {200, 206} and type_ok and not missing,
        "status": status,
        "content_type": content_type,
        "final_url": final_url,
        "bytes_read": len(body),
        "missing_signatures": missing,
        "content_type_ok": type_ok,
    }


def update_feed(output_root: Path, summary: dict[str, Any]) -> None:
    path = output_root / "operation_feed_latest.json"
    feed = load(path) if path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    for item in summary["probes"]:
        operations.append({
            "sequence": sequence,
            "status": "PASS" if item["passed"] else "BLOCKED",
            "operation": "OFFICIAL_SOURCE_ACCESS_PREFLIGHT",
            "detail": f"{item['id']}; status={item.get('status')}; content_type={item.get('content_type')}; bytes={item.get('bytes_read')}",
        })
        sequence += 1
    feed.update({
        "updated_at": summary["updated_at"],
        "display_mode": "line_by_line",
        "final_ready": False,
        "operations": operations,
        "safety": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False},
    })
    write(path, feed)


def main() -> int:
    options = args()
    repo = root(options.repo_root)
    registry = load(repo / options.registry)
    probes = [probe(source, options.timeout) for source in registry["sources"]]
    required = set(registry["required_source_ids"])
    failures = [item for item in probes if item["id"] in required and not item["passed"]]
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "passed" if not failures else "blocked",
        "updated_at": now,
        "probes": probes,
        "required_failures": failures,
        "result": {
            "sources_checked": len(probes),
            "sources_passed": sum(1 for item in probes if item["passed"]),
            "required_failures": len(failures),
            "actual_business_data_rows_written": 0,
            "confidence_uplifts": 0,
        },
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output_root = repo / options.output_root
    write(output_root / "official_source_access_preflight_latest.json", summary)
    write(repo / options.runner_output, summary)
    update_feed(output_root, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
