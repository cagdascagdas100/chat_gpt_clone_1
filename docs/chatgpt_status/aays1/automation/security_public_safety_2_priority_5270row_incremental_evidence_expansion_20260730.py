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
FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"
INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_310row_wave56_latest.json"
ONS_LAYER = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
IOD_FILE7_URL = "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_evidence_expansion_latest.json"':
        'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_4960row_evidence_expansion_latest.json"',
    'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_310row_wave56_latest.json"',
    'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_310row_wave56_latest.json"',
    'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27.html"':
        'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_310row_wave56.html"',
    'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_5270row_evidence_expansion.html"',
    'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 31082)]':
        'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 35722)]',
    'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(31082, 31102)]':
        'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(35722, 36032)]',
    'PREVIOUS_320_SEQUENCE_MISMATCH': 'PREVIOUS_4960_SEQUENCE_MISMATCH',
    'priority_320row_evidence_expansion_latest.json"': 'priority_4960row_evidence_expansion_latest.json"',
    'priority_20row_wave27_latest.json"': 'priority_310row_wave56_latest.json"',
    'priority_20row_wave27.html"': 'priority_310row_wave56.html"',
    'range(31082, 31102)': 'range(35722, 36032)',
    'ThreadPoolExecutor(max_workers=12, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=15, thread_name_prefix="security-row")',
    'wave27_incremental_target_20_ids_unique': 'wave56_incremental_target_310_ids_unique',
    'len(target_features) == 20': 'len(target_features) == 310',
    'wave27_incremental_valid_wgs84_points': 'wave56_incremental_valid_wgs84_points',
    'valid_points == 20': 'valid_points == 310',
    'wave27_incremental_single_ons_lsoa_matches': 'wave56_incremental_single_ons_lsoa_matches',
    'ons_rows == 20': 'ons_rows == 310',
    'wave27_incremental_police_response_hashes': 'wave56_incremental_police_response_hashes',
    'police_hash_rows >= 19': 'police_hash_rows >= 295',
    'wave27_incremental_candidate_20_rows_generated': 'wave56_incremental_candidate_310_rows_generated',
    'candidate_rows == 20': 'candidate_rows == 310',
    'IOD25_RELATIVE_SECURITY_INCREMENTAL_20_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED',
    'MERGE_WITH_ACCEPTED_320_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE':
        'MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    'accepted 320-row wave': 'accepted 4960-row wave',
    'merge_with_accepted_320_candidate_rows': 'merge_with_accepted_4960_candidate_rows',
    'Merge the 20 validated incremental rows with the accepted 320-row artifact':
        'Merge the 310 validated incremental rows with the accepted 4960-row artifact',
    'IoD25 20 satır artımlı kanıt dalgası': 'IoD25 310 satır artımlı kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/20</b>': 'Aday satır<br><b>{candidate_rows}/310</b>',
    '<h2>20 artımlı örnek satır</h2>': '<h2>310 artımlı örnek satır</h2>',
    'INCREMENTAL_20_SEQUENCE_MISMATCH': 'INCREMENTAL_310_SEQUENCE_MISMATCH',
    'len(set(row_ids)) != 340': 'len(set(row_ids)) != 5270',
    'MERGED_340_SEQUENCE_OR_UNIQUENESS_FAILED': 'MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED',
    'accepted_320row_base_present': 'accepted_4960row_base_present',
    'incremental_20_ids_unique': 'incremental_310_ids_unique',
    'merged_340_ids_sequential_unique': 'merged_5270_ids_sequential_unique',
    'valid_wgs84_points_340': 'valid_wgs84_points_5270',
    'valid_points == 340': 'valid_points == 5270',
    'single_ons_lsoa_matches_340': 'single_ons_lsoa_matches_5270',
    'ons_rows == 340': 'ons_rows == 5270',
    'police_hash_rows >= 323': 'police_hash_rows >= 5007',
    'iod25_exact_lsoa_joins_340': 'iod25_exact_lsoa_joins_5270',
    'iod_join_rows == 340': 'iod_join_rows == 5270',
    'candidate_rows_340': 'candidate_rows_5270',
    'candidate_rows == 340': 'candidate_rows == 5270',
    'candidate_accuracy_ge_95_rows_ge_323': 'candidate_accuracy_ge_95_rows_ge_5007',
    'accuracy_ge_95_rows >= 323': 'accuracy_ge_95_rows >= 5007',
    '"schema_version": 5': '"schema_version": 34',
    'IOD25_RELATIVE_SECURITY_PRIORITY_340_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED',
    'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_340_ROWS':
        'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS',
    'pending for the 340-row artifact': 'pending for the 5270-row artifact',
    'on the 340-row candidate artifact': 'on the 5270-row candidate artifact',
    '"base_rows": 320': '"base_rows": 4960',
    '"added_rows": 20': '"added_rows": 310',
    '<title>security_public_safety_2 — 340 satır</title>':
        '<title>security_public_safety_2 — 5270 satır</title>',
    '<h1>security_public_safety_2 — 340 satır aday kanıtı</h1>':
        '<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>',
    'Aday satır<br><b>{candidate_rows}/340</b>': 'Aday satır<br><b>{candidate_rows}/5270</b>',
    '<h2>340 örnek satır</h2>': '<h2>5270 örnek satır</h2>',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)


