from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-planning-data-constraints-v1-20260802"
BASE_URL = "https://www.planning.data.gov.uk/entity.json"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/planning_data_constraints_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/planning_data_constraints_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
DATASETS = (
    "brownfield-land",
    "listed-building",
    "conservation-area",
    "article-4-direction-area",
)
MAX_BYTES = 1024 * 1024
MAX_RECORDS = 10
REQUEST_SPACING_SECONDS = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, path)


def load_points(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {item.get("parcel_id"): item for item in points if isinstance(item, dict)}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        point = by_id.get(parcel_id)
        if not point or point.get("geometry_type") != "Point" or point.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = point.get("longitude")
        lat = point.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return selected


def build_url(point: dict[str, Any]) -> str:
    params: list[tuple[str, str]] = [
        ("latitude", f"{point['latitude']:.7f}"),
        ("longitude", f"{point['longitude']:.7f}"),
    ]
    params.extend(("dataset", dataset) for dataset in DATASETS)
    params.extend([
        ("field", "entity"),
        ("field", "name"),
        ("field", "dataset"),
        ("field", "reference"),
        ("limit", str(MAX_RECORDS)),
    ])
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def request_json(url: str, timeout: int) -> tuple[int | None, bytes | None, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return getattr(response, "status", None), None, "ResponseTooLarge"
            return getattr(response, "status", None), body, None
    except Exception as exc:  # fail closed and persist bounded evidence only
        return None, None, type(exc).__name__


def validate_only() -> None:
    if not PROBE.startswith("england_map_web/"):
        raise SystemExit("invalid relative read path")
    if any(path.startswith("/") or ".." in Path(path).parts for path in OUTPUTS):
        raise SystemExit("invalid relative output path")
    if len(IDS) != 3 or MAX_RECORDS != 10 or MAX_BYTES != 1024 * 1024:
        raise SystemExit("invalid bounded-task constants")
    if DATASETS != ("brownfield-land", "listed-building", "conservation-area", "article-4-direction-area"):
        raise SystemExit("invalid dataset scope")
    print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_PLANNING_DATA_CONSTRAINTS_MAX10_MAX1MIB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0

    root = Path(args.root).resolve()
    points = load_points(root)
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for index, point in enumerate(points):
        if index:
            time.sleep(REQUEST_SPACING_SECONDS)
        url = build_url(point)
        accessed_at = now()
        status, body, error = request_json(url, args.timeout)
        record: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha256(url),
            "record_scope": "one bounded coordinate-intersection query across four Planning Data datasets; max 10 records",
            "proven_fields": ["query URL", "access time", "query SHA-256"],
            "http_status": status,
            "candidate_count": 0,
        }
        if body is None:
            bounded = f"PLANNING_DATA_CONSTRAINTS_ERROR:{error}"
            record.update({
                "content_sha256": sha256(bounded),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": bounded,
            })
        else:
            record.update({
                "content_sha256": sha256(body),
                "sha256_basis": "bounded_raw_response_bytes",
            })
            try:
                parsed = json.loads(body.decode("utf-8"))
                entities = parsed.get("entities", []) if isinstance(parsed, dict) else []
                if isinstance(entities, list):
                    for item in entities[:MAX_RECORDS]:
                        if not isinstance(item, dict):
                            continue
                        candidate = {
                            "parcel_id": point["parcel_id"],
                            "entity": item.get("entity"),
                            "dataset": item.get("dataset"),
                            "name": item.get("name"),
                            "reference": item.get("reference"),
                            "source_candidate_only": True,
                        }
                        candidates.append(candidate)
                    record["candidate_count"] = len(entities[:MAX_RECORDS])
                    record["relevant_record_ids_or_excerpt"] = [item.get("entity") for item in entities[:MAX_RECORDS] if isinstance(item, dict)]
                    record["proven_fields"].extend(["raw response SHA-256", "returned entity ids", "dataset", "name", "reference"])
            except Exception as exc:
                record["parse_error"] = type(exc).__name__
        evidence.append(record)

    completed = len(evidence)
    target = len(points)
    result_state = "CANDIDATES_PUBLISHED" if candidates else "NO_DATA_CONTINUE"
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": result_state,
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": [point["parcel_id"] for point in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "PLANNING_DATA_CONSTRAINTS_NO_USABLE_RESPONSE" if not candidates else None,
            "state": result_state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_PLANNING_DATA_CONSTRAINTS",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for relative in OUTPUTS:
        atomic_write(root / relative, payload)
    print(json.dumps({"state": result_state, "completed": completed, "target": target, "candidate_rows": len(candidates)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
