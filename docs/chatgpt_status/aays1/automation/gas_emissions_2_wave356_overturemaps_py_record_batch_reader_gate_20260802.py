#!/usr/bin/env python3
"""Wave356: temporary overturemaps-py install and three bounded RecordBatchReader calls.

The package is installed only into a temporary directory. Each Enfield bbox is executed
in an isolated subprocess with a hard timeout and only the first streamed batch is
inspected. Returned features remain noncanonical candidates until independent exact
parcel/UPRN identity proof exists.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any

PACKAGE_SPEC = "overturemaps==1.0.1"


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


def _canonical_assessments(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    rows = canonical.get("rows") or []
    if len(rows) != 3:
        raise ValueError(f"Expected exactly three canonical rows, got {len(rows)}")
    assessments: list[dict[str, Any]] = []
    for row in rows:
        props = row.get("properties") or {}
        geometry = row.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        geometry_type = geometry.get("type") or row.get("geometry_type")
        if geometry_type != "Point":
            raise ValueError(f"{row.get('parcel_id')}: expected Point carrier")
        if len(coords) == 2:
            lon, lat = float(coords[0]), float(coords[1])
        else:
            lon, lat = float(props.get("hmlr_lon")), float(props.get("hmlr_lat"))
        delta = 0.00035
        assessments.append(
            {
                "parcel_id": row.get("parcel_id"),
                "hmlr_inspire_id": props.get("hmlr_inspire_id"),
                "longitude": lon,
                "latitude": lat,
                "london_authority": props.get("london_authority"),
                "geometry_type": geometry_type,
                "bbox": [
                    round(lon - delta, 7),
                    round(lat - delta, 7),
                    round(lon + delta, 7),
                    round(lat + delta, 7),
                ],
            }
        )
    return assessments


def _install_client(target: str, timeout: int) -> dict[str, Any]:
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
        PACKAGE_SPEC,
    ]
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        log = proc.stdout or b""
        return {
            "attempted": True,
            "returncode": proc.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "log_bytes": len(log),
            "log_sha256": _sha256(log),
            "log_excerpt": log.decode("utf-8", errors="replace")[-2500:],
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
            "log_excerpt": log.decode("utf-8", errors="replace")[-2500:],
            "temporary_target_only": True,
        }


_CHILD_CODE = r'''
import json, sys
from overturemaps import record_batch_reader
bbox = json.loads(sys.argv[1])
result = {"attempted": True, "success": False, "candidate_count": 0, "candidate_ids": [], "batch_rows": 0}
try:
    reader = record_batch_reader("building", bbox=bbox, connect_timeout=5, request_timeout=15, stac=True)
    if reader is None:
        result["reason"] = "READER_NONE"
    else:
        try:
            batch = reader.read_next_batch()
        except StopIteration:
            batch = None
        if batch is None:
            result["success"] = True
            result["reason"] = "EMPTY_STREAM"
        else:
            result["success"] = True
            result["batch_rows"] = batch.num_rows
            if "id" in batch.schema.names:
                values = batch.column(batch.schema.get_field_index("id")).to_pylist()[:25]
                result["candidate_ids"] = [str(v) for v in values if v is not None]
            result["candidate_count"] = len(result["candidate_ids"])
except Exception as exc:
    result["error"] = f"{type(exc).__name__}:{exc}"
print(json.dumps(result, sort_keys=True))
'''


def _run_bbox(temp_target: str | None, assessment: dict[str, Any], timeout: int) -> dict[str, Any]:
    env = os.environ.copy()
    if temp_target:
        env["PYTHONPATH"] = temp_target + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _CHILD_CODE, json.dumps(assessment["bbox"])],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
        stdout = (proc.stdout or b"").decode("utf-8", errors="replace").strip()
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        parsed = None
        if stdout:
            try:
                parsed = json.loads(stdout.splitlines()[-1])
            except json.JSONDecodeError:
                parsed = None
        receipt = {
            "parcel_id": assessment["parcel_id"],
            "bbox": assessment["bbox"],
            "returncode": proc.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_sha256": _sha256(proc.stdout or b""),
            "stderr_sha256": _sha256(proc.stderr or b""),
            "stderr_excerpt": stderr,
        }
        if parsed:
            receipt.update(parsed)
        else:
            receipt.update(
                {
                    "attempted": True,
                    "success": False,
                    "candidate_count": 0,
                    "candidate_ids": [],
                    "error": "INVALID_CHILD_JSON",
                }
            )
        return receipt
    except subprocess.TimeoutExpired as exc:
        return {
            "parcel_id": assessment["parcel_id"],
            "bbox": assessment["bbox"],
            "attempted": True,
            "success": False,
            "candidate_count": 0,
            "candidate_ids": [],
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_sha256": _sha256(exc.stdout or b""),
            "stderr_sha256": _sha256(exc.stderr or b""),
            "error": "SUBPROCESS_TIMEOUT",
        }


def _self_test(canonical_path: str, fixture_path: str) -> None:
    canonical = _read_json(canonical_path)
    fixture = _read_json(fixture_path)
    assessments = _canonical_assessments(canonical)
    if [a["parcel_id"] for a in assessments] != [
        "parcel_30762",
        "parcel_30763",
        "parcel_30764",
    ]:
        raise AssertionError("Unexpected canonical parcel IDs")
    if len(fixture.get("source_evidence_manifest") or []) != 6:
        raise AssertionError("Expected six source evidence records")
    if fixture.get("package_spec") != PACKAGE_SPEC:
        raise AssertionError("Unexpected package specification")
    print("SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output")
    parser.add_argument("--install-timeout", type=int, default=120)
    parser.add_argument("--bbox-timeout", type=int, default=45)
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
    preinstalled = importlib.util.find_spec("overturemaps") is not None
    install: dict[str, Any] = {"attempted": False, "temporary_target_only": True}
    temp_target: str | None = None
    ready = preinstalled
    version: str | None = None
    bbox_reads: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="aays-wave356-overturemaps-") as temp_dir:
        if not preinstalled:
            temp_target = os.path.join(temp_dir, "site")
            os.makedirs(temp_target, exist_ok=True)
            install = _install_client(temp_target, args.install_timeout)
        env = os.environ.copy()
        if temp_target:
            env["PYTHONPATH"] = temp_target + (
                os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
            )
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import overturemaps, importlib.metadata as m; print(m.version('overturemaps'))",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
            env=env,
        )
        ready = probe.returncode == 0
        if ready:
            version = (probe.stdout or b"").decode().strip().splitlines()[-1]
            bbox_reads = [
                _run_bbox(temp_target, assessment, args.bbox_timeout)
                for assessment in assessments
            ]
        else:
            bbox_reads = [
                {
                    "parcel_id": assessment["parcel_id"],
                    "bbox": assessment["bbox"],
                    "attempted": False,
                    "success": False,
                    "candidate_count": 0,
                    "candidate_ids": [],
                    "reason": "OVERTUREMAPS_NOT_INSTALLED",
                }
                for assessment in assessments
            ]

    successful = sum(1 for receipt in bbox_reads if receipt.get("success"))
    candidates = sum(int(receipt.get("candidate_count") or 0) for receipt in bbox_reads)
    if not ready:
        blocker = (
            "OVERTUREMAPS_PY_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX;"
            "RECORD_BATCH_READER_NOT_EXECUTED;THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
    elif successful < 3:
        blocker = (
            "THREE_OVERTUREMAPS_PY_RECORD_BATCH_BBOX_READS_NOT_COMPLETED;"
            "THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_CONFIRMED;THREE_EXACT_UPRNS_NOT_ACQUIRED;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
    else:
        blocker = (
            "OVERTURE_BBOX_CANDIDATES_ARE_NOT_EXACT_PARCEL_OR_UPRN_BINDINGS;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )

    runtime_payload = {
        "install": install,
        "ready": ready,
        "version": version,
        "bbox_reads": bbox_reads,
    }
    runtime = {
        "accessed_at": args.accessed_at,
        "content_sha256": _sha256(
            json.dumps(runtime_payload, sort_keys=True, default=str).encode("utf-8")
        ),
        "hash_scope": "temporary_overturemaps_install_and_three_record_batch_bbox_receipts",
        "license_or_terms_url": "https://github.com/OvertureMaps/overturemaps-py/blob/main/LICENSE",
        "record_scope": "Temporary official client install receipt and up to three isolated first-batch bbox reads; no full GeoParquet download or exact binding claim.",
        "relevant_record_ids_or_excerpt": (
            f"overturemaps_ready={ready}; version={version}; "
            f"successful_bbox_reads={successful}; candidate_feature_count={candidates}"
        ),
        "source_url": "https://github.com/OvertureMaps/overturemaps-py",
        "supports_fields": [
            "client_installability",
            "record_batch_reader",
            "three_bounded_bbox_reads",
            "candidate_count",
            "no_full_download",
            "no_exact_binding_claim",
        ],
    }
    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 356,
        "accessed_at": args.accessed_at,
        "canonical_sample_rows_in_scope": 3,
        "assessments": assessments,
        "package_spec": PACKAGE_SPEC,
        "overturemaps_preinstalled": preinstalled,
        "temporary_overturemaps_install": install,
        "overturemaps_ready": ready,
        "overturemaps_version": version,
        "bbox_execution_count": 3,
        "bbox_reads": bbox_reads,
        "successful_bbox_read_count": successful,
        "candidate_feature_count": candidates,
        "full_geoparquet_downloaded": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "OVERTUREMAPS_PY_RECORD_BATCH_READER_THREE_BBOX_GATE_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": blocker,
        "first_unverified_step": "ASSESS_OVERTUREMAPS_CLI_UVX_OR_STANDALONE_BINARY_THREE_BOUNDED_BBOX_STREAM_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "runtime_source_evidence": [runtime],
        "fake_data": False,
        "final_ready": False,
    }
    _atomic_json(args.output, payload)
    print(
        json.dumps(
            {
                "state": payload["state"],
                "blocker": blocker,
                "candidate_feature_count": candidates,
                "successful_bbox_read_count": successful,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
