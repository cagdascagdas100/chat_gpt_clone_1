from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path.cwd()
HARDENED_REL = "docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_hardened_20260722.py"
HARDENED_PATH = ROOT / HARDENED_REL
EXPECTED_HARDENED_BLOB = "cdb20cb578be5de1789e7821d2a435c1a9f77d58"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"JOIN_PATCH_FRAGMENT_{label}_COUNT={count}")
    return text.replace(old, new, 1)


if not HARDENED_PATH.is_file():
    raise SystemExit(f"HARDENED_ENTRY_MISSING={HARDENED_REL}")
actual_blob = git_blob_sha(HARDENED_PATH)
if actual_blob != EXPECTED_HARDENED_BLOB:
    raise SystemExit(f"HARDENED_ENTRY_BLOB_MISMATCH={actual_blob}")

code = HARDENED_PATH.read_text(encoding="utf-8")
old_terminal = '''namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)'''
new_terminal = r"""# Retry-5 candidate-only IoD25 join extension. This mutates the already-hardened
# generated base script before it executes, so the official File 7 download is
# reused and never downloaded twice.
join_iod_inspector = '''def inspect_iod_csv(path: Path) -> dict[str, Any]:
    row_count = 0
    unique_lsoa: set[str] = set()
    duplicate_lsoa: set[str] = set()
    rank_values: list[int] = []
    invalid_rank_count = 0
    invalid_decile_count = 0
    rows_by_lsoa: dict[str, dict[str, Any]] = {}
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
            decile_raw = str(row.get(crime_decile_header or "", "")).strip()
            score_raw = str(row.get(crime_score_header or "", "")).strip()
            rank = None
            decile = None
            score = None
            try:
                rank = int(float(rank_raw))
                rank_values.append(rank)
            except ValueError:
                invalid_rank_count += 1
            try:
                decile = int(float(decile_raw))
                if not 1 <= decile <= 10:
                    invalid_decile_count += 1
            except ValueError:
                invalid_decile_count += 1
            try:
                score = float(score_raw)
            except ValueError:
                score = None
            if code and rank is not None and decile is not None:
                rows_by_lsoa[code] = {
                    "lsoa21_code": code,
                    "crime_rank": rank,
                    "crime_decile": decile,
                    "crime_score": score,
                }
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
        and len(rows_by_lsoa) == expected_count
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
        "_rows_by_lsoa": rows_by_lsoa,
    }'''
text = replace_between(text, "def inspect_iod_csv(path: Path) -> dict[str, Any]:", "def xlsx_sheet_names", join_iod_inspector, "JOIN_IOD_INSPECTOR")
text = replace_exact(
    text,
    "police_date = next(\n",
    "iod_rows_by_lsoa = iod_schema.pop(\"_rows_by_lsoa\", {})\n\npolice_date = next(\n",
    "JOIN_MAPPING_EXTRACT",
)
join_block = '''id_continuity_pass = set(target_features) == set(TARGET_IDS)
feature_count_pass = actual_feature_count == 92283

for row in rows:
    lsoa_code = str(row.get("ons_lsoa_code") or "")
    iod_row = iod_rows_by_lsoa.get(lsoa_code)
    rank = iod_row.get("crime_rank") if iod_row else None
    decile = iod_row.get("crime_decile") if iod_row else None
    join_ready = bool(
        source_blob == "bb48164e7a0af78df875f30421a6a3068c43edb8"
        and feature_count_pass
        and id_continuity_pass
        and (row.get("ons_query") or {}).get("feature_count") == 1
        and iod_schema.get("schema_gate_pass")
        and iod_download.get("reachable")
        and iod_download.get("sha256")
        and method_preregistered
        and isinstance(rank, int)
        and 1 <= rank <= 33755
        and isinstance(decile, int)
        and 1 <= decile <= 10
    )
    candidate_integrity = 0
    candidate_integrity += 25 if id_continuity_pass else 0
    candidate_integrity += 20 if row.get("geometry_type") == "Point" and row.get("longitude") is not None else 0
    candidate_integrity += 25 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
    candidate_integrity += 20 if iod_row and iod_schema.get("schema_gate_pass") and iod_download.get("sha256") else 0
    candidate_integrity += 10 if method_preregistered else 0
    row["iod25_lsoa_code"] = iod_row.get("lsoa21_code") if iod_row else None
    row["iod25_crime_rank"] = rank
    row["iod25_crime_decile"] = decile
    row["iod25_crime_score_official"] = iod_row.get("crime_score") if iod_row else None
    row["candidate_value"] = round(100 * (rank - 1) / (33755 - 1), 1) if join_ready else None
    row["candidate_semantics"] = "RELATIVE_LSOA_CRIME_DOMAIN_ORDINAL_POSITION_CANDIDATE_NOT_CARDINAL_SAFETY_SCORE"
    row["candidate_evidence_integrity_percent"] = candidate_integrity
    row["candidate_status"] = "IOD25_ORDINAL_CANDIDATE_READY_BROWSER_PENDING" if join_ready else "IOD25_EXACT_JOIN_BLOCKED"
    row["business_score"] = None
    row["business_confidence"] = 0
    row["promotion_allowed"] = False

iod25_joined_candidate_rows = sum(item.get("candidate_value") is not None for item in rows)
accuracy_ge_95_candidate_rows = sum(int(item.get("candidate_evidence_integrity_percent") or 0) >= 95 for item in rows)
'''
text = replace_exact(
    text,
    '''id_continuity_pass = set(target_features) == set(TARGET_IDS)
feature_count_pass = actual_feature_count == 92283
''',
    join_block,
    "JOIN_ROWS",
)
text = replace_exact(
    text,
    '{"gate": "join_current_v2_iod25_to_12_exact_lsoa_rows", "state": "PENDING"},',
    '{"gate": "join_current_v2_iod25_to_12_exact_lsoa_rows", "state": "PASS" if iod25_joined_candidate_rows == 12 else "PARTIAL", "evidence": iod25_joined_candidate_rows},',
    "JOIN_GATE_STATE",
)
text = replace_exact(
    text,
    '"state": "TWELVE_UNIQUE_POINT_LSOA_POLICE_ROWS_STRONG_SCHEMAS_AND_ORDINAL_METHOD_PREPARED",',
    '"state": "TWELVE_EXACT_LSOA_CURRENT_V2_IOD25_ORDINAL_CANDIDATES_PREPARED_BROWSER_PENDING",',
    "JOIN_STATE",
)
text = replace_exact(
    text,
    '"first_unverified_step": "JOIN_CURRENT_V2_IOD25_TO_12_EXACT_LSOA_ROWS_THEN_BROWSER_ACCEPTANCE",',
    '"first_unverified_step": "SERVED_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_THEN_EXPAND_300",',
    "JOIN_FIRST_STEP",
)
text = replace_exact(
    text,
    '"accuracy_ge_95_evidence_rows": accuracy_ge_95_rows,',
    '"accuracy_ge_95_evidence_rows": accuracy_ge_95_rows,\n    "iod25_joined_candidate_rows": iod25_joined_candidate_rows,\n    "accuracy_ge_95_candidate_rows": accuracy_ge_95_candidate_rows,',
    "JOIN_PAYLOAD_COUNTS",
)
text = replace_exact(
    text,
    '"next_required_action": "Join the current corrected v2 IoD25 Crime Rank and official Crime Decile to the 12 exact verified LSOA codes using the published ordinal method; keep Police.uk context separate and expand only after served acceptance.",',
    '"next_required_action": "Run served HTTP JSON-hash DOM console browser acceptance for the 12 exact IoD25 ordinal candidates; expand to 300 only after acceptance.",',
    "JOIN_NEXT_ACTION",
)
text = replace_exact(
    text,
    "<div class='notice'>12 parsel için unique Point → resmî ONS LSOA → Police.uk açık ay kanıtı hazırlanır. IoD25 değerleri yalnız ordinal göreli bağlamdır; Police.uk bir mil yaklaşık sonuçları oran veya skora çevrilmez. Business skoru null kalır.</div>",
    "<div class='notice'>12 parsel için unique Point → resmî ONS LSOA → corrected v2 IoD25 Crime Rank/Decile candidate join hazırlanır. Candidate yalnız ordinal göreli bağlamdır; Police.uk bir mil yaklaşık sonuçları oran veya skora çevrilmez. Business skoru null kalır.</div>",
    "JOIN_HTML_NOTICE",
)
text = replace_exact(
    text,
    'f"<td>{html.escape(str(item.get(\'evidence_status\')))}</td><td>null</td></tr>"',
    'f"<td>{html.escape(str(item.get(\'evidence_status\')))}</td>"\n    f"<td>{html.escape(str(item.get(\'iod25_crime_rank\') or \'-\'))}</td>"\n    f"<td>{html.escape(str(item.get(\'iod25_crime_decile\') or \'-\'))}</td>"\n    f"<td>{html.escape(str(item.get(\'candidate_value\') if item.get(\'candidate_value\') is not None else \'-\'))}</td>"\n    f"<td>{html.escape(str(item.get(\'candidate_evidence_integrity_percent\') or 0))}%</td><td>null</td></tr>"',
    "JOIN_HTML_ROWS",
)
text = replace_exact(
    text,
    '<th>Kanıt bütünlüğü</th><th>Durum</th><th>Skor</th>',
    '<th>Kanıt bütünlüğü</th><th>Durum</th><th>IoD25 rank</th><th>Crime decile</th><th>Ordinal candidate</th><th>Candidate kanıtı</th><th>Business skor</th>',
    "JOIN_HTML_HEADERS",
)
text = replace_exact(
    text,
    '<div class=\'card\'>Kanıtı geçen satır<br><b>{verified_evidence_rows}</b></div><div class=\'card\'>≥95 satır kanıtı<br><b>{accuracy_ge_95_rows}</b></div>',
    '<div class=\'card\'>Kanıtı geçen satır<br><b>{verified_evidence_rows}</b></div><div class=\'card\'>≥95 satır kanıtı<br><b>{accuracy_ge_95_rows}</b></div>\n<div class=\'card\'>IoD25 aday join<br><b>{iod25_joined_candidate_rows}</b></div><div class=\'card\'>≥95 aday kanıtı<br><b>{accuracy_ge_95_candidate_rows}</b></div>',
    "JOIN_HTML_CARDS",
)
text = replace_exact(
    text,
    '"verified_slot_rows": 0,\n    "promoted_sources": len(source_promoted),',
    '"verified_slot_rows": 0,\n    "iod25_joined_candidate_rows": iod25_joined_candidate_rows,\n    "accuracy_ge_95_candidate_rows": accuracy_ge_95_candidate_rows,\n    "promoted_sources": len(source_promoted),',
    "JOIN_STDOUT_COUNTS",
)
namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)"""
code = replace_exact(code, old_terminal, new_terminal, "TERMINAL_EXTENSION")
namespace = {"__name__": "__main__", "__file__": str(HARDENED_PATH), "__package__": None}
exec(compile(code, str(HARDENED_PATH), "exec"), namespace, namespace)
