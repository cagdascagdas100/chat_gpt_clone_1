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
PARTITION_START = 30762
PARTITION_END = 61522
SOURCE_SNAPSHOT = "2026-05"
INPUT_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2/data/003_24_sample_identity_and_coverage_candidates.jsonl"
)
SHARD_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2"
)
SERVICES = (
    {
        "name": "ONSPD_MAY_2026_HOSTED_TABLE",
        "url": (
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
            "ONS_Postcode_Directory_May_2026_for_the_United_Kingdom_Hosted_Table/"
            "FeatureServer/0/query"
        ),
        "field": "pcds",
        "out_fields": "pcd7,pcds,dointr,doterm,lat,long,lad25cd,ctry25cd",
    },
    {
        "name": "ONSPD_ONLINE_LATEST_POSTCODE_CENTROIDS",
        "url": (
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
            "ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query"
        ),
        "field": "PCDS",
        "out_fields": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
    },
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
    if len(compact) < 5:
        return compact
    return compact[:-3] + " " + compact[-3:]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def attr(attributes: dict[str, Any], *names: str) -> Any:
    lookup = {str(key).casefold(): value for key, value in attributes.items()}
    for name in names:
        if name.casefold() in lookup:
            return lookup[name.casefold()]
    return None


def query_service(service: dict[str, str], spaced_values: list[str]) -> tuple[dict[str, dict[str, Any]], str | None, str]:
    quoted = ",".join("'" + value.replace("'", "''") + "'" for value in spaced_values)
    where = f"{service['field']} IN ({quoted})"
    params = {
        "where": where,
        "outFields": service["out_fields"],
        "returnGeometry": "false",
        "f": "json",
    }
    url = service["url"] + "?" + urllib.parse.urlencode(params)
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
            postcode = norm_postcode(attr(attributes, "pcds", "pcd7"))
            if postcode:
                found[postcode] = attributes
        return found, None, url
    except Exception as exc:
        return {}, f"{service['name']}_QUERY_BLOCKED: {type(exc).__name__}: {exc}", url


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    root = repo_root()
    shard = root / SHARD_REL
    progress_path = shard / "progress/004_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    append_progress(progress_path, 1, "slot_partition_guard", "PASS",
                    slot_id=SLOT_ID, partition=[PARTITION_START, PARTITION_END])

    source_rows = load_jsonl(root / INPUT_REL)
    if len(source_rows) != 24:
        raise RuntimeError(f"EXPECTED_24_INPUT_ROWS_GOT_{len(source_rows)}")
    if any(not (PARTITION_START <= int(row.get("row_no") or 0) <= PARTITION_END) for row in source_rows):
        raise RuntimeError("INPUT_ROW_OUTSIDE_SLOT_PARTITION")
    append_progress(progress_path, 2, "wave003_remote_input_readback", "PASS", rows=len(source_rows))

    spaced_values = sorted({spaced_postcode(row.get("postcode")) for row in source_rows if norm_postcode(row.get("postcode"))})
    official: dict[str, dict[str, Any]] = {}
    source_used: dict[str, str] = {}
    attempts: list[dict[str, Any]] = []
    for service in SERVICES:
        missing = [value for value in spaced_values if norm_postcode(value) not in official]
        if not missing:
            break
        found, blocker, query_url = query_service(service, missing)
        for postcode, attributes in found.items():
            if postcode not in official:
                official[postcode] = attributes
                source_used[postcode] = service["name"]
        attempts.append({
            "service": service["name"],
            "requested": len(missing),
            "returned": len(found),
            "blocker": blocker,
            "query_url": query_url,
        })
        append_progress(progress_path, 2 + len(attempts), "official_onspd_pcds_query",
                        "PASS" if not blocker else "BLOCKED",
                        service=service["name"], requested=len(missing),
                        returned=len(found), blocker=blocker)

    output: list[dict[str, Any]] = []
    confirmed = live = terminated = missing_count = 0
    for line_no, row in enumerate(source_rows, start=1):
        compact = norm_postcode(row.get("postcode"))
        spaced = spaced_postcode(compact)
        attributes = official.get(compact)
        if attributes is None:
            status = "ONSPD_NOT_CONFIRMED_AFTER_NORMALIZED_PCDS_QUERY"
            accuracy = "0/4"
            missing_count += 1
        else:
            confirmed += 1
            termination = str(attr(attributes, "doterm") or "").strip()
            if termination:
                status = "ONSPD_TERMINATED_REVIEW_REQUIRED"
                accuracy = "1/4"
                terminated += 1
            else:
                status = "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING"
                accuracy = "2/4"
                live += 1
        updated = {
            **row,
            "line": line_no,
            "postcode": compact,
            "postcode_space": spaced,
            "onspd_snapshot_date": SOURCE_SNAPSHOT,
            "onspd_normalization_method": "INSERT_SINGLE_SPACE_BEFORE_FINAL_3_CHARACTERS",
            "onspd_source": source_used.get(compact),
            "onspd": attributes,
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
        append_progress(progress_path, 4 + line_no, "candidate_row", status,
                        line=line_no, row_no=updated.get("row_no"),
                        postcode=compact, postcode_space=spaced,
                        identity_confirmed=attributes is not None,
                        accuracy=accuracy)

    blockers = []
    if missing_count:
        blockers.append("ONSPD_POSTCODE_IDENTITY_INCOMPLETE")
    blockers.append("OFCom_2026_DOWNLOAD_BLOCKED_AFTER_BROWSER_AND_CURL_FALLBACKS")

    data_path = shard / "data/004_24_sample_postcode_normalized_candidates.jsonl"
    web_path = shard / "web/004_24_sample_rows_latest.json"
    validation_path = shard / "validation/004_24_sample_validation.json"
    source_path = shard / "source_snapshots/004_onspd_normalized_query_readback.json"
    status_path = shard / "status/004_status.json"
    report_path = shard / "reports/004_onspd_pcds_normalization_24_sample.md"

    write_jsonl(data_path, output)
    write_json(web_path, {
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "rows": output,
        "counts": {
            "sample_rows": len(output),
            "postcode_identity_confirmed": confirmed,
            "postcode_live": live,
            "postcode_terminated_review_required": terminated,
            "postcode_not_confirmed": missing_count,
            "official_coverage_verified_candidates": 0,
        },
        "final_ready": False,
    })
    write_json(source_path, {
        "slot_id": SLOT_ID,
        "snapshot": SOURCE_SNAPSHOT,
        "normalization": "PCDS_SINGLE_SPACE_BEFORE_FINAL_3_CHARACTERS",
        "attempts": attempts,
        "official_rows_returned": confirmed,
        "final_ready": False,
    })
    validation = {
        "slot_id": SLOT_ID,
        "partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "sample_rows": len(output),
        "postcode_identity_confirmed": confirmed,
        "postcode_live": live,
        "postcode_terminated_review_required": terminated,
        "postcode_not_confirmed": missing_count,
        "official_coverage_verified_candidates": 0,
        "maximum_accuracy_without_ofcom_coverage": "2/4_POSTCODE_IDENTITY_ONLY",
        "maximum_accuracy_with_exact_ofcom_r2": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "blockers": blockers,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    }
    write_json(validation_path, validation)
    write_json(status_path, {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "POSTCODE_IDENTITY_NORMALIZATION_COMPLETE_COVERAGE_PENDING",
        "completed_operations": 4 + len(output) + 1,
        "total_operations": 4 + len(output) + 2,
        "progress_percent": round(100 * (5 + len(output)) / (6 + len(output)), 2),
        **validation,
        "next_step": "RESOLVE_OFFICIAL_OFCom_R2_BINARY_ACCESS_THEN_EXPAND_TO_ALL_11013_EXISTING_SHARD2_ROWS",
        "updated_at": utc_now(),
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — ONSPD PCDS normalization, 24-sample wave\n\n"
        f"- Input rows: {len(output)}\n"
        f"- Postcode identity confirmed: {confirmed}\n"
        f"- Live postcodes: {live}\n"
        f"- Terminated/review: {terminated}\n"
        f"- Not confirmed: {missing_count}\n"
        "- Official Ofcom coverage verified: 0\n"
        "- Accuracy: at most 2/4 until exact Ofcom r2 coverage row is present\n"
        "- Parcel-measured values written: 0\n"
        "- final_ready: false\n",
        encoding="utf-8",
    )
    append_progress(progress_path, 29, "web_and_remote_artifacts_written", "PASS",
                    files=[str(path.relative_to(root)).replace("\\", "/") for path in
                           (data_path, web_path, validation_path, source_path, status_path, report_path)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
