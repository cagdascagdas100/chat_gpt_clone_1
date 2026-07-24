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
from typing import Any

SLOT_ID = "internet_access_2"
START, END = 30762, 61522
SAMPLE_SIZE = 48
SNAPSHOT = "2026-05"
MATRIX_REL = "england_map_web/data/program_layer_matrix/internet.geojson"
PRIOR_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2/data/004_24_sample_postcode_normalized_candidates.jsonl"
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
            "ONS_Postcode_Directory_%28May_2026%29_for_the_United_Kingdom_"
            "%28Hosted_Table%29/FeatureServer/0/query"
        ),
        "field": "pcds",
        "out": "pcd7,pcds,dointr,doterm,lat,long,lad25cd,ctry25cd",
    },
    {
        "name": "ONSPD_LATEST_CENTROIDS_FALLBACK",
        "url": (
            "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
            "ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query"
        ),
        "field": "PCDS",
        "out": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
    },
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for path in (start, *start.parents):
        if (path / "england_map_web").is_dir() and (path / "docs/chatgpt_status").is_dir():
            return path
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def norm(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def spaced(value: Any) -> str:
    compact = norm(value)
    return compact[:-3] + " " + compact[-3:] if len(compact) >= 5 else compact


def attr(row: dict[str, Any], *names: str) -> Any:
    folded = {str(key).casefold(): value for key, value in row.items()}
    for name in names:
        if name.casefold() in folded:
            return folded[name.casefold()]
    return None


def parse_legacy(value: Any) -> dict[str, Any]:
    raw = str(value or "")
    patterns = {
        "postcode": r"postcode=([^;]+)",
        "gigabit_available_pct": r"gigabit=([0-9.]+)%",
        "ultrafast_100mbps_available_pct": r"ufbb100=([0-9.]+)%",
        "superfast_30mbps_available_pct": r"sfbb=([0-9.]+)%",
        "unable_30mbps_pct": r"unable30=([0-9.]+)%",
    }
    result: dict[str, Any] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, flags=re.I)
        if key == "postcode":
            result[key] = norm(match.group(1)) if match else None
        else:
            result[key] = float(match.group(1)) if match else None
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def progress(path: Path, line: int, operation: str, state: str, **extra: Any) -> None:
    row = {"at": now(), "line": line, "operation": operation, "state": state, **extra}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def read_prior_rows(path: Path) -> set[int]:
    rows: set[int] = set()
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.add(int(json.loads(line).get("row_no") or 0))
    return rows


def select_evenly(features: list[dict[str, Any]], excluded: set[int]) -> list[dict[str, Any]]:
    available = [
        feature for feature in features
        if int((feature.get("properties") or {}).get("row_no") or 0) not in excluded
    ]
    if len(available) < SAMPLE_SIZE:
        raise RuntimeError("INSUFFICIENT_AVAILABLE_SAMPLE_ROWS")
    selected: list[dict[str, Any]] = []
    used: set[int] = set()
    for index in range(SAMPLE_SIZE):
        position = round(index * (len(available) - 1) / (SAMPLE_SIZE - 1))
        while position < len(available):
            row_no = int((available[position].get("properties") or {}).get("row_no") or 0)
            if row_no not in used:
                selected.append(available[position])
                used.add(row_no)
                break
            position += 1
    if len(selected) != SAMPLE_SIZE:
        raise RuntimeError(f"EXPECTED_{SAMPLE_SIZE}_SELECTED_GOT_{len(selected)}")
    return selected


