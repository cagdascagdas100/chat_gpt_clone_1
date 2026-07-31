from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
SLOT_ID = "security_public_safety_2"
TASK_ID = "security_public_safety_2_wave118_corrected_2011_boundary_full_audit_20260731"
PARENT_TASK_ID = "security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731"
PARENT_CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"
CONTINUATION_KEY = "6b73473065869edaf7a215f4f5978cc1c9993fe5a0ac27eb4f19c16ea4501203"

STATUS_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/status_latest.json"
OWNERSHIP_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/ownership_latest.json"
WAVE116_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_transition_quality_audit_wave116_latest.json"
OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_corrected_2011_boundary_full_audit_wave118_latest.json"
OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_corrected_2011_boundary_full_audit_wave118.html"

CSV_URL = "https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/cbfe64cc03d74af982c1afec639bafd1/csv?layers=0"
BOUNDARY_2011 = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Clipped_BFC_EW_V3_2022/FeatureServer/0"
)
BOUNDARY_2021 = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
)
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave118/1.0"
EXPECTED_PARENT_ROWS = 30761
EXPECTED_HELD_ROWS = 394
PARENT_HIGH_CONFIDENCE_ROWS = 30367
MAX_WORKERS = 15
TOTAL_OPERATIONS = 5 + EXPECTED_HELD_ROWS * 5


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"REQUIRED_FILE_MISSING:{path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"REQUIRED_OBJECT_INVALID:{path}")
    return value


def http_get(url: str, *, attempts: int = 4, timeout: int = 90) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                return {
                    "reachable": True,
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "attempt": attempt,
                    "body": body,
                }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    return {
        "reachable": False,
        "http_status": None,
        "final_url": url,
        "content_type": "",
        "bytes": 0,
        "sha256": None,
        "attempt": attempts,
        "error": last_error or "UNKNOWN_FETCH_ERROR",
        "body": b"",
    }


def public_meta(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "reachable": bool(result.get("reachable")),
        "http_status": result.get("http_status"),
        "final_url": result.get("final_url"),
        "content_type": result.get("content_type"),
        "bytes": result.get("bytes"),
        "sha256": result.get("sha256"),
        "attempt": result.get("attempt"),
        "error": result.get("error"),
    }


def fetch_json(url: str, *, timeout: int = 90) -> dict[str, Any]:
    result = http_get(url, timeout=timeout)
    parsed: dict[str, Any] = {}
    if result["reachable"]:
        try:
            candidate = json.loads(result["body"].decode("utf-8-sig"))
            if not isinstance(candidate, dict):
                raise ValueError("NON_OBJECT_JSON")
            if candidate.get("error"):
                raise ValueError(f"ARCGIS_ERROR:{candidate['error']}")
            parsed = candidate
        except Exception as exc:
            result["reachable"] = False
            result["error"] = f"{type(exc).__name__}: {exc}"
    result["parsed"] = parsed
    result.pop("body", None)
    return result


def arcgis_point_query(layer: str, longitude: Any, latitude: Any, out_fields: str) -> dict[str, Any]:
    if longitude is None or latitude is None:
        return {
            "reachable": False,
            "http_status": None,
            "final_url": None,
            "content_type": "",
            "bytes": 0,
            "sha256": None,
            "attempt": 0,
            "error": "MISSING_COORDINATE",
            "parsed": {},
        }
    params = {
        "where": "1=1",
        "geometry": f"{longitude},{latitude}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "false",
        "resultRecordCount": "5",
        "f": "json",
    }
    return fetch_json(f"{layer}/query?{urllib.parse.urlencode(params)}")


status = read_json(STATUS_JSON)
if status.get("state") != "COMPLETED_ACCEPTED_PUBLISHED" or not status.get("final_ready"):
    raise SystemExit("PARENT_SLOT_NOT_TERMINAL_ACCEPTED")
if status.get("task_id") != PARENT_TASK_ID:
    raise SystemExit("PARENT_TASK_MISMATCH")
if status.get("continuation_key") != PARENT_CONTINUATION_KEY:
    raise SystemExit("PARENT_CONTINUATION_MISMATCH")
if status.get("owner") not in (None, "", "null"):
    raise SystemExit("LIVE_OWNER_PRESENT")
if int((status.get("progress") or {}).get("merged_rows_ready") or 0) != EXPECTED_PARENT_ROWS:
    raise SystemExit("PARENT_ROW_COUNT_MISMATCH")

