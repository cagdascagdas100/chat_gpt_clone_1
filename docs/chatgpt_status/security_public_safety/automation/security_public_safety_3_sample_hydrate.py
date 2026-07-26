from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "security_public_safety_3"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
OUT_ROOT = REPO / "docs" / "chatgpt_status" / "security_public_safety" / "runner_outputs"
WEB_ROOT = REPO / "outputs" / "england_program_parcel_matrix_20260629" / "security_public_safety_updates"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def http_json(url: str, timeout: int = 60) -> tuple[int, bytes, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-security-public-safety-slot3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return response.status, body, json.loads(body.decode("utf-8"))


def locate_targets() -> tuple[Path | None, dict[str, dict]]:
    found: dict[str, dict] = {}
    candidates = sorted(
        [p for p in DATA_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".geojson"}],
        key=lambda p: p.stat().st_size,
        reverse=True,
    )
    for path in candidates:
        if path.name in {"parcel_security_scores_verified.geojson", "security_evidence_manifest.json"}:
            continue
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception:
            continue
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            continue
        for feature in features:
            props = feature.get("properties") or {}
            parcel_id = props.get("security_parcel_id") or props.get("parcel_id")
            if parcel_id in TARGET_IDS:
                found[parcel_id] = feature
        if len(found) == len(TARGET_IDS):
            return path, found
    return None, found


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    source_path, features = locate_targets()

    latest_status = None
    latest_month = None
    latest_hash = None
    latest_error = None
    try:
        latest_status, latest_body, latest_payload = http_json("https://data.police.uk/api/crime-last-updated")
        latest_hash = hashlib.sha256(latest_body).hexdigest()
        latest_month = str(latest_payload.get("date", ""))[:7]
    except Exception as exc:
        latest_error = str(exc)

    rows = []
    for parcel_id in TARGET_IDS:
        feature = features.get(parcel_id)
        if not feature:
            rows.append({
                "parcel_id": parcel_id,
                "candidate_status": "CANONICAL_FEATURE_NOT_FOUND",
                "accuracy_score_4": 0,
                "needs_manual_review": True,
                "security_score_percent": None,
            })
            continue

        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") if geometry.get("type") == "Point" else None
        row = {
            "parcel_id": parcel_id,
            "candidate_status": "CANONICAL_FEATURE_FOUND_API_PENDING",
            "existing_security_score_percent": props.get("safety_score") or props.get("security_score"),
            "existing_score_semantics": "preexisting_candidate_not_recomputed",
            "security_level": props.get("safety_level") or props.get("security_level"),
            "lsoa_code": props.get("security_lsoa_code"),
            "lsoa_name": props.get("security_lsoa_name"),
            "spatial_match_method": props.get("spatial_match_method"),
            "canonical_confidence_score": props.get("confidence_score"),
            "canonical_spatial_score": props.get("spatial_score"),
            "geometry": geometry,
            "accuracy_score_4": 2,
            "needs_manual_review": True,
            "official_api_month": latest_month,
        }
        if coordinates and latest_month:
            lng, lat = coordinates
            query = urllib.parse.urlencode({"date": latest_month, "lat": lat, "lng": lng})
            url = f"https://data.police.uk/api/crimes-street/all-crime?{query}"
            try:
                status, body, crimes = http_json(url)
                row.update({
                    "official_api_http_status": status,
                    "official_api_url": url,
                    "official_api_response_sha256": hashlib.sha256(body).hexdigest(),
                    "official_api_one_mile_supporting_count": len(crimes) if isinstance(crimes, list) else None,
                    "official_api_semantics": "anonymised one-mile supporting evidence; not an exact parcel count",
                    "candidate_status": "CANONICAL_AND_OFFICIAL_API_VERIFIED_IOD25_JOIN_PENDING",
                    "accuracy_score_4": 3,
                })
            except Exception as exc:
                row.update({"official_api_error": str(exc), "candidate_status": "CANONICAL_FOUND_API_FAILED"})
            time.sleep(0.35)
        rows.append(row)

    verified_three = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    output = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 61523, "end": 92283, "count": 30761},
        "source_file": str(source_path) if source_path else None,
        "source_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path else None,
        "official_api_latest": {
            "http_status": latest_status,
            "month": latest_month,
            "response_sha256": latest_hash,
            "error": latest_error,
        },
        "rows": rows,
        "sample_count": len(rows),
        "accuracy_ge_3_count": verified_three,
        "actual_slot_rows_written": verified_three,
        "next_gate": "Join corrected IoD25 v2 crime-domain LSOA data before accuracy_score_4 may become 4",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    sample_path = OUT_ROOT / "security_public_safety_3_sample_candidates_latest.json"
    web_path = WEB_ROOT / "security_public_safety_3_rows_latest.json"
    text = json.dumps(output, ensure_ascii=False, indent=2)
    sample_path.write_text(text, encoding="utf-8")
    web_path.write_text(text, encoding="utf-8")
    print(f"SLOT_ID={SLOT_ID}")
    print(f"SOURCE_FILE={source_path}")
    print(f"SAMPLE_COUNT={len(rows)}")
    print(f"ACCURACY_GE_3_COUNT={verified_three}")
    print(f"OUTPUT={sample_path}")
    print(f"WEB_OUTPUT={web_path}")
    print("FINAL_READY=false")
    return 0 if source_path and verified_three > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
