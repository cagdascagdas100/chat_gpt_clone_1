# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
START, END = 30762, 61522
SNAPSHOT = "2026-05"
INPUT_REL = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/data/003_24_sample_identity_and_coverage_candidates.jsonl"
SHARD_REL = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2"
SERVICES = (
    {
        "name": "ONSPD_MAY_2026_HOSTED_TABLE",
        "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/ONS_Postcode_Directory_%28May_2026%29_for_the_United_Kingdom_%28Hosted_Table%29/FeatureServer/0/query",
        "field": "pcds",
        "outFields": "pcd7,pcds,dointr,doterm,lat,long,lad25cd,ctry25cd",
    },
    {
        "name": "ONSPD_LATEST_CENTROIDS_FALLBACK",
        "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query",
        "field": "PCDS",
        "outFields": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
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

def norm(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()

def spaced(value: Any) -> str:
    c = norm(value)
    return c[:-3] + " " + c[-3:] if len(c) >= 5 else c

def attr(row: dict[str, Any], *names: str) -> Any:
    folded = {str(k).casefold(): v for k, v in row.items()}
    for name in names:
        if name.casefold() in folded:
            return folded[name.casefold()]
    return None

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")

def progress(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    row = {"at": now(), "step": step, "operation": operation, "state": state, **extra}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)

def query(service: dict[str, str], values: list[str]) -> tuple[dict[str, dict[str, Any]], str | None, str]:
    quoted = ",".join("'" + v.replace("'", "''") + "'" for v in values)
    params = {
        "where": f"{service['field']} IN ({quoted})",
        "outFields": service["outFields"],
        "returnGeometry": "false",
        "f": "json",
    }
    url = service["url"] + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 AAYS-TerraYield official-postcode-validation",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://www.arcgis.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
        found: dict[str, dict[str, Any]] = {}
        for feature in payload.get("features") or []:
            a = feature.get("attributes") or {}
            p = norm(attr(a, "pcds", "pcd7"))
            if p:
                found[p] = a
        return found, None, url
    except Exception as exc:
        return {}, f"{service['name']}_QUERY_BLOCKED:{type(exc).__name__}:{exc}", url

def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    repo = root()
    shard = repo / SHARD_REL
    ppath = shard / "progress/004_progress.jsonl"
    ppath.parent.mkdir(parents=True, exist_ok=True)
    ppath.write_text("", encoding="utf-8")
    progress(ppath, 1, "slot_partition_guard", "PASS", partition=[START, END])

    rows = read_jsonl(repo / INPUT_REL)
    if len(rows) != 24:
        raise RuntimeError(f"EXPECTED_24_INPUT_ROWS_GOT_{len(rows)}")
    if any(not START <= int(r.get("row_no") or 0) <= END for r in rows):
        raise RuntimeError("INPUT_OUTSIDE_SLOT")
    progress(ppath, 2, "wave003_input_readback", "PASS", rows=len(rows))

    values = sorted({spaced(r.get("postcode")) for r in rows if norm(r.get("postcode"))})
    official: dict[str, dict[str, Any]] = {}
    source_used: dict[str, str] = {}
    attempts: list[dict[str, Any]] = []
    for service in SERVICES:
        missing = [v for v in values if norm(v) not in official]
        if not missing:
            break
        found, blocker, query_url = query(service, missing)
        for postcode, data in found.items():
            if postcode not in official:
                official[postcode] = data
                source_used[postcode] = service["name"]
        attempts.append({"service": service["name"], "requested": len(missing), "returned": len(found), "blocker": blocker, "query_url": query_url})
        progress(ppath, 2 + len(attempts), "official_onspd_exact_pcds_query", "PASS" if not blocker else "BLOCKED",
                 service=service["name"], requested=len(missing), returned=len(found), blocker=blocker)

    output: list[dict[str, Any]] = []
    confirmed = live = terminated = absent = 0
    for line, row in enumerate(rows, 1):
        postcode = norm(row.get("postcode"))
        data = official.get(postcode)
        if data is None:
            status, accuracy = "ONSPD_NOT_CONFIRMED_AFTER_TWO_OFFICIAL_SERVICES", "0/4"
            absent += 1
        else:
            confirmed += 1
            if str(attr(data, "doterm") or "").strip():
                status, accuracy = "ONSPD_TERMINATED_REVIEW_REQUIRED", "1/4"
                terminated += 1
            else:
                status, accuracy = "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING", "2/4"
                live += 1
        updated = {
            **row,
            "line": line,
            "postcode": postcode,
            "postcode_space": spaced(postcode),
            "onspd_snapshot_date": SNAPSHOT,
            "onspd_source": source_used.get(postcode),
            "onspd": data,
            "onspd_status": status,
            "candidate_status": status,
            "internet_accuracy": accuracy,
            "match_confidence": 0.0,
            "official_coverage_verified": False,
            "parcel_measured_speed": False,
            "fake_data": False,
            "final_ready": False,
        }
        output.append(updated)
        progress(ppath, 4 + line, "candidate_row", status, line=line, row_no=updated.get("row_no"),
                 postcode=postcode, identity_confirmed=data is not None, accuracy=accuracy)

    blockers = ["OFCom_2026_EXACT_R2_COVERAGE_PENDING"]
    if absent:
        blockers.append("ONSPD_POSTCODE_IDENTITY_INCOMPLETE")
    validation = {
        "slot_id": SLOT_ID,
        "partition": {"start": START, "end": END, "count": END - START + 1},
        "sample_rows": len(output),
        "postcode_identity_confirmed": confirmed,
        "postcode_live": live,
        "postcode_terminated_review_required": terminated,
        "postcode_not_confirmed": absent,
        "official_coverage_verified_candidates": 0,
        "maximum_accuracy_without_ofcom_coverage": "2/4_POSTCODE_IDENTITY_ONLY",
        "maximum_accuracy_with_exact_ofcom_r2": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "blockers": blockers,
        "fake_data": False, "db_write": False, "migration": False,
        "production_deploy": False, "final_ready": False, "validated_at": now(),
    }
    write_jsonl(shard / "data/004_24_sample_postcode_normalized_candidates.jsonl", output)
    write_json(shard / "web/004_24_sample_rows_latest.json",
               {"slot_id": SLOT_ID, "generated_at": now(), "rows": output,
                "counts": {"sample_rows": 24, "confirmed": confirmed, "live": live,
                           "terminated": terminated, "missing": absent, "official_coverage_verified": 0},
                "final_ready": False})
    write_json(shard / "validation/004_24_sample_validation.json", validation)
    write_json(shard / "source_snapshots/004_onspd_normalized_query_readback.json",
               {"slot_id": SLOT_ID, "snapshot": SNAPSHOT, "attempts": attempts,
                "official_rows_returned": confirmed, "corrected_hosted_table_service_item_id": "d1317f804688417287de8f8224ecc942",
                "final_ready": False})
    write_json(shard / "status/004_status.json",
               {"slot_id": SLOT_ID, "task_id": os.environ.get("AAYS_TASK_ID"),
                "state": "POSTCODE_IDENTITY_NORMALIZATION_COMPLETE_COVERAGE_PENDING",
                "completed_operations": 29, "total_operations": 30,
                "progress_percent": 96.67, **validation,
                "next_step": "EXPAND_EXACT_PCDS_IDENTITY_TO_11013_THEN_RESOLVE_OFCom_R2",
                "updated_at": now()})
    report = (
        "# internet_access_2 — corrected ONSPD May 2026 PCDS normalization\n\n"
        f"- Input rows: 24\n- Identity confirmed: {confirmed}\n- Live: {live}\n"
        f"- Terminated/review: {terminated}\n- Not confirmed: {absent}\n"
        "- Official Ofcom coverage verified: 0\n"
        "- Accuracy ceiling without Ofcom exact r2: 2/4\n- final_ready: false\n"
    )
    rpath = shard / "reports/004_onspd_pcds_normalization_24_sample.md"
    rpath.parent.mkdir(parents=True, exist_ok=True)
    rpath.write_text(report, encoding="utf-8")
    progress(ppath, 30, "web_and_remote_artifacts_written", "PASS", rows=24, confirmed=confirmed)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
