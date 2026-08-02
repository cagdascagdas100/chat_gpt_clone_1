#!/usr/bin/env python3
"""Wave355: bounded PyArrow filtered row-group assessment for three Enfield bboxes.

The script never treats a bbox candidate as an exact parcel/UPRN binding. PyArrow is
installed only into a temporary directory. At most three STAC-selected building assets
are scanned, with projection limited to ``id`` and ``bbox`` and a hard candidate cap.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CATALOG_URL = "https://stac.overturemaps.org/catalog.json"
MAX_CATALOG_BYTES = 500_000
MAX_COLLECTIONS_BYTES = 20_000_000
MAX_ASSETS = 3
MAX_CANDIDATES_PER_BBOX = 25


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _atomic_json(path: str | Path, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def _bounded_get(url: str, max_bytes: int, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    request = Request(url, headers={"User-Agent": "AAYS-Wave355/1.0", "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            truncated = len(data) > max_bytes
            if truncated:
                data = data[:max_bytes]
            return {
                "ok": not truncated,
                "url": url,
                "status": getattr(response, "status", None),
                "bytes": len(data),
                "sha256": _sha256(data),
                "truncated": truncated,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "data": data,
                "error": "MAX_BYTES_EXCEEDED" if truncated else None,
            }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "url": url,
            "status": getattr(exc, "code", None),
            "bytes": 0,
            "sha256": None,
            "truncated": False,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "data": b"",
            "error": f"{type(exc).__name__}:{exc}",
        }


def _canonical_assessments(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    rows = canonical.get("rows") or []
    if len(rows) != 3:
        raise ValueError(f"Expected exactly three canonical rows, got {len(rows)}")
    assessments: list[dict[str, Any]] = []
    for row in rows:
        parcel_id = row.get("parcel_id")
        props = row.get("properties") or {}
        geometry = row.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        geometry_type = geometry.get("type") or row.get("geometry_type")
        if len(coords) == 2:
            lon, lat = float(coords[0]), float(coords[1])
        else:
            lon, lat = float(props.get("hmlr_lon")), float(props.get("hmlr_lat"))
        if geometry_type != "Point":
            raise ValueError(f"{parcel_id}: canonical carrier is not a Point")
        delta = 0.00035
        assessments.append(
            {
                "parcel_id": parcel_id,
                "hmlr_inspire_id": props.get("hmlr_inspire_id"),
                "longitude": lon,
                "latitude": lat,
                "london_authority": props.get("london_authority"),
                "geometry_type": geometry_type,
                "bbox": [round(lon - delta, 7), round(lat - delta, 7), round(lon + delta, 7), round(lat + delta, 7)],
            }
        )
    return assessments


def _install_pyarrow(target: str, timeout: int) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--no-cache-dir",
        "--target",
        target,
        "pyarrow",
    ]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        log = proc.stdout or b""
        return {
            "attempted": True,
            "returncode": proc.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "log_bytes": len(log),
            "log_sha256": _sha256(log),
            "log_excerpt": log.decode("utf-8", errors="replace")[-2000:],
            "temporary_target_only": True,
        }
    except subprocess.TimeoutExpired as exc:
        log = (exc.stdout or b"") + (exc.stderr or b"")
        return {
            "attempted": True,
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "log_bytes": len(log),
            "log_sha256": _sha256(log),
            "log_excerpt": log.decode("utf-8", errors="replace")[-2000:],
            "temporary_target_only": True,
        }


def _import_pyarrow(temp_target: str | None) -> tuple[bool, str | None]:
    if temp_target:
        sys.path.insert(0, temp_target)
    try:
        import pyarrow  # type: ignore
        return True, getattr(pyarrow, "__version__", None)
    except Exception:
        return False, None


def _bbox_expression(pc: Any, bbox: list[float]) -> Any:
    xmin, ymin, xmax, ymax = bbox
    return (
        (pc.field("bbox", "xmin") < xmax)
        & (pc.field("bbox", "xmax") > xmin)
        & (pc.field("bbox", "ymin") < ymax)
        & (pc.field("bbox", "ymax") > ymin)
    )


def _run_pyarrow_gate(assessments: list[dict[str, Any]], timeout: int) -> dict[str, Any]:
    import pyarrow.compute as pc  # type: ignore
    import pyarrow.dataset as ds  # type: ignore
    import pyarrow.fs as fs  # type: ignore
    import pyarrow.parquet as pq  # type: ignore

    receipts: list[dict[str, Any]] = []
    catalog = _bounded_get(CATALOG_URL, MAX_CATALOG_BYTES, timeout)
    receipts.append({k: v for k, v in catalog.items() if k != "data"})
    if not catalog["ok"]:
        return {
            "latest_release": None,
            "request_receipts": receipts,
            "network_error_count": 1,
            "total_bytes_read": catalog["bytes"],
            "selected_asset_count": 0,
            "successful_bbox_read_count": 0,
            "candidate_feature_count": 0,
            "bbox_reads": [],
        }

    catalog_json = json.loads(catalog["data"].decode("utf-8"))
    latest = catalog_json.get("latest")
    if not latest:
        raise ValueError("STAC catalog did not provide latest release")
    index_url = f"https://stac.overturemaps.org/{latest}/collections.parquet"
    index = _bounded_get(index_url, MAX_COLLECTIONS_BYTES, timeout)
    receipts.append({k: v for k, v in index.items() if k != "data"})
    if not index["ok"]:
        return {
            "latest_release": latest,
            "request_receipts": receipts,
            "network_error_count": int(bool(index["error"])),
            "total_bytes_read": catalog["bytes"] + index["bytes"],
            "selected_asset_count": 0,
            "successful_bbox_read_count": 0,
            "candidate_feature_count": 0,
            "bbox_reads": [],
        }

    stac_table = pq.read_table(io.BytesIO(index["data"]), columns=["collection", "type", "bbox", "assets"])
    s3_paths: list[str] = []
    for assessment in assessments:
        combined = (pc.field("collection") == "building") & (pc.field("type") == "Feature") & _bbox_expression(pc, assessment["bbox"])
        subset = stac_table.filter(combined)
        for asset in subset.column("assets").to_pylist()[:MAX_ASSETS]:
            try:
                href = asset["aws"]["alternate"]["s3"]["href"]
            except (KeyError, TypeError):
                continue
            path = href[len("s3://") :] if href.startswith("s3://") else href
            if path not in s3_paths:
                s3_paths.append(path)
            if len(s3_paths) >= MAX_ASSETS:
                break
        if len(s3_paths) >= MAX_ASSETS:
            break

    bbox_reads: list[dict[str, Any]] = []
    candidate_count = 0
    successful = 0
    if s3_paths:
        filesystem = fs.S3FileSystem(anonymous=True, region="us-west-2", connect_timeout=timeout, request_timeout=timeout)
        dataset = ds.dataset(s3_paths, filesystem=filesystem, format="parquet")
        for assessment in assessments:
            try:
                table = dataset.to_table(
                    columns=["id", "bbox"],
                    filter=_bbox_expression(pc, assessment["bbox"]),
                    use_threads=False,
                ).slice(0, MAX_CANDIDATES_PER_BBOX)
                ids = table.column("id").to_pylist() if "id" in table.column_names else []
                bbox_reads.append({
                    "parcel_id": assessment["parcel_id"],
                    "attempted": True,
                    "success": True,
                    "candidate_count": len(ids),
                    "candidate_ids": ids,
                })
                candidate_count += len(ids)
                successful += 1
            except Exception as exc:
                bbox_reads.append({
                    "parcel_id": assessment["parcel_id"],
                    "attempted": True,
                    "success": False,
                    "candidate_count": 0,
                    "error": f"{type(exc).__name__}:{exc}",
                })
    else:
        bbox_reads = [{"parcel_id": a["parcel_id"], "attempted": False, "success": False, "candidate_count": 0, "reason": "NO_STAC_ASSET"} for a in assessments]

    return {
        "latest_release": latest,
        "request_receipts": receipts,
        "network_error_count": sum(1 for r in receipts if r.get("error")),
        "total_bytes_read": sum(int(r.get("bytes") or 0) for r in receipts),
        "selected_asset_count": len(s3_paths),
        "successful_bbox_read_count": successful,
        "candidate_feature_count": candidate_count,
        "bbox_reads": bbox_reads,
    }


def _self_test(canonical_path: str, fixture_path: str) -> None:
    canonical = _read_json(canonical_path)
    fixture = _read_json(fixture_path)
    assessments = _canonical_assessments(canonical)
    if [a["parcel_id"] for a in assessments] != ["parcel_30762", "parcel_30763", "parcel_30764"]:
        raise AssertionError("Unexpected canonical parcel IDs")
    if len(fixture.get("source_evidence_manifest") or []) != 6:
        raise AssertionError("Expected six source evidence records")
    print("SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--install-timeout", type=int, default=120)
    parser.add_argument("--accessed-at", required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        _self_test(args.canonical, args.fixture)
        return 0
    if not args.output:
        parser.error("--output is required unless --self-test is used")

    canonical = _read_json(args.canonical)
    fixture = _read_json(args.fixture)
    assessments = _canonical_assessments(canonical)

    preinstalled = importlib.util.find_spec("pyarrow") is not None
    install_receipt: dict[str, Any] = {"attempted": False, "temporary_target_only": True}
    temp_target: str | None = None
    pyarrow_ready = preinstalled
    pyarrow_version: str | None = None

    with tempfile.TemporaryDirectory(prefix="aays-wave355-pyarrow-") as temp_dir:
        if not preinstalled:
            temp_target = os.path.join(temp_dir, "site")
            os.makedirs(temp_target, exist_ok=True)
            install_receipt = _install_pyarrow(temp_target, args.install_timeout)
        pyarrow_ready, pyarrow_version = _import_pyarrow(temp_target)

        if pyarrow_ready:
            try:
                gate = _run_pyarrow_gate(assessments, args.timeout)
            except Exception as exc:
                gate = {
                    "latest_release": None,
                    "request_receipts": [],
                    "network_error_count": 0,
                    "total_bytes_read": 0,
                    "selected_asset_count": 0,
                    "successful_bbox_read_count": 0,
                    "candidate_feature_count": 0,
                    "bbox_reads": [{"parcel_id": a["parcel_id"], "attempted": False, "success": False, "candidate_count": 0, "reason": f"PYARROW_GATE_ERROR:{type(exc).__name__}:{exc}"} for a in assessments],
                }
        else:
            gate = {
                "latest_release": None,
                "request_receipts": [],
                "network_error_count": 0,
                "total_bytes_read": 0,
                "selected_asset_count": 0,
                "successful_bbox_read_count": 0,
                "candidate_feature_count": 0,
                "bbox_reads": [{"parcel_id": a["parcel_id"], "attempted": False, "success": False, "candidate_count": 0, "reason": "PYARROW_NOT_INSTALLED"} for a in assessments],
            }

    if not pyarrow_ready:
        blocker = "PYARROW_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX;FILTERED_ROW_GROUP_READS_NOT_EXECUTED;THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    elif gate["selected_asset_count"] == 0:
        blocker = "OVERTURE_STAC_ASSETS_NOT_LIVE_ACQUIRED;PYARROW_FILTERED_ROW_GROUP_READS_NOT_EXECUTED;THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    elif gate["successful_bbox_read_count"] < 3:
        blocker = "THREE_PYARROW_FILTERED_BBOX_READS_NOT_COMPLETED;THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_CONFIRMED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    else:
        blocker = "BBOX_CANDIDATES_ARE_NOT_EXACT_PARCEL_OR_UPRN_BINDINGS;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"

    runtime_record = {
        "accessed_at": args.accessed_at,
        "content_sha256": _sha256(json.dumps({"install": install_receipt, "gate": gate}, sort_keys=True, default=str).encode("utf-8")),
        "hash_scope": "temporary_pyarrow_install_and_filtered_row_group_read_receipts",
        "license_or_terms_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "record_scope": "Temporary PyArrow install receipt, bounded STAC index fetch and up to three filtered id+bbox scans; no full GeoParquet download.",
        "relevant_record_ids_or_excerpt": f"pyarrow_ready={pyarrow_ready}; selected_assets={gate['selected_asset_count']}; successful_bbox_reads={gate['successful_bbox_read_count']}; candidate_feature_count={gate['candidate_feature_count']}",
        "source_url": "https://arrow.apache.org/docs/python/dataset.html",
        "supports_fields": ["pyarrow_installability", "predicate_pushdown", "column_projection", "three_bounded_bbox_reads", "candidate_count", "no_exact_binding_claim"],
    }

    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 355,
        "accessed_at": args.accessed_at,
        "canonical_sample_rows_in_scope": 3,
        "assessments": assessments,
        "pyarrow_preinstalled": preinstalled,
        "temporary_pyarrow_install": install_receipt,
        "pyarrow_ready": pyarrow_ready,
        "pyarrow_version": pyarrow_version,
        **gate,
        "full_geoparquet_downloaded": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "PYARROW_FILTERED_ROW_GROUP_THREE_BBOX_GATE_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": blocker,
        "first_unverified_step": "ASSESS_OVERTUREMAPS_PY_TEMPORARY_CLIENT_INSTALL_AND_RECORD_BATCH_READER_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "runtime_source_evidence": [runtime_record],
        "fake_data": False,
        "final_ready": False,
    }
    _atomic_json(args.output, payload)
    print(json.dumps({"state": payload["state"], "blocker": blocker, "candidate_feature_count": gate["candidate_feature_count"], "successful_bbox_read_count": gate["successful_bbox_read_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
