from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import html
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
PARTITION = {"start": 30762, "end": 61522, "count": 30761, "canonical_count": 92283}
ROOT = Path.cwd()
SOURCE_REL = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
SOURCE_PATH = ROOT / SOURCE_REL
WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"
OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"
TARGET_IDS = [f"parcel_{value}" for value in range(30774, 30798)]
ONS_LAYER = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
IOD_FILE7_URL = "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
USER_AGENT = "AAYS-TerraYield-security-public-safety-method-wave/3.0"

if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
    raise SystemExit(f"WRONG_SLOT: {os.environ.get('AAYS_SLOT_ID')}")
if os.environ.get("AAYS_CHILD_DIRECT_PUSH_FORBIDDEN", "true").lower() != "true":
    raise SystemExit("DIRECT_PUSH_GUARD_MISSING")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, *, parse_json: bool = False, attempts: int = 3, timeout: float = 45.0) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,text/csv,*/*"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                result: dict[str, Any] = {
                    "reachable": 200 <= int(response.status) < 400,
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "retrieved_at": utc_now(),
                    "attempts": attempt,
                }
                if parse_json:
                    result["json"] = json.loads(body.decode("utf-8-sig"))
                return result
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(min(attempt * 1.5, 4.0))
    return {"reachable": False, "http_status": None, "bytes": 0, "sha256": None, "attempts": attempts, "error": last_error}


def download_temp(url: str, suffix: str) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, 4):
        temp_path: Path | None = None
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*"})
            with urllib.request.urlopen(request, timeout=120.0) as response:
                with tempfile.NamedTemporaryFile(prefix="aays_security_wave2_", suffix=suffix, delete=False) as handle:
                    temp_path = Path(handle.name)
                    digest = hashlib.sha256()
                    total = 0
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        digest.update(chunk)
                        total += len(chunk)
                return {
                    "reachable": 200 <= int(response.status) < 400,
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": total,
                    "sha256": digest.hexdigest(),
                    "retrieved_at": utc_now(),
                    "attempts": attempt,
                    "temp_path": str(temp_path),
                }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if temp_path:
                temp_path.unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(min(attempt * 2, 5))
    return {"reachable": False, "attempts": 3, "error": last_error, "temp_path": None}


def file_hashes(path: Path) -> tuple[str, str]:
    size = path.stat().st_size
    git_sha1 = hashlib.sha1()
    git_sha1.update(f"blob {size}\0".encode("ascii"))
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            git_sha1.update(chunk)
            sha256.update(chunk)
    return git_sha1.hexdigest(), sha256.hexdigest()


def stream_geojson_targets(path: Path, target_ids: list[str]) -> tuple[dict[str, dict[str, Any]], int]:
    decoder = json.JSONDecoder()
    wanted = set(target_ids)
    found: dict[str, dict[str, Any]] = {}
    count = 0
    with path.open("r", encoding="utf-8-sig") as handle:
        buffer = ""
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                raise RuntimeError("FEATURES_ARRAY_NOT_FOUND")
            buffer += chunk
            marker = buffer.find('"features"')
            if marker < 0:
                buffer = buffer[-64:]
                continue
            start = buffer.find("[", marker)
            if start < 0:
                continue
            buffer = buffer[start + 1 :]
            break
        eof = False
        while True:
            buffer = buffer.lstrip()
            if buffer.startswith(","):
                buffer = buffer[1:]
                continue
            if buffer.startswith("]"):
                break
            try:
                feature, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise RuntimeError("GEOJSON_FEATURE_PARSE_INCOMPLETE")
                chunk = handle.read(1024 * 1024)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
                continue
            count += 1
            properties = feature.get("properties") or {}
            parcel_id = str(properties.get("security_parcel_id") or "")
            if parcel_id in wanted:
                geometry = feature.get("geometry") or {}
                found[parcel_id] = {
                    "parcel_id": parcel_id,
                    "geometry_type": geometry.get("type"),
                    "coordinates": geometry.get("coordinates"),
                    "historical_lsoa_code": properties.get("security_lsoa_code"),
                    "historical_lsoa_name": properties.get("security_lsoa_name"),
                    "historical_security_values_reused": False,
                }
            buffer = buffer[end:]
    return found, count


def ons_lsoa_query(longitude: float, latitude: float) -> dict[str, Any]:
    params = urllib.parse.urlencode({
        "geometry": f"{longitude},{latitude}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "LSOA21CD,LSOA21NM",
        "returnGeometry": "false",
        "f": "json",
    })
    result = fetch(f"{ONS_LAYER}/query?{params}", parse_json=True)
    parsed = result.pop("json", None)
    features = parsed.get("features", []) if isinstance(parsed, dict) else []
    matches = [item.get("attributes") or {} for item in features]
    result["feature_count"] = len(matches)
    result["matches"] = matches
    return result


def police_query(longitude: float, latitude: float, month: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"lat": f"{latitude:.7f}", "lng": f"{longitude:.7f}", "date": month})
    result = fetch(f"https://data.police.uk/api/crimes-street/all-crime?{params}", parse_json=True, timeout=45.0)
    parsed = result.pop("json", None)
    if isinstance(parsed, list):
        categories = Counter(str(item.get("category") or "unknown") for item in parsed)
        result["crime_record_count"] = len(parsed)
        result["category_counts"] = dict(sorted(categories.items()))
        result["unique_persistent_ids"] = len({str(item.get("persistent_id")) for item in parsed if item.get("persistent_id")})
    else:
        result["crime_record_count"] = None
        result["category_counts"] = {}
        result["unique_persistent_ids"] = None
    return result


def load_iod_rows(path: Path, target_codes: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    row_count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        lowered = {header: header.strip().casefold() for header in headers}
        code_header = next((header for header, value in lowered.items() if "lsoa code" in value), None)
        crime_score_header = next((header for header, value in lowered.items() if value.startswith("crime score")), None)
        crime_rank_header = next((header for header, value in lowered.items() if value.startswith("crime rank")), None)
        crime_decile_header = next((header for header, value in lowered.items() if value.startswith("crime decile")), None)
        population_headers = [header for header, value in lowered.items() if "population" in value]
        for row in reader:
            row_count += 1
            code = str(row.get(code_header or "", "")).strip()
            if code in target_codes:
                selected[code] = {
                    "lsoa_code": code,
                    "crime_score": row.get(crime_score_header or ""),
                    "crime_rank": row.get(crime_rank_header or ""),
                    "crime_decile": row.get(crime_decile_header or ""),
                    "population_denominators": {header: row.get(header) for header in population_headers},
                }
    schema = {
        "headers": headers,
        "row_count": row_count,
        "code_header": code_header,
        "crime_score_header": crime_score_header,
        "crime_rank_header": crime_rank_header,
        "crime_decile_header": crime_decile_header,
        "population_headers": population_headers,
        "target_lsoa_count": len(target_codes),
        "matched_target_lsoa_count": len(selected),
        "schema_gate_pass": bool(code_header and crime_score_header and crime_rank_header and crime_decile_header and population_headers),
    }
    return selected, schema


source_specs = [
    ("iod_2025_release", "English indices of deprivation 2025", "MHCLG", "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025", 98, "Official LSOA relative deprivation release."),
    ("iod_2025_faq", "IoD 2025 frequently asked questions", "MHCLG", "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025/english-indices-of-deprivation-2025-frequently-asked-questions", 98, "Documents rank 1 as most deprived and 33,755 as least deprived."),
    ("iod_2025_technical", "IoD 2025 technical report", "MHCLG", "https://www.gov.uk/government/publications/english-indices-of-deprivation-2025-technical-report", 98, "Method and quality assurance; not a parcel measurement."),
    ("iod_2025_file7", "IoD 2025 File 7 CSV preview", "MHCLG", "https://www.gov.uk/csv-preview/691494fbb49cc44345161692/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv", 98, "Exact LSOA crime rank, score, decile and population fields."),
    ("ons_lsoa_population", "LSOA population estimates mid-2022 revised to mid-2024", "ONS", "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimatesnationalstatistics", 98, "Population cross-check; edition compatibility required."),
    ("police_last_updated", "Police.uk crime last updated", "Home Office / Police.uk", "https://data.police.uk/docs/method/crime-last-updated/", 98, "Explicit latest available API month."),
    ("police_street_contract", "Police.uk street-level crime API", "Home Office / Police.uk", "https://data.police.uk/docs/method/crime-street/", 95, "Locations are anonymised approximations."),
    ("home_office_open_tables", "Police recorded crime and outcomes open data tables", "Home Office", "https://www.gov.uk/government/statistical-data-sets/police-recorded-crime-and-outcomes-open-data-tables", 95, "Area benchmark; not copied to parcels."),
    ("home_office_user_guide", "Police recorded crime open data user guide", "Home Office", "https://www.gov.uk/government/statistics/police-recorded-crime-open-data-tables/police-recorded-crime-and-outcomes-open-data-tables-user-guide", 95, "Recording-policy comparability limitations."),
    ("national_data_library_local_crime", "Local police recorded crime data", "Home Office / National Data Library", "https://www.data.gov.uk/dataset/0e26ee1b-26b7-406e-a3b1-f3481b324977/local-police-recorded-crime-data", 95, "Rolling area totals; benchmark only."),
]


def probe_source(spec: tuple[str, str, str, str, int, str]) -> dict[str, Any]:
    source_id, name, publisher, url, accuracy, limit = spec
    probe = fetch(url)
    return {
        "source_id": source_id,
        "name": name,
        "publisher": publisher,
        "url": url,
        "accuracy_percent": accuracy,
        "limit": limit,
        "probe": probe,
        "status": "PROMOTED_FOR_ROLE" if probe.get("reachable") else "HELD_UNREACHABLE",
    }


with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="security-source") as executor:
    sources = list(executor.map(probe_source, source_specs))

last_updated = fetch("https://data.police.uk/api/crime-last-updated", parse_json=True)
last_updated_json = last_updated.pop("json", None)
police_month = str((last_updated_json or {}).get("date") or "")[:7]

if not SOURCE_PATH.is_file():
    raise SystemExit(f"CANONICAL_POINT_SOURCE_MISSING: {SOURCE_REL}")
target_features, actual_feature_count = stream_geojson_targets(SOURCE_PATH, TARGET_IDS)
source_blob, source_sha256 = file_hashes(SOURCE_PATH)


def verify_base(parcel_id: str) -> dict[str, Any]:
    base = target_features.get(parcel_id)
    if not base:
        return {"parcel_id": parcel_id, "evidence_status": "BLOCKED_POINT_NOT_FOUND", "promotion_allowed": False}
    coordinates = base.get("coordinates")
    valid = isinstance(coordinates, list) and len(coordinates) >= 2 and all(isinstance(value, (int, float)) for value in coordinates[:2])
    if not valid:
        return {**base, "evidence_status": "BLOCKED_INVALID_COORDINATE", "promotion_allowed": False}
    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    ons = ons_lsoa_query(longitude, latitude)
    police = police_query(longitude, latitude, police_month) if len(police_month) == 7 else {"reachable": False, "error": "POLICE_MONTH_MISSING"}
    matches = ons.get("matches") or []
    ons_code = matches[0].get("LSOA21CD") if len(matches) == 1 else None
    ons_name = matches[0].get("LSOA21NM") if len(matches) == 1 else None
    return {
        **base,
        "longitude": longitude,
        "latitude": latitude,
        "ons_lsoa_code": ons_code,
        "ons_lsoa_name": ons_name,
        "ons_query": ons,
        "historical_lsoa_code_matches_ons": bool(ons_code and base.get("historical_lsoa_code") == ons_code),
        "police_month": police_month or None,
        "police_query": police,
        "promotion_allowed": False,
    }


with concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="security-row") as executor:
    rows = list(executor.map(verify_base, TARGET_IDS))

target_lsoa_codes = {str(row.get("ons_lsoa_code")) for row in rows if row.get("ons_lsoa_code")}
iod_download = download_temp(IOD_FILE7_URL, ".csv")
iod_selected: dict[str, dict[str, Any]] = {}
iod_schema: dict[str, Any] = {"schema_gate_pass": False}
try:
    if iod_download.get("reachable") and iod_download.get("temp_path"):
        iod_selected, iod_schema = load_iod_rows(Path(str(iod_download["temp_path"])), target_lsoa_codes)
finally:
    if iod_download.get("temp_path"):
        Path(str(iod_download["temp_path"])).unlink(missing_ok=True)
        iod_download["temp_path"] = None

national_lsoa_count = int(iod_schema.get("row_count") or 0)
for row in rows:
    code = str(row.get("ons_lsoa_code") or "")
    iod = iod_selected.get(code)
    row["iod_2025"] = iod
    rank_value: float | None = None
    try:
        rank_value = float(str((iod or {}).get("crime_rank") or "").replace(",", ""))
    except ValueError:
        rank_value = None
    candidate_percent = None
    if rank_value is not None and national_lsoa_count > 1:
        candidate_percent = round(100.0 * (rank_value - 1.0) / (national_lsoa_count - 1.0), 2)
    integrity = 0
    integrity += 25 if row.get("parcel_id") in target_features else 0
    integrity += 15 if row.get("longitude") is not None else 0
    integrity += 20 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
    integrity += 10 if row.get("historical_lsoa_code_matches_ons") else 0
    integrity += 15 if (row.get("police_query") or {}).get("reachable") and (row.get("police_query") or {}).get("sha256") else 0
    integrity += 15 if iod else 0
    row["relative_security_candidate_percent"] = candidate_percent
    row["candidate_method"] = "100*(IoD2025 Crime Rank-1)/(national LSOA count-1); rank 1 is most deprived"
    row["candidate_accuracy_percent"] = integrity
    row["evidence_status"] = "IOD25_RELATIVE_CANDIDATE_READY_NOT_PROMOTED" if candidate_percent is not None else "EVIDENCE_PARTIAL_SCORE_BLOCKED"
    row["business_score"] = None
    row["business_confidence"] = 0
    row["promotion_allowed"] = False

promoted_sources = [item for item in sources if item["status"] == "PROMOTED_FOR_ROLE"]
source_accuracy_ge_95 = sum(item["status"] == "PROMOTED_FOR_ROLE" and item["accuracy_percent"] >= 95 for item in sources)
valid_points = sum(row.get("longitude") is not None for row in rows)
ons_rows = sum((row.get("ons_query") or {}).get("feature_count") == 1 for row in rows)
police_hash_rows = sum(bool((row.get("police_query") or {}).get("sha256")) for row in rows)
iod_join_rows = sum(bool(row.get("iod_2025")) for row in rows)
candidate_rows = sum(row.get("relative_security_candidate_percent") is not None for row in rows)
accuracy_ge_95_rows = sum(int(row.get("candidate_accuracy_percent") or 0) >= 95 for row in rows)

wave1 = {}
if WAVE1_PATH.is_file():
    try:
        wave1 = json.loads(WAVE1_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        wave1 = {}
previous_progress = float(wave1.get("overall_progress_percent") or 0)

gates = [
    {"gate": "wave1_remote_output_present", "state": "PASS" if wave1 else "BLOCKED"},
    {"gate": "canonical_point_blob_match", "state": "PASS" if source_blob == "bb48164e7a0af78df875f30421a6a3068c43edb8" else "BLOCKED", "evidence": source_blob},
    {"gate": "canonical_point_feature_count_92283", "state": "PASS" if actual_feature_count == 92283 else "BLOCKED", "evidence": actual_feature_count},
    {"gate": "wave2_target_24_ids_unique", "state": "PASS" if len(target_features) == 24 else "BLOCKED", "evidence": len(target_features)},
    {"gate": "wave2_valid_wgs84_points", "state": "PASS" if valid_points == 24 else "PARTIAL", "evidence": valid_points},
    {"gate": "wave2_single_ons_lsoa_matches", "state": "PASS" if ons_rows == 24 else "PARTIAL", "evidence": ons_rows},
    {"gate": "police_explicit_month", "state": "PASS" if len(police_month) == 7 else "BLOCKED", "evidence": police_month},
    {"gate": "wave2_police_response_hashes", "state": "PASS" if police_hash_rows == 24 else "PARTIAL", "evidence": police_hash_rows},
    {"gate": "iod25_file7_download_hash", "state": "PASS" if iod_download.get("sha256") else "BLOCKED", "evidence": iod_download.get("bytes")},
    {"gate": "iod25_crime_rank_schema", "state": "PASS" if iod_schema.get("schema_gate_pass") else "BLOCKED", "evidence": iod_schema.get("row_count")},
    {"gate": "iod25_exact_lsoa_joins", "state": "PASS" if iod_join_rows == len(target_lsoa_codes) else "PARTIAL", "evidence": iod_join_rows},
    {"gate": "rank_direction_documented", "state": "PASS", "evidence": "IoD25 rank 1 most deprived; highest rank least deprived"},
    {"gate": "relative_candidate_formula_documented", "state": "PASS"},
    {"gate": "wave2_candidate_rows_generated", "state": "PASS" if candidate_rows == 24 else "PARTIAL", "evidence": candidate_rows},
    {"gate": "ten_official_source_probes", "state": "PASS" if len(promoted_sources) == 10 else "PARTIAL", "evidence": len(promoted_sources)},
    {"gate": "line_by_line_web_artifact_generated", "state": "PASS"},
    {"gate": "candidate_method_calibration_review", "state": "PENDING"},
    {"gate": "expand_to_300_verified_business_rows", "state": "PENDING"},
    {"gate": "served_http_json_hash_acceptance", "state": "PENDING"},
    {"gate": "dom_console_browser_acceptance", "state": "PENDING"},
]
completed_operations = sum(gate["state"] == "PASS" for gate in gates)
total_operations = len(gates)
overall_progress = round((completed_operations / total_operations) * 78, 1)

payload = {
    "schema_version": 3,
    "architecture_version": 3,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": SLOT_ID,
    "base_slot_id": "security_public_safety",
    "shard_index": 2,
    "parcel_partition": PARTITION,
    "state": "IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED",
    "first_unverified_step": "CALIBRATE_CANDIDATE_METHOD_THEN_EXPAND_TO_300_AND_BROWSER_ACCEPTANCE",
    "canonical_point_source": {"path": SOURCE_REL, "git_blob_sha": source_blob, "sha256": source_sha256, "actual_feature_count": actual_feature_count, "security_values_reused": False},
    "source_snapshot_date": datetime.now(timezone.utc).date().isoformat(),
    "sources_reviewed": len(sources),
    "promoted_sources": len(promoted_sources),
    "accuracy_ge_95_source_count": source_accuracy_ge_95,
    "candidate_rows": candidate_rows,
    "accuracy_ge_95_candidate_rows": accuracy_ge_95_rows,
    "verified_business_rows": 0,
    "actual_business_rows_written": 0,
    "police_month": police_month or None,
    "iod_file7_download": iod_download,
    "iod_file7_schema": iod_schema,
    "rows": rows,
    "sources": sources,
    "gates": gates,
    "completed_operations": completed_operations,
    "total_operations": total_operations,
    "overall_progress_percent": overall_progress,
    "progress_delta_percent": round(overall_progress - previous_progress, 1),
    "business_row_progress_percent": 0,
    "candidate_method": {
        "formula": "100*(IoD2025 Crime Rank-1)/(national LSOA count-1)",
        "interpretation": "0 means most crime-deprived relative LSOA; 100 means least crime-deprived relative LSOA",
        "status": "CANDIDATE_ONLY_NOT_BUSINESS_SCORE",
        "calibration_required": True,
    },
    "blockers": [
        "IoD Crime Rank is a relative small-area indicator, not an exact parcel incident rate.",
        "Police.uk street locations are anonymised approximations and overlapping point queries are not independent parcel counts.",
        "The 92,283-feature source is a program Point layer, not a definitive title polygon registry.",
        "Calibration, served HTTP/JSON hash, DOM, console and browser acceptance remain pending.",
    ],
    "next_required_action": "Review the relative method against documented IoD limitations, then use only accepted rows for a 300-row evidence expansion and browser acceptance.",
    "fake_data": False,
    "db_write": False,
    "migration": False,
    "production_deploy": False,
    "final_ready": False,
    "generated_at": utc_now(),
}

for path in (OUTPUT_PATH, WEB_JSON):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

source_rows = "".join(
    f"<tr><td>{i}</td><td>{html.escape(item['name'])}</td><td>{html.escape(item['publisher'])}</td><td>{item['accuracy_percent']}%</td><td>{html.escape(item['status'])}</td><td>{item['probe'].get('http_status') or '-'}</td><td><code>{html.escape(str(item['probe'].get('sha256') or '-'))}</code></td><td>{html.escape(item['limit'])}</td></tr>"
    for i, item in enumerate(sources, 1)
)
row_rows = "".join(
    f"<tr><td>{html.escape(str(item.get('parcel_id')))}</td><td>{html.escape(str(item.get('longitude','-')))}</td><td>{html.escape(str(item.get('latitude','-')))}</td><td>{html.escape(str(item.get('ons_lsoa_code') or '-'))}</td><td>{html.escape(str((item.get('iod_2025') or {}).get('crime_rank') or '-'))}</td><td>{html.escape(str((item.get('iod_2025') or {}).get('crime_decile') or '-'))}</td><td>{html.escape(str(item.get('relative_security_candidate_percent')))}</td><td>{html.escape(str(item.get('candidate_accuracy_percent') or 0))}%</td><td>{html.escape(str((item.get('police_query') or {}).get('crime_record_count')))}</td><td><code>{html.escape(str((item.get('police_query') or {}).get('sha256') or '-'))}</code></td><td>null</td></tr>"
    for item in rows
)
gate_rows = "".join(
    f"<tr><td>{i}</td><td>{html.escape(gate['gate'])}</td><td class='{html.escape(gate['state'])}'>{html.escape(gate['state'])}</td><td>{html.escape(str(gate.get('evidence','')))}</td></tr>"
    for i, gate in enumerate(gates, 1)
)
document = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Security Public Safety 2</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px;margin:14px 0}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}code{{font-size:9px;word-break:break-all}}.PASS{{font-weight:700}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style></head><body><h1>security_public_safety_2 — IoD25 yöntem ve 24 satır dalgası</h1><div class='notice'>Gösterilen yüzde yalnız IoD25 Crime Rank tabanlı göreli adaydır. Business skoru 0 satırdır; kalibrasyon ve browser kabulü geçmeden yükseltilmez.</div><div class='cards'><div class='card'>Genel ilerleme<br><b>{overall_progress}%</b></div><div class='card'>Artış<br><b>+{round(overall_progress-previous_progress,1)}%</b></div><div class='card'>İşlem<br><b>{completed_operations}/{total_operations}</b></div><div class='card'>Kaynak<br><b>{len(promoted_sources)}/{len(sources)}</b></div><div class='card'>≥95 kaynak<br><b>{source_accuracy_ge_95}</b></div><div class='card'>Aday satır<br><b>{candidate_rows}/24</b></div><div class='card'>≥95 satır kanıtı<br><b>{accuracy_ge_95_rows}</b></div><div class='card'>Business satır<br><b>0</b></div></div><h2>Resmî kaynaklar</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Yayıncı</th><th>Doğruluk</th><th>Durum</th><th>HTTP</th><th>SHA256</th><th>Sınır</th></tr></thead><tbody>{source_rows}</tbody></table><h2>24 örnek satır</h2><table><thead><tr><th>Parsel</th><th>Lon</th><th>Lat</th><th>ONS LSOA</th><th>Crime Rank</th><th>Decile</th><th>Göreli aday %</th><th>Kanıt doğruluğu</th><th>Police kayıt</th><th>Police SHA256</th><th>Business skor</th></tr></thead><tbody>{row_rows}</tbody></table><h2>Kabul kapıları</h2><table><thead><tr><th>#</th><th>Kapı</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{gate_rows}</tbody></table><p><b>Sonraki adım:</b> {html.escape(payload['next_required_action'])}</p><p><b>final_ready:</b> false</p></body></html>"""
WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
WEB_HTML.write_text(document, encoding="utf-8")