ownership = read_json(OWNERSHIP_JSON)
if ownership.get("owner_page_session_id") not in (None, "", "null"):
    raise SystemExit("OWNERSHIP_SESSION_PRESENT")
if ownership.get("lease_expires_at") not in (None, "", "null"):
    raise SystemExit("OWNERSHIP_LEASE_PRESENT")
if bool(ownership.get("runtime_live_owner")):
    raise SystemExit("RUNTIME_LIVE_OWNER_PRESENT")

wave116 = read_json(WAVE116_JSON)
held_rows = [
    row for row in (wave116.get("rows") or [])
    if isinstance(row, dict) and str(row.get("audit_status") or "").startswith("HELD_")
]
if len(held_rows) != EXPECTED_HELD_ROWS:
    raise SystemExit(f"HELD_ROW_COUNT_MISMATCH:{len(held_rows)}")

metadata_2011 = fetch_json(f"{BOUNDARY_2011}?f=json")
metadata_2021 = fetch_json(f"{BOUNDARY_2021}?f=json")
if not metadata_2011.get("reachable") or not metadata_2021.get("reachable"):
    raise SystemExit("OFFICIAL_BOUNDARY_METADATA_UNREACHABLE")
fields_2011 = {str(item.get("name") or "") for item in (metadata_2011["parsed"].get("fields") or [])}
fields_2021 = {str(item.get("name") or "") for item in (metadata_2021["parsed"].get("fields") or [])}
if metadata_2011["parsed"].get("geometryType") != "esriGeometryPolygon" or not {"LSOA11CD", "LSOA11NM"}.issubset(fields_2011):
    raise SystemExit("OFFICIAL_2011_BOUNDARY_SCHEMA_MISMATCH")
if metadata_2021["parsed"].get("geometryType") != "esriGeometryPolygon" or not {"LSOA21CD", "LSOA21NM"}.issubset(fields_2021):
    raise SystemExit("OFFICIAL_2021_BOUNDARY_SCHEMA_MISMATCH")

csv_result = http_get(CSV_URL, attempts=4, timeout=150)
if not csv_result["reachable"]:
    raise SystemExit(f"OFFICIAL_CSV_UNREACHABLE:{csv_result.get('error')}")
reader = csv.DictReader(io.StringIO(csv_result["body"].decode("utf-8-sig")))
required_fields = {"LSOA11CD", "LSOA11NM", "CHGIND", "LSOA21CD", "LSOA21NM"}
if not required_fields.issubset(set(reader.fieldnames or [])):
    raise SystemExit(f"OFFICIAL_CSV_SCHEMA_MISMATCH:{reader.fieldnames}")
pairs: dict[tuple[str, str], dict[str, str]] = {}
for record in reader:
    code_2011 = str(record.get("LSOA11CD") or "").strip()
    code_2021 = str(record.get("LSOA21CD") or "").strip()
    if code_2011 and code_2021:
        pairs[(code_2011, code_2021)] = {key: str(value or "") for key, value in record.items()}
