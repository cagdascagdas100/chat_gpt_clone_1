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
PARTITION_START = 30762
PARTITION_END = 61522
SOURCE_SNAPSHOT = "2026-05"
BATCH_SIZE = 180
WEB_CHUNK_SIZE = 500
LAYER_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
    "ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query"
)
MATRIX_REL = "england_map_web/data/program_layer_matrix/internet.geojson"
SHARD_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def norm_postcode(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def spaced_postcode(value: Any) -> str:
    compact = norm_postcode(value)
    return compact[:-3] + " " + compact[-3:] if len(compact) >= 5 else compact


def parse_legacy(text: Any) -> dict[str, Any]:
    raw = str(text or "")
    patterns = {
        "postcode": r"postcode=([^;]+)",
        "gigabit_available_pct": r"gigabit=([0-9.]+)%",
        "ultrafast_100mbps_available_pct": r"ufbb100=([0-9.]+)%",
        "superfast_30mbps_available_pct": r"sfbb=([0-9.]+)%",
        "unable_30mbps_pct": r"unable30=([0-9.]+)%",
    }
    output: dict[str, Any] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, flags=re.I)
        if key == "postcode":
            output[key] = norm_postcode(match.group(1)) if match else None
        else:
            output[key] = float(match.group(1)) if match else None
    return output


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def append_progress(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    row = {"at": utc_now(), "step": step, "operation": operation, "state": state, **extra}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def attr(attributes: dict[str, Any], *names: str) -> Any:
    lookup = {str(key).casefold(): value for key, value in attributes.items()}
    for name in names:
        if name.casefold() in lookup:
            return lookup[name.casefold()]
    return None


def query_batch(spaced_values: list[str]) -> tuple[dict[str, dict[str, Any]], str | None]:
    quoted = ",".join("'" + value.replace("'", "''") + "'" for value in spaced_values)
    params = {
        "where": f"PCDS IN ({quoted})",
        "outFields": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
        "returnGeometry": "false",
        "f": "json",
    }
    url = LAYER_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 AAYS-TerraYield official-postcode-validation",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.arcgis.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
        found: dict[str, dict[str, Any]] = {}
        for feature in payload.get("features") or []:
            attributes = feature.get("attributes") or {}
            postcode = norm_postcode(attr(attributes, "PCDS", "PCD7"))
            if postcode:
                found[postcode] = attributes
        return found, None
    except Exception as exc:
        return {}, f"ONSPD_BATCH_QUERY_BLOCKED: {type(exc).__name__}: {exc}"


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / SHARD_REL
    progress_path = shard / "progress/005_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    append_progress(progress_path, 1, "slot_partition_guard", "PASS",
                    partition=[PARTITION_START, PARTITION_END])

    matrix = json.loads((root / MATRIX_REL).read_text(encoding="utf-8-sig"))
    features = sorted(
        [
            feature for feature in matrix.get("features") or []
            if PARTITION_START <= int((feature.get("properties") or {}).get("row_no") or 0) <= PARTITION_END
        ],
        key=lambda feature: int((feature.get("properties") or {}).get("row_no") or 0),
    )
    if len(features) != 11013:
        raise RuntimeError(f"EXPECTED_11013_EXISTING_SHARD2_ROWS_GOT_{len(features)}")
    append_progress(progress_path, 2, "existing_shard2_matrix_filter", "PASS", rows=len(features))

    candidates: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties") or {}
        legacy = parse_legacy(props.get("internet_level_value"))
        candidates.append({
            "row_no": int(props.get("row_no") or 0),
            "parcel_id": props.get("parcel_id"),
            "hmlr_inspire_id": props.get("hmlr_inspire_id"),
            "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
            "postcode": legacy.get("postcode"),
            "postcode_space": spaced_postcode(legacy.get("postcode")),
            "legacy_metrics": legacy,
        })
    postcodes = sorted({row["postcode"] for row in candidates if row.get("postcode")})
    append_progress(progress_path, 3, "canonical_postcode_extraction", "PASS",
                    rows=len(candidates), distinct_postcodes=len(postcodes))

    official: dict[str, dict[str, Any]] = {}
    batch_errors: list[dict[str, Any]] = []
    batch_count = 0
    spaced_values = [spaced_postcode(value) for value in postcodes]
    for batch_count, batch in enumerate(chunks(spaced_values, BATCH_SIZE), start=1):
        found, blocker = query_batch(batch)
        official.update(found)
        if blocker:
            batch_errors.append({"batch": batch_count, "blocker": blocker, "requested": len(batch)})
        append_progress(progress_path, 3 + batch_count, "official_onspd_batch",
                        "PASS" if not blocker else "BLOCKED",
                        batch=batch_count, requested=len(batch), returned=len(found), blocker=blocker)
        time.sleep(0.1)

    rows: list[dict[str, Any]] = []
    confirmed = live = terminated = missing = 0
    for line_no, candidate in enumerate(candidates, start=1):
        postcode = candidate.get("postcode")
        attributes = official.get(postcode)
        if attributes is None:
            status = "ONSPD_NOT_CONFIRMED"
            accuracy = "0/4"
            missing += 1
        else:
            confirmed += 1
            termination = str(attr(attributes, "DOTERM") or "").strip()
            if termination:
                status = "ONSPD_TERMINATED_REVIEW_REQUIRED"
                accuracy = "1/4"
                terminated += 1
            else:
                status = "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING"
                accuracy = "2/4"
                live += 1
        rows.append({
            "line": line_no,
            **candidate,
            "onspd_snapshot_date": SOURCE_SNAPSHOT,
            "onspd": attributes,
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
    for chunk_no, start in enumerate(range(0, len(rows), WEB_CHUNK_SIZE), start=1):
        chunk_rows = rows[start:start + WEB_CHUNK_SIZE]
        chunk_path = web_root / f"part_{chunk_no:03d}.json"
        write_json(chunk_path, {
            "slot_id": SLOT_ID,
            "chunk": chunk_no,
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "rows": chunk_rows,
            "final_ready": False,
        })
        manifest_chunks.append({
            "chunk": chunk_no,
            "path": str(chunk_path.relative_to(root)).replace("\\", "/"),
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "count": len(chunk_rows),
        })

    blockers = ["OFCom_2026_DOWNLOAD_BLOCKED_AFTER_BROWSER_AND_CURL_FALLBACKS"]
    if batch_errors:
        blockers.append("ONSPD_BATCH_QUERY_PARTIAL")
    if missing:
        blockers.append("ONSPD_POSTCODE_IDENTITY_INCOMPLETE")

    validation = {
        "slot_id": SLOT_ID,
        "partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "existing_shard2_rows": len(rows),
        "distinct_postcodes": len(postcodes),
        "postcode_identity_confirmed": confirmed,
        "postcode_live": live,
        "postcode_terminated_review_required": terminated,
        "postcode_not_confirmed": missing,
        "official_coverage_verified_candidates": 0,
        "maximum_accuracy_without_ofcom_coverage": "2/4_POSTCODE_IDENTITY_ONLY",
        "maximum_accuracy_with_exact_ofcom_r2": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "batch_count": batch_count,
        "batch_errors": batch_errors,
        "blockers": blockers,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    }
    validation_path = shard / "validation/005_existing_11013_identity_validation.json"
    status_path = shard / "status/005_status.json"
    manifest_path = shard / "web/005_existing_11013_rows_manifest.json"
    source_path = shard / "source_snapshots/005_onspd_batch_readback.json"
    report_path = shard / "reports/005_existing_11013_onspd_identity.md"
    write_json(validation_path, validation)
    write_json(manifest_path, {
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "total_rows": len(rows),
        "chunk_size": WEB_CHUNK_SIZE,
        "chunks": manifest_chunks,
        "counts": {
            "confirmed": confirmed,
            "live": live,
            "terminated": terminated,
            "missing": missing,
            "official_coverage_verified": 0,
        },
        "final_ready": False,
    })
    write_json(source_path, {
        "slot_id": SLOT_ID,
        "source": "ONS Postcode Directory May 2026 online postcode centroids",
        "layer_url": LAYER_URL.rsplit("/query", 1)[0],
        "snapshot": SOURCE_SNAPSHOT,
        "batch_size": BATCH_SIZE,
        "batch_count": batch_count,
        "batch_errors": batch_errors,
        "official_rows_returned": len(official),
        "final_ready": False,
    })
    write_json(status_path, {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "EXISTING_SHARD2_POSTCODE_IDENTITY_COMPLETE_COVERAGE_PENDING" if not missing and not batch_errors
                 else "EXISTING_SHARD2_POSTCODE_IDENTITY_PARTIAL_COVERAGE_PENDING",
        "completed_operations": 4 + batch_count,
        "total_operations": 5 + batch_count,
        "progress_percent": round(100 * (4 + batch_count) / (5 + batch_count), 2),
        **validation,
        "next_step": "RESOLVE_OFFICIAL_OFCom_R2_BINARY_ACCESS_THEN_JOIN_EXACT_COVERAGE_FOR_11013_ROWS",
        "updated_at": utc_now(),
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — existing 11,013 rows ONSPD identity wave\n\n"
        f"- Existing shard-2 rows: {len(rows)}\n"
        f"- Distinct postcodes: {len(postcodes)}\n"
        f"- Identity confirmed: {confirmed}\n"
        f"- Live: {live}\n"
        f"- Terminated/review: {terminated}\n"
        f"- Not confirmed: {missing}\n"
        "- Official Ofcom coverage verified: 0\n"
        f"- Web chunks: {len(manifest_chunks)}\n"
        "- Accuracy: at most 2/4 until exact Ofcom r2 postcode coverage row is present\n"
        "- Parcel-measured values written: 0\n"
        "- final_ready: false\n",
        encoding="utf-8",
    )
    append_progress(progress_path, 4 + batch_count, "web_chunk_manifest_and_outputs_written", "PASS",
                    rows=len(rows), chunks=len(manifest_chunks), confirmed=confirmed,
                    missing=missing, files=[str(path.relative_to(root)).replace("\\", "/") for path in
                    (data_path, validation_path, status_path, manifest_path, source_path, report_path)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