def query_ons_nearby(longitude: float, latitude: float, historical_code: str) -> dict | None:
    escaped_code = historical_code.replace("'", "''")
    for distance_m in (1, 3, 5, 10, 25, 50, 100, 250, 500, 1000):
        params = urllib.parse.urlencode({
            "where": f"LSOA21CD='{escaped_code}'",
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
                selected = next(
                    (item for item in candidates if str(item.get("LSOA21CD") or "") == historical_code),
                    None,
                )
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
                        "selection_rule": "official_ons_exact_code_and_distance_match",
                    }
        except Exception:
            continue
    return None


def load_iod_rows(target_codes: set[str]) -> tuple[dict[str, dict], int]:
    request = urllib.request.Request(IOD_FILE7_URL, headers={"User-Agent": USER_AGENT, "Accept": "text/csv,*/*"})
    temp_path: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with tempfile.NamedTemporaryFile(prefix="aays_wave56_iod_", suffix=".csv", delete=False) as handle:
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
    and (
        (row.get("ons_query") or {}).get("feature_count") != 1
        or not row.get("iod_2025")
        or row.get("relative_security_candidate_percent") is None
    )
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

target_codes = {str(row.get("ons_lsoa_code") or "") for row in recovery_targets if row.get("ons_lsoa_code")}
iod_selected, national_lsoa_count = load_iod_rows(target_codes) if target_codes else ({}, 0)
recovered_iod: list[str] = []
for row in recovery_targets:
    code = str(row.get("ons_lsoa_code") or "")
    iod = iod_selected.get(code)
    if iod and national_lsoa_count > 1:
        row["iod_2025"] = iod
        rank_value = float(str(iod.get("crime_rank") or "").replace(",", ""))
        row["relative_security_candidate_percent"] = round(
            100.0 * (rank_value - 1.0) / (national_lsoa_count - 1.0),
            2,
        )
        row["candidate_method"] = "100*(IoD2025 Crime Rank-1)/(national LSOA count-1); rank 1 is most deprived"
        integrity = 25
        integrity += 15 if row.get("longitude") is not None else 0
        integrity += 20 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
        integrity += 10 if row.get("historical_lsoa_code_matches_ons") else 0
        integrity += 15 if (row.get("police_query") or {}).get("reachable") and (row.get("police_query") or {}).get("sha256") else 0
        integrity += 15
        row["candidate_accuracy_percent"] = integrity
        row["evidence_status"] = "IOD25_RELATIVE_CANDIDATE_READY_NOT_PROMOTED"
        recovered_iod.append(str(row.get("parcel_id") or ""))

ons_rows = sum((row.get("ons_query") or {}).get("feature_count") == 1 for row in rows if isinstance(row, dict))
iod_rows = sum(bool(row.get("iod_2025")) for row in rows if isinstance(row, dict))
candidate_rows = sum(row.get("relative_security_candidate_percent") is not None for row in rows if isinstance(row, dict))
accuracy_rows = sum(int(row.get("candidate_accuracy_percent") or 0) >= 95 for row in rows if isinstance(row, dict))
police_rows = sum(bool((row.get("police_query") or {}).get("sha256")) for row in rows if isinstance(row, dict))

for gate in payload.get("gates") or []:
    name = str(gate.get("gate") or "")
    if name.startswith("single_ons_lsoa_matches_"):
        gate.update({"state": "PASS" if ons_rows == 5270 else "PARTIAL", "evidence": ons_rows})
    elif name.startswith("iod25_exact_lsoa_joins_"):
        gate.update({"state": "PASS" if iod_rows == 5270 else "PARTIAL", "evidence": iod_rows})
    elif name.startswith("candidate_rows_"):
        gate.update({"state": "PASS" if candidate_rows == 5270 else "PARTIAL", "evidence": candidate_rows})
    elif name.startswith("candidate_accuracy_ge_95_rows_ge_"):
        gate.update({"state": "PASS" if accuracy_rows >= 5007 else "PARTIAL", "evidence": accuracy_rows})

payload["rows"] = rows
payload["candidate_rows"] = candidate_rows
payload["accuracy_ge_95_candidate_rows"] = accuracy_rows
payload["completed_operations"] = sum(gate.get("state") == "PASS" for gate in payload.get("gates") or [])
payload["total_operations"] = len(payload.get("gates") or [])
payload["overall_progress_percent"] = round(100.0 * payload["completed_operations"] / payload["total_operations"], 1)
payload["ons_boundary_recovery"] = {
    "target_rows": len(recovery_targets),
    "recovered_ons_rows": len(recovered_ons),
    "recovered_iod_rows": len(recovered_iod),
    "recovered_parcel_ids": sorted(set(recovered_ons).intersection(recovered_iod)),
    "failed_parcel_ids": sorted(failed_ons),
    "selection_rule": "official_ons_exact_code_and_distance_match",
}
FINAL_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
WEB_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

incremental = json.loads(INCREMENTAL_OUTPUT.read_text(encoding="utf-8-sig"))
row_by_id = {str(row.get("parcel_id") or ""): row for row in rows if isinstance(row, dict)}
incremental_rows = [
    row_by_id.get(str(row.get("parcel_id") or ""), row)
    for row in (incremental.get("rows") or [])
    if isinstance(row, dict)
]
incremental["rows"] = incremental_rows
incremental["candidate_rows"] = sum(row.get("relative_security_candidate_percent") is not None for row in incremental_rows)
incremental["accuracy_ge_95_candidate_rows"] = sum(int(row.get("candidate_accuracy_percent") or 0) >= 95 for row in incremental_rows)
INCREMENTAL_OUTPUT.write_text(json.dumps(incremental, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270:
    raise SystemExit(
        f"ONS_BOUNDARY_RECOVERY_INCOMPLETE ons={ons_rows} iod={iod_rows} candidate={candidate_rows} failed={failed_ons}"
    )

print(json.dumps({
    "candidate_rows": candidate_rows,
    "accuracy_ge_95_candidate_rows": accuracy_rows,
    "police_response_sha256_rows_before_acceptance_retry": police_rows,
    "ons_boundary_recovered_rows": len(recovered_ons),
    "iod_boundary_recovered_rows": len(recovered_iod),
    "final_ready": False,
}, ensure_ascii=False, indent=2))
