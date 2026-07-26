from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "security_public_safety_3"
TASK_VERSION = "4.1"
TARGET_IDS = [f"parcel_{value}" for value in range(61523, 61547)]
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
DATA_ROOT = REPO / "england_map_web" / "data"
OUT_ROOT = REPO / "docs" / "chatgpt_status" / "security_public_safety" / "runner_outputs"
WEB_ROOT = REPO / "outputs" / "england_program_parcel_matrix_20260629" / "security_public_safety_updates"
CACHE_ROOT = Path(tempfile.gettempdir()) / "aays_security_public_safety_slot3"

POLICE_LAST_UPDATED_URL = "https://data.police.uk/api/crime-last-updated"
IOD25_FILE7_V2_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
HISTORICAL_SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
HISTORICAL_SOURCE_REPO_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
HISTORICAL_SOURCE_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
HISTORICAL_CACHE_PATH = CACHE_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson"
PREFERRED_SOURCE_PATHS = [
    DATA_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson",
    DATA_ROOT / "parcel_security_scores_compact.geojson",
    DATA_ROOT / "parcel_security_scores.geojson",
    DATA_ROOT / "security_public_safety" / "parcel_security_scores_verified.geojson",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git(args: list[str], timeout: int = 300, stdout_handle=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=False,
        stdout=stdout_handle if stdout_handle is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def git_blob_sha(path: Path) -> str | None:
    try:
        result = run_git(["hash-object", str(path)], timeout=120)
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip() or None


def export_git_object(ref: str, destination: Path) -> dict:
    part = destination.with_suffix(destination.suffix + ".part")
    part.parent.mkdir(parents=True, exist_ok=True)
    part.unlink(missing_ok=True)
    evidence = {
        "ref": ref,
        "git_show_returncode": None,
        "stderr": None,
        "blob_sha": None,
        "verified": False,
    }
    try:
        with part.open("wb") as handle:
            result = run_git(["show", f"{ref}:{HISTORICAL_SOURCE_REPO_PATH}"], stdout_handle=handle)
        evidence["git_show_returncode"] = result.returncode
        evidence["stderr"] = result.stderr.decode("utf-8", errors="replace")[-2000:]
        if result.returncode != 0:
            part.unlink(missing_ok=True)
            return evidence
        evidence["blob_sha"] = git_blob_sha(part)
        evidence["verified"] = evidence["blob_sha"] == HISTORICAL_SOURCE_BLOB_SHA
        if not evidence["verified"]:
            part.unlink(missing_ok=True)
            return evidence
        os.replace(part, destination)
        return evidence
    except Exception as exc:
        part.unlink(missing_ok=True)
        evidence["stderr"] = str(exc)
        return evidence


def materialize_historical_source() -> tuple[Path | None, dict]:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "branch": HISTORICAL_SOURCE_BRANCH,
        "repo_path": HISTORICAL_SOURCE_REPO_PATH,
        "expected_blob_sha": HISTORICAL_SOURCE_BLOB_SHA,
        "cache_path": str(HISTORICAL_CACHE_PATH),
        "cache_hit": False,
        "fetch_attempted": False,
        "fetch_returncode": None,
        "fetch_stderr": None,
        "attempts": [],
        "verified": False,
        "error": None,
    }
    if HISTORICAL_CACHE_PATH.is_file():
        cached_sha = git_blob_sha(HISTORICAL_CACHE_PATH)
        if cached_sha == HISTORICAL_SOURCE_BLOB_SHA:
            evidence.update({"cache_hit": True, "cache_blob_sha": cached_sha, "verified": True})
            return HISTORICAL_CACHE_PATH, evidence
        HISTORICAL_CACHE_PATH.unlink(missing_ok=True)

    for ref in (f"origin/{HISTORICAL_SOURCE_BRANCH}", HISTORICAL_SOURCE_BRANCH):
        attempt = export_git_object(ref, HISTORICAL_CACHE_PATH)
        evidence["attempts"].append(attempt)
        if attempt["verified"]:
            evidence.update({"source_ref": ref, "verified": True})
            return HISTORICAL_CACHE_PATH, evidence

    evidence["fetch_attempted"] = True
    try:
        fetch = run_git(["fetch", "origin", HISTORICAL_SOURCE_BRANCH], timeout=600)
        evidence["fetch_returncode"] = fetch.returncode
        evidence["fetch_stderr"] = fetch.stderr.decode("utf-8", errors="replace")[-2000:]
    except Exception as exc:
        evidence["error"] = str(exc)
        return None, evidence

    if evidence["fetch_returncode"] == 0:
        attempt = export_git_object("FETCH_HEAD", HISTORICAL_CACHE_PATH)
        evidence["attempts"].append(attempt)
        if attempt["verified"]:
            evidence.update({"source_ref": "FETCH_HEAD", "verified": True})
            return HISTORICAL_CACHE_PATH, evidence

    evidence["error"] = "Exact canonical blob could not be materialized and verified."
    return None, evidence


def http_bytes(url: str, timeout: int = 180, attempts: int = 3) -> tuple[int, bytes]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"AAYS-security-public-safety-slot3/{TASK_VERSION}",
                "Accept": "application/json,text/csv,*/*",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == attempts:
                raise
        except Exception as exc:
            last_error = exc
            if attempt == attempts:
                raise
        time.sleep(1.5 * attempt)
    raise RuntimeError(str(last_error) if last_error else "HTTP request failed")


def http_json(url: str, timeout: int = 180) -> tuple[int, bytes, object]:
    status, body = http_bytes(url, timeout=timeout)
    return status, body, json.loads(body.decode("utf-8"))


def file_contains_targets(path: Path) -> bool:
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


def source_candidates(materialized_path: Path | None) -> list[Path]:
    ordered: list[Path] = []
    seen: set[Path] = set()
    if materialized_path and materialized_path.is_file():
        ordered.append(materialized_path)
        seen.add(materialized_path)
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


def locate_targets(materialized_path: Path | None) -> tuple[Path | None, dict[str, dict], list[dict]]:
    found: dict[str, dict] = {}
    audit: list[dict] = []
    for path in source_candidates(materialized_path):
        try:
            size = path.stat().st_size
        except OSError as exc:
            audit.append({"path": str(path), "decision": "STAT_FAILED", "error": str(exc)})
            continue
        if path.name == "parcel_security_scores_verified.geojson" and size < 1024 * 1024:
            audit.append({"path": str(path), "decision": "SKIP_KNOWN_SMALL_UNUSABLE_VERIFIED_OUTPUT"})
            continue
        if not file_contains_targets(path):
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
        "semantic_rule": "Crime fields are relative LSOA context; never convert rank, score or decile directly to an absolute parcel security percentage.",
    }
    matches: dict[str, dict] = {}
    if not lsoa_codes:
        return matches, evidence
    try:
        status, body = http_bytes(IOD25_FILE7_V2_URL)
        evidence.update({"http_status": status, "response_sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
        reader = csv.DictReader(io.StringIO(body.decode("utf-8-sig")))
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
                "iod25_crime_decile": source_row.get("Crime Decile (where 1 is most deprived 10% of LSOAs)"),
            }
        evidence["matched_lsoa_count"] = len(matches)
    except Exception as exc:
        evidence["error"] = str(exc)
    return matches, evidence


def request_area_evidence(lat: float, lng: float, month: str, cache: dict[str, dict]) -> dict:
    cache_key = f"{lat:.6f},{lng:.6f},{month}"
    if cache_key in cache:
        return cache[cache_key]
    query = urllib.parse.urlencode({"date": month, "lat": lat, "lng": lng})
    crime_url = f"https://data.police.uk/api/crimes-street/all-crime?{query}"
    outcomes_url = f"https://data.police.uk/api/outcomes-at-location?{query}"
    result = {
        "crime_url": crime_url,
        "crime_http_status": None,
        "crime_response_sha256": None,
        "crime_one_mile_supporting_count": None,
        "crime_error": None,
        "outcomes_url": outcomes_url,
        "outcomes_http_status": None,
        "outcomes_response_sha256": None,
        "outcomes_one_mile_supporting_count": None,
        "outcomes_error": None,
        "semantic_rule": "Both endpoints use anonymised approximate locations; counts are supporting area evidence, never exact parcel counts.",
    }
    try:
        status, body, payload = http_json(crime_url)
        result.update({
            "crime_http_status": status,
            "crime_response_sha256": hashlib.sha256(body).hexdigest(),
            "crime_one_mile_supporting_count": len(payload) if isinstance(payload, list) else None,
        })
    except Exception as exc:
        result["crime_error"] = str(exc)
    time.sleep(0.35)
    try:
        status, body, payload = http_json(outcomes_url)
        result.update({
            "outcomes_http_status": status,
            "outcomes_response_sha256": hashlib.sha256(body).hexdigest(),
            "outcomes_one_mile_supporting_count": len(payload) if isinstance(payload, list) else None,
        })
    except Exception as exc:
        result["outcomes_error"] = str(exc)
    time.sleep(0.35)
    cache[cache_key] = result
    return result


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    materialized_path, materialization_evidence = materialize_historical_source()
    source_path, features, source_audit = locate_targets(materialized_path)

    police_latest = {"url": POLICE_LAST_UPDATED_URL, "http_status": None, "month": None, "response_sha256": None, "error": None}
    try:
        status, body, payload = http_json(POLICE_LAST_UPDATED_URL)
        police_latest.update({
            "http_status": status,
            "month": str(payload.get("date", ""))[:7],
            "response_sha256": hashlib.sha256(body).hexdigest(),
        })
    except Exception as exc:
        police_latest["error"] = str(exc)

    lsoa_codes = {
        str((feature.get("properties") or {}).get("security_lsoa_code"))
        for feature in features.values()
        if (feature.get("properties") or {}).get("security_lsoa_code")
    }
    iod_rows, iod_evidence = load_iod25_rows(lsoa_codes)
    api_cache: dict[str, dict] = {}
    rows: list[dict] = []

    for line, parcel_id in enumerate(TARGET_IDS, start=1):
        feature = features.get(parcel_id)
        if not feature:
            rows.append({
                "line": line,
                "parcel_id": parcel_id,
                "candidate_status": "CANONICAL_FEATURE_NOT_FOUND",
                "canonical_gate": False,
                "crime_api_gate": False,
                "outcomes_api_gate": False,
                "iod25_gate": False,
                "accuracy_score_4": 0,
                "needs_manual_review": True,
                "security_score_percent": None,
            })
            continue

        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") if geometry.get("type") == "Point" else None
        lsoa_code = props.get("security_lsoa_code")
        existing_score = props.get("safety_score")
        if existing_score is None:
            existing_score = props.get("security_score")
        canonical_gate = bool(coordinates and existing_score is not None)

        area_evidence = None
        crime_gate = False
        outcomes_gate = False
        if coordinates and police_latest.get("month"):
            lng, lat = coordinates
            area_evidence = request_area_evidence(float(lat), float(lng), str(police_latest["month"]), api_cache)
            crime_gate = bool(area_evidence.get("crime_http_status") == 200 and area_evidence.get("crime_response_sha256"))
            outcomes_gate = bool(area_evidence.get("outcomes_http_status") == 200 and area_evidence.get("outcomes_response_sha256"))

        iod_row = iod_rows.get(str(lsoa_code)) if lsoa_code else None
        iod_gate = bool(iod_row)
        accuracy = sum((canonical_gate, crime_gate, outcomes_gate, iod_gate))
        status_by_accuracy = {
            0: "NO_ACCEPTANCE_GATE_PASSED",
            1: "ONE_OF_FOUR_GATES_PASSED",
            2: "TWO_OF_FOUR_GATES_PASSED",
            3: "THREE_OF_FOUR_GATES_PASSED",
            4: "CANONICAL_APIS_IOD25_V2_VERIFIED",
        }
        row = {
            "line": line,
            "parcel_id": parcel_id,
            "candidate_status": status_by_accuracy[accuracy],
            "security_score_percent": existing_score,
            "score_origin": "preexisting_canonical_score_not_recomputed",
            "security_level": props.get("safety_level") or props.get("security_level"),
            "lsoa_code": lsoa_code,
            "lsoa_name": props.get("security_lsoa_name"),
            "spatial_match_method": props.get("spatial_match_method"),
            "canonical_confidence_score": props.get("confidence_score"),
            "canonical_spatial_score": props.get("spatial_score"),
            "geometry": geometry,
            "official_api_month": police_latest.get("month"),
            "canonical_gate": canonical_gate,
            "crime_api_gate": crime_gate,
            "outcomes_api_gate": outcomes_gate,
            "iod25_gate": iod_gate,
            "accuracy_score_4": accuracy,
            "needs_manual_review": accuracy != 4,
        }
        if area_evidence:
            row["area_evidence"] = area_evidence
        if iod_row:
            row["iod25_v2"] = iod_row
        rows.append(row)

    accuracy_ge_3 = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in rows if row.get("accuracy_score_4") == 4)
    output = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "task_version": TASK_VERSION,
        "generated_at": utc_now(),
        "parcel_partition": {"start": 61523, "end": 92283, "count": 30761},
        "target_parcels": TARGET_IDS,
        "historical_source_materialization": materialization_evidence,
        "source_file": str(source_path) if source_path else None,
        "source_file_git_blob_sha": git_blob_sha(source_path) if source_path else None,
        "source_file_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path else None,
        "source_discovery_audit": source_audit,
        "official_api_latest": police_latest,
        "iod25_v2_evidence": iod_evidence,
        "acceptance_gates": [
            "exact historical canonical blob SHA and Point geometry plus non-null preexisting score",
            "explicit latest-month street crimes HTTP 200 response SHA256",
            "explicit latest-month outcomes-at-location HTTP 200 response SHA256",
            "corrected IoD2025 File 7 v2 LSOA Crime join",
        ],
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
        "person_level_data": False,
        "final_ready": False,
    }
    sample_path = OUT_ROOT / "security_public_safety_3_sample_candidates_v4_latest.json"
    web_path = WEB_ROOT / "security_public_safety_3_rows_latest.json"
    text = json.dumps(output, ensure_ascii=False, indent=2)
    sample_path.write_text(text, encoding="utf-8")
    web_path.write_text(text, encoding="utf-8")
    print(f"SLOT_ID={SLOT_ID}")
    print(f"TASK_VERSION={TASK_VERSION}")
    print(f"CANONICAL_BLOB_VERIFIED={materialization_evidence.get('verified')}")
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
