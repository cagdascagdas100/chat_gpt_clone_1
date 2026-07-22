from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path.cwd()
SOURCE_REL = "docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_20260722.py"
SOURCE = ROOT / SOURCE_REL
EXPECTED_SOURCE_BLOB = "ce080f565fc79c99e6a98df0afb9302c6b98343d"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_FRAGMENT_{label}_COUNT={count}")
    return text.replace(old, new, 1)


if not SOURCE.is_file():
    raise SystemExit(f"WAVE2_SOURCE_MISSING={SOURCE_REL}")
actual_blob = git_blob_sha(SOURCE)
if actual_blob != EXPECTED_SOURCE_BLOB:
    raise SystemExit(f"WAVE2_SOURCE_BLOB_MISMATCH={actual_blob}")

text = SOURCE.read_text(encoding="utf-8")
text = replace_exact(
    text,
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-method-wave/3.0"',
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-method-wave/4.0-ordinal-corrected"',
    "USER_AGENT",
)

old_loader = '''def load_iod_rows(path: Path, target_codes: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
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
'''
new_loader = '''def load_iod_rows(path: Path, target_codes: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    row_count = 0
    unique_codes: set[str] = set()
    duplicate_codes: set[str] = set()
    rank_values: list[int] = []
    rank_missing_count = 0
    decile_invalid_count = 0
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
            if code:
                if code in unique_codes:
                    duplicate_codes.add(code)
                unique_codes.add(code)
            rank_raw = str(row.get(crime_rank_header or "", "")).replace(",", "").strip()
            try:
                rank_value = int(float(rank_raw))
                rank_values.append(rank_value)
            except ValueError:
                rank_missing_count += 1
            decile_raw = str(row.get(crime_decile_header or "", "")).strip()
            try:
                decile_value = int(float(decile_raw))
                if not 1 <= decile_value <= 10:
                    decile_invalid_count += 1
            except ValueError:
                decile_invalid_count += 1
            if code in target_codes:
                if code in selected:
                    selected[code]["duplicate_match"] = True
                else:
                    selected[code] = {
                        "lsoa_code": code,
                        "crime_score": row.get(crime_score_header or ""),
                        "crime_rank": row.get(crime_rank_header or ""),
                        "crime_decile": row.get(crime_decile_header or ""),
                        "population_denominators": {header: row.get(header) for header in population_headers},
                        "duplicate_match": False,
                    }
    expected_count = 33755
    schema = {
        "headers": headers,
        "row_count": row_count,
        "expected_lsoa_count": expected_count,
        "unique_lsoa_count": len(unique_codes),
        "duplicate_lsoa_count": len(duplicate_codes),
        "rank_min": min(rank_values) if rank_values else None,
        "rank_max": max(rank_values) if rank_values else None,
        "unique_rank_count": len(set(rank_values)),
        "rank_missing_count": rank_missing_count,
        "decile_invalid_count": decile_invalid_count,
        "code_header": code_header,
        "crime_score_header": crime_score_header,
        "crime_rank_header": crime_rank_header,
        "crime_decile_header": crime_decile_header,
        "population_headers": population_headers,
        "target_lsoa_count": len(target_codes),
        "matched_target_lsoa_count": len(selected),
        "current_corrected_v2_release_route_required": True,
        "schema_gate_pass": bool(
            code_header and crime_score_header and crime_rank_header and crime_decile_header and population_headers
            and row_count == expected_count
            and len(unique_codes) == expected_count
            and not duplicate_codes
            and rank_missing_count == 0
            and decile_invalid_count == 0
            and min(rank_values or [0]) == 1
            and max(rank_values or [0]) == expected_count
            and len(set(rank_values)) == expected_count
        ),
    }
    return selected, schema
'''
text = replace_exact(text, old_loader, new_loader, "IOD_LOADER")

old_candidate = '''national_lsoa_count = int(iod_schema.get("row_count") or 0)
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
'''
new_candidate = '''national_lsoa_count = int(iod_schema.get("row_count") or 0)
for row in rows:
    code = str(row.get("ons_lsoa_code") or "")
    iod = iod_selected.get(code)
    row["iod_2025"] = iod
    rank_value: int | None = None
    try:
        rank_value = int(float(str((iod or {}).get("crime_rank") or "").replace(",", "")))
    except ValueError:
        rank_value = None
    candidate_percent = None
    rank_in_range = bool(rank_value is not None and 1 <= rank_value <= national_lsoa_count)
    unique_target_join = bool(iod and not iod.get("duplicate_match"))
    if iod_schema.get("schema_gate_pass") and rank_in_range and unique_target_join and national_lsoa_count > 1:
        candidate_percent = round(100.0 * (rank_value - 1.0) / (national_lsoa_count - 1.0), 1)
    integrity = 0
    integrity += 20 if row.get("parcel_id") in target_features else 0
    integrity += 20 if row.get("longitude") is not None else 0
    integrity += 25 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
    integrity += 15 if row.get("historical_lsoa_code_matches_ons") else 0
    integrity += 20 if unique_target_join and rank_in_range else 0
    row["less_deprived_ordinal_position_percent"] = candidate_percent
    row["relative_security_candidate_percent"] = None
    row["legacy_relative_security_field_deprecated"] = True
    row["candidate_method"] = "Ordinal position only: 100*(IoD2025 Crime Rank-1)/(33755-1); rank 1 most deprived; differences are not cardinal safety differences"
    row["candidate_accuracy_percent"] = integrity
    row["police_context_excluded_from_candidate_confidence"] = True
    row["evidence_status"] = "IOD25_CRIME_DOMAIN_ORDINAL_CANDIDATE_READY_NOT_PROMOTED" if candidate_percent is not None else "EVIDENCE_PARTIAL_CANDIDATE_BLOCKED"
    row["business_score"] = None
    row["business_confidence"] = 0
    row["promotion_allowed"] = False
'''
text = replace_exact(text, old_candidate, new_candidate, "CANDIDATE_BLOCK")

