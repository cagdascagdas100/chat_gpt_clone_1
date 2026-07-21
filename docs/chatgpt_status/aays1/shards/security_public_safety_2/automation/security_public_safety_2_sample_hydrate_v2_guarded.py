from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
SAMPLE_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
LATEST_ENDPOINT = "https://data.police.uk/api/crime-last-updated"
RATE_SECONDS = 0.35


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_sibling(filename: str, module_name: str) -> Any:
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_runtime_contract(repo: Path) -> list[str]:
    failures: list[str] = []
    slot = os.environ.get("AAYS_SLOT_ID", SLOT_ID)
    branch = os.environ.get("AAYS_TARGET_BRANCH", TARGET_BRANCH)
    if slot != SLOT_ID:
        failures.append(f"WRONG_SLOT:{slot}")
    if branch != TARGET_BRANCH:
        failures.append(f"WRONG_BRANCH:{branch}")
    shared = repo / "docs/chatgpt_status/_shared/slots_18" / SLOT_ID
    for name in ("current_task_latest.json", "status_latest.json", "ownership_latest.json"):
        if not (shared / name).is_file():
            failures.append(f"MISSING_CONTRACT:{shared / name}")
    return failures


def extract_samples(source: Path, stream_features: Any, parcel_id: Any) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for feature in stream_features(source):
        current = parcel_id(feature)
        if current in SAMPLE_IDS and current not in found:
            found[current] = feature
        if len(found) == len(SAMPLE_IDS):
            break
    return found


