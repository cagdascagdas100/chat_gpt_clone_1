#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT = "future_growth_2"
WORKSTREAM = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
TARGET_ROWS = (30762, 46142, 61522)
GEOMETRY_KEYS = {
    "geometry", "parcel_geometry", "polygon", "multipolygon", "geojson",
    "wkt", "boundary", "parcel_boundary", "coordinates"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def row_map(items: Any, label: str) -> dict[int, dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError(f"{label} must be a list")
    result: dict[int, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or "row_no" not in item:
            raise ValueError(f"invalid {label} record")
        row_no = int(item["row_no"])
        if row_no in result:
            raise ValueError(f"duplicate row {row_no} in {label}")
        result[row_no] = item
    if set(result) != set(TARGET_ROWS):
        raise ValueError(f"{label} rows must equal {TARGET_ROWS}")
    return result


def polygon_evidence(value: Any, path: str = "$") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        geometry_type = str(value.get("type", "")).lower()
        if geometry_type in {"polygon", "multipolygon"} and isinstance(value.get("coordinates"), list):
            found.append({"path": path, "kind": geometry_type.upper()})
        for key, child in value.items():
            key_lower = str(key).lower()
            child_path = f"{path}.{key}"
            if key_lower in GEOMETRY_KEYS:
                if isinstance(child, str) and child.lstrip().upper().startswith(("POLYGON", "MULTIPOLYGON")):
                    found.append({"path": child_path, "kind": "WKT_POLYGON"})
                elif isinstance(child, dict):
                    child_type = str(child.get("type", "")).lower()
                    if child_type in {"polygon", "multipolygon"} and isinstance(child.get("coordinates"), list):
                        found.append({"path": child_path, "kind": child_type.upper()})
            found.extend(polygon_evidence(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(polygon_evidence(child, f"{path}[{index}]"))
    return found


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def run_gate(
    manifest: dict[str, Any],
    evidence_matrix: dict[str, Any],
    query_receipts: dict[str, Any],
    continuation_key: str,
    read_paths: list[str],
) -> dict[str, Any]:
    if len(continuation_key) != 64 or any(ch not in "0123456789abcdef" for ch in continuation_key):
        raise ValueError("continuation key must be lowercase SHA-256")
    if manifest.get("slot_id") != SLOT or evidence_matrix.get("slot_id") != SLOT or query_receipts.get("slot_id") != SLOT:
        raise ValueError("slot lineage mismatch")

    manifest_rows = row_map(manifest.get("rows"), "manifest.rows")
    matrix_rows = row_map(evidence_matrix.get("records"), "evidence_matrix.records")
    receipt_rows = row_map(query_receipts.get("records"), "query_receipts.records")

    records: list[dict[str, Any]] = []
    exact_count = 0
    for row_no in TARGET_ROWS:
        sources = {
            "manifest": manifest_rows[row_no],
            "evidence_matrix": matrix_rows[row_no],
            "query_receipt": receipt_rows[row_no],
        }
        found: list[dict[str, str]] = []
        for source_name, source_record in sources.items():
            for item in polygon_evidence(source_record, f"$.{source_name}"):
                found.append({"source": source_name, **item})
        exact_found = bool(found)
        exact_count += int(exact_found)
        records.append({
            "row_no": row_no,
            "parcel_id": str(manifest_rows[row_no].get("parcel_id", "")),
            "lpa": str(manifest_rows[row_no].get("lpa", "")),
            "point_proxy_lon": manifest_rows[row_no].get("lon"),
            "point_proxy_lat": manifest_rows[row_no].get("lat"),
            "point_proxy_present": manifest_rows[row_no].get("lon") is not None and manifest_rows[row_no].get("lat") is not None,
            "exact_canonical_parcel_geometry_found": exact_found,
            "geometry_evidence": found,
            "data_status": "EXACT_CANONICAL_PARCEL_GEOMETRY_FOUND" if exact_found else "NO_EXACT_CANONICAL_PARCEL_GEOMETRY_IN_REPO_EVIDENCE",
            "parcel_binding_status": "READY_FOR_EXACT_GEOMETRY_BINDING" if exact_found else "NO_DATA_CONTINUE",
            "membership_inferred": False,
            "score_written": False,
            "source_record_sha256": {name: canonical_digest(record) for name, record in sources.items()},
            "source_paths_checked": read_paths,
        })

    state = "PUBLISHED" if exact_count == len(TARGET_ROWS) else "NO_DATA_CONTINUE"
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "task_continuation_key": continuation_key,
        "state": state,
        "panel_status": "PUBLISHED" if state == "PUBLISHED" else "BİLGİ TOPLANIYOR",
        "generated_at": utc_now(),
        "completed_count": len(records),
        "target_count": len(TARGET_ROWS),
        "progress_percent": round(len(records) / len(TARGET_ROWS) * 100.0, 6),
        "exact_geometry_found_count": exact_count,
        "no_exact_geometry_count": len(TARGET_ROWS) - exact_count,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "records": records,
        "raw_geometry_copied": False,
        "point_proxy_used_as_geometry": False,
        "membership_inferred": False,
        "scores_written": False,
        "fake_data": False,
    }


def fixtures() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = []
    matrix = []
    receipts = []
    for row_no, lpa, lon, lat in (
        (30762, "Enfield", -0.0407406, 51.6769078),
        (46142, "Havering", 0.1928191, 51.5931140),
        (61522, "Lambeth", -0.1392630, 51.4153374),
    ):
        rows.append({"row_no": row_no, "parcel_id": f"parcel_{row_no}", "lpa": lpa, "lon": lon, "lat": lat, "layers": []})
        matrix.append({"row_no": row_no, "parcel_id": f"parcel_{row_no}", "parcel_binding_status": "MANIFEST_DECLARED_ANCHOR_ONLY", "lon": lon, "lat": lat})
        receipts.append({"row_no": row_no, "parcel_id": f"parcel_{row_no}", "query_scope": "ANCHOR_POINT_INTERSECTS_ONLY_NOT_PARCEL_POLYGON", "features": []})
    return (
        {"slot_id": SLOT, "rows": rows},
        {"slot_id": SLOT, "records": matrix},
        {"slot_id": SLOT, "records": receipts},
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--evidence-matrix", type=Path)
    parser.add_argument("--query-receipts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task-continuation-key", required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    read_paths = [
        str(args.manifest) if args.manifest else "fixture_manifest.json",
        str(args.evidence_matrix) if args.evidence_matrix else "fixture_evidence_matrix.json",
        str(args.query_receipts) if args.query_receipts else "fixture_query_receipts.json",
    ]
    if args.self_test:
        manifest, matrix, receipts = fixtures()
    else:
        if args.manifest is None or args.evidence_matrix is None or args.query_receipts is None:
            raise ValueError("all three input paths are required")
        manifest = load_json(args.manifest)
        matrix = load_json(args.evidence_matrix)
        receipts = load_json(args.query_receipts)

    result = run_gate(manifest, matrix, receipts, args.task_continuation_key, read_paths)
    atomic_write(args.output, result)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "exact_geometry_found_count": result["exact_geometry_found_count"],
        "no_exact_geometry_count": result["no_exact_geometry_count"],
        "output": str(args.output),
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