if len(pairs) < 30000:
    raise SystemExit(f"OFFICIAL_CSV_TOO_SMALL:{len(pairs)}")


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    parcel_id = str(row.get("parcel_id") or "")
    original_code = str(row.get("historical_lsoa_code") or "").strip()
    current_code = str(row.get("current_ons_lsoa_code") or "").strip()
    longitude = row.get("longitude")
    latitude = row.get("latitude")

    probe_2011 = arcgis_point_query(BOUNDARY_2011, longitude, latitude, "LSOA11CD,LSOA11NM")
    attrs_2011 = [
        feature.get("attributes") or {}
        for feature in ((probe_2011.get("parsed") or {}).get("features") or [])
        if isinstance(feature, dict)
    ]
    probe_2021 = arcgis_point_query(BOUNDARY_2021, longitude, latitude, "LSOA21CD,LSOA21NM")
    attrs_2021 = [
        feature.get("attributes") or {}
        for feature in ((probe_2021.get("parsed") or {}).get("features") or [])
        if isinstance(feature, dict)
    ]

    corrected_code = str(attrs_2011[0].get("LSOA11CD") or "") if len(attrs_2011) == 1 else ""
    point_2011_exact = bool(corrected_code)
    point_2021_exact = len(attrs_2021) == 1 and str(attrs_2021[0].get("LSOA21CD") or "") == current_code
    pair_record = pairs.get((corrected_code, current_code)) if corrected_code else None
    exact_pair = pair_record is not None
    original_already_correct = bool(corrected_code and corrected_code == original_code)

    if not probe_2011.get("reachable") or not probe_2021.get("reachable"):
        audit_status = "BLOCKED_BOUNDARY_NETWORK"
        confidence = int(row.get("parent_candidate_accuracy_percent") or 0)
    elif len(attrs_2011) != 1:
        audit_status = "HELD_2011_BOUNDARY_AMBIGUOUS"
        confidence = 91
    elif len(attrs_2021) != 1:
        audit_status = "HELD_2021_BOUNDARY_AMBIGUOUS"
        confidence = 91
    elif not point_2021_exact:
        audit_status = "HELD_2021_POINT_CODE_MISMATCH"
        confidence = 92
    elif not exact_pair:
        audit_status = "HELD_CORRECTED_PAIR_ABSENT"
        confidence = 93
    else:
        audit_status = "PASS_CORRECTED_2011_POINT_AND_EXACT_RELATION"
        confidence = 99

    return {
        "parcel_id": parcel_id,
        "longitude": longitude,
        "latitude": latitude,
        "original_historical_lsoa_code": original_code,
        "corrected_2011_lsoa_code": corrected_code or None,
        "corrected_2011_lsoa_name": attrs_2011[0].get("LSOA11NM") if len(attrs_2011) == 1 else None,
        "current_2021_lsoa_code": current_code,
        "current_2021_lsoa_name": attrs_2021[0].get("LSOA21NM") if len(attrs_2021) == 1 else None,
        "original_historical_code_already_correct": original_already_correct,
        "proposed_historical_code_correction": corrected_code if corrected_code and corrected_code != original_code else None,
        "corrected_2011_point_confirmed": point_2011_exact,
        "current_2021_point_confirmed": point_2021_exact,
        "corrected_exact_pair_confirmed": exact_pair,
        "change_indicator": (pair_record or {}).get("CHGIND"),
        "official_pair_attributes": pair_record,
        "boundary_2011_attributes": attrs_2011,
        "boundary_2021_attributes": attrs_2021,
        "boundary_2011_probe": public_meta(probe_2011),
        "boundary_2021_probe": public_meta(probe_2021),
        "parent_candidate_accuracy_percent": int(row.get("parent_candidate_accuracy_percent") or 0),
        "audit_status": audit_status,
        "audit_confidence_percent": confidence,
        "candidate_value_changed": False,
        "direct_score_input": False,
    }


audited: list[dict[str, Any]] = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="wave118") as executor:
    future_map = {executor.submit(audit_row, row): str(row.get("parcel_id") or "") for row in held_rows}
    for future in as_completed(future_map):
        parcel_id = future_map[future]
        try:
            audited.append(future.result())
        except Exception as exc:
            audited.append({
                "parcel_id": parcel_id,
                "audit_status": "BLOCKED_WORKER_EXCEPTION",
                "audit_confidence_percent": 0,
                "worker_error": f"{type(exc).__name__}: {exc}",
                "candidate_value_changed": False,
                "direct_score_input": False,
                "corrected_2011_point_confirmed": False,
                "current_2021_point_confirmed": False,
                "corrected_exact_pair_confirmed": False,
                "original_historical_code_already_correct": False,
                "proposed_historical_code_correction": None,
                "boundary_2011_probe": {"reachable": False},
                "boundary_2021_probe": {"reachable": False},
            })

audited.sort(key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]))
passed = sum(row.get("audit_status") == "PASS_CORRECTED_2011_POINT_AND_EXACT_RELATION" for row in audited)
held = sum(str(row.get("audit_status") or "").startswith("HELD_") for row in audited)
blocked = sum(str(row.get("audit_status") or "").startswith("BLOCKED_") for row in audited)
point_2011 = sum(bool(row.get("corrected_2011_point_confirmed")) for row in audited)
point_2021 = sum(bool(row.get("current_2021_point_confirmed")) for row in audited)
pair_confirmed = sum(bool(row.get("corrected_exact_pair_confirmed")) for row in audited)
already_correct = sum(bool(row.get("original_historical_code_already_correct")) for row in audited)
proposed_corrections = sum(bool(row.get("proposed_historical_code_correction")) for row in audited)
high_confidence_after = min(EXPECTED_PARENT_ROWS, PARENT_HIGH_CONFIDENCE_ROWS + passed)
parent_accuracy = round(100.0 * PARENT_HIGH_CONFIDENCE_ROWS / EXPECTED_PARENT_ROWS, 6)
support_accuracy = round(100.0 * high_confidence_after / EXPECTED_PARENT_ROWS, 6)
delta_pp = round(support_accuracy - parent_accuracy, 6)