def compact_feature(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") if geometry.get("type") == "Point" else None
    return {
        "geometry": geometry,
        "coordinates": coordinates,
        "row_no": props.get("row_no"),
        "hmlr_row_id": props.get("hmlr_row_id"),
        "hmlr_inspire_id": props.get("hmlr_inspire_id"),
        "hmlr_area_m2": props.get("hmlr_area_m2"),
        "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
        "london_authority": props.get("london_authority"),
        "lsoa_code": props.get("security_lsoa_code") or props.get("lsoa_code"),
        "lsoa_name": props.get("security_lsoa_name") or props.get("lsoa_name"),
        "existing_security_score_percent": props.get("safety_score") or props.get("security_score"),
        "security_level": props.get("safety_level") or props.get("security_level"),
        "canonical_confidence_score": props.get("confidence_score"),
        "canonical_spatial_score": props.get("spatial_score"),
        "spatial_match_method": props.get("spatial_match_method"),
        "existing_score_semantics": "PREEXISTING_AREA_PROXY_NOT_RECOMPUTED",
    }


def build_payload(
    source: Path,
    guard: dict[str, Any],
    features: dict[str, dict[str, Any]],
    http_json: Any,
    skip_api: bool = False,
    test_month: str | None = None,
) -> dict[str, Any]:
    latest = (
        {"url": LATEST_ENDPOINT, "http_status": 200, "sha256": "SELFTEST", "json": {"date": test_month}, "error": None}
        if test_month
        else http_json(LATEST_ENDPOINT)
    )
    latest_month = str((latest.get("json") or {}).get("date") or "")[:7] or None
    rows: list[dict[str, Any]] = []
    for parcel_id in SAMPLE_IDS:
        feature = features.get(parcel_id)
        if feature is None:
            rows.append({
                "parcel_id": parcel_id,
                "candidate_status": "CANONICAL_FEATURE_NOT_FOUND",
                "accuracy_score_4": 0,
                "needs_manual_review": True,
                "official_api_month": latest_month,
                "output_semantics": "NO_DATA",
                "parcel_measurement": False,
                "source_git_blob_sha": guard.get("observed_blob_sha"),
            })
            continue
        evidence = compact_feature(feature)
        row: dict[str, Any] = {
            "parcel_id": parcel_id,
            **evidence,
            "candidate_status": "CANONICAL_FEATURE_FOUND_API_PENDING",
            "accuracy_score_4": 2,
            "needs_manual_review": True,
            "official_api_month": latest_month,
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "source_git_blob_sha": guard.get("observed_blob_sha"),
        }
        coordinates = evidence.get("coordinates")
        if isinstance(coordinates, list) and len(coordinates) >= 2 and latest_month and not skip_api:
            lng, lat = coordinates[0], coordinates[1]
            url = "https://data.police.uk/api/crimes-street/all-crime?" + urllib.parse.urlencode(
                {"date": latest_month, "lat": lat, "lng": lng}
            )
            live = http_json(url)
            crimes = live.get("json")
            api_ok = live.get("http_status") == 200 and isinstance(crimes, list) and bool(live.get("sha256"))
            row.update({
                "official_api_url": url,
                "official_api_http_status": live.get("http_status"),
                "official_api_sha256": live.get("sha256"),
                "official_api_one_mile_supporting_count": len(crimes) if isinstance(crimes, list) else None,
                "official_api_semantics": "ANONYMISED_APPROXIMATE_ONE_MILE_SUPPORTING_EVIDENCE;NOT_EXACT_PARCEL_OR_LSOA_COUNT",
                "official_api_error": live.get("error"),
                "candidate_status": "CANONICAL_AND_OFFICIAL_API_VERIFIED_IOD25_V2_MPS_JOIN_PENDING" if api_ok else "CANONICAL_FOUND_OFFICIAL_API_FAILED",
                "accuracy_score_4": 3 if api_ok else 2,
            })
            time.sleep(RATE_SECONDS)
        rows.append(row)
    canonical = sum(row.get("candidate_status") != "CANONICAL_FEATURE_NOT_FOUND" for row in rows)
    accuracy_3 = sum(int(row.get("accuracy_score_4") or 0) == 3 for row in rows)
    return {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "task_step": "EXACT_BLOB_THREE_CANONICAL_SAMPLES",
        "generated_at": utc_now(),
        "target_ids": SAMPLE_IDS,
        "source_file": str(source),
        "canonical_guard": guard,
        "official_api_latest": {key: value for key, value in latest.items() if key != "json"} | {"month": latest_month},
        "rows": rows,
        "sample_count": len(rows),
        "canonical_sample_count": canonical,
        "accuracy_score_3_count": accuracy_3,
        "accuracy_score_4_count": 0,
        "actual_business_rows_written": 0,
        "output_semantics": "AREA_LEVEL_PROXY",
        "fake_data": False,
        "final_ready": False,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    failures = validate_runtime_contract(repo)
    if failures:
        raise RuntimeError(";".join(failures))
    guarded = load_sibling("security_public_safety_2_batch_hydrate_v3_guarded.py", "slot2_guarded_batch")
    base = load_sibling("security_public_safety_2_batch_hydrate.py", "slot2_stream_base")
    source, guard = guarded.materialize_exact_source(repo)
    if source is None or guard.get("pass") is not True or guard.get("observed_blob_sha") != REQUIRED_BLOB_SHA:
        guarded.write_fail_closed(repo, guard)
        raise RuntimeError("EXACT_CANONICAL_GIT_BLOB_NOT_VERIFIED")
    features = extract_samples(source, base.stream_features, base.pid)
    payload = build_payload(source, guard, features, base.http_json, args.skip_api, args.test_month)
    shard = repo / "docs/chatgpt_status/aays1/shards" / SLOT_ID
    web = repo / "england_map_web/data/aays_18_slots" / SLOT_ID
    out = shard / "runner_outputs/security_public_safety_2_sample_candidates_latest.json"
    web_json = web / "sample_candidates_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    out.write_text(text, encoding="utf-8")
    web_json.write_text(text, encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--skip-api", action="store_true")
    parser.add_argument("--test-month")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({
        "slot_id": SLOT_ID,
        "canonical_sample_count": result["canonical_sample_count"],
        "accuracy_score_3_count": result["accuracy_score_3_count"],
        "accuracy_score_4_count": 0,
        "final_ready": False,
    }))