def query(service: dict[str, str], postcodes: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    quoted = ",".join("'" + spaced(value).replace("'", "''") + "'" for value in postcodes)
    body = urllib.parse.urlencode({
        "where": f"{service['field']} IN ({quoted})",
        "outFields": service["out"],
        "returnGeometry": "false",
        "f": "json",
    }).encode("utf-8")
    for attempt in range(1, 4):
        request = urllib.request.Request(
            service["url"],
            data=body,
            method="POST",
            headers={
                "User-Agent": "Mozilla/5.0 AAYS-TerraYield official-postcode-validation",
                "Accept": "application/json,text/plain,*/*",
                "Content-Type": "application/x-www-form-urlencoded",
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
                postcode = norm(attr(attributes, "pcds", "pcd7"))
                if postcode:
                    found[postcode] = attributes
            return found, errors
        except Exception as exc:
            errors.append(f"attempt={attempt}:{type(exc).__name__}:{exc}")
            time.sleep(attempt)
    return {}, errors


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / SHARD_REL
    progress_path = shard / "progress/007_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    progress(progress_path, 1, "slot_partition_guard", "PASS", partition=[START, END])

    matrix = json.loads((root / MATRIX_REL).read_text(encoding="utf-8-sig"))
    features = sorted(
        [
            feature for feature in matrix.get("features") or []
            if START <= int((feature.get("properties") or {}).get("row_no") or 0) <= END
        ],
        key=lambda feature: int((feature.get("properties") or {}).get("row_no") or 0),
    )
    if len(features) != 11013:
        raise RuntimeError(f"EXPECTED_11013_EXISTING_ROWS_GOT_{len(features)}")
    prior = read_prior_rows(root / PRIOR_REL)
    selected = select_evenly(features, prior)
    progress(progress_path, 2, "deterministic_additional_sample_selection", "PASS",
             selected=SAMPLE_SIZE, excluded_prior_rows=len(prior))

    candidates: list[dict[str, Any]] = []
    for feature in selected:
        props = feature.get("properties") or {}
        legacy = parse_legacy(props.get("internet_level_value"))
        candidates.append({
            "row_no": int(props.get("row_no") or 0),
            "parcel_id": props.get("parcel_id"),
            "hmlr_inspire_id": props.get("hmlr_inspire_id"),
            "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
            "postcode": legacy.get("postcode"),
            "postcode_space": spaced(legacy.get("postcode")),
            "legacy_metrics": legacy,
        })
    postcodes = sorted({row["postcode"] for row in candidates if row.get("postcode")})
    progress(progress_path, 3, "sample_postcode_extraction", "PASS",
             rows=len(candidates), distinct_postcodes=len(postcodes))

    official: dict[str, dict[str, Any]] = {}
    source_used: dict[str, str] = {}
    attempts: list[dict[str, Any]] = []
    for service in SERVICES:
        missing = [postcode for postcode in postcodes if postcode not in official]
        if not missing:
            break
        found, errors = query(service, missing)
        for postcode, attributes in found.items():
            if postcode not in official:
                official[postcode] = attributes
                source_used[postcode] = service["name"]
        attempts.append({
            "service": service["name"],
            "requested": len(missing),
            "returned": len(found),
            "errors": errors,
        })
        progress(progress_path, 3 + len(attempts), "official_onspd_exact_query",
                 "PASS" if found or not errors else "BLOCKED", **attempts[-1])

    output: list[dict[str, Any]] = []
    confirmed = live = terminated = missing_count = 0
    for line, candidate in enumerate(candidates, start=1):
        postcode = candidate.get("postcode")
        attributes = official.get(postcode)
        if attributes is None:
            status, accuracy = "ONSPD_NOT_CONFIRMED_AFTER_TWO_OFFICIAL_SERVICES", "0/4"
            missing_count += 1
        else:
            confirmed += 1
            if str(attr(attributes, "doterm") or "").strip():
                status, accuracy = "ONSPD_TERMINATED_REVIEW_REQUIRED", "1/4"
                terminated += 1
            else:
                status, accuracy = "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING", "2/4"
                live += 1
        row = {
            "line": line,
            **candidate,
            "onspd_snapshot_date": SNAPSHOT,
            "onspd_source": source_used.get(postcode),
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
        }
        output.append(row)
        progress(progress_path, 5 + line, "candidate_row", status,
                 line=line, row_no=row["row_no"], postcode=postcode, accuracy=accuracy)

    blockers = ["OFCom_2026_EXACT_R2_COVERAGE_PENDING"]
    if missing_count:
        blockers.append("ONSPD_ADDITIONAL_SAMPLE_IDENTITY_INCOMPLETE")
    validation = {
        "slot_id": SLOT_ID,
        "sample_rows": len(output),
        "distinct_postcodes": len(postcodes),
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
        "validated_at": now(),
    }
    write_jsonl(shard / "data/007_additional_48_onspd_candidates.jsonl", output)
    write_json(shard / "web/007_additional_48_rows_latest.json", {
        "slot_id": SLOT_ID,
        "generated_at": now(),
        "rows": output,
        "counts": {
            "sample_rows": len(output),
            "confirmed": confirmed,
            "live": live,
            "terminated": terminated,
            "missing": missing_count,
            "official_coverage_verified": 0,
        },
        "final_ready": False,
    })
    write_json(shard / "validation/007_additional_48_validation.json", validation)
    write_json(shard / "source_snapshots/007_onspd_additional_sample_readback.json", {
        "slot_id": SLOT_ID,
        "snapshot": SNAPSHOT,
        "services": SERVICES,
        "attempts": attempts,
        "official_rows_returned": len(official),
        "prior_sample_rows_excluded": len(prior),
        "final_ready": False,
    })
    write_json(shard / "status/007_status.json", {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "ADDITIONAL_SAMPLE_IDENTITY_COMPLETE_COVERAGE_PENDING" if not missing_count
                 else "ADDITIONAL_SAMPLE_IDENTITY_PARTIAL_COVERAGE_PENDING",
        "completed_operations": 5 + len(output),
        "total_operations": 6 + len(output),
        "progress_percent": round(100 * (5 + len(output)) / (6 + len(output)), 2),
        **validation,
        "next_step": "ACCEPT_SAMPLE_THEN_CONTINUE_11013_ROW_EXPANSION_AND_OFCom_JOIN",
        "updated_at": now(),
    })
    report = (
        "# internet_access_2 — additional 48-row ONSPD sample\n\n"
        f"- Sample rows: {len(output)}\n"
        f"- Identity confirmed: {confirmed}\n"
        f"- Live: {live}\n"
        f"- Terminated/review: {terminated}\n"
        f"- Not confirmed: {missing_count}\n"
        "- Official Ofcom coverage verified: 0\n"
        "- Accuracy ceiling without Ofcom: 2/4\n"
        "- final_ready: false\n"
    )
    report_path = shard / "reports/007_additional_48_onspd_sample.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    progress(progress_path, 54, "web_and_validation_outputs_written", "PASS",
             rows=len(output), confirmed=confirmed, missing=missing_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
