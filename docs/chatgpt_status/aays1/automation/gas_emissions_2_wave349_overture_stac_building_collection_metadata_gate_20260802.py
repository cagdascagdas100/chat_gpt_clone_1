#!/usr/bin/env python3
"""Wave349: bounded Overture STAC building-collection metadata gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from urllib import request

MAX_ROOT = 300_000
MAX_RELEASE = 500_000
MAX_THEME = 500_000
MAX_COLLECTION = 2_000_000
UA = "AAYS-Wave349/1.0 metadata-only"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def bounded_json_get(url: str, timeout: float, max_bytes: int) -> dict:
    req = request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"}, method="GET")
    out = {
        "source_url": url, "method": "GET", "http_status": None, "final_url": None,
        "content_type": None, "content_length_header": None, "bytes_read": 0,
        "content_sha256": sha256_bytes(b""), "truncated": False,
        "network_error": None, "parse_error": None, "_json": None,
    }
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            out["http_status"] = getattr(response, "status", None)
            out["final_url"] = response.geturl()
            out["content_type"] = response.headers.get("Content-Type")
            out["content_length_header"] = response.headers.get("Content-Length")
            if len(data) > max_bytes:
                data = data[:max_bytes]
                out["truncated"] = True
            out["bytes_read"] = len(data)
            out["content_sha256"] = sha256_bytes(data)
            try:
                out["_json"] = json.loads(data.decode("utf-8"))
            except Exception as exc:
                out["parse_error"] = f"{type(exc).__name__}:{exc}"
    except Exception as exc:
        out["network_error"] = f"{type(exc).__name__}:{exc}"
    return out

def canonical_rows(doc: dict) -> list[dict]:
    rows = []
    for row in doc.get("rows", []):
        p = row.get("properties") or {}
        rows.append({
            "parcel_id": row.get("parcel_id") or p.get("parcel_id"),
            "row_no": p.get("row_no"),
            "hmlr_inspire_id": p.get("hmlr_inspire_id"),
            "longitude": p.get("hmlr_lon"),
            "latitude": p.get("hmlr_lat"),
            "london_authority": p.get("london_authority"),
            "geometry_type": row.get("geometry_type"),
        })
    return rows

def child_link_present(doc: dict | None, expected_id: str) -> bool:
    if not isinstance(doc, dict):
        return False
    for link in doc.get("links", []):
        href = str(link.get("href", ""))
        title = str(link.get("title", ""))
        if link.get("rel") == "child" and (expected_id in href or expected_id == title):
            return True
    return False

def collection_summary(doc: dict | None) -> dict:
    if not isinstance(doc, dict):
        return {
            "collection_type_valid": False, "collection_id": None, "license": None,
            "feature_count": None, "columns": [], "item_link_count": 0,
            "required_columns_present": False, "spatial_extent_present": False,
        }
    summaries = doc.get("summaries") or {}
    columns = summaries.get("columns") or []
    if isinstance(columns, dict):
        columns = list(columns)
    if not isinstance(columns, list):
        columns = []
    item_links = [link for link in doc.get("links", []) if link.get("rel") == "item"]
    extent = ((doc.get("extent") or {}).get("spatial") or {}).get("bbox")
    features = doc.get("features")
    return {
        "collection_type_valid": doc.get("type") == "Collection",
        "collection_id": doc.get("id"),
        "license": doc.get("license"),
        "feature_count": features,
        "columns": columns,
        "item_link_count": len(item_links),
        "required_columns_present": all(x in columns for x in ("id", "geometry", "bbox")),
        "spatial_extent_present": bool(extent),
    }

def self_test() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    sample = {"rows":[{"parcel_id":"parcel_30762","geometry_type":"Point","properties":{
        "row_no":30762,"hmlr_inspire_id":"46058185","hmlr_lon":-0.0407406,
        "hmlr_lat":51.6769078,"london_authority":"Enfield"}}]}
    assert canonical_rows(sample)[0]["parcel_id"] == "parcel_30762"
    root = {"links":[{"rel":"child","href":"./2026-07-22.0/catalog.json","title":"Latest Overture Release"}]}
    assert child_link_present(root, "2026-07-22.0")
    collection = {
        "type":"Collection","id":"building","license":"ODbL-1.0","features":123,
        "extent":{"spatial":{"bbox":[[-180,-90,180,90]]}},
        "summaries":{"columns":["id","geometry","bbox"]},
        "links":[{"rel":"item","href":"00000.json"}],
    }
    summary = collection_summary(collection)
    assert summary["collection_type_valid"] and summary["required_columns_present"]
    assert summary["item_link_count"] == 1
    print("SELF_TEST_PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical")
    ap.add_argument("--fixture")
    ap.add_argument("--output")
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--accessed-at")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not (args.canonical and args.fixture and args.output):
        ap.error("--canonical, --fixture and --output are required")

    canonical = json.loads(Path(args.canonical).read_text(encoding="utf-8"))
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    rows = canonical_rows(canonical)
    targets = {"parcel_30762", "parcel_30763", "parcel_30764"}
    scoped = [row for row in rows if row["parcel_id"] in targets]
    if len(scoped) != 3 or any(row["london_authority"] != "Enfield" for row in scoped):
        raise SystemExit("CANONICAL_SCOPE_VALIDATION_FAILED")

    urls = fixture["candidate_urls"]
    specs = [
        ("root_catalog", MAX_ROOT),
        ("release_catalog", MAX_RELEASE),
        ("theme_catalog", MAX_THEME),
        ("building_collection", MAX_COLLECTION),
    ]
    probes = []
    for index, (name, limit) in enumerate(specs):
        probe = bounded_json_get(urls[name], args.timeout, limit)
        probe["probe_name"] = name
        probes.append(probe)
        if index < len(specs) - 1:
            time.sleep(args.delay)

    docs = {probe["probe_name"]: probe.pop("_json") for probe in probes}
    expected = fixture["expected_release"]
    root = docs["root_catalog"]
    release = docs["release_catalog"]
    theme = docs["theme_catalog"]
    collection = docs["building_collection"]
    summary = collection_summary(collection)

    root_latest = root.get("latest") if isinstance(root, dict) else None
    root_release_link = child_link_present(root, expected)
    release_buildings_link = child_link_present(release, "buildings")
    theme_building_link = child_link_present(theme, "building")
    collection_metadata_valid = (
        summary["collection_type_valid"]
        and summary["collection_id"] == "building"
        and summary["license"] == "ODbL-1.0"
        and isinstance(summary["feature_count"], int)
        and summary["feature_count"] > 0
        and summary["required_columns_present"]
        and summary["spatial_extent_present"]
        and summary["item_link_count"] > 0
    )
    live_count = sum(
        1 for probe in probes
        if probe["network_error"] is None
        and probe["parse_error"] is None
        and probe["http_status"] is not None
        and 200 <= probe["http_status"] < 400
        and not probe["truncated"]
    )
    metadata_live = (
        live_count == 4
        and root_latest == expected
        and root_release_link
        and release_buildings_link
        and theme_building_link
        and collection_metadata_valid
    )
    state = (
        "OVERTURE_STAC_BUILDING_COLLECTION_METADATA_AVAILABLE_CONTINUE_ITEM_SELECTION"
        if metadata_live else "NO_DATA_CONTINUE"
    )
    blocker = (
        "PARQUET_NOT_DOWNLOADED_BY_DESIGN;THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_SELECTED;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    )
    if not metadata_live:
        blocker = "OVERTURE_STAC_BUILDING_COLLECTION_METADATA_NOT_LIVE_ACQUIRED;" + blocker
    next_step = (
        "ASSESS_OVERTURE_STAC_ITEM_BBOX_SELECTION_FOR_THREE_CANONICAL_POINTS"
        if metadata_live else
        "ASSESS_SOURCE_COOPERATIVE_OVERTURE_BUILDING_MIRROR_METADATA_OR_NO_DATA_CONTINUE"
    )

    receipts = []
    for probe in probes:
        receipts.append(
            f"{probe['probe_name']}:{probe['network_error'] or probe['parse_error'] or probe['http_status']}"
        )
    runtime_evidence = [{
        "source_url": "https://stac.overturemaps.org/catalog.json",
        "accessed_at": args.accessed_at,
        "content_sha256": sha256_bytes("\n".join(receipts).encode("utf-8")),
        "hash_scope": "four_bounded_stac_json_probe_receipts",
        "record_scope": (
            "STAC root, current release catalog, buildings theme catalog and building "
            "collection metadata; no parquet body download."
        ),
        "relevant_record_ids_or_excerpt": "; ".join(receipts),
        "supports_fields": [
            "bounded_metadata_probe","latest_release","theme_and_type_links",
            "collection_metadata","parquet_body_not_downloaded","no_exact_binding_claim"
        ],
        "license_or_terms_url": "https://docs.overturemaps.org/attribution/",
    }]

    payload = {
        "schema_version": 1, "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2", "wave": 349,
        "accessed_at": args.accessed_at, "state": state,
        "decision": "OVERTURE_STAC_BUILDING_COLLECTION_METADATA_GATE_ASSESSED",
        "canonical_sample_rows_in_scope": 3, "assessments": scoped,
        "expected_release": expected, "root_latest": root_latest,
        "root_release_link": root_release_link,
        "release_buildings_link": release_buildings_link,
        "theme_building_link": theme_building_link,
        "collection_summary": summary,
        "probe_count": 4, "live_probe_count": live_count,
        "network_error_count": sum(1 for p in probes if p["network_error"]),
        "parse_error_count": sum(1 for p in probes if p["parse_error"]),
        "total_bytes_read": sum(p["bytes_read"] for p in probes),
        "parquet_body_downloaded": False, "probes": probes,
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "runtime_source_evidence": runtime_evidence,
        "business_rows_produced": 0, "parcel_rows_bound": 0,
        "completed_count": 0, "target_count": 30761,
        "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0,
        "blocker": blocker, "first_unverified_step": next_step,
        "fake_data": False, "final_ready": False,
    }
    atomic_json(Path(args.output), payload)
    print(json.dumps({
        "state": state, "probe_count": 4, "live_probe_count": live_count,
        "network_error_count": payload["network_error_count"],
        "parse_error_count": payload["parse_error_count"],
        "total_bytes_read": payload["total_bytes_read"],
        "parquet_body_downloaded": False,
        "business_rows_produced": 0, "parcel_rows_bound": 0,
        "first_unverified_step": next_step,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