replacements = [
    ('candidate_rows = sum(row.get("relative_security_candidate_percent") is not None for row in rows)', 'candidate_rows = sum(row.get("less_deprived_ordinal_position_percent") is not None for row in rows)', "CANDIDATE_COUNT"),
    ('{"gate": "rank_direction_documented", "state": "PASS", "evidence": "IoD25 rank 1 most deprived; highest rank least deprived"},', '{"gate": "rank_direction_and_noncardinal_interpretation_documented", "state": "PASS", "evidence": "IoD25 rank 1 most deprived; ranks provide relative order and not proportional safety differences"},\n    {"gate": "current_corrected_v2_file7_universe_unique_rank_validation", "state": "PASS" if iod_schema.get("schema_gate_pass") else "BLOCKED", "evidence": {"rows": iod_schema.get("row_count"), "unique_lsoa": iod_schema.get("unique_lsoa_count"), "unique_ranks": iod_schema.get("unique_rank_count")}},', "RANK_GATES"),
    ('{"gate": "relative_candidate_formula_documented", "state": "PASS"},', '{"gate": "ordinal_candidate_formula_documented", "state": "PASS"},\n    {"gate": "police_point_query_excluded_from_candidate_confidence", "state": "PASS", "evidence": "Police.uk one-mile approximate point results remain context only"},', "METHOD_GATES"),
    ('{"gate": "candidate_method_calibration_review", "state": "PENDING"},', '{"gate": "ordinal_method_human_review", "state": "PENDING"},', "HUMAN_REVIEW_GATE"),
    ('"state": "IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED",', '"state": "IOD25_CRIME_DOMAIN_ORDINAL_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED",', "STATE"),
    ('"first_unverified_step": "CALIBRATE_CANDIDATE_METHOD_THEN_EXPAND_TO_300_AND_BROWSER_ACCEPTANCE",', '"first_unverified_step": "HUMAN_REVIEW_ORDINAL_METHOD_THEN_BROWSER_ACCEPTANCE",', "FIRST_STEP"),
    ('"formula": "100*(IoD2025 Crime Rank-1)/(national LSOA count-1)",\n        "interpretation": "0 means most crime-deprived relative LSOA; 100 means least crime-deprived relative LSOA",', '"formula": "less_deprived_ordinal_position_percent = 100*(IoD2025 Crime Rank-1)/(33755-1)",\n        "interpretation": "Ordinal relative Crime Domain position only; 0 is rank 1 and 100 is rank 33755. Differences are not proportional safety differences.",', "METHOD_PAYLOAD"),
    ('"status": "CANDIDATE_ONLY_NOT_BUSINESS_SCORE",', '"status": "ORDINAL_CONTEXT_CANDIDATE_ONLY_NOT_CARDINAL_SAFETY_OR_BUSINESS_SCORE",', "METHOD_STATUS"),
    ('"IoD Crime Rank is a relative small-area indicator, not an exact parcel incident rate.",', '"IoD Crime Rank is an ordinal relative small-area indicator; rank differences do not quantify proportional deprivation or safety differences.",', "BLOCKER_IOD"),
    ('"Police.uk street locations are anonymised approximations and overlapping point queries are not independent parcel counts.",', '"Police.uk street locations are anonymised one-mile-context approximations and are excluded from IoD candidate confidence and scoring.",', "BLOCKER_POLICE"),
    ('"next_required_action": "Review the relative method against documented IoD limitations, then use only accepted rows for a 300-row evidence expansion and browser acceptance.",', '"next_required_action": "Human-review the ordinal interpretation and current-v2 File 7 validation, then use only exact accepted LSOA joins for later expansion and browser acceptance.",', "NEXT_ACTION"),
    ("item.get('relative_security_candidate_percent')", "item.get('less_deprived_ordinal_position_percent')", "HTML_VALUE"),
    ("<th>Göreli aday %</th>", "<th>Less-deprived ordinal konum %</th>", "HTML_HEADER"),
    ("Gösterilen yüzde yalnız IoD25 Crime Rank tabanlı göreli adaydır.", "Gösterilen yüzde yalnız IoD25 Crime Rank tabanlı ordinal konumdur; kardinal güvenlik skoru değildir.", "HTML_NOTICE"),
]
for old, new, label in replacements:
    text = replace_exact(text, old, new, label)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
