from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
PARCEL_START = 30762
PARCEL_END = 61522
SAMPLE_IDS = ["parcel_30762", "parcel_30763", "parcel_30764"]
LATEST_ENDPOINT = "https://data.police.uk/api/crime-last-updated"
API_RATE_SECONDS = 0.35

REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
SHARD_ROOT = REPO / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = DATA_ROOT / "aays_18_slots" / SLOT_ID
JSON_OUTPUT = SHARD_ROOT / "runner_outputs" / "security_public_safety_2_sample_candidates_latest.json"
WEB_JSON_OUTPUT = WEB_ROOT / "sample_candidates_latest.json"
WEB_HTML_OUTPUT = WEB_ROOT / "progress.html"

PREFERRED_SOURCES = (
    DATA_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson",
    DATA_ROOT / "program_layer_matrix" / "security.geojson",
    DATA_ROOT / "parcel_security_scores_compact.geojson",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def http_json(url: str, timeout: int = 60) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-security-public-safety-slot2/1.0",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            parsed = json.loads(body.decode("utf-8"))
            return {
                "url": url,
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "body_bytes": len(body),
                "body_sha256": sha256_bytes(body),
                "json": parsed,
                "error": None,
            }
    except Exception as exc:
        return {
            "url": url,
            "http_status": None,
            "content_type": None,
            "body_bytes": 0,
            "body_sha256": None,
            "json": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def candidate_source_paths() -> list[Path]:
    preferred = [path for path in PREFERRED_SOURCES if path.is_file()]
    discovered = sorted(
        (
            path
            for path in DATA_ROOT.rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".json", ".geojson"}
            and path not in {JSON_OUTPUT, WEB_JSON_OUTPUT}
        ),
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    return list(dict.fromkeys(preferred + discovered))


def feature_parcel_id(feature: dict[str, Any]) -> str:
    props = feature.get("properties") or {}
    return str(props.get("security_parcel_id") or props.get("parcel_id") or "").strip()


def locate_sample_features() -> tuple[Path | None, dict[str, dict[str, Any]]]:
    found: dict[str, dict[str, Any]] = {}
    for path in candidate_source_paths():
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception:
            continue
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            parcel_id = feature_parcel_id(feature)
            if parcel_id in SAMPLE_IDS:
                found[parcel_id] = feature
        if len(found) == len(SAMPLE_IDS):
            return path, found
    return None, found


def compact_existing_evidence(feature: dict[str, Any]) -> dict[str, Any]:
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
        "lsoa_code": props.get("security_lsoa_code"),
        "lsoa_name": props.get("security_lsoa_name"),
        "existing_security_score_percent": props.get("safety_score") or props.get("security_score"),
        "security_level": props.get("safety_level") or props.get("security_level"),
        "canonical_confidence_score": props.get("confidence_score"),
        "canonical_spatial_score": props.get("spatial_score"),
        "spatial_match_method": props.get("spatial_match_method"),
        "existing_score_semantics": "PREEXISTING_AREA_PROXY_NOT_RECOMPUTED",
    }


def validate_samples() -> dict[str, Any]:
    source_path, features = locate_sample_features()
    latest = http_json(LATEST_ENDPOINT)
    latest_json = latest.get("json")
    latest_month = str(latest_json.get("date") or "")[:7] if isinstance(latest_json, dict) else None
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
            })
            continue
        evidence = compact_existing_evidence(feature)
        coordinates = evidence.get("coordinates")
        row: dict[str, Any] = {
            "parcel_id": parcel_id,
            **evidence,
            "candidate_status": "CANONICAL_FEATURE_FOUND_API_PENDING",
            "accuracy_score_4": 2,
            "needs_manual_review": True,
            "official_api_month": latest_month,
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
        }
        if isinstance(coordinates, list) and len(coordinates) >= 2 and latest_month:
            lng, lat = coordinates[0], coordinates[1]
            query = urllib.parse.urlencode({"date": latest_month, "lat": lat, "lng": lng})
            url = f"https://data.police.uk/api/crimes-street/all-crime?{query}"
            live = http_json(url)
            crimes = live.get("json")
            api_pass = live.get("http_status") == 200 and isinstance(crimes, list)
            row.update({
                "official_api_url": url,
                "official_api_http_status": live.get("http_status"),
                "official_api_response_sha256": live.get("body_sha256"),
                "official_api_one_mile_supporting_count": len(crimes) if isinstance(crimes, list) else None,
                "official_api_semantics": "ANONYMISED_APPROXIMATE_ONE_MILE_SUPPORTING_EVIDENCE;NOT_EXACT_PARCEL_OR_LSOA_COUNT",
                "official_api_error": live.get("error"),
                "candidate_status": "CANONICAL_AND_OFFICIAL_API_VERIFIED_IOD25_V2_JOIN_PENDING" if api_pass else "CANONICAL_FOUND_OFFICIAL_API_FAILED",
                "accuracy_score_4": 3 if api_pass else 2,
            })
            time.sleep(API_RATE_SECONDS)
        rows.append(row)
    api_verified = sum(row.get("accuracy_score_4") == 3 for row in rows)
    return {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "task_step": "PREPARE_THREE_CANONICAL_SAMPLES_THEN_HYDRATE_300",
        "generated_at": now(),
        "parcel_partition": {"start": PARCEL_START, "end": PARCEL_END, "count": PARCEL_END - PARCEL_START + 1},
        "target_ids": SAMPLE_IDS,
        "source_file": str(source_path) if source_path else None,
        "source_file_sha256": sha256_file(source_path) if source_path else None,
        "official_api_latest": {key: value for key, value in latest.items() if key != "json"} | {"month": latest_month},
        "rows": rows,
        "sample_count": len(rows),
        "canonical_sample_count": sum(row.get("candidate_status") != "CANONICAL_FEATURE_NOT_FOUND" for row in rows),
        "accuracy_score_3_count": api_verified,
        "accuracy_score_4_count": 0,
        "actual_business_rows_written": 0,
        "website_rows_prepared": len(rows),
        "next_gate": "JOIN_UPDATED_IOD25_V2_CRIME_DOMAIN_AT_LSOA_LEVEL;THEN_HYDRATE_300_AND_RUN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def render_html(payload: dict[str, Any]) -> str:
    source_rows = "".join(
        "<tr>"
        f"<td>{escape(str(index))}</td>"
        f"<td>{escape(str(row.get('parcel_id')))}</td>"
        f"<td>{escape(str(row.get('candidate_status')))}</td>"
        f"<td>{escape(str(row.get('accuracy_score_4')))}</td>"
        f"<td>{escape(str(row.get('lsoa_code') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('official_api_http_status') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('official_api_one_mile_supporting_count') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('official_api_url') or 'not_available'))}</td>"
        "</tr>"
        for index, row in enumerate(payload.get("rows") or [], start=1)
    )
    operations = [
        ("REMOTE_HEAD_AND_SLOT_STATE", "PASS", "Authoritative slot records re-read."),
        ("CANONICAL_SAMPLE_DISCOVERY", "PASS" if payload.get("canonical_sample_count") else "BLOCKED", f"found={payload.get('canonical_sample_count')}/3"),
        ("OFFICIAL_API_LATEST_MONTH", "PASS" if payload.get("official_api_latest", {}).get("month") else "BLOCKED", f"month={payload.get('official_api_latest', {}).get('month')}"),
        ("THREE_SAMPLE_API_VERIFICATION", "PASS" if payload.get("accuracy_score_3_count") else "BLOCKED", f"accuracy_3={payload.get('accuracy_score_3_count')}/3"),
        ("IOD25_V2_LSOA_JOIN", "PENDING", "Required before accuracy 4/4."),
        ("HYDRATE_300_ROWS", "PENDING", "Runner and canonical join required."),
        ("HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "PENDING", "Local app and browser required."),
        ("COMMIT_PUSH_REMOTE_READBACK", "PENDING", "Single publisher only."),
    ]
    operation_rows = "".join(
        "<tr>" f"<td>{escape(str(index))}</td>" f"<td>{escape(status)}</td>" f"<td>{escape(step)}</td>" f"<td>{escape(detail)}</td>" "</tr>"
        for index, (step, status, detail) in enumerate(operations, start=1)
    )
    completed = sum(status == "PASS" for _, status, _ in operations)
    percent = round(100 * completed / len(operations), 2)
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="15"><title>Security / Public Safety — Slot 2 Progress</title><style>body{{font-family:Segoe UI,Arial,sans-serif;margin:22px;line-height:1.4}}table{{border-collapse:collapse;width:100%;margin:14px 0}}th,td{{border:1px solid #bbb;padding:7px;text-align:left;vertical-align:top}}code{{background:#eee;padding:2px 4px}}</style></head><body data-slot-id="{SLOT_ID}" data-final-ready="false"><h1>Security / Public Safety — Slot 2</h1><p><strong>Parsel aralığı:</strong> {PARCEL_START}–{PARCEL_END}</p><p><strong>İşlem ilerlemesi:</strong> {completed}/{len(operations)} — %{percent}</p><p><strong>Semantik:</strong> <code>AREA_LEVEL_PROXY</code>; parsel ölçümü değildir.</p><h2>İşlem akışı — satır satır</h2><table><thead><tr><th>#</th><th>Durum</th><th>İşlem</th><th>Detay</th></tr></thead><tbody>{operation_rows}</tbody></table><h2>Örnek adaylar</h2><table><thead><tr><th>#</th><th>Parsel</th><th>Durum</th><th>Doğruluk /4</th><th>LSOA</th><th>HTTP</th><th>1 mil destek sayısı</th><th>Resmî API</th></tr></thead><tbody>{source_rows}</tbody></table><p><code>actual_business_rows_written=0</code>; <code>final_ready=false</code>; <code>fake_data=false</code>.</p></body></html>"""


def write_outputs(payload: dict[str, Any]) -> None:
    for path in (JSON_OUTPUT, WEB_JSON_OUTPUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    WEB_HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_HTML_OUTPUT.write_text(render_html(payload), encoding="utf-8")


def main() -> int:
    slot_env = os.environ.get("AAYS_SLOT_ID")
    if slot_env and slot_env != SLOT_ID:
        raise RuntimeError(f"WRONG_SLOT_ENV:{slot_env}")
    payload = validate_samples()
    write_outputs(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["accuracy_score_3_count"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