operations: list[dict[str, Any]] = [
    {"operation": "parent_terminal_acceptance_gate", "status": "PASS"},
    {"operation": "owner_and_lease_absence_gate", "status": "PASS"},
    {"operation": "wave116_held_scope_gate", "status": "PASS"},
    {
        "operation": "official_boundary_schema_gate",
        "status": "PASS",
        "source_2011_sha256": metadata_2011.get("sha256"),
        "source_2021_sha256": metadata_2021.get("sha256"),
    },
    {
        "operation": "official_ons_exact_fit_csv_download",
        "status": "PASS",
        "source_sha256": csv_result.get("sha256"),
    },
]
for row in audited:
    network_blocked = str(row.get("audit_status") or "").startswith("BLOCKED_")
    operations.extend([
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_2011_full_resolution_point_boundary",
            "status": "PASS" if row.get("corrected_2011_point_confirmed") else ("BLOCKED" if network_blocked else "FAIL_CLOSED"),
            "source_sha256": (row.get("boundary_2011_probe") or {}).get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_2021_point_boundary",
            "status": "PASS" if row.get("current_2021_point_confirmed") else ("BLOCKED" if network_blocked else "FAIL_CLOSED"),
            "source_sha256": (row.get("boundary_2021_probe") or {}).get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_corrected_exact_fit_pair",
            "status": "PASS" if row.get("corrected_exact_pair_confirmed") else ("BLOCKED" if network_blocked else "FAIL_CLOSED"),
            "source_sha256": csv_result.get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "original_historical_code_comparison",
            "status": "PASS" if row.get("original_historical_code_already_correct") else "FAIL_CLOSED",
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "correction_candidate_classification",
            "status": "BLOCKED" if network_blocked else "PASS",
        },
    ])
if len(operations) != TOTAL_OPERATIONS:
    raise SystemExit(f"OPERATION_COUNT_MISMATCH:{len(operations)}")
completed_or_fail_closed = sum(item["status"] in {"PASS", "FAIL_CLOSED"} for item in operations)
blocked_operations = sum(item["status"] == "BLOCKED" for item in operations)

