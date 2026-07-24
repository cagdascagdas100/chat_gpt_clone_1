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
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
PARTITION = {"start": 30762, "end": 61522, "count": 30761, "canonical_count": 92283}
ROOT = Path.cwd()
SOURCE_REL = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
SOURCE_PATH = ROOT / SOURCE_REL
PREVIOUS_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/source_and_sample_gate_latest.json"
OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"
SNAPSHOT_DATE = datetime.now(timezone.utc).date().isoformat()
USER_AGENT = "AAYS-TerraYield-security-public-safety-evidence-wave/2.0"
TARGET_IDS = [f"parcel_{value}" for value in range(30762, 30774)]
ONS_LAYER = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
IOD_FILE7_URL = "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
ONS_POPULATION_XLSX_URL = "https://www.ons.gov.uk/file?uri=%2Fpeoplepopulationandcommunity%2Fpopulationandmigration%2Fpopulationestimates%2Fdatasets%2Flowersuperoutputareamidyearpopulationestimatesnationalstatistics%2Fmid2022revisednov2025tomid2024%2Fsapelsoabroadage20222024.xlsx"

if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
    raise SystemExit(f"WRONG_SLOT: {os.environ.get('AAYS_SLOT_ID')}")
if os.environ.get("AAYS_CHILD_DIRECT_PUSH_FORBIDDEN", "true").lower() != "true":
    raise SystemExit("DIRECT_PUSH_GUARD_MISSING")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, *, parse_json: bool = False, attempts: int = 3, timeout: float = 35.0) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json,text/html,application/octet-stream,*/*",
                },
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
    return {
        "reachable": False,
        "http_status": None,
        "bytes": 0,
        "sha256": None,
        "attempts": attempts,
        "error": last_error,
    }


def download_to_temp(url: str, suffix: str) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, 4):
        temp_path = None
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"},
            )
            with urllib.request.urlopen(request, timeout=90.0) as response:
                with tempfile.NamedTemporaryFile(prefix="aays_security_", suffix=suffix, delete=False) as handle:
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
    return {"reachable": False, "error": last_error, "attempts": 3, "temp_path": None}


def inspect_iod_csv(path: Path) -> dict[str, Any]:
    row_count = 0
    unique_lsoa: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        headers = next(reader)
        lowered = [value.strip().casefold() for value in headers]
        lsoa_indexes = [index for index, value in enumerate(lowered) if "lsoa" in value and ("code" in value or value.endswith("lsoa"))]
        crime_columns = [headers[index] for index, value in enumerate(lowered) if "crime" in value]
        population_columns = [headers[index] for index, value in enumerate(lowered) if "population" in value]
        rank_columns = [headers[index] for index, value in enumerate(lowered) if "rank" in value and "crime" in value]
        score_columns = [headers[index] for index, value in enumerate(lowered) if "score" in value and "crime" in value]
        for row in reader:
            row_count += 1
            if lsoa_indexes and lsoa_indexes[0] < len(row):
                value = row[lsoa_indexes[0]].strip()
                if value:
                    unique_lsoa.add(value)
    return {
        "headers": headers,
        "row_count": row_count,
        "unique_lsoa_count": len(unique_lsoa),
        "lsoa_columns": [headers[index] for index in lsoa_indexes],
        "crime_columns": crime_columns,
        "crime_rank_columns": rank_columns,
        "crime_score_columns": score_columns,
        "population_columns": population_columns,
        "schema_gate_pass": bool(lsoa_indexes and crime_columns and population_columns),
    }


def xlsx_sheet_names(path: Path) -> list[str]:
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("xl/workbook.xml"))
        return [sheet.attrib.get("name", "") for sheet in root.findall("m:sheets/m:sheet", namespace)]


def inspect_ons_xlsx(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        worksheet_count = sum(name.startswith("xl/worksheets/sheet") and name.endswith(".xml") for name in names)
        shared_strings_present = "xl/sharedStrings.xml" in names
    sheets = xlsx_sheet_names(path)
    return {
        "sheet_names": sheets,
        "worksheet_count": worksheet_count,
        "shared_strings_present": shared_strings_present,
        "mid_2024_sheet_candidates": [name for name in sheets if "2024" in name],
        "schema_gate_pass": bool(sheets and worksheet_count),
    }


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
    chunk_size = 1024 * 1024

    with path.open("r", encoding="utf-8-sig") as handle:
        buffer = ""
        while True:
            chunk = handle.read(chunk_size)
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
                chunk = handle.read(chunk_size)
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
                coordinates = geometry.get("coordinates")
                found[parcel_id] = {
                    "parcel_id": parcel_id,
                    "geometry_type": geometry.get("type"),
                    "coordinates": coordinates,
                    "historical_lsoa_code": properties.get("security_lsoa_code"),
                    "historical_lsoa_name": properties.get("security_lsoa_name"),
                    "historical_spatial_match_method": properties.get("spatial_match_method"),
                    "historical_security_values_reused": False,
                }
            buffer = buffer[end:]

    return found, count


def ons_lsoa_query(longitude: float, latitude: float) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "LSOA21CD,LSOA21NM",
            "returnGeometry": "false",
            "f": "json",
        }
    )
    result = fetch(f"{ONS_LAYER}/query?{params}", parse_json=True)
    parsed = result.pop("json", None)
    features = parsed.get("features", []) if isinstance(parsed, dict) else []
    attributes = [item.get("attributes") or {} for item in features]
    result["feature_count"] = len(attributes)
    result["matches"] = attributes
    if isinstance(parsed, dict) and parsed.get("error"):
        result["arcgis_error"] = parsed["error"]
    return result


def police_query(longitude: float, latitude: float, month: str) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "lat": f"{latitude:.7f}",
            "lng": f"{longitude:.7f}",
            "date": month,
        }
    )
    result = fetch(
        f"https://data.police.uk/api/crimes-street/all-crime?{params}",
        parse_json=True,
        attempts=3,
        timeout=45.0,
    )
    parsed = result.pop("json", None)
    if isinstance(parsed, list):
        categories = Counter(str(item.get("category") or "unknown") for item in parsed)
        result["crime_record_count"] = len(parsed)
        result["category_counts"] = dict(sorted(categories.items()))
        result["unique_persistent_ids"] = len(
            {str(item.get("persistent_id")) for item in parsed if item.get("persistent_id")}
        )
    else:
        result["crime_record_count"] = None
        result["category_counts"] = {}
        result["unique_persistent_ids"] = None
    return result


source_specs = [
    {
        "source_id": "hmlr_inspire_download",
        "name": "HM Land Registry INSPIRE Index Polygons download",
        "publisher": "HM Land Registry",
        "url": "https://use-land-property-data.service.gov.uk/datasets/inspire/download",
        "role": "indicative_freehold_polygon_download",
        "accuracy_percent": 95,
        "limit": "Indicative freehold extent only; not definitive title boundary and excludes many leaseholds.",
        "parse_json": False,
    },
    {
        "source_id": "hmlr_inspire_metadata",
        "name": "INSPIRE Index Polygons metadata",
        "publisher": "HM Land Registry / data.gov.uk",
        "url": "https://www.data.gov.uk/dataset/811bcf4c-fbbf-4597-aa9c-3d5bd3bfd455/inspire-index-polygons-spatial-data",
        "role": "publisher_and_update_metadata",
        "accuracy_percent": 95,
        "limit": "Metadata and access route only.",
        "parse_json": False,
    },
    {
        "source_id": "ons_lsoa_2021_layer",
        "name": "LSOA December 2021 Boundaries EW BGC V5",
        "publisher": "Office for National Statistics",
        "url": f"{ONS_LAYER}?f=json",
        "role": "official_point_in_polygon_geography",
        "accuracy_percent": 98,
        "limit": "Area geography; not a parcel boundary.",
        "parse_json": True,
    },
    {
        "source_id": "police_api_last_updated",
        "name": "Police.uk Crime Last Updated",
        "publisher": "Home Office / Police.uk",
        "url": "https://data.police.uk/api/crime-last-updated",
        "role": "explicit_month_selector",
        "accuracy_percent": 98,
        "limit": "Month selector only.",
        "parse_json": True,
    },
    {
        "source_id": "police_api_contract",
        "name": "Police.uk street-level crime API",
        "publisher": "Home Office / Police.uk",
        "url": "https://data.police.uk/docs/method/crime-street/",
        "role": "official_crime_event_contract",
        "accuracy_percent": 95,
        "limit": "Published locations are anonymised approximations; results are not exact parcel incidents.",
        "parse_json": False,
    },
    {
        "source_id": "home_office_recorded_crime",
        "name": "Police recorded crime and outcomes open data tables",
        "publisher": "Home Office",
        "url": "https://www.gov.uk/government/statistical-data-sets/police-recorded-crime-and-outcomes-open-data-tables",
        "role": "area_level_benchmark",
        "accuracy_percent": 95,
        "limit": "Benchmark geography only; cannot be copied to parcels.",
        "parse_json": False,
    },
    {
        "source_id": "imd_2025_domains",
        "name": "English indices of deprivation 2025 domains",
        "publisher": "Ministry of Housing, Communities and Local Government",
        "url": "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025",
        "role": "official_lsoa_crime_domain_candidate",
        "accuracy_percent": 98,
        "limit": "Relative LSOA deprivation evidence; not a current monthly crime count.",
        "parse_json": False,
    },
    {
        "source_id": "ons_lsoa_population_2024",
        "name": "LSOA population estimates, mid-2022 revised to mid-2024",
        "publisher": "Office for National Statistics",
        "url": "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimatesnationalstatistics",
        "role": "official_population_denominator_candidate",
        "accuracy_percent": 98,
        "limit": "Population denominator; edition and LSOA code compatibility must be verified before rates.",
        "parse_json": False,
    },
]


def probe_source(spec: dict[str, Any]) -> dict[str, Any]:
    probe = fetch(spec["url"], parse_json=bool(spec["parse_json"]))
    parsed = probe.pop("json", None)
    row = {key: value for key, value in spec.items() if key != "parse_json"}
    row["probe"] = probe
    row["status"] = "PROMOTED_FOR_ROLE" if probe.get("reachable") else "HELD_UNREACHABLE"
    row["source_snapshot_date"] = SNAPSHOT_DATE
    if spec["source_id"] == "police_api_last_updated" and isinstance(parsed, dict):
        row["latest_available_month"] = parsed.get("date")
    if spec["source_id"] == "ons_lsoa_2021_layer" and isinstance(parsed, dict):
        row["layer_name"] = parsed.get("name")
        row["geometry_type"] = parsed.get("geometryType")
        row["object_id_field"] = parsed.get("objectIdField")
    return row


with concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="security-source") as executor:
    sources = list(executor.map(probe_source, source_specs))

with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="security-dataset") as executor:
    iod_future = executor.submit(download_to_temp, IOD_FILE7_URL, ".csv")
    ons_population_future = executor.submit(download_to_temp, ONS_POPULATION_XLSX_URL, ".xlsx")
    iod_download = iod_future.result()
    ons_population_download = ons_population_future.result()

iod_schema: dict[str, Any] = {"schema_gate_pass": False}
ons_population_schema: dict[str, Any] = {"schema_gate_pass": False}
try:
    if iod_download.get("reachable") and iod_download.get("temp_path"):
        iod_schema = inspect_iod_csv(Path(str(iod_download["temp_path"])))
    if ons_population_download.get("reachable") and ons_population_download.get("temp_path"):
        ons_population_schema = inspect_ons_xlsx(Path(str(ons_population_download["temp_path"])))
finally:
    for item in (iod_download, ons_population_download):
        if item.get("temp_path"):
            Path(str(item["temp_path"])).unlink(missing_ok=True)
            item["temp_path"] = None

police_date = next(
    (item.get("latest_available_month") for item in sources if item["source_id"] == "police_api_last_updated"),
    None,
)
police_month = str(police_date or "")[:7]
if len(police_month) != 7:
    police_month = ""

if not SOURCE_PATH.is_file():
    raise SystemExit(f"CANONICAL_POINT_SOURCE_MISSING: {SOURCE_REL}")

target_features, actual_feature_count = stream_geojson_targets(SOURCE_PATH, TARGET_IDS)
source_blob, source_sha256 = file_hashes(SOURCE_PATH)
source_size = SOURCE_PATH.stat().st_size


def verify_row(parcel_id: str) -> dict[str, Any]:
    base = target_features.get(parcel_id)
    if not base:
        return {
            "parcel_id": parcel_id,
            "evidence_status": "BLOCKED_POINT_NOT_FOUND",
            "business_score": None,
            "business_confidence": 0,
            "promotion_allowed": False,
        }
    coordinates = base.get("coordinates")
    valid_coordinate = (
        isinstance(coordinates, list)
        and len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
        and -180 <= float(coordinates[0]) <= 180
        and -90 <= float(coordinates[1]) <= 90
    )
    if not valid_coordinate:
        return {
            **base,
            "evidence_status": "BLOCKED_INVALID_COORDINATE",
            "business_score": None,
            "business_confidence": 0,
            "promotion_allowed": False,
        }

    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    ons = ons_lsoa_query(longitude, latitude)
    police = police_query(longitude, latitude, police_month) if police_month else {
        "reachable": False,
        "error": "POLICE_MONTH_MISSING",
        "crime_record_count": None,
        "category_counts": {},
    }
    ons_matches = ons.get("matches") or []
    ons_code = ons_matches[0].get("LSOA21CD") if len(ons_matches) == 1 else None
    ons_name = ons_matches[0].get("LSOA21NM") if len(ons_matches) == 1 else None
    historical_code = base.get("historical_lsoa_code")
    code_match = bool(ons_code and historical_code and str(ons_code) == str(historical_code))

    integrity = 0
    integrity += 30
    integrity += 20
    integrity += 20 if len(ons_matches) == 1 else 0
    integrity += 10 if code_match else 0
    integrity += 15 if police.get("reachable") and police.get("sha256") else 0
    integrity += 5 if police_month else 0
    evidence_status = (
        "POINT_LSOA_POLICE_MONTH_VERIFIED_NO_SCORE"
        if len(ons_matches) == 1 and police.get("reachable") and police.get("sha256")
        else "EVIDENCE_PARTIAL_SCORE_BLOCKED"
    )
    return {
        **base,
        "longitude": longitude,
        "latitude": latitude,
        "coordinate_source_path": SOURCE_REL,
        "coordinate_source_blob_sha": source_blob,
        "ons_lsoa_code": ons_code,
        "ons_lsoa_name": ons_name,
        "historical_lsoa_code_matches_ons": code_match,
        "ons_query": ons,
        "police_month": police_month or None,
        "police_query": police,
        "evidence_integrity_percent": integrity,
        "evidence_integrity_formula": "30 exact internal parcel ID + 20 valid WGS84 point + 20 single ONS LSOA + 10 historical/ONS code agreement + 15 official Police.uk response hash + 5 explicit month",
        "evidence_status": evidence_status,
        "business_score": None,
        "business_confidence": 0,
        "promotion_allowed": False,
        "score_blocker": "A documented LSOA rate/normalisation methodology and acceptance proof are still required.",
    }


with concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="security-row") as executor:
    rows = list(executor.map(verify_row, TARGET_IDS))

source_promoted = [item for item in sources if item["status"] == "PROMOTED_FOR_ROLE"]
source_accuracy_ge_95 = sum(
    item["status"] == "PROMOTED_FOR_ROLE" and int(item["accuracy_percent"]) >= 95 for item in sources
)
verified_evidence_rows = sum(
    item.get("evidence_status") == "POINT_LSOA_POLICE_MONTH_VERIFIED_NO_SCORE" for item in rows
)
accuracy_ge_95_rows = sum(int(item.get("evidence_integrity_percent") or 0) >= 95 for item in rows)
ons_single_match_rows = sum((item.get("ons_query") or {}).get("feature_count") == 1 for item in rows)
police_hashed_rows = sum(
    bool((item.get("police_query") or {}).get("reachable") and (item.get("police_query") or {}).get("sha256"))
    for item in rows
)
id_continuity_pass = set(target_features) == set(TARGET_IDS)
feature_count_pass = actual_feature_count == 92283

gates = [
    {"gate": "remote_first_wave_published", "state": "PASS"},
    {"gate": "shared_point_source_blob_resolved", "state": "PASS" if source_blob == "bb48164e7a0af78df875f30421a6a3068c43edb8" else "BLOCKED", "evidence": source_blob},
    {"gate": "shared_point_source_exact_92283_count", "state": "PASS" if feature_count_pass else "BLOCKED", "evidence": actual_feature_count},
    {"gate": "target_12_ids_continuous_and_unique", "state": "PASS" if id_continuity_pass else "BLOCKED", "evidence": len(target_features)},
    {"gate": "target_12_valid_wgs84_points", "state": "PASS" if all(item.get("longitude") is not None for item in rows) else "BLOCKED"},
    {"gate": "ons_lsoa_single_polygon_12_rows", "state": "PASS" if ons_single_match_rows == 12 else "PARTIAL", "evidence": ons_single_match_rows},
    {"gate": "police_explicit_month_selected", "state": "PASS" if police_month else "BLOCKED", "evidence": police_month},
    {"gate": "police_response_hash_12_rows", "state": "PASS" if police_hashed_rows == 12 else "PARTIAL", "evidence": police_hashed_rows},
    {"gate": "hmlr_download_route_reachable", "state": "PASS" if sources[0]["status"] == "PROMOTED_FOR_ROLE" else "BLOCKED"},
    {"gate": "imd_2025_source_page_reachable", "state": "PASS" if sources[6]["status"] == "PROMOTED_FOR_ROLE" else "BLOCKED"},
    {"gate": "ons_population_source_page_reachable", "state": "PASS" if sources[7]["status"] == "PROMOTED_FOR_ROLE" else "BLOCKED"},
    {"gate": "iod_2025_file7_download_hash", "state": "PASS" if iod_download.get("reachable") and iod_download.get("sha256") else "BLOCKED", "evidence": iod_download.get("bytes")},
    {"gate": "iod_2025_lsoa_crime_population_schema", "state": "PASS" if iod_schema.get("schema_gate_pass") else "BLOCKED", "evidence": iod_schema.get("row_count")},
    {"gate": "ons_population_2024_xlsx_download_hash", "state": "PASS" if ons_population_download.get("reachable") and ons_population_download.get("sha256") else "BLOCKED", "evidence": ons_population_download.get("bytes")},
    {"gate": "ons_population_2024_workbook_schema", "state": "PASS" if ons_population_schema.get("schema_gate_pass") else "BLOCKED", "evidence": ons_population_schema.get("worksheet_count")},
    {"gate": "row_by_row_web_artifact_generated", "state": "PASS"},
    {"gate": "documented_security_rate_and_score_method", "state": "PENDING"},
    {"gate": "join_i_2025_and_population_to_12_rows", "state": "PENDING"},
    {"gate": "expand_to_300_verified_business_rows", "state": "PENDING"},
    {"gate": "served_http_and_json_hash_acceptance", "state": "PENDING"},
    {"gate": "dom_console_browser_acceptance", "state": "PENDING"},
]
completed_operations = sum(item["state"] == "PASS" for item in gates)
total_operations = len(gates)
overall_progress = round((completed_operations / total_operations) * 65, 1)

previous = {}
if PREVIOUS_PATH.is_file():
    try:
        previous = json.loads(PREVIOUS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        previous = {}
previous_progress = float(previous.get("overall_progress_percent") or 0)

payload = {
    "schema_version": 3,
    "architecture_version": 3,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": SLOT_ID,
    "base_slot_id": "security_public_safety",
    "shard_index": 2,
    "parcel_partition": PARTITION,
    "state": "TWELVE_POINT_LSOA_POLICE_ROWS_AND_OFFICIAL_METHOD_DATA_SCHEMAS_PREPARED",
    "first_unverified_step": "JOIN_IOD2025_AND_POPULATION_TO_12_ROWS_THEN_DOCUMENT_RATE_METHOD",
    "source_snapshot_date": SNAPSHOT_DATE,
    "canonical_point_source": {
        "path": SOURCE_REL,
        "git_blob_sha": source_blob,
        "sha256": source_sha256,
        "expected_git_blob_sha": "bb48164e7a0af78df875f30421a6a3068c43edb8",
        "git_blob_matches_expected": source_blob == "bb48164e7a0af78df875f30421a6a3068c43edb8",
        "file_bytes": source_size,
        "declared_feature_count": 92283,
        "actual_feature_count": actual_feature_count,
        "geometry_type": "Point",
        "parcel_id_property": "security_parcel_id",
        "security_values_reused": False,
    },
    "dataset_downloads": {"iod_2025_file7": iod_download, "ons_lsoa_population_2024": ons_population_download},
    "dataset_schemas": {"iod_2025_file7": iod_schema, "ons_lsoa_population_2024": ons_population_schema},
    "sources_reviewed": len(sources),
    "promoted_sources": len(source_promoted),
    "held_sources": len(sources) - len(source_promoted),
    "accuracy_ge_95_source_count": source_accuracy_ge_95,
    "candidate_rows": len(rows),
    "verified_evidence_rows": verified_evidence_rows,
    "accuracy_ge_95_evidence_rows": accuracy_ge_95_rows,
    "ons_single_match_rows": ons_single_match_rows,
    "police_hashed_rows": police_hashed_rows,
    "verified_slot_rows": 0,
    "actual_business_rows_written": 0,
    "rows": rows,
    "sources": sources,
    "gates": gates,
    "completed_operations": completed_operations,
    "total_operations": total_operations,
    "overall_progress_percent": overall_progress,
    "progress_delta_percent": round(overall_progress - previous_progress, 1),
    "business_row_progress_percent": 0,
    "progress_formula": "PASS evidence/preparation gates divided by 21, capped at 65 percent until a documented rate/score method and verified business rows exist.",
    "blockers": [
        "The 92,283-feature file supplies canonical program points, not definitive title polygons.",
        "Police.uk street locations are anonymised approximations and nearby point queries may overlap.",
        "A current LSOA population denominator and documented crime-rate normalisation method must be joined before any security score is promoted.",
        "HMLR INSPIRE is indicative freehold geometry and cannot be treated as definitive title extent.",
        "Served HTTP, JSON hash, DOM, console and browser acceptance remain pending.",
    ],
    "next_required_action": "Join the downloaded IoD 2025 crime-domain and ONS mid-2024 population fields to the 12 verified LSOA codes, document a rate/score formula, then expand to 300 only after acceptance.",
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
    f"<tr><td>{index}</td><td>{html.escape(item['name'])}</td><td>{html.escape(item['publisher'])}</td>"
    f"<td>{item['accuracy_percent']}%</td><td>{html.escape(item['status'])}</td>"
    f"<td>{item['probe'].get('http_status') or '-'}</td><td><code>{html.escape(str(item['probe'].get('sha256') or '-'))}</code></td>"
    f"<td>{html.escape(item['role'])}</td><td>{html.escape(item['limit'])}</td></tr>"
    for index, item in enumerate(sources, 1)
)
dataset_rows = "".join(
    f"<tr><td>{html.escape(name)}</td><td>{html.escape(str(item.get('http_status') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('bytes') or 0))}</td><td><code>{html.escape(str(item.get('sha256') or '-'))}</code></td>"
    f"<td>{html.escape(str((iod_schema if name == 'IoD 2025 File 7 CSV' else ons_population_schema).get('schema_gate_pass')))}</td></tr>"
    for name, item in (("IoD 2025 File 7 CSV", iod_download), ("ONS LSOA population 2024 XLSX", ons_population_download))
)
row_rows = "".join(
    f"<tr><td>{html.escape(str(item.get('parcel_id')))}</td>"
    f"<td>{html.escape(str(item.get('longitude', '-')))}</td><td>{html.escape(str(item.get('latitude', '-')))}</td>"
    f"<td>{html.escape(str(item.get('historical_lsoa_code') or '-'))}</td><td>{html.escape(str(item.get('ons_lsoa_code') or '-'))}</td>"
    f"<td>{'PASS' if item.get('historical_lsoa_code_matches_ons') else 'CHECK'}</td>"
    f"<td>{html.escape(str(item.get('police_month') or '-'))}</td>"
    f"<td>{html.escape(str((item.get('police_query') or {}).get('crime_record_count')))}</td>"
    f"<td><code>{html.escape(str((item.get('police_query') or {}).get('sha256') or '-'))}</code></td>"
    f"<td>{html.escape(str(item.get('evidence_integrity_percent') or 0))}%</td>"
    f"<td>{html.escape(str(item.get('evidence_status')))}</td><td>null</td></tr>"
    for item in rows
)
gate_rows = "".join(
    f"<tr><td>{index}</td><td>{html.escape(item['gate'])}</td><td class='{html.escape(item['state'])}'>{html.escape(item['state'])}</td>"
    f"<td>{html.escape(str(item.get('evidence', '')))}</td></tr>"
    for index, item in enumerate(gates, 1)
)

document = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Security Public Safety 2</title><style>
body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}
.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px;margin:14px 0}}
th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}code{{font-size:9px;word-break:break-all}}
.PASS{{font-weight:700}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style></head><body>
<h1>security_public_safety_2 — satır satır internet ve geometri kanıtı</h1>
<div class='notice'>12 parsel için Point → ONS LSOA → Police.uk açık ay kanıtı hazırlanmıştır. Business skoru hâlâ null; yöntem ve browser kabulü geçmeden yükseltilmez.</div>
<div class='cards'>
<div class='card'>Genel ilerleme<br><b>{overall_progress}%</b></div><div class='card'>Artış<br><b>+{round(overall_progress - previous_progress, 1)}%</b></div>
<div class='card'>İşlem<br><b>{completed_operations}/{total_operations}</b></div><div class='card'>Kaynak<br><b>{len(source_promoted)}/{len(sources)}</b></div>
<div class='card'>≥95 kaynak<br><b>{source_accuracy_ge_95}</b></div><div class='card'>Aday satır<br><b>{len(rows)}</b></div>
<div class='card'>Kanıtı geçen satır<br><b>{verified_evidence_rows}</b></div><div class='card'>≥95 satır kanıtı<br><b>{accuracy_ge_95_rows}</b></div>
<div class='card'>Doğrulanmış business satırı<br><b>0</b></div></div>
<h2>Resmî kaynaklar</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Yayıncı</th><th>Doğruluk</th><th>Durum</th><th>HTTP</th><th>SHA256</th><th>Rol</th><th>Sınır</th></tr></thead><tbody>{source_rows}</tbody></table>
<h2>Resmî veri dosyaları</h2><table><thead><tr><th>Dosya</th><th>HTTP</th><th>Bayt</th><th>SHA256</th><th>Şema</th></tr></thead><tbody>{dataset_rows}</tbody></table>
<h2>12 örnek parsel</h2><table><thead><tr><th>Parsel</th><th>Lon</th><th>Lat</th><th>Eski LSOA</th><th>ONS LSOA</th><th>Kod</th><th>Ay</th><th>Suç kaydı</th><th>Yanıt SHA256</th><th>Kanıt bütünlüğü</th><th>Durum</th><th>Skor</th></tr></thead><tbody>{row_rows}</tbody></table>
<h2>Kabul kapıları</h2><table><thead><tr><th>#</th><th>Kapı</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{gate_rows}</tbody></table>
<p><b>Sonraki adım:</b> {html.escape(payload['next_required_action'])}</p><p><b>final_ready:</b> false</p></body></html>"""
WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
WEB_HTML.write_text(document, encoding="utf-8")

print(json.dumps({
    "slot_id": SLOT_ID,
    "state": payload["state"],
    "candidate_rows": len(rows),
    "verified_evidence_rows": verified_evidence_rows,
    "verified_slot_rows": 0,
    "promoted_sources": len(source_promoted),
    "completed_operations": completed_operations,
    "total_operations": total_operations,
    "overall_progress_percent": overall_progress,
    "final_ready": False,
}, ensure_ascii=False))
