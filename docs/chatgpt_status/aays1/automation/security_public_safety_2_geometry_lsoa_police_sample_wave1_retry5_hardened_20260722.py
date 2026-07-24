from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path.cwd()
SOURCE_REL = "docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_20260722.py"
SOURCE = ROOT / SOURCE_REL
EXPECTED_SOURCE_BLOB = "d29c33ea894878f063fc930692cc684176fb291a"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_FRAGMENT_{label}_COUNT={count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    start_count = text.count(start)
    end_count = text.count(end)
    if start_count != 1 or end_count != 1:
        raise SystemExit(f"PATCH_BOUNDARY_{label}_START={start_count}_END={end_count}")
    left, remainder = text.split(start, 1)
    _, right = remainder.split(end, 1)
    return left + replacement + "\n\n" + end + right


if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING={SOURCE_REL}")
actual_source_blob = git_blob_sha(SOURCE)
if actual_source_blob != EXPECTED_SOURCE_BLOB:
    raise SystemExit(f"SOURCE_SCRIPT_BLOB_MISMATCH={actual_source_blob}")

text = SOURCE.read_text(encoding="utf-8")
text = replace_exact(
    text,
    'PREVIOUS_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/source_and_sample_gate_latest.json"',
    'PREVIOUS_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/source_and_sample_gate_latest.json"\nMETHOD_PATH = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/official_security_scoring_method_preregistration_20260722.json"',
    "METHOD_PATH",
)
text = replace_exact(
    text,
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-evidence-wave/2.0"',
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-evidence-wave/3.0-hardened"',
    "USER_AGENT",
)
text = replace_exact(
    text,
    '"https://use-land-property-data.service.gov.uk/datasets/inspire/download"',
    '"https://use-land-property-data.service.gov.uk/datasets/inspire"',
    "HMLR_URL",
)
text = replace_exact(
    text,
    '"name": "HM Land Registry INSPIRE Index Polygons download"',
    '"name": "HM Land Registry INSPIRE Index Polygons dataset"',
    "HMLR_NAME",
)
text = replace_exact(
    text,
    '"role": "indicative_freehold_polygon_download"',
    '"role": "indicative_freehold_dataset_access_page"',
    "HMLR_ROLE",
)

new_iod_inspector = '''def inspect_iod_csv(path: Path) -> dict[str, Any]:
    row_count = 0
    unique_lsoa: set[str] = set()
    duplicate_lsoa: set[str] = set()
    rank_values: list[int] = []
    invalid_rank_count = 0
    invalid_decile_count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        lowered = {header: header.strip().casefold() for header in headers}
        code_header = next((header for header, value in lowered.items() if "lsoa" in value and "code" in value), None)
        crime_score_header = next((header for header, value in lowered.items() if value.startswith("crime score")), None)
        crime_rank_header = next((header for header, value in lowered.items() if value.startswith("crime rank")), None)
        crime_decile_header = next((header for header, value in lowered.items() if value.startswith("crime decile")), None)
        population_headers = [header for header, value in lowered.items() if "population" in value]
        for row in reader:
            row_count += 1
            code = str(row.get(code_header or "", "")).strip()
            if code:
                if code in unique_lsoa:
                    duplicate_lsoa.add(code)
                unique_lsoa.add(code)
            rank_raw = str(row.get(crime_rank_header or "", "")).replace(",", "").strip()
            try:
                rank_values.append(int(float(rank_raw)))
            except ValueError:
                invalid_rank_count += 1
            decile_raw = str(row.get(crime_decile_header or "", "")).strip()
            try:
                decile = int(float(decile_raw))
                if not 1 <= decile <= 10:
                    invalid_decile_count += 1
            except ValueError:
                invalid_decile_count += 1
    expected_count = 33755
    unique_ranks = set(rank_values)
    schema_gate_pass = bool(
        code_header and crime_score_header and crime_rank_header and crime_decile_header and population_headers
        and row_count == expected_count
        and len(unique_lsoa) == expected_count
        and not duplicate_lsoa
        and invalid_rank_count == 0
        and invalid_decile_count == 0
        and min(rank_values or [0]) == 1
        and max(rank_values or [0]) == expected_count
        and len(unique_ranks) == expected_count
    )
    return {
        "headers": headers,
        "row_count": row_count,
        "expected_lsoa_count": expected_count,
        "unique_lsoa_count": len(unique_lsoa),
        "duplicate_lsoa_count": len(duplicate_lsoa),
        "rank_min": min(rank_values) if rank_values else None,
        "rank_max": max(rank_values) if rank_values else None,
        "unique_rank_count": len(unique_ranks),
        "invalid_rank_count": invalid_rank_count,
        "invalid_decile_count": invalid_decile_count,
        "lsoa_columns": [code_header] if code_header else [],
        "crime_columns": [header for header in (crime_score_header, crime_rank_header, crime_decile_header) if header],
        "crime_rank_columns": [crime_rank_header] if crime_rank_header else [],
        "crime_score_columns": [crime_score_header] if crime_score_header else [],
        "population_columns": population_headers,
        "current_corrected_v2_release_required": True,
        "schema_gate_pass": schema_gate_pass,
    }'''
text = replace_between(text, "def inspect_iod_csv(path: Path) -> dict[str, Any]:", "def xlsx_sheet_names", new_iod_inspector, "IOD_INSPECTOR")

new_ons_inspector = '''def inspect_ons_xlsx(path: Path) -> dict[str, Any]:
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        worksheet_names = [name for name in names if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")]
        shared_strings_present = "xl/sharedStrings.xml" in names
        searchable_text: list[str] = []
        if shared_strings_present:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", namespace):
                searchable_text.append("".join(node.text or "" for node in item.iter() if node.tag.endswith("}t")))
        for worksheet_name in worksheet_names[:4]:
            try:
                root = ET.fromstring(archive.read(worksheet_name))
                searchable_text.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
            except (KeyError, ET.ParseError):
                continue
    sheets = xlsx_sheet_names(path)
    folded = " ".join(searchable_text).casefold()
    has_lsoa_marker = "lsoa" in folded or "lower layer super output area" in folded
    has_2024_marker = "2024" in folded or any("2024" in name for name in sheets)
    has_population_marker = "population" in folded or "persons" in folded or "all ages" in folded
    return {
        "sheet_names": sheets,
        "worksheet_count": len(worksheet_names),
        "shared_strings_present": shared_strings_present,
        "mid_2024_sheet_candidates": [name for name in sheets if "2024" in name],
        "lsoa_marker_present": has_lsoa_marker,
        "population_marker_present": has_population_marker,
        "year_2024_marker_present": has_2024_marker,
        "schema_gate_pass": bool(sheets and worksheet_names and has_lsoa_marker and has_population_marker and has_2024_marker),
    }'''
text = replace_between(text, "def inspect_ons_xlsx(path: Path) -> dict[str, Any]:", "def file_hashes", new_ons_inspector, "ONS_INSPECTOR")

new_streamer = '''def stream_geojson_targets(path: Path, target_ids: list[str]) -> tuple[dict[str, dict[str, Any]], int]:
    decoder = json.JSONDecoder()
    wanted = set(target_ids)
    if len(wanted) != len(target_ids):
        raise RuntimeError("TARGET_ID_REQUEST_DUPLICATE")
    found: dict[str, dict[str, Any]] = {}
    duplicate_target_ids: set[str] = set()
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
                if parcel_id in found:
                    duplicate_target_ids.add(parcel_id)
                geometry = feature.get("geometry") or {}
                found[parcel_id] = {
                    "parcel_id": parcel_id,
                    "geometry_type": geometry.get("type"),
                    "coordinates": geometry.get("coordinates"),
                    "historical_lsoa_code": properties.get("security_lsoa_code"),
                    "historical_lsoa_name": properties.get("security_lsoa_name"),
                    "historical_spatial_match_method": properties.get("spatial_match_method"),
                    "historical_security_values_reused": False,
                }
            buffer = buffer[end:]

    if duplicate_target_ids:
        raise RuntimeError("DUPLICATE_TARGET_IDS=" + ",".join(sorted(duplicate_target_ids)))
    return found, count'''
text = replace_between(text, "def stream_geojson_targets(path: Path, target_ids: list[str]) -> tuple[dict[str, dict[str, Any]], int]:", "def ons_lsoa_query", new_streamer, "GEOJSON_STREAMER")

text = replace_exact(
    text,
    '''    valid_coordinate = (
        isinstance(coordinates, list)
        and len(coordinates) >= 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
        and -180 <= float(coordinates[0]) <= 180
        and -90 <= float(coordinates[1]) <= 90
    )''',
    '''    valid_coordinate = (
        base.get("geometry_type") == "Point"
        and isinstance(coordinates, list)
        and len(coordinates) == 2
        and isinstance(coordinates[0], (int, float))
        and isinstance(coordinates[1], (int, float))
        and -180 <= float(coordinates[0]) <= 180
        and -90 <= float(coordinates[1]) <= 90
    )''',
    "POINT_COORDINATE_GATE",
)

old_integrity = '''    integrity = 0
    integrity += 30
    integrity += 20
    integrity += 20 if len(ons_matches) == 1 else 0
    integrity += 10 if code_match else 0
    integrity += 15 if police.get("reachable") and police.get("sha256") else 0
    integrity += 5 if police_month else 0'''
new_integrity = '''    integrity = 0
    integrity += 25
    integrity += 20
    integrity += 30 if len(ons_matches) == 1 else 0
    integrity += 20 if police.get("reachable") and police.get("sha256") else 0
    integrity += 5 if police_month else 0'''
text = replace_exact(text, old_integrity, new_integrity, "INTEGRITY_POINTS")
text = replace_exact(
    text,
    '"evidence_integrity_formula": "30 exact internal parcel ID + 20 valid WGS84 point + 20 single ONS LSOA + 10 historical/ONS code agreement + 15 official Police.uk response hash + 5 explicit month",',
    '"evidence_integrity_formula": "25 unique exact internal parcel ID + 20 valid Point WGS84 geometry + 30 single official ONS LSOA + 20 official Police.uk response hash + 5 explicit month; historical LSOA agreement is displayed only as a cross-check",',
    "INTEGRITY_FORMULA",
)
text = replace_exact(
    text,
    '"score_blocker": "A documented LSOA rate/normalisation methodology and acceptance proof are still required.",',
    '"score_blocker": "The published IoD25 Crime Domain ordinal method, exact current-v2 LSOA join and served acceptance are required; Police.uk one-mile context is not a parcel rate or score.",',
    "SCORE_BLOCKER",
)

method_loader = '''method_preregistration: dict[str, Any] = {}
if METHOD_PATH.is_file():
    try:
        method_preregistration = json.loads(METHOD_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        method_preregistration = {}
method_preregistered = bool(
    method_preregistration.get("state") == "OFFICIAL_IOD25_RELATIVE_CRIME_ORDINAL_METHOD_PREREGISTERED_NO_SCORE"
    and method_preregistration.get("method_version") == "iod25-crime-rank-less-deprived-ordinal-position-v2"
    and method_preregistration.get("parcel_score_promotion_allowed") is False
)

'''
text = replace_exact(text, "police_date = next(\n", method_loader + "police_date = next(\n", "METHOD_LOAD")
text = replace_exact(
    text,
    '{"gate": "target_12_ids_continuous_and_unique", "state": "PASS" if id_continuity_pass else "BLOCKED", "evidence": len(target_features)},',
    '{"gate": "target_12_ids_continuous_and_unique", "state": "PASS" if id_continuity_pass else "BLOCKED", "evidence": len(target_features)},\n    {"gate": "target_duplicate_ids_fail_closed", "state": "PASS", "evidence": 0},',
    "DUPLICATE_GATE",
)
text = replace_exact(
    text,
    '{"gate": "iod_2025_lsoa_crime_population_schema", "state": "PASS" if iod_schema.get("schema_gate_pass") else "BLOCKED", "evidence": iod_schema.get("row_count")},',
    '{"gate": "iod_2025_current_v2_33755_unique_lsoa_rank_schema", "state": "PASS" if iod_schema.get("schema_gate_pass") else "BLOCKED", "evidence": {"rows": iod_schema.get("row_count"), "unique_lsoa": iod_schema.get("unique_lsoa_count"), "unique_ranks": iod_schema.get("unique_rank_count")}},',
    "IOD_GATE",
)
text = replace_exact(
    text,
    '{"gate": "ons_population_2024_workbook_schema", "state": "PASS" if ons_population_schema.get("schema_gate_pass") else "BLOCKED", "evidence": ons_population_schema.get("worksheet_count")},',
    '{"gate": "ons_population_2024_workbook_lsoa_population_year_schema", "state": "PASS" if ons_population_schema.get("schema_gate_pass") else "BLOCKED", "evidence": {"worksheets": ons_population_schema.get("worksheet_count"), "lsoa": ons_population_schema.get("lsoa_marker_present"), "population": ons_population_schema.get("population_marker_present"), "year_2024": ons_population_schema.get("year_2024_marker_present")}},',
    "ONS_GATE",
)
text = replace_exact(
    text,
    '{"gate": "documented_security_rate_and_score_method", "state": "PENDING"},',
    '{"gate": "official_iod25_ordinal_method_preregistered", "state": "PASS" if method_preregistered else "BLOCKED", "evidence": method_preregistration.get("method_version")},',
    "METHOD_GATE",
)
text = replace_exact(
    text,
    '{"gate": "join_i_2025_and_population_to_12_rows", "state": "PENDING"},',
    '{"gate": "join_current_v2_iod25_to_12_exact_lsoa_rows", "state": "PENDING"},',
    "JOIN_GATE",
)
text = replace_exact(
    text,
    '"state": "TWELVE_POINT_LSOA_POLICE_ROWS_AND_OFFICIAL_METHOD_DATA_SCHEMAS_PREPARED",',
    '"state": "TWELVE_UNIQUE_POINT_LSOA_POLICE_ROWS_STRONG_SCHEMAS_AND_ORDINAL_METHOD_PREPARED",',
    "STATE",
)
text = replace_exact(
    text,
    '"first_unverified_step": "JOIN_IOD2025_AND_POPULATION_TO_12_ROWS_THEN_DOCUMENT_RATE_METHOD",',
    '"first_unverified_step": "JOIN_CURRENT_V2_IOD25_TO_12_EXACT_LSOA_ROWS_THEN_BROWSER_ACCEPTANCE",',
    "FIRST_STEP",
)
text = replace_exact(
    text,
    '"dataset_schemas": {"iod_2025_file7": iod_schema, "ons_lsoa_population_2024": ons_population_schema},',
    '"dataset_schemas": {"iod_2025_file7": iod_schema, "ons_lsoa_population_2024": ons_population_schema},\n    "method_preregistration": {"path": str(METHOD_PATH.relative_to(ROOT)), "valid": method_preregistered, "method_version": method_preregistration.get("method_version")},',
    "METHOD_PAYLOAD",
)
text = replace_exact(
    text,
    '"progress_formula": "PASS evidence/preparation gates divided by 21, capped at 65 percent until a documented rate/score method and verified business rows exist.",',
    '"progress_formula": "PASS evidence/preparation gates divided by the current gate count, capped at 65 percent until exact current-v2 IoD25 joins and verified business rows exist.",',
    "PROGRESS_FORMULA",
)
text = replace_exact(
    text,
    '"A current LSOA population denominator and documented crime-rate normalisation method must be joined before any security score is promoted.",',
    '"The IoD25 Crime Rank is ordinal relative context only; current-v2 exact LSOA joins and acceptance are required, and Police.uk one-mile point counts must not be normalised with an LSOA population denominator.",',
    "BLOCKER_METHOD",
)
text = replace_exact(
    text,
    '"next_required_action": "Join the downloaded IoD 2025 crime-domain and ONS mid-2024 population fields to the 12 verified LSOA codes, document a rate/score formula, then expand to 300 only after acceptance.",',
    '"next_required_action": "Join the current corrected v2 IoD25 Crime Rank and official Crime Decile to the 12 exact verified LSOA codes using the published ordinal method; keep Police.uk context separate and expand only after served acceptance.",',
    "NEXT_ACTION",
)
text = replace_exact(
    text,
    "<div class='notice'>12 parsel için Point → ONS LSOA → Police.uk açık ay kanıtı hazırlanmıştır. Business skoru hâlâ null; yöntem ve browser kabulü geçmeden yükseltilmez.</div>",
    "<div class='notice'>12 parsel için unique Point → resmî ONS LSOA → Police.uk açık ay kanıtı hazırlanır. IoD25 değerleri yalnız ordinal göreli bağlamdır; Police.uk bir mil yaklaşık sonuçları oran veya skora çevrilmez. Business skoru null kalır.</div>",
    "HTML_NOTICE",
)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
