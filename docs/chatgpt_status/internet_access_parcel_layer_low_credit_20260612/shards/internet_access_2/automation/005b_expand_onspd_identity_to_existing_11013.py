# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
START, END = 30762, 61522
EXPECTED_ROWS = 11013
SNAPSHOT = "2026-05"
BATCH_SIZE = 100
MIN_SPLIT = 10
MAX_RETRIES = 3
WEB_CHUNK = 500
MATRIX_REL = "england_map_web/data/program_layer_matrix/internet.geojson"
SHARD_REL = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2"
SERVICES = (
    {
        "name": "ONSPD_MAY_2026_HOSTED_TABLE",
        "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/ONS_Postcode_Directory_%28May_2026%29_for_the_United_Kingdom_%28Hosted_Table%29/FeatureServer/0/query",
        "field": "pcds",
        "out": "pcd7,pcds,dointr,doterm,lat,long,lad25cd,ctry25cd",
    },
    {
        "name": "ONSPD_LATEST_CENTROIDS_FALLBACK",
        "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query",
        "field": "PCDS",
        "out": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
    },
)

def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def root() -> Path:
    start = Path.cwd().resolve()
    for p in (start, *start.parents):
        if (p / "england_map_web").is_dir() and (p / "docs/chatgpt_status").is_dir():
            return p
    raise RuntimeError("REPO_ROOT_NOT_FOUND")

def norm(v: Any) -> str:
    return re.sub(r"\s+", "", str(v or "")).upper()

def spaced(v: Any) -> str:
    c = norm(v)
    return c[:-3] + " " + c[-3:] if len(c) >= 5 else c

def attr(row: dict[str, Any], *names: str) -> Any:
    folded = {str(k).casefold(): v for k, v in row.items()}
    for n in names:
        if n.casefold() in folded:
            return folded[n.casefold()]
    return None

def legacy(text: Any) -> dict[str, Any]:
    raw = str(text or "")
    patterns = {
        "postcode": r"postcode=([^;]+)",
        "gigabit_available_pct": r"gigabit=([0-9.]+)%",
        "ultrafast_100mbps_available_pct": r"ufbb100=([0-9.]+)%",
        "superfast_30mbps_available_pct": r"sfbb=([0-9.]+)%",
        "unable_30mbps_pct": r"unable30=([0-9.]+)%",
    }
    out: dict[str, Any] = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, raw, flags=re.I)
        out[key] = norm(m.group(1)) if key == "postcode" and m else (float(m.group(1)) if m else None)
    return out

def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(values), size):
        yield values[i:i + size]

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as h:
        for row in rows:
            h.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

def log(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    row = {"at": now(), "step": step, "operation": operation, "state": state, **extra}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as h:
        h.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)

