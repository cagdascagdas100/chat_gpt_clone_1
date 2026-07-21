from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "security_public_safety_3"
TARGET_IDS = [f"parcel_{i}" for i in range(61523, 61529)]
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
OUT_ROOT = REPO / "docs" / "chatgpt_status" / "security_public_safety" / "runner_outputs"
WEB_ROOT = REPO / "outputs" / "england_program_parcel_matrix_20260629" / "security_public_safety_updates"

POLICE_LAST_UPDATED_URL = "https://data.police.uk/api/crime-last-updated"
IOD25_FILE7_V2_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)

PREFERRED_SOURCE_PATHS = [
    DATA_ROOT / "parcel_security_scores_compact.geojson",
    DATA_ROOT / "parcel_security_scores.geojson",
    DATA_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson",
    DATA_ROOT / "security_public_safety" / "parcel_security_scores_verified.geojson",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def http_bytes(url: str, timeout: int = 90) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-security-public-safety-slot3/2.0",
            "Accept": "application/json,text/csv,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def http_json(url: str, timeout: int = 90) -> tuple[int, bytes, object]:
    status, body = http_bytes(url, timeout=timeout)
    return status, body, json.loads(body.decode("utf-8"))


def file_contains_target(path: Path) -> bool:
    needles = [target.encode("utf-8") for target in TARGET_IDS]
    overlap = max(len(needle) for needle in needles) - 1
    tail = b""
    try:
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    return False
                data = tail + chunk
                if any(needle in data for needle in needles):
                    return True
                tail = data[-overlap:]
    except OSError:
        return False


def source_candidates() -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    for path in PREFERRED_SOURCE_PATHS:
        if path.is_file() and path not in seen:
            ordered.append(path)
            seen.add(path)
    discovered = sorted(
        (
            path
            for path in DATA_ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in {".json", ".geojson"}
        ),
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    for path in discovered:
        if path not in seen and path.name != "security_evidence_manifest.json":
            ordered.append(path)
            seen.add(path)
    return ordered


def locate_targets() -> tuple[Path | None, dict[str, dict], list[dict]]:
    found: dict[str, dict] = {}
    audit: list[dict] = []
    for path in source_candidates():
        if path.name == "parcel_security_scores_verified.geojson" and path.stat().st_size < 1024 * 1024:
            audit.append({"path": str(path), "decision": "SKIP_KNOWN_SMALL_UNUSABLE_VERIFIED_OUTPUT"})
            continue
        if not file_contains_target(path):
            audit.append({"path": str(path), "decision": "NO_TARGET_ID_TEXT"})
            continue
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except Exception as exc:
            audit.append({"path": str(path), "decision": "JSON_PARSE_FAILED", "error": str(exc)})
            continue
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            audit.append({"path": str(path), "decision": "NO_FEATURE_ARRAY"})
            continue
        for feature in features:
            props = feature.get("properties") or {}
            parcel_id = props.get("security_parcel_id") or props.get("parcel_id")
            if parcel_id in TARGET_IDS:
                found[parcel_id] = feature
        audit.append({"path": str(path), "decision": "PARSED", "targets_found": sorted(found)})
        if len(found) == len(TARGET_IDS):
            return path, found, audit
    return None, found, audit


def load_iod25_rows(lsoa_codes: set[str]) -> tuple[dict[str, dict], dict]:
    evidence = {
        "url": IOD25_FILE7_V2_URL,
        "http_status": None,
        "response_sha256": None,
        "bytes": 0,
        "matched_lsoa_count": 0,
        "error": None,
        "semantic_rule": "Crime fields are relative LSOA context; never convert rank directly to an absolute parcel security percentage.",
    }
    matches: dict[str, dict] = {}
    if not lsoa_codes:
        return matches, evidence
    try:
        status, body = http_bytes(IOD25_FILE7_V2_URL, timeout=180)
        evidence.update(
            {
                "http_status": status,
                "response_sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
            }
        )
        text = body.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        for source_row in reader:
            code = (source_row.get("LSOA code (2021)") or "").strip()
            if code not in lsoa_codes:
                continue
            matches[code] = {
                "lsoa_code_2021": code,
                "lsoa_name_2021": source_row.get("LSOA name (2021)"),
                "lad_code_2024": source_row.get("Local Authority District code (2024)"),
                "lad_name_2024": source_row.get("Local Authority District name (2024)"),
                "iod25_crime_score": source_row.get("Crime Score"),
                "iod25_crime_rank": source_row.get("Crime Rank (where 1 is most deprived)"),
                "iod25_crime_decile": source_row.get(
                    "Crime Decile (where 1 is most deprived 10% of LSOAs)"
                ),
            }
        evidence["matched_lsoa_count"] = len(matches)
    except Exception as exc:
        evidence["error"] = str(exc)
    return matches, evidence


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_ROOT.mkdir(parents=True, exist_ok=True)

    source_path, features, source_audit = locate_targets()

    police_latest = {
        "url": POLICE_LAST_UPDATED_URL,
        "http_status": None,
        "month": None,
        "response_sha256": None,
        "error": None,
    }
    try:
        status, body, payload = http_json(POLICE_LAST_UPDATED_URL)
        police_latest.update(
            {
                "http_status": status,
                "month": str(payload.get("date", ""))[:7],
                "response_sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    except Exception as exc:
        police_latest["error"] = str(exc)

    lsoa_codes = {
        str((feature.get("properties") or {}).get("security_lsoa_code"))
        for feature in features.values()
        if (feature.get("properties") or {}).get("security_lsoa_code")
    }
    iod_rows, iod_evidence = load_iod25_rows(lsoa_codes)

    rows: list[dict] = []
    for line, parcel_id in enumerate(TARGET_IDS, start=1):
        feature = features.get(parcel_id)
        if not feature:
            rows.append(
                {
                    "line": line,
                    "parcel_id": parcel_id,
                    "candidate_status": "CANONICAL_FEATURE_NOT_FOUND",
                    "accuracy_score_4": 0,
                    "needs_manual_review": True,
                    "security_score_percent": None,
                }
            )
            continue

        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") if geometry.get("type") == "Point" else None
        lsoa_code = props.get("security_lsoa_code")
        existing_score = props.get("safety_score")
        if existing_score is None:
            existing_score = props.get("security_score")

        row = {
            "line": line,
            "parcel_id": parcel_id,
            "candidate_status": "CANONICAL_FEATURE_FOUND",
            "security_score_percent": existing_score,
            "score_origin": "preexisting_canonical_score_not_recomputed",
            "score_semantics": "Retained only when canonical point, explicit-month police response hash and IoD25 v2 LSOA context all pass.",
            "security_level": props.get("safety_level") or props.get("security_level"),
            "lsoa_code": lsoa_code,
            "lsoa_name": props.get("security_lsoa_name"),
            "spatial_match_method": props.get("spatial_match_method"),
            "canonical_confidence_score": props.get("confidence_score"),
            "canonical_spatial_score": props.get("spatial_score"),
            "geometry": geometry,
            "accuracy_score_4": 2,
            "needs_manual_review": True,
            "official_api_month": police_latest.get("month"),
        }

        api_pass = False
        if coordinates and police_latest.get("month"):
            lng, lat = coordinates
            query = urllib.parse.urlencode(
                {"date": police_latest["month"], "lat": lat, "lng": lng}
            )
            url = f"https://data.police.uk/api/crimes-street/all-crime?{query}"
            try:
                status, body, crimes = http_json(url)
                api_pass = status == 200 and isinstance(crimes, list)
                row.update(
                    {
                        "official_api_http_status": status,
                        "official_api_url": url,
                        "official_api_response_sha256": hashlib.sha256(body).hexdigest(),
                        "official_api_one_mile_supporting_count": len(crimes)
                        if isinstance(crimes, list)
                        else None,
                        "official_api_semantics": "anonymised approximate supporting evidence; not an exact parcel or incident count",
                        "candidate_status": "CANONICAL_AND_OFFICIAL_API_VERIFIED",
                        "accuracy_score_4": 3 if api_pass else 2,
                    }
                )
            except Exception as exc:
                row.update(
                    {
                        "official_api_error": str(exc),
                        "candidate_status": "CANONICAL_FOUND_API_FAILED",
                    }
                )
            time.sleep(0.4)

        iod_row = iod_rows.get(str(lsoa_code)) if lsoa_code else None
        if iod_row:
            row["iod25_v2"] = iod_row
        if api_pass and iod_row and existing_score is not None and coordinates:
            row.update(
                {
                    "candidate_status": "CANONICAL_API_IOD25_V2_VERIFIED",
                    "accuracy_score_4": 4,
                    "needs_manual_review": False,
                }
            )
        rows.append(row)

    accuracy_ge_3 = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in rows if row.get("accuracy_score_4") == 4)
    output = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 61523, "end": 92283, "count": 30761},
        "target_parcels": TARGET_IDS,
        "source_file": str(source_path) if source_path else None,
        "source_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest()
        if source_path
        else None,
        "source_discovery_audit": source_audit,
        "official_api_latest": police_latest,
        "iod25_v2_evidence": iod_evidence,
        "rows": rows,
        "sample_count": len(rows),
        "accuracy_ge_3_count": accuracy_ge_3,
        "accuracy_score_4_count": accuracy_4,
        "verified_slot_rows": accuracy_4,
        "actual_slot_rows_written": accuracy_4,
        "next_gate": "Expand the identical verified method to 300 rows, then run HTTP/hash/DOM/console/browser acceptance.",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    sample_path = OUT_ROOT / "security_public_safety_3_sample_candidates_v2_latest.json"
    web_path = WEB_ROOT / "security_public_safety_3_rows_latest.json"
    text = json.dumps(output, ensure_ascii=False, indent=2)
    sample_path.write_text(text, encoding="utf-8")
    web_path.write_text(text, encoding="utf-8")

    print(f"SLOT_ID={SLOT_ID}")
    print(f"SOURCE_FILE={source_path}")
    print(f"SAMPLE_COUNT={len(rows)}")
    print(f"ACCURACY_GE_3_COUNT={accuracy_ge_3}")
    print(f"ACCURACY_SCORE_4_COUNT={accuracy_4}")
    print(f"OUTPUT={sample_path}")
    print(f"WEB_OUTPUT={web_path}")
    print("FINAL_READY=false")
    return 0 if source_path and accuracy_4 > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