payload = {
    "schema_version": 1,
    "architecture_version": 3,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": SLOT_ID,
    "task_id": TASK_ID,
    "continuation_key": CONTINUATION_KEY,
    "parent_task_id": PARENT_TASK_ID,
    "parent_continuation_key": PARENT_CONTINUATION_KEY,
    "state": "COMPLETED_CORRECTED_BOUNDARY_AUDIT_PUBLISHED",
    "generated_at": utc_now(),
    "scope": {
        "parent_candidate_rows": EXPECTED_PARENT_ROWS,
        "wave116_held_rows": EXPECTED_HELD_ROWS,
        "rows_audited": len(audited),
        "candidate_values_changed": 0,
        "business_rows_written": 0,
    },
    "parallelism": {
        "maximum_simultaneous_workers": MAX_WORKERS,
        "official_probe_types_per_row": 5,
    },
    "sources": {
        "reviewed_official_source_families": 3,
        "promoted_official_source_families": 3,
        "exact_fit_csv_url": CSV_URL,
        "exact_fit_csv_sha256": csv_result.get("sha256"),
        "exact_fit_pair_count": len(pairs),
        "boundary_2011_full_resolution": BOUNDARY_2011,
        "boundary_2011_metadata_sha256": metadata_2011.get("sha256"),
        "boundary_2021": BOUNDARY_2021,
        "boundary_2021_metadata_sha256": metadata_2021.get("sha256"),
    },
    "result": {
        "candidate_rows": EXPECTED_PARENT_ROWS,
        "new_correction_candidates": passed,
        "rows_audited": len(audited),
        "corrected_2011_point_confirmed_rows": point_2011,
        "current_2021_point_confirmed_rows": point_2021,
        "corrected_exact_pair_confirmed_rows": pair_confirmed,
        "original_historical_code_already_correct_rows": already_correct,
        "proposed_historical_code_corrections": proposed_corrections,
        "fully_confirmed_support_rows": passed,
        "held_rows": held,
        "blocked_rows": blocked,
        "parent_high_confidence_rows": PARENT_HIGH_CONFIDENCE_ROWS,
        "high_confidence_support_rows_after_audit": high_confidence_after,
        "parent_accuracy_percent": parent_accuracy,
        "support_accuracy_percent": support_accuracy,
        "progress_delta_percentage_points": delta_pp,
        "line_by_line_rows": len(audited),
        "completed_or_fail_closed_operations": completed_or_fail_closed,
        "blocked_operations": blocked_operations,
        "total_operations": len(operations),
    },
    "quality_policy": {
        "direct_score_input": False,
        "parent_candidate_value_changed": False,
        "parent_candidate_accuracy_mutated": False,
        "promotion_rule": "support-only; derive 2011 code from official full-resolution point polygon, require current 2021 point match and exact official 2011-to-2021 relation",
        "fail_closed": True,
        "fake_data": False,
    },
    "operations": operations,
    "rows": audited,
    "fake_data": False,
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

cards = [
    ("Denetlenen satır", f"{len(audited)}/{EXPECTED_HELD_ROWS}"),
    ("Tam doğrulanan", str(passed)),
    ("2011 nokta", str(point_2011)),
    ("2021 nokta", str(point_2021)),
    ("Exact pair", str(pair_confirmed)),
    ("Kod düzeltme adayı", str(proposed_corrections)),
    ("HELD / BLOCKED", f"{held} / {blocked}"),
    ("İşlem", f"{completed_or_fail_closed}/{len(operations)}"),
    ("Kaynak ailesi", "3/3 resmî"),
    ("Destek doğruluğu", f"%{support_accuracy}"),
    ("Artış", f"+{delta_pp} yüzde puan"),
]
rows_html = []
for row in audited:
    h = lambda value: html.escape(str(value if value is not None else ""))
    rows_html.append(
        "<tr>"
        f"<td>{h(row.get('parcel_id'))}</td>"
        f"<td>{h(row.get('original_historical_lsoa_code'))}</td>"
        f"<td>{h(row.get('corrected_2011_lsoa_code'))}</td>"
        f"<td>{h(row.get('current_2021_lsoa_code'))}</td>"
        f"<td>{'PASS' if row.get('corrected_2011_point_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('current_2021_point_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('corrected_exact_pair_confirmed') else '—'}</td>"
        f"<td>{h(row.get('change_indicator'))}</td>"
        f"<td>{h(row.get('audit_status'))}</td>"
        f"<td>{h(row.get('audit_confidence_percent'))}</td>"
        f"<td><code>{h((row.get('boundary_2011_probe') or {}).get('sha256'))}</code></td>"
        f"<td><code>{h((row.get('boundary_2021_probe') or {}).get('sha256'))}</code></td>"
        "</tr>"
    )
cards_html = "".join(f"<div class='card'><b>{html.escape(k)}</b><br>{html.escape(v)}</div>" for k, v in cards)
page = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{SLOT_ID} — Wave118 düzeltilmiş 2011 sınır denetimi</title>
<style>body{{font-family:system-ui,sans-serif;margin:20px;background:#f7f7f8;color:#171717}}h1{{font-size:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:12px}}table{{width:100%;border-collapse:collapse;background:white;font-size:12px}}th,td{{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eee}}code{{font-size:10px;word-break:break-all}}</style></head>
<body><h1>{SLOT_ID} — Wave118 resmî ONS tam çözünürlüklü 2011 sınır denetimi</h1>
<p>Wave116 içinde HELD kalan 394 satır, gerçek ONS 2011 BFC tam çözünürlüklü sınırı, 2021 sınırı ve resmî exact-fit ilişki tablosuyla satır bazında doğrulanmıştır. Ana aday değerleri ve skorları değiştirilmemiştir.</p>
<div class="cards">{cards_html}</div>
<p>Exact-fit CSV SHA-256: <code>{html.escape(str(csv_result.get('sha256')))}</code></p>
<table><thead><tr><th>Parsel</th><th>Önceki tarihsel kod</th><th>Doğru 2011 kodu</th><th>2021 kodu</th><th>2011 nokta</th><th>2021 nokta</th><th>Exact pair</th><th>Değişim</th><th>Durum</th><th>Güven</th><th>2011 SHA-256</th><th>2021 SHA-256</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table></body></html>"""
OUTPUT_HTML.write_text(page, encoding="utf-8")

print(json.dumps({
    "state": payload["state"],
    **payload["result"],
    "json_sha256": hashlib.sha256(OUTPUT_JSON.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest(),
}, ensure_ascii=False))
