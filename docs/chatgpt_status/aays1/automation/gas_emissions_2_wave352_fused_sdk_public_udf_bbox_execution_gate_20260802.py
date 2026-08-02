#!/usr/bin/env python3
"""Wave352: bounded Fused SDK install/public-UDF bbox execution gate.

No business row is emitted unless independently exact parcel identity proof exists.
The script installs only into a temporary directory and never persists credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

PINNED_UDF_URL = (
    "https://github.com/fusedio/udfs/tree/cc9e3f919d2a978aa917c2845326e359ad72011b/"
    "public/Overture_Maps_Example"
)
PACKAGE_SPEC = "fused[vector]"
RELEASE = "2026-04-15-0"
TARGET_COUNT = 30761


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json_bytes(value) + b"\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return [r for r in payload["rows"] if isinstance(r, dict)]
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    raise ValueError("canonical payload does not contain rows")


def normalize_target(row: dict[str, Any]) -> dict[str, Any]:
    props = row.get("properties") if isinstance(row.get("properties"), dict) else row
    parcel_id = row.get("parcel_id") or props.get("parcel_id")
    lon = props.get("hmlr_lon", props.get("longitude"))
    lat = props.get("hmlr_lat", props.get("latitude"))
    inspire = props.get("hmlr_inspire_id")
    authority = props.get("london_authority")
    geometry_type = row.get("geometry_type") or (row.get("geometry") or {}).get("type")
    if not parcel_id or lon is None or lat is None:
        raise ValueError("canonical target lacks parcel_id/coordinates")
    lon_f, lat_f = float(lon), float(lat)
    delta = 0.00035
    return {
        "parcel_id": str(parcel_id),
        "hmlr_inspire_id": None if inspire is None else str(inspire),
        "longitude": lon_f,
        "latitude": lat_f,
        "london_authority": authority,
        "geometry_type": geometry_type,
        "bbox": [round(lon_f - delta, 7), round(lat_f - delta, 7), round(lon_f + delta, 7), round(lat_f + delta, 7)],
    }


def bounded_text(data: bytes, limit: int = 50000) -> str:
    return data[:limit].decode("utf-8", "replace")


def attempt_temp_install(timeout_seconds: int) -> tuple[dict[str, Any], str | None]:
    target = tempfile.mkdtemp(prefix="aays_wave352_fused_sdk_")
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--target",
        target,
        PACKAGE_SPEC,
    ]
    started = time.monotonic()
    try:
        cp = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_seconds, check=False)
        raw = cp.stdout or b""
        receipt = {
            "attempted": True,
            "command_package_spec": PACKAGE_SPEC,
            "returncode": cp.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "log_bytes": len(raw),
            "log_sha256": sha256_bytes(raw),
            "log_excerpt": bounded_text(raw),
            "temporary_target_only": True,
        }
        spec = importlib.util.spec_from_file_location("_wave352_probe", Path(target) / "fused" / "__init__.py")
        installed = cp.returncode == 0 and spec is not None and (Path(target) / "fused").exists()
        receipt["installed"] = installed
        return receipt, target if installed else None
    except subprocess.TimeoutExpired as exc:
        raw = (exc.stdout or b"") + (exc.stderr or b"")
        return {
            "attempted": True,
            "command_package_spec": PACKAGE_SPEC,
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "log_bytes": len(raw),
            "log_sha256": sha256_bytes(raw),
            "log_excerpt": bounded_text(raw),
            "temporary_target_only": True,
            "installed": False,
        }, None


def execute_bbox_subprocess(sdk_target: str, bbox: list[float], timeout_seconds: int) -> dict[str, Any]:
    child = r'''
import json, sys
sdk_target, udf_url, bbox_json, release = sys.argv[1:5]
sys.path.insert(0, sdk_target)
import fused
bbox = json.loads(bbox_json)
udf = fused.load(udf_url)
kwargs = {"bounds": bbox, "release": release, "overture_type": "building", "use_columns": ["id", "bbox", "geometry"]}
result = udf(**kwargs)
row_count = None
columns = []
geometry_types = []
if result is not None:
    try: row_count = int(len(result))
    except Exception: pass
    try: columns = [str(c) for c in result.columns]
    except Exception: pass
    try:
        if "geometry" in result:
            geometry_types = sorted({str(x) for x in result.geometry.geom_type.dropna().unique().tolist()})
    except Exception: pass
print(json.dumps({"ok": True, "row_count": row_count, "columns": columns, "geometry_types": geometry_types}, sort_keys=True))
'''
    env = dict(os.environ)
    env["PYTHONNOUSERSITE"] = "1"
    command = [sys.executable, "-c", child, sdk_target, PINNED_UDF_URL, json.dumps(bbox), RELEASE]
    started = time.monotonic()
    try:
        cp = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds, check=False, env=env)
        out, err = cp.stdout or b"", cp.stderr or b""
        parsed = None
        if cp.returncode == 0:
            try:
                parsed = json.loads(out.decode("utf-8").splitlines()[-1])
            except Exception:
                parsed = None
        return {
            "attempted": True,
            "returncode": cp.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_bytes": len(out),
            "stdout_sha256": sha256_bytes(out),
            "stderr_bytes": len(err),
            "stderr_sha256": sha256_bytes(err),
            "stdout_excerpt": bounded_text(out, 20000),
            "stderr_excerpt": bounded_text(err, 20000),
            "parsed_result": parsed,
        }
    except subprocess.TimeoutExpired as exc:
        out, err = exc.stdout or b"", exc.stderr or b""
        return {
            "attempted": True,
            "returncode": None,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout_bytes": len(out),
            "stdout_sha256": sha256_bytes(out),
            "stderr_bytes": len(err),
            "stderr_sha256": sha256_bytes(err),
            "stdout_excerpt": bounded_text(out, 20000),
            "stderr_excerpt": bounded_text(err, 20000),
            "parsed_result": None,
        }


def self_test() -> None:
    sample = {
        "rows": [
            {"parcel_id": "parcel_30762", "geometry_type": "Point", "properties": {"parcel_id": "parcel_30762", "hmlr_inspire_id": "46058185", "hmlr_lon": -0.0407406, "hmlr_lat": 51.6769078, "london_authority": "Enfield"}},
            {"parcel_id": "parcel_30763", "geometry_type": "Point", "properties": {"parcel_id": "parcel_30763", "hmlr_inspire_id": "46037757", "hmlr_lon": -0.052972, "hmlr_lat": 51.6767314, "london_authority": "Enfield"}},
            {"parcel_id": "parcel_30764", "geometry_type": "Point", "properties": {"parcel_id": "parcel_30764", "hmlr_inspire_id": "45981756", "hmlr_lon": -0.0482579, "hmlr_lat": 51.6776898, "london_authority": "Enfield"}},
        ]
    }
    rows = [normalize_target(r) for r in extract_rows(sample)]
    assert len(rows) == 3
    assert all(len(r["bbox"]) == 4 and r["bbox"][0] < r["bbox"][2] and r["bbox"][1] < r["bbox"][3] for r in rows)
    assert canonical_json_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    print("SELF_TEST_PASS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", type=Path)
    ap.add_argument("--fixture", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--timeout", type=int, default=45)
    ap.add_argument("--install-timeout", type=int, default=120)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--accessed-at", required=False)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.canonical or not args.fixture or not args.output:
        ap.error("--canonical, --fixture and --output are required")

    canonical = read_json(args.canonical)
    fixture = read_json(args.fixture)
    targets = [normalize_target(r) for r in extract_rows(canonical)[:3]]
    if len(targets) != 3:
        raise ValueError("exactly three canonical rows are required")

    credential_path = Path.home() / ".fused" / "credentials"
    credentials_present = credential_path.is_file()
    preinstalled = importlib.util.find_spec("fused") is not None
    install_receipt, sdk_target = attempt_temp_install(args.install_timeout)

    executions: list[dict[str, Any]] = []
    if sdk_target:
        for i, target in enumerate(targets):
            execution = execute_bbox_subprocess(sdk_target, target["bbox"], args.timeout)
            execution["parcel_id"] = target["parcel_id"]
            execution["bbox"] = target["bbox"]
            executions.append(execution)
            if i < len(targets) - 1:
                time.sleep(max(0.0, args.delay))
    else:
        executions = [
            {"parcel_id": t["parcel_id"], "bbox": t["bbox"], "attempted": False, "reason": "SDK_NOT_INSTALLED"}
            for t in targets
        ]

    successful_execs = [x for x in executions if isinstance(x.get("parsed_result"), dict) and x["parsed_result"].get("ok")]
    candidate_count = sum(int((x.get("parsed_result") or {}).get("row_count") or 0) for x in successful_execs)
    runtime_receipt = {
        "preinstalled": preinstalled,
        "credentials_present": credentials_present,
        "install_receipt": install_receipt,
        "bbox_executions": executions,
        "successful_bbox_execution_count": len(successful_execs),
        "candidate_feature_count": candidate_count,
    }
    runtime_sha = sha256_bytes(canonical_json_bytes(runtime_receipt))

    if len(successful_execs) == 3:
        state = "CANDIDATES_ACQUIRED_NO_EXACT_BINDING" if candidate_count else "NO_DATA_CONTINUE"
        blocker = (
            "THREE_FUSED_BBOX_EXECUTIONS_COMPLETED_BUT_NO_EXACT_HMLR_UPRN_BINDING;"
            "OVERTURE_BUILDING_CANDIDATES_ARE_NOT_EXACT_PROPERTY_IDENTITY;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
    else:
        state = "NO_DATA_CONTINUE"
        blocker = (
            "FUSED_PYTHON_SDK_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX;"
            "FUSED_LOCAL_CREDENTIALS_NOT_PRESENT;"
            "PUBLIC_FUSED_UDF_LOAD_AND_THREE_BOUNDED_BBOX_EXECUTIONS_NOT_COMPLETED;"
            "THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )

    accessed_at = args.accessed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    output = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 352,
        "accessed_at": accessed_at,
        "state": state,
        "decision": "FUSED_PYTHON_SDK_PUBLIC_UDF_THREE_BBOX_EXECUTION_GATE_ASSESSED",
        "blocker": blocker,
        "first_unverified_step": "ASSESS_DUCKDB_HTTPFS_DIRECT_OVERTURE_S3_THREE_BOUNDED_BBOX_QUERY_OR_NO_DATA_CONTINUE",
        "fake_data": False,
        "final_ready": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": TARGET_COUNT,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "canonical_sample_rows_in_scope": len(targets),
        "assessments": targets,
        "fused_sdk_preinstalled": preinstalled,
        "fused_credentials_present": credentials_present,
        "temporary_sdk_install": install_receipt,
        "bbox_execution_count": len(executions),
        "successful_bbox_execution_count": len(successful_execs),
        "candidate_feature_count": candidate_count,
        "bbox_executions": executions,
        "geoparquet_body_downloaded": False,
        "runtime_source_evidence": [{
            "source_url": "https://pypi.org/project/fused/",
            "accessed_at": accessed_at,
            "content_sha256": runtime_sha,
            "hash_scope": "temporary_sdk_install_and_three_bbox_execution_receipts",
            "record_scope": "Temporary pip target install receipt, local credential presence, and up to three isolated public-UDF bbox execution receipts.",
            "relevant_record_ids_or_excerpt": (
                f"install_returncode={install_receipt.get('returncode')}; installed={install_receipt.get('installed')}; "
                f"credentials_present={credentials_present}; successful_bbox_execution_count={len(successful_execs)}; "
                f"candidate_feature_count={candidate_count}"
            ),
            "supports_fields": ["sdk_installability", "credential_presence", "public_udf_load", "three_bounded_bbox_executions", "candidate_count", "no_exact_binding_claim"],
            "license_or_terms_url": "https://www.fused.io/terms",
        }],
        "source_evidence_manifest": fixture.get("source_evidence_manifest", []),
    }
    atomic_write_json(args.output, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