def request_once(service: dict[str, str], values: list[str]) -> tuple[dict[str, dict[str, Any]], str | None]:
    quoted = ",".join("'" + v.replace("'", "''") + "'" for v in values)
    payload = urllib.parse.urlencode({
        "where": f"{service['field']} IN ({quoted})",
        "outFields": service["out"],
        "returnGeometry": "false",
        "f": "json",
    }).encode("utf-8")
    req = urllib.request.Request(service["url"], data=payload, method="POST", headers={
        "User-Agent": "Mozilla/5.0 AAYS-TerraYield official-postcode-validation",
        "Accept": "application/json,text/plain,*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.arcgis.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            obj = json.loads(response.read().decode("utf-8"))
        if obj.get("error"):
            raise RuntimeError(json.dumps(obj["error"], ensure_ascii=False))
        found: dict[str, dict[str, Any]] = {}
        for feature in obj.get("features") or []:
            a = feature.get("attributes") or {}
            p = norm(attr(a, "pcds", "pcd7"))
            if p:
                found[p] = a
        return found, None
    except Exception as exc:
        return {}, f"{service['name']}:{type(exc).__name__}:{exc}"

def robust_query(service: dict[str, str], values: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    for attempt in range(1, MAX_RETRIES + 1):
        found, error = request_once(service, values)
        if error is None:
            return found, errors
        errors.append(f"attempt={attempt}:{error}")
        time.sleep(min(attempt, 3))
    if len(values) > MIN_SPLIT:
        mid = len(values) // 2
        left, le = robust_query(service, values[:mid])
        right, re_ = robust_query(service, values[mid:])
        left.update(right)
        return left, [*errors, *le, *re_]
    return {}, errors

def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    repo = root()
    shard = repo / SHARD_REL
    ppath = shard / "progress/005_progress.jsonl"
    ppath.parent.mkdir(parents=True, exist_ok=True)
    ppath.write_text("", encoding="utf-8")
    log(ppath, 1, "slot_partition_guard", "PASS", partition=[START, END])

    matrix = json.loads((repo / MATRIX_REL).read_text(encoding="utf-8-sig"))
    features = sorted(
        [f for f in matrix.get("features") or [] if START <= int((f.get("properties") or {}).get("row_no") or 0) <= END],
        key=lambda f: int((f.get("properties") or {}).get("row_no") or 0),
    )
    if len(features) != EXPECTED_ROWS:
        raise RuntimeError(f"EXPECTED_{EXPECTED_ROWS}_ROWS_GOT_{len(features)}")
    log(ppath, 2, "existing_shard2_matrix_filter", "PASS", rows=len(features))

    candidates: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties") or {}
        old = legacy(props.get("internet_level_value"))
        candidates.append({
            "row_no": int(props.get("row_no") or 0),
            "parcel_id": props.get("parcel_id"),
            "hmlr_inspire_id": props.get("hmlr_inspire_id"),
            "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
            "postcode": old.get("postcode"),
            "postcode_space": spaced(old.get("postcode")),
            "legacy_metrics": old,
        })
    postcodes = sorted({r["postcode"] for r in candidates if r.get("postcode")})
    log(ppath, 3, "canonical_postcode_extraction", "PASS", rows=len(candidates), distinct_postcodes=len(postcodes))

    official: dict[str, dict[str, Any]] = {}
    source_used: dict[str, str] = {}
    batch_log: list[dict[str, Any]] = []
    step = 3
    for service in SERVICES:
        missing = [p for p in postcodes if p not in official]
        if not missing:
            break
        for batch_no, compact_batch in enumerate(chunks(missing, BATCH_SIZE), 1):
            step += 1
            values = [spaced(p) for p in compact_batch]
            found, errors = robust_query(service, values)
            for p, a in found.items():
                if p not in official:
                    official[p] = a
                    source_used[p] = service["name"]
            entry = {"service": service["name"], "batch": batch_no, "requested": len(values), "returned": len(found), "errors": errors}
            batch_log.append(entry)
            log(ppath, step, "official_onspd_batch", "PASS" if found or not errors else "BLOCKED", **entry)

    rows: list[dict[str, Any]] = []
    confirmed = live = terminated = missing_count = 0
    for line, candidate in enumerate(candidates, 1):
        p = candidate.get("postcode")
        a = official.get(p)
        if a is None:
            status, accuracy = "ONSPD_NOT_CONFIRMED_AFTER_TWO_OFFICIAL_SERVICES", "0/4"
            missing_count += 1
        else:
            confirmed += 1
            if str(attr(a, "doterm") or "").strip():
                status, accuracy = "ONSPD_TERMINATED_REVIEW_REQUIRED", "1/4"
                terminated += 1
            else:
                status, accuracy = "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING", "2/4"
                live += 1
        rows.append({
            "line": line, **candidate,
            "onspd_snapshot_date": SNAPSHOT,
            "onspd_source": source_used.get(p),
            "onspd": a,
            "onspd_status": status,
            "candidate_status": status,
            "internet_accuracy": accuracy,
            "match_confidence": 0.0,
            "official_coverage_verified": False,
            "source_level": "POSTCODE_IDENTITY_ONLY",
            "parcel_measured_speed": False,
            "fake_data": False,
            "final_ready": False,
        })

    data_path = shard / "data/005_existing_11013_postcode_identity_candidates.jsonl"
    write_jsonl(data_path, rows)
    web_root = shard / "web/005_chunks"
    manifest_chunks: list[dict[str, Any]] = []
    for chunk_no, start in enumerate(range(0, len(rows), WEB_CHUNK), 1):
        chunk_rows = rows[start:start + WEB_CHUNK]
        path = web_root / f"part_{chunk_no:03d}.json"
        write_json(path, {"slot_id": SLOT_ID, "chunk": chunk_no, "row_start": start + 1,
                          "row_end": start + len(chunk_rows), "rows": chunk_rows, "final_ready": False})
        manifest_chunks.append({"chunk": chunk_no, "path": str(path.relative_to(repo)).replace("\\", "/"),
                                "row_start": start + 1, "row_end": start + len(chunk_rows), "count": len(chunk_rows)})

    errors = [e for b in batch_log for e in b["errors"]]
    blockers = ["OFCom_2026_EXACT_R2_COVERAGE_PENDING"]
    if errors:
        blockers.append("ONSPD_BATCH_RETRY_ERRORS_PRESENT")
    if missing_count:
        blockers.append("ONSPD_POSTCODE_IDENTITY_INCOMPLETE")
    validation = {
        "slot_id": SLOT_ID,
        "partition": {"start": START, "end": END, "count": END - START + 1},
        "existing_shard2_rows": len(rows),
        "distinct_postcodes": len(postcodes),
        "postcode_identity_confirmed": confirmed,
        "postcode_live": live,
        "postcode_terminated_review_required": terminated,
        "postcode_not_confirmed": missing_count,
        "official_coverage_verified_candidates": 0,
        "maximum_accuracy_without_ofcom_coverage": "2/4_POSTCODE_IDENTITY_ONLY",
        "maximum_accuracy_with_exact_ofcom_r2": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "official_service_count": len(SERVICES),
        "batch_attempts": len(batch_log),
        "retry_error_count": len(errors),
        "blockers": blockers,
        "fake_data": False, "db_write": False, "migration": False,
        "production_deploy": False, "final_ready": False, "validated_at": now(),
    }
    write_json(shard / "validation/005_existing_11013_identity_validation.json", validation)
    write_json(shard / "web/005_existing_11013_rows_manifest.json",
               {"slot_id": SLOT_ID, "generated_at": now(), "total_rows": len(rows), "chunk_size": WEB_CHUNK,
                "chunks": manifest_chunks, "counts": {"confirmed": confirmed, "live": live,
                "terminated": terminated, "missing": missing_count, "official_coverage_verified": 0},
                "final_ready": False})
    write_json(shard / "source_snapshots/005_onspd_batch_readback.json",
               {"slot_id": SLOT_ID, "snapshot": SNAPSHOT, "services": SERVICES,
                "batch_log": batch_log, "official_rows_returned": len(official),
                "corrected_hosted_table_service_item_id": "d1317f804688417287de8f8224ecc942",
                "final_ready": False})
    total_ops = step + 1
    write_json(shard / "status/005_status.json",
               {"slot_id": SLOT_ID, "task_id": os.environ.get("AAYS_TASK_ID"),
                "state": "EXISTING_SHARD2_POSTCODE_IDENTITY_COMPLETE_COVERAGE_PENDING" if not missing_count else "EXISTING_SHARD2_POSTCODE_IDENTITY_PARTIAL_COVERAGE_PENDING",
                "completed_operations": step, "total_operations": total_ops,
                "progress_percent": round(100 * step / total_ops, 2), **validation,
                "next_step": "JOIN_EXACT_OFCom_R2_POSTCODE_COVERAGE_TO_CONFIRMED_IDENTITIES",
                "updated_at": now()})
    report = (
        "# internet_access_2 — corrected two-source ONSPD identity expansion\n\n"
        f"- Existing rows: {len(rows)}\n- Distinct postcodes: {len(postcodes)}\n"
        f"- Identity confirmed: {confirmed}\n- Live: {live}\n- Terminated/review: {terminated}\n"
        f"- Not confirmed: {missing_count}\n- Web chunks: {len(manifest_chunks)}\n"
        "- Official Ofcom coverage verified: 0\n- Accuracy ceiling without Ofcom: 2/4\n- final_ready: false\n"
    )
    rpath = shard / "reports/005_existing_11013_onspd_identity.md"
    rpath.parent.mkdir(parents=True, exist_ok=True)
    rpath.write_text(report, encoding="utf-8")
    log(ppath, step + 1, "web_chunk_manifest_and_outputs_written", "PASS",
        rows=len(rows), chunks=len(manifest_chunks), confirmed=confirmed, missing=missing_count)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
