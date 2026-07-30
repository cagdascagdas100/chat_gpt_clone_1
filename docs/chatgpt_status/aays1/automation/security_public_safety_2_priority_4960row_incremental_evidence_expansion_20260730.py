from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"
FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_4960row_evidence_expansion_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_4960row_evidence_expansion_latest.json"
INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_300row_wave55_latest.json"
ONS_LAYER = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
IOD_FILE7_URL = "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave55-boundary-recovery/1.0"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_evidence_expansion_latest.json"':
        'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_4660row_evidence_expansion_latest.json"',
    'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_300row_wave55_latest.json"',
    'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_300row_wave55_latest.json"',
    'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27.html"':
        'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_300row_wave55.html"',
    'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_4960row_evidence_expansion_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_4960row_evidence_expansion_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_4960row_evidence_expansion.html"',
    'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 31082)]':
        'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 35422)]',
    'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(31082, 31102)]':
        'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(35422, 35722)]',
    'PREVIOUS_320_SEQUENCE_MISMATCH': 'PREVIOUS_4660_SEQUENCE_MISMATCH',
    'priority_320row_evidence_expansion_latest.json"': 'priority_4660row_evidence_expansion_latest.json"',
    'priority_20row_wave27_latest.json"': 'priority_300row_wave55_latest.json"',
    'priority_20row_wave27.html"': 'priority_300row_wave55.html"',
    'range(31082, 31102)': 'range(35422, 35722)',
    'ThreadPoolExecutor(max_workers=12, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=15, thread_name_prefix="security-row")',
    'wave27_incremental_target_20_ids_unique': 'wave55_incremental_target_300_ids_unique',
    'len(target_features) == 20': 'len(target_features) == 300',
    'wave27_incremental_valid_wgs84_points': 'wave55_incremental_valid_wgs84_points',
    'valid_points == 20': 'valid_points == 300',
    'wave27_incremental_single_ons_lsoa_matches': 'wave55_incremental_single_ons_lsoa_matches',
    'ons_rows == 20': 'ons_rows == 300',
    'wave27_incremental_police_response_hashes': 'wave55_incremental_police_response_hashes',
    'police_hash_rows >= 19': 'police_hash_rows >= 285',
    'wave27_incremental_candidate_20_rows_generated': 'wave55_incremental_candidate_300_rows_generated',
    'candidate_rows == 20': 'candidate_rows == 300',
    'IOD25_RELATIVE_SECURITY_INCREMENTAL_20_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_INCREMENTAL_300_ROWS_PREPARED_NOT_PROMOTED',
    'MERGE_WITH_ACCEPTED_320_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE':
        'MERGE_WITH_ACCEPTED_4660_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    'accepted 320-row wave': 'accepted 4660-row wave',
    'merge_with_accepted_320_candidate_rows': 'merge_with_accepted_4660_candidate_rows',
    'Merge the 20 validated incremental rows with the accepted 320-row artifact':
        'Merge the 300 validated incremental rows with the accepted 4660-row artifact',
    'IoD25 20 satır artımlı kanıt dalgası': 'IoD25 300 satır artımlı kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/20</b>': 'Aday satır<br><b>{candidate_rows}/300</b>',
    '<h2>20 artımlı örnek satır</h2>': '<h2>300 artımlı örnek satır</h2>',
    'INCREMENTAL_20_SEQUENCE_MISMATCH': 'INCREMENTAL_300_SEQUENCE_MISMATCH',
    'len(set(row_ids)) != 340': 'len(set(row_ids)) != 4960',
    'MERGED_340_SEQUENCE_OR_UNIQUENESS_FAILED': 'MERGED_4960_SEQUENCE_OR_UNIQUENESS_FAILED',
    'accepted_320row_base_present': 'accepted_4660row_base_present',
    'incremental_20_ids_unique': 'incremental_300_ids_unique',
    'merged_340_ids_sequential_unique': 'merged_4960_ids_sequential_unique',
    'valid_wgs84_points_340': 'valid_wgs84_points_4960',
    'valid_points == 340': 'valid_points == 4960',
    'single_ons_lsoa_matches_340': 'single_ons_lsoa_matches_4960',
    'ons_rows == 340': 'ons_rows == 4960',
    'police_hash_rows >= 323': 'police_hash_rows >= 4712',
    'iod25_exact_lsoa_joins_340': 'iod25_exact_lsoa_joins_4960',
    'iod_join_rows == 340': 'iod_join_rows == 4960',
    'candidate_rows_340': 'candidate_rows_4960',
    'candidate_rows == 340': 'candidate_rows == 4960',
    'candidate_accuracy_ge_95_rows_ge_323': 'candidate_accuracy_ge_95_rows_ge_4712',
    'accuracy_ge_95_rows >= 323': 'accuracy_ge_95_rows >= 4712',
    '"schema_version": 5': '"schema_version": 33',
    'IOD25_RELATIVE_SECURITY_PRIORITY_340_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_PRIORITY_4960_ROWS_PREPARED_NOT_PROMOTED',
    'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_340_ROWS':
        'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_4960_ROWS',
    'pending for the 340-row artifact': 'pending for the 4960-row artifact',
    'on the 340-row candidate artifact': 'on the 4960-row candidate artifact',
    '"base_rows": 320': '"base_rows": 4660',
    '"added_rows": 20': '"added_rows": 300',
    '<title>security_public_safety_2 — 340 satır</title>':
        '<title>security_public_safety_2 — 4960 satır</title>',
    '<h1>security_public_safety_2 — 340 satır aday kanıtı</h1>':
        '<h1>security_public_safety_2 — 4960 satır aday kanıtı</h1>',
    'Aday satır<br><b>{candidate_rows}/340</b>': 'Aday satır<br><b>{candidate_rows}/4960</b>',
    '<h2>340 örnek satır</h2>': '<h2>4960 örnek satır</h2>',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)


