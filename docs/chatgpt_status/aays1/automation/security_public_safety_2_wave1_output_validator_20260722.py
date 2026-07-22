from __future__ import annotations

import hashlib
import html
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
ROOT = Path.cwd()
INPUT_REL = "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"
INPUT_PATH = ROOT / INPUT_REL
SHARD_JSON = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/wave1_output_validation_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/wave1_output_validation_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/wave1_output_validation_latest.html"
EXPECTED_IDS = [f"parcel_{value}" for value in range(30762, 30774)]
EXPECTED_POINT_BLOB = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_FEATURE_COUNT = 92283
LSOA_RE = re.compile(r"^E010\d{5}$")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def valid_point(row: dict[str, Any]) -> bool:
    coordinates = row.get("coordinates")
    return bool(
        row.get("geometry_type") == "Point"
        and isinstance(coordinates, list)
        and len(coordinates) == 2
        and all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in coordinates)
        and -180 <= float(coordinates[0]) <= 180
        and -90 <= float(coordinates[1]) <= 90
    )


def row_validation(index: int, row: dict[str, Any]) -> dict[str, Any]:
    parcel_id = str(row.get("parcel_id") or "")
    ons_query = row.get("ons_query") if isinstance(row.get("ons_query"), dict) else {}
    police_query = row.get("police_query") if isinstance(row.get("police_query"), dict) else {}
    police_sha = str(police_query.get("sha256") or "").lower()
    ons_code = str(row.get("ons_lsoa_code") or "")
    police_month = str(row.get("police_month") or "")
    checks = {
        "expected_position_id": parcel_id == EXPECTED_IDS[index],
        "exact_point_geometry": valid_point(row),
        "coordinate_blob_exact": str(row.get("coordinate_source_blob_sha") or "") == EXPECTED_POINT_BLOB,
        "ons_single_match": as_int(ons_query.get("feature_count"), -1) == 1,
        "ons_lsoa21_code_format": bool(LSOA_RE.fullmatch(ons_code)),
        "police_month_format": bool(MONTH_RE.fullmatch(police_month)),
        "police_response_reachable": police_query.get("reachable") is True,
        "police_response_sha256": bool(SHA256_RE.fullmatch(police_sha)),
        "evidence_integrity_ge_95": as_int(row.get("evidence_integrity_percent"), 0) >= 95,
        "business_score_null": row.get("business_score") is None,
        "business_confidence_zero": as_int(row.get("business_confidence"), -1) == 0,
        "promotion_forbidden": row.get("promotion_allowed") is False,
        "historical_values_not_reused": row.get("historical_security_values_reused") is False,
    }
    return {
        "row": index + 1,
        "parcel_id": parcel_id,
        "ons_lsoa_code": ons_code or None,
        "police_month": police_month or None,
        "police_response_sha256": police_sha or None,
        "evidence_integrity_percent": as_int(row.get("evidence_integrity_percent"), 0),
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "state": "PASS" if all(checks.values()) else "BLOCKED",
    }