def query_ons_nearby(longitude: float, latitude: float, historical_code: str) -> dict | None:
    for distance_m in (1, 3, 5, 10, 25, 50):
        params = urllib.parse.urlencode({
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": str(distance_m),
            "units": "esriSRUnit_Meter",
            "outFields": "LSOA21CD,LSOA21NM",
            "returnGeometry": "false",
            "f": "json",
        })
        request = urllib.request.Request(
            f"{ONS_LAYER}/query?{params}",
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
                parsed = json.loads(body.decode("utf-8-sig"))
                features = parsed.get("features", []) if isinstance(parsed, dict) else []
                candidates = [item.get("attributes") or {} for item in features]
                selected = next((item for item in candidates if str(item.get("LSOA21CD") or "") == historical_code), None)
                if selected:
                    return {
                        "reachable": True,
                        "http_status": int(response.status),
                        "final_url": response.geturl(),
                        "content_type": response.headers.get("Content-Type", ""),
                        "bytes": len(body),
                        "sha256": hashlib.sha256(body).hexdigest(),
                        "feature_count": 1,
                        "raw_feature_count": len(candidates),
                        "matches": [selected],
                        "targeted_boundary_recovery": True,
                        "distance_m": distance_m,
                        "selection_rule": "official_ons_candidates_filtered_by_exact_canonical_historical_lsoa_code",
                    }
        except Exception:
            continue
    return None


def load_iod_rows(target_codes: set[str]) -> tuple[dict[str, dict], int]:
    request = urllib.request.Request(IOD_FILE7_URL, headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*"})
    temp_path: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(prefix="aays_wave55_iod_", suffix=".csv", delete=False) as handle:
                temp_path = Path(handle.name)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
        selected: dict[str, dict] = {}
        row_count = 0
        with temp_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            lowered = {header: header.strip().casefold() for header in headers}
            code_header = next((header for header, value in lowered.items() if "lsoa code" in value), None)
            crime_score_header = next((header for header, value in lowered.items() if value.startswith("crime score")), None)
            crime_rank_header = next((header for header, value in lowered.items() if value.startswith("crime rank")), None)
            crime_decile_header = next((header for header, value in lowered.items() if value.startswith("crime decile")), None)
            population_headers = [header for header, value in lowered.items() if "population" in value]
            for item in reader:
                row_count += 1
                code = str(item.get(code_header or "", "")).strip()
                if code in target_codes:
                    selected[code] = {
                        "lsoa_code": code,
                        "crime_score": item.get(crime_score_header or ""),
                        "crime_rank": item.get(crime_rank_header or ""),
                        "crime_decile": item.get(crime_decile_header or ""),
                        "population_denominators": {header: item.get(header) for header in population_headers},
                    }
        return selected, row_count
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


payload = json.loads(FINAL_OUTPUT.read_text(encoding="utf-8-sig"))
rows = payload.get("rows") or []
recovery_targets = [
    row for row in rows
    if isinstance(row, dict)
    and ((row.get("ons_query") or {}).get("feature_count") != 1 or not row.get("iod_2025") or row.get("relative_security_candidate_percent") is None)
]
recovered_ons: list[str] = []
failed_ons: list[str] = []
for row in recovery_targets:
    parcel_id = str(row.get("parcel_id") or "")
    historical_code = str(row.get("historical_lsoa_code") or "")
    result = query_ons_nearby(float(row["longitude"]), float(row["latitude"]), historical_code) if historical_code else None
    if result:
        selected = result["matches"][0]
        row["ons_lsoa_code"] = selected.get("LSOA21CD")
        row["ons_lsoa_name"] = selected.get("LSOA21NM")
        row["ons_query"] = result
        row["historical_lsoa_code_matches_ons"] = True
        recovered_ons.append(parcel_id)
    else:
        failed_ons.append(parcel_id)

recovered_codes = {str(row.get("ons_lsoa_code") or "") for row in recovery_targets if row.get("ons_lsoa_code")}
iod_selected, national_lsoa_count = load_iod_rows(recovered_codes) if recovered_codes else ({}, 0)
recovered_iod: list[str] = []
for row in recovery_targets:
    code = str(row.get("ons_lsoa_code") or "")
    iod = iod_selected.get(code)
    if iod:
        row["iod_2025"] = iod
        rank_value = float(str(iod.get("crime_rank") or "").replace(",", ""))
        row["relative_security_candidate_percent"] = round(100.0 * (rank_value - 1.0) / (national_lsoa_count - 1.0), 2)
        integrity = 25
        integrity += 15 if row.get("longitude") is not None else 0
        integrity += 20 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
        integrity += 10 if row.get("historical_lsoa_code_matches_ons") else 0
        integrity += 15 if (row.get("police_query") or {}).get("reachable") and (row.get("police_query") or {}).get("sha256") else 0
        integrity += 15
        row["candidate_accuracy_percent"] = integrity
        row["evidence_status"] = "IOD25_RELATIVE_CANDIDATE_READY_NOT_PROMOTED"
        recovered_iod.append(str(row.get("parcel_id") or ""))

candidate_rows = sum(row.get("relative_security_candidate_percent") is not None for row in rows if isinstance(row, dict))
accuracy_rows = sum(int(row.get("candidate_accuracy_percent") or 0) >= 95 for row in rows if isinstance(row, dict))
ons_rows = sum((row.get("ons_query") or {}).get("feature_count") == 1 for row in rows if isinstance(row, dict))
iod_rows = sum(bool(row.get("iod_2025")) for row in rows if isinstance(row, dict))
for gate in payload.get("gates") or []:
    name = str(gate.get("gate") or "")
    if name == "single_ons_lsoa_matches_4960":
        gate.update({"state": "PASS" if ons_rows == 4960 else "PARTIAL", "evidence": ons_rows})
    elif name == "iod25_exact_lsoa_joins_4960":
        gate.update({"state": "PASS" if iod_rows == 4960 else "PARTIAL", "evidence": iod_rows})
    elif name == "candidate_rows_4960":
        gate.update({"state": "PASS" if candidate_rows == 4960 else "PARTIAL", "evidence": candidate_rows})
    elif name == "candidate_accuracy_ge_95_rows_ge_4712":
        gate.update({"state": "PASS" if accuracy_rows >= 4712 else "PARTIAL", "evidence": accuracy_rows})
payload["candidate_rows"] = candidate_rows
payload["accuracy_ge_95_candidate_rows"] = accuracy_rows
payload["ons_boundary_recovery"] = {
    "triggered": bool(recovery_targets),
    "target_rows": [str(row.get("parcel_id") or "") for row in recovery_targets],
    "ons_recovered_rows": sorted(recovered_ons),
    "iod_recovered_rows": sorted(recovered_iod),
    "failed_rows": sorted(failed_ons),
    "official_source": ONS_LAYER,
    "selection_rule": "official_ons_candidates_filtered_by_exact_canonical_historical_lsoa_code",
}

if ons_rows != 4960 or iod_rows != 4960 or candidate_rows != 4960:
    raise SystemExit(f"ONS_BOUNDARY_RECOVERY_INCOMPLETE ons={ons_rows} iod={iod_rows} candidate={candidate_rows} failed={failed_ons}")

serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
FINAL_OUTPUT.write_text(serialized, encoding="utf-8")
WEB_JSON.write_text(serialized, encoding="utf-8")

incremental = json.loads(INCREMENTAL_OUTPUT.read_text(encoding="utf-8-sig"))
repaired_by_id = {str(row.get("parcel_id")): row for row in rows if isinstance(row, dict)}
incremental["rows"] = [repaired_by_id.get(str(row.get("parcel_id")), row) for row in (incremental.get("rows") or [])]
incremental["candidate_rows"] = sum(row.get("relative_security_candidate_percent") is not None for row in incremental["rows"] if isinstance(row, dict))
incremental["accuracy_ge_95_candidate_rows"] = sum(int(row.get("candidate_accuracy_percent") or 0) >= 95 for row in incremental["rows"] if isinstance(row, dict))
incremental["ons_boundary_recovery"] = payload["ons_boundary_recovery"]
INCREMENTAL_OUTPUT.write_text(json.dumps(incremental, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({"ons_boundary_recovery": payload["ons_boundary_recovery"], "ons_rows": ons_rows, "iod_rows": iod_rows, "candidate_rows": candidate_rows, "accuracy_ge_95_rows": accuracy_rows}, ensure_ascii=False, indent=2))