def write_outputs(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for path in (SHARD_JSON, WEB_JSON):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    rows = "".join(
        "<tr>"
        f"<td>{item['row']}</td><td>{html.escape(item['parcel_id'])}</td>"
        f"<td>{html.escape(str(item.get('ons_lsoa_code') or '-'))}</td>"
        f"<td>{html.escape(str(item.get('police_month') or '-'))}</td>"
        f"<td><code>{html.escape(str(item.get('police_response_sha256') or '-'))}</code></td>"
        f"<td>{item['evidence_integrity_percent']}%</td>"
        f"<td>{item['passed_checks']}/{item['total_checks']}</td>"
        f"<td class='{item['state']}'>{item['state']}</td></tr>"
        for item in payload.get("row_validations", [])
    )
    operations = "".join(
        f"<tr><td>{item['row']}</td><td>{html.escape(item['operation'])}</td>"
        f"<td class='{item['state']}'>{item['state']}</td><td>{html.escape(str(item.get('evidence', '')))}</td></tr>"
        for item in payload.get("operations", [])
    )
    document = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>security_public_safety_2 — Wave1 output validation</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f4f6f8;color:#17202a}}.notice{{background:#fff3cd;border:1px solid #ffe69c;padding:12px}}.cards{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:12px;margin-top:14px}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}.PASS{{font-weight:700}}.BLOCKED,.PENDING{{font-weight:700}}code{{font-size:9px;word-break:break-all}}</style></head><body>
<h1>security_public_safety_2 — Wave1 çıktı doğrulaması</h1><div class='notice'>{html.escape(payload['summary'])}</div>
<div class='cards'><div class='card'>Durum<br><b>{html.escape(payload['state'])}</b></div><div class='card'>Satır<br><b>{payload['row_count']}/12</b></div><div class='card'>Geçen satır<br><b>{payload['passed_rows']}</b></div><div class='card'>≥95 satır<br><b>{payload['confidence_ge_95_rows']}</b></div><div class='card'>Business<br><b>{payload['business_rows_written']}</b></div><div class='card'>İşlem<br><b>{payload['operations_completed']}/{payload['operations_total']}</b></div></div>
<h2>12 satır</h2><table><thead><tr><th>#</th><th>Parsel</th><th>ONS LSOA</th><th>Police ay</th><th>Police SHA256</th><th>Kanıt</th><th>Kontrol</th><th>Durum</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Kabul işlemleri</h2><table><thead><tr><th>#</th><th>İşlem</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{operations}</tbody></table>
<p><b>final_ready:</b> false</p></body></html>"""
    WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
    WEB_HTML.write_text(document, encoding="utf-8")


def main() -> int:
    if not INPUT_PATH.is_file():
        payload = {
            "schema_version": 3,
            "slot_id": SLOT_ID,
            "state": "WAITING_WAVE1_OUTPUT",
            "summary": "Wave1 çıktısı henüz mevcut değil; validator skor veya business satırı üretmedi.",
            "input_path": INPUT_REL,
            "input_exists": False,
            "input_sha256": None,
            "row_count": 0,
            "passed_rows": 0,
            "confidence_ge_95_rows": 0,
            "business_rows_written": 0,
            "row_validations": [],
            "operations": [
                {"row": 1, "operation": "validator_contract_published", "state": "PASS"},
                {"row": 2, "operation": "wave1_output_exists", "state": "PENDING"},
                {"row": 3, "operation": "twelve_row_fail_closed_validation", "state": "PENDING"},
                {"row": 4, "operation": "served_http_json_dom_console_acceptance", "state": "PENDING"},
            ],
            "operations_completed": 1,
            "operations_total": 4,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
            "generated_at": utc_now(),
        }
        write_outputs(payload)
        return 2

    try:
        data = json.loads(INPUT_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"WAVE1_OUTPUT_INVALID_JSON={exc}")

    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = [str(row.get("parcel_id") or "") for row in rows if isinstance(row, dict)]
    row_validations = [row_validation(index, row) for index, row in enumerate(rows[:12]) if isinstance(row, dict)]
    canonical = data.get("canonical_point_source") if isinstance(data.get("canonical_point_source"), dict) else {}
    schemas = data.get("dataset_schemas") if isinstance(data.get("dataset_schemas"), dict) else {}
    iod_schema = schemas.get("iod_2025_file7") if isinstance(schemas.get("iod_2025_file7"), dict) else {}
    ons_schema = schemas.get("ons_lsoa_population_2024") if isinstance(schemas.get("ons_lsoa_population_2024"), dict) else {}
    method = data.get("method_preregistration") if isinstance(data.get("method_preregistration"), dict) else {}

    global_checks = {
        "slot_id_exact": data.get("slot_id") == SLOT_ID,
        "candidate_rows_exact_12": as_int(data.get("candidate_rows"), -1) == 12 and len(rows) == 12,
        "target_ids_exact_order_and_unique": ids == EXPECTED_IDS and len(set(ids)) == 12,
        "canonical_blob_exact": canonical.get("git_blob_sha") == EXPECTED_POINT_BLOB and canonical.get("git_blob_matches_expected") is True,
        "canonical_feature_count_exact": as_int(canonical.get("actual_feature_count"), -1) == EXPECTED_FEATURE_COUNT,
        "iod_current_v2_schema_pass": iod_schema.get("schema_gate_pass") is True and as_int(iod_schema.get("row_count"), -1) == 33755 and as_int(iod_schema.get("unique_lsoa_count"), -1) == 33755 and as_int(iod_schema.get("unique_rank_count"), -1) == 33755,
        "ons_population_schema_pass": ons_schema.get("schema_gate_pass") is True and ons_schema.get("lsoa_marker_present") is True and ons_schema.get("population_marker_present") is True and ons_schema.get("year_2024_marker_present") is True,
        "method_preregistered": method.get("valid") is True and method.get("method_version") == "iod25-crime-rank-less-deprived-ordinal-position-v2",
        "twelve_ons_single_matches": as_int(data.get("ons_single_match_rows"), -1) == 12,
        "twelve_police_hashes": as_int(data.get("police_hashed_rows"), -1) == 12,
        "business_rows_zero": as_int(data.get("actual_business_rows_written"), -1) == 0,
        "final_ready_false": data.get("final_ready") is False,
    }
    passed_rows = sum(item["state"] == "PASS" for item in row_validations)
    confidence_ge_95_rows = sum(item["evidence_integrity_percent"] >= 95 for item in row_validations)
    all_pass = all(global_checks.values()) and passed_rows == 12
    operations = [
        {"row": 1, "operation": "wave1_output_json_and_sha256_read", "state": "PASS", "evidence": file_sha256(INPUT_PATH)},
        {"row": 2, "operation": "slot_candidate_and_exact_target_identity", "state": "PASS" if global_checks["slot_id_exact"] and global_checks["candidate_rows_exact_12"] and global_checks["target_ids_exact_order_and_unique"] else "BLOCKED", "evidence": len(rows)},
        {"row": 3, "operation": "canonical_blob_and_92283_feature_count", "state": "PASS" if global_checks["canonical_blob_exact"] and global_checks["canonical_feature_count_exact"] else "BLOCKED", "evidence": canonical.get("actual_feature_count")},
        {"row": 4, "operation": "twelve_point_geometry_and_coordinate_blob_checks", "state": "PASS" if len(row_validations) == 12 and all(item["checks"]["exact_point_geometry"] and item["checks"]["coordinate_blob_exact"] for item in row_validations) else "BLOCKED", "evidence": len(row_validations)},
        {"row": 5, "operation": "twelve_single_ons_lsoa21_matches", "state": "PASS" if global_checks["twelve_ons_single_matches"] and all(item["checks"]["ons_single_match"] and item["checks"]["ons_lsoa21_code_format"] for item in row_validations) else "BLOCKED", "evidence": data.get("ons_single_match_rows")},
        {"row": 6, "operation": "twelve_explicit_police_month_and_response_hashes", "state": "PASS" if global_checks["twelve_police_hashes"] and all(item["checks"]["police_month_format"] and item["checks"]["police_response_reachable"] and item["checks"]["police_response_sha256"] for item in row_validations) else "BLOCKED", "evidence": data.get("police_hashed_rows")},
        {"row": 7, "operation": "iod25_current_v2_33755_schema", "state": "PASS" if global_checks["iod_current_v2_schema_pass"] else "BLOCKED", "evidence": iod_schema.get("row_count")},
        {"row": 8, "operation": "ons_population_2024_lsoa_schema", "state": "PASS" if global_checks["ons_population_schema_pass"] else "BLOCKED", "evidence": ons_schema.get("worksheet_count")},
        {"row": 9, "operation": "official_ordinal_method_preregistered", "state": "PASS" if global_checks["method_preregistered"] else "BLOCKED", "evidence": method.get("method_version")},
        {"row": 10, "operation": "twelve_rows_evidence_ge_95", "state": "PASS" if confidence_ge_95_rows == 12 else "BLOCKED", "evidence": confidence_ge_95_rows},
        {"row": 11, "operation": "business_and_promotion_fail_closed", "state": "PASS" if global_checks["business_rows_zero"] and all(item["checks"]["business_score_null"] and item["checks"]["business_confidence_zero"] and item["checks"]["promotion_forbidden"] for item in row_validations) else "BLOCKED", "evidence": data.get("actual_business_rows_written")},
        {"row": 12, "operation": "served_http_json_dom_console_acceptance", "state": "PENDING"},
    ]
    payload = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "state": "WAVE1_OUTPUT_VALIDATED_BROWSER_PENDING" if all_pass else "WAVE1_OUTPUT_VALIDATION_BLOCKED",
        "summary": "12 satırlık Wave1 kanıtı fail-closed doğrulandı; browser kabulü geçmeden business/promosyon kapalıdır." if all_pass else "Wave1 çıktısında en az bir zorunlu veri bütünlüğü kapısı geçmedi; skor ve promosyon kapalıdır.",
        "input_path": INPUT_REL,
        "input_exists": True,
        "input_sha256": file_sha256(INPUT_PATH),
        "row_count": len(rows),
        "passed_rows": passed_rows,
        "confidence_ge_95_rows": confidence_ge_95_rows,
        "business_rows_written": 0,
        "global_checks": global_checks,
        "row_validations": row_validations,
        "operations": operations,
        "operations_completed": sum(item["state"] == "PASS" for item in operations),
        "operations_total": len(operations),
        "browser_acceptance_pending": True,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "generated_at": utc_now(),
    }
    write_outputs(payload)
    return 0 if all_pass else 3


if __name__ == "__main__":
    raise SystemExit(main())
