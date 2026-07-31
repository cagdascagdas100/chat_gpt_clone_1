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
TASK_ID = "security_public_safety_2_wave117_ons_exactfit_dual_boundary_sample_20260731"
PARENT_TASK_ID = "security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731"
PARENT_CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"
CONTINUATION_KEY = "9c54a433077899598f478332ae17983d80a3cc36b5ed9b6955a5043fb195a633"

STATUS_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/status_latest.json"
OWNERSHIP_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/ownership_latest.json"
WAVE116_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_transition_quality_audit_wave116_latest.json"
OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_exactfit_dual_boundary_sample_wave117_latest.json"
OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_exactfit_dual_boundary_sample_wave117.html"

CSV_URL = "https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/cbfe64cc03d74af982c1afec639bafd1/csv?layers=0"
BOUNDARY_2011 = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/lsoa/FeatureServer/0"
BOUNDARY_2021 = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave117/1.0"

EXPECTED_PARENT_ROWS = 30761
EXPECTED_HELD_ROWS = 394
SAMPLE_ROWS = 64
MAX_WORKERS = 15


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"REQUIRED_FILE_MISSING:{path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"REQUIRED_OBJECT_INVALID:{path}")
    return value


def http_get(url: str, *, attempts: int = 4, timeout: int = 75) -> dict[str, Any]:
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
    result = http_get(f"{layer}/query?{urllib.parse.urlencode(params)}")
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

wave116 = read_json(WAVE116_JSON)
held_rows = [
    row for row in (wave116.get("rows") or [])
    if isinstance(row, dict) and str(row.get("audit_status") or "").startswith("HELD_")
]
if len(held_rows) != EXPECTED_HELD_ROWS:
    raise SystemExit(f"HELD_ROW_COUNT_MISMATCH:{len(held_rows)}")

sample_indexes = sorted({
    round(i * (len(held_rows) - 1) / (SAMPLE_ROWS - 1))
    for i in range(SAMPLE_ROWS)
})
if len(sample_indexes) != SAMPLE_ROWS:
    raise SystemExit(f"SAMPLE_INDEX_COUNT_MISMATCH:{len(sample_indexes)}")
selected = [held_rows[index] for index in sample_indexes]

csv_result = http_get(CSV_URL, attempts=4, timeout=120)
if not csv_result["reachable"]:
    raise SystemExit(f"OFFICIAL_CSV_UNREACHABLE:{csv_result.get('error')}")
csv_text = csv_result["body"].decode("utf-8-sig")
reader = csv.DictReader(io.StringIO(csv_text))
required_fields = {"LSOA11CD", "LSOA11NM", "CHGIND", "LSOA21CD", "LSOA21NM"}
if not required_fields.issubset(set(reader.fieldnames or [])):
    raise SystemExit(f"OFFICIAL_CSV_SCHEMA_MISMATCH:{reader.fieldnames}")

pairs: dict[tuple[str, str], dict[str, str]] = {}
historical_targets: dict[str, list[dict[str, str]]] = {}
current_sources: dict[str, list[dict[str, str]]] = {}
for record in reader:
    historical_code = str(record.get("LSOA11CD") or "").strip()
    current_code = str(record.get("LSOA21CD") or "").strip()
    if not historical_code or not current_code:
        continue
    normalized = {key: str(value or "") for key, value in record.items()}
    pairs[(historical_code, current_code)] = normalized
    historical_targets.setdefault(historical_code, []).append(normalized)
    current_sources.setdefault(current_code, []).append(normalized)

if len(pairs) < 30000:
    raise SystemExit(f"OFFICIAL_CSV_TOO_SMALL:{len(pairs)}")


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    parcel_id = str(row.get("parcel_id") or "")
    historical_code = str(row.get("historical_lsoa_code") or "").strip()
    current_code = str(row.get("current_ons_lsoa_code") or "").strip()
    longitude = row.get("longitude")
    latitude = row.get("latitude")

    pair_record = pairs.get((historical_code, current_code))
    historical_records = historical_targets.get(historical_code, [])
    current_records = current_sources.get(current_code, [])

    boundary_2011 = arcgis_point_query(
        BOUNDARY_2011, longitude, latitude, "LSOA11CD,LSOA11NM"
    )
    attrs_2011 = [
        feature.get("attributes") or {}
        for feature in ((boundary_2011.get("parsed") or {}).get("features") or [])
        if isinstance(feature, dict)
    ]
    historical_point_confirmed = (
        len(attrs_2011) == 1
        and str(attrs_2011[0].get("LSOA11CD") or "") == historical_code
    )

    boundary_2021 = arcgis_point_query(
        BOUNDARY_2021, longitude, latitude, "LSOA21CD,LSOA21NM"
    )
    attrs_2021 = [
        feature.get("attributes") or {}
        for feature in ((boundary_2021.get("parsed") or {}).get("features") or [])
        if isinstance(feature, dict)
    ]
    current_point_confirmed = (
        len(attrs_2021) == 1
        and str(attrs_2021[0].get("LSOA21CD") or "") == current_code
    )

    exact_pair = pair_record is not None
    if exact_pair and historical_point_confirmed and current_point_confirmed:
        audit_status = "PASS_EXACT_PAIR_AND_DUAL_BOUNDARY"
        audit_confidence = 99
    elif not boundary_2011.get("reachable") or not boundary_2021.get("reachable"):
        audit_status = "BLOCKED_BOUNDARY_NETWORK"
        audit_confidence = int(row.get("parent_candidate_accuracy_percent") or 0)
    elif not exact_pair:
        audit_status = "HELD_EXACT_FIT_PAIR_ABSENT"
        audit_confidence = 90
    elif not historical_point_confirmed:
        audit_status = "HELD_2011_POINT_CODE_MISMATCH"
        audit_confidence = 91
    else:
        audit_status = "HELD_2021_POINT_CODE_MISMATCH"
        audit_confidence = 92

    return {
        "parcel_id": parcel_id,
        "longitude": longitude,
        "latitude": latitude,
        "historical_lsoa_code": historical_code,
        "current_lsoa_code": current_code,
        "parent_candidate_accuracy_percent": row.get("parent_candidate_accuracy_percent"),
        "exact_fit_pair_confirmed": exact_pair,
        "change_indicator": (pair_record or {}).get("CHGIND"),
        "historical_code_relation_count": len(historical_records),
        "current_code_source_count": len(current_records),
        "historical_relation_targets": [
            {"LSOA21CD": item.get("LSOA21CD"), "CHGIND": item.get("CHGIND")}
            for item in historical_records[:8]
        ],
        "current_relation_sources": [
            {"LSOA11CD": item.get("LSOA11CD"), "CHGIND": item.get("CHGIND")}
            for item in current_records[:8]
        ],
        "historical_point_confirmed": historical_point_confirmed,
        "current_point_confirmed": current_point_confirmed,
        "boundary_2011_attributes": attrs_2011,
        "boundary_2021_attributes": attrs_2021,
        "boundary_2011_probe": public_meta(boundary_2011),
        "boundary_2021_probe": public_meta(boundary_2021),
        "audit_status": audit_status,
        "audit_confidence_percent": audit_confidence,
        "candidate_value_changed": False,
        "direct_score_input": False,
    }


audited: list[dict[str, Any]] = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="wave117") as executor:
    future_map = {executor.submit(audit_row, row): row.get("parcel_id") for row in selected}
    for future in as_completed(future_map):
        parcel_id = future_map[future]
        try:
            audited.append(future.result())
        except Exception as exc:
            audited.append({
                "parcel_id": parcel_id,
                "audit_status": "BLOCKED_WORKER_EXCEPTION",
                "audit_confidence_percent": 0,
                "candidate_value_changed": False,
                "direct_score_input": False,
                "worker_error": f"{type(exc).__name__}: {exc}",
                "exact_fit_pair_confirmed": False,
                "historical_point_confirmed": False,
                "current_point_confirmed": False,
                "boundary_2011_probe": {"reachable": False},
                "boundary_2021_probe": {"reachable": False},
            })

audited.sort(key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]))
passed = sum(row.get("audit_status") == "PASS_EXACT_PAIR_AND_DUAL_BOUNDARY" for row in audited)
held = sum(str(row.get("audit_status") or "").startswith("HELD_") for row in audited)
blocked = sum(str(row.get("audit_status") or "").startswith("BLOCKED_") for row in audited)
historical_point_pass = sum(bool(row.get("historical_point_confirmed")) for row in audited)
current_point_pass = sum(bool(row.get("current_point_confirmed")) for row in audited)
exact_pair_pass = sum(bool(row.get("exact_fit_pair_confirmed")) for row in audited)

operations: list[dict[str, Any]] = [
    {"operation": "parent_terminal_acceptance_gate", "status": "PASS"},
    {"operation": "owner_and_lease_absence_gate", "status": "PASS"},
    {"operation": "wave116_held_scope_gate", "status": "PASS"},
    {
        "operation": "official_ons_exact_fit_csv_download",
        "status": "PASS",
        "source_sha256": csv_result.get("sha256"),
    },
    {"operation": "representative_sample_selection_gate", "status": "PASS"},
]
for row in audited:
    operations.extend([
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_exact_fit_pair_membership",
            "status": "PASS" if row.get("exact_fit_pair_confirmed") else "FAIL_CLOSED",
            "source_sha256": csv_result.get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_historical_code_presence",
            "status": "PASS" if int(row.get("historical_code_relation_count") or 0) > 0 else "FAIL_CLOSED",
            "source_sha256": csv_result.get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_2011_point_boundary",
            "status": "PASS" if row.get("historical_point_confirmed") else (
                "FAIL_CLOSED" if (row.get("boundary_2011_probe") or {}).get("reachable") else "BLOCKED"
            ),
            "source_sha256": (row.get("boundary_2011_probe") or {}).get("sha256"),
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_2021_point_boundary",
            "status": "PASS" if row.get("current_point_confirmed") else (
                "FAIL_CLOSED" if (row.get("boundary_2021_probe") or {}).get("reachable") else "BLOCKED"
            ),
            "source_sha256": (row.get("boundary_2021_probe") or {}).get("sha256"),
        },
    ])

completed_or_fail_closed = sum(item["status"] in {"PASS", "FAIL_CLOSED"} for item in operations)
blocked_operations = sum(item["status"] == "BLOCKED" for item in operations)
total_operations = len(operations)

payload = {
    "schema_version": 1,
    "architecture_version": 3,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": SLOT_ID,
    "task_id": TASK_ID,
    "continuation_key": CONTINUATION_KEY,
    "parent_task_id": PARENT_TASK_ID,
    "parent_continuation_key": PARENT_CONTINUATION_KEY,
    "state": "COMPLETED_SAMPLE_AUDIT_PUBLISHED" if blocked == 0 else "COMPLETED_SAMPLE_AUDIT_WITH_BLOCKED",
    "generated_at": utc_now(),
    "scope": {
        "parent_candidate_rows": EXPECTED_PARENT_ROWS,
        "wave116_held_rows": EXPECTED_HELD_ROWS,
        "sample_rows_audited": len(audited),
        "candidate_values_changed": 0,
        "business_rows_written": 0,
    },
    "parallelism": {
        "maximum_simultaneous_workers": MAX_WORKERS,
        "sample_rows": SAMPLE_ROWS,
        "official_probe_types_per_row": 4,
    },
    "sources": {
        "reviewed_official_source_families": 3,
        "promoted_official_source_families": 3,
        "exact_fit_csv_url": CSV_URL,
        "exact_fit_csv_sha256": csv_result.get("sha256"),
        "exact_fit_pair_count": len(pairs),
        "boundary_2011": BOUNDARY_2011,
        "boundary_2021": BOUNDARY_2021,
    },
    "result": {
        "candidate_rows": EXPECTED_PARENT_ROWS,
        "new_candidates": 0,
        "sample_rows": len(audited),
        "exact_pair_confirmed_rows": exact_pair_pass,
        "historical_point_confirmed_rows": historical_point_pass,
        "current_point_confirmed_rows": current_point_pass,
        "fully_confirmed_rows": passed,
        "held_rows": held,
        "blocked_rows": blocked,
        "parent_high_confidence_rows": int((status.get("progress") or {}).get("candidate_accuracy_ge_95_rows") or 0),
        "parent_accuracy_percent": round(
            100.0 * int((status.get("progress") or {}).get("candidate_accuracy_ge_95_rows") or 0) / EXPECTED_PARENT_ROWS,
            6,
        ),
        "progress_delta_percentage_points": 0.0,
        "line_by_line_rows": len(audited),
        "completed_or_fail_closed_operations": completed_or_fail_closed,
        "blocked_operations": blocked_operations,
        "total_operations": total_operations,
    },
    "quality_policy": {
        "direct_score_input": False,
        "parent_candidate_value_changed": False,
        "parent_candidate_accuracy_mutated": False,
        "promotion_rule": "support-only; no parent mutation unless exact official pair and both 2011 and 2021 point boundaries agree",
        "fail_closed": True,
        "fake_data": False,
    },
    "operations": operations,
    "rows": audited,
    "fake_data": False,
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

rows_html = []
for row in audited:
    historical_targets_text = ", ".join(
        f"{item.get('LSOA21CD')}({item.get('CHGIND')})"
        for item in (row.get("historical_relation_targets") or [])
    )
    rows_html.append(
        "<tr>"
        f"<td>{html.escape(str(row.get('parcel_id') or ''))}</td>"
        f"<td>{html.escape(str(row.get('historical_lsoa_code') or ''))}</td>"
        f"<td>{html.escape(str(row.get('current_lsoa_code') or ''))}</td>"
        f"<td>{'PASS' if row.get('exact_fit_pair_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('historical_point_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('current_point_confirmed') else '—'}</td>"
        f"<td>{html.escape(str(row.get('audit_status') or ''))}</td>"
        f"<td>{html.escape(str(row.get('audit_confidence_percent') or ''))}</td>"
        f"<td>{html.escape(historical_targets_text)}</td>"
        f"<td><code>{html.escape(str((row.get('boundary_2011_probe') or {}).get('sha256') or ''))}</code></td>"
        f"<td><code>{html.escape(str((row.get('boundary_2021_probe') or {}).get('sha256') or ''))}</code></td>"
        "</tr>"
    )

html_text = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{SLOT_ID} — Wave117 ONS çift sınır örnek denetimi</title>
<style>
body{{font-family:system-ui,sans-serif;margin:20px;background:#f7f7f8;color:#171717}}
h1{{font-size:24px}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}
.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:12px}}
table{{width:100%;border-collapse:collapse;background:white;font-size:12px}}
th,td{{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}}
th{{position:sticky;top:0;background:#eee}} code{{font-size:10px;word-break:break-all}}
</style>
</head>
<body>
<h1>{SLOT_ID} — Wave117 resmî ONS exact-fit ve çift sınır örnek denetimi</h1>
<p>Wave116 içinde HELD kalan 394 satırdan eşit aralıklı 64 örnek; resmî ONS exact-fit CSV,
2011 nokta-poligon ve 2021 nokta-poligon kanıtlarıyla satır bazında doğrulanmıştır.</p>
<div class="cards">
<div class="card"><b>Örnek satır</b><br>{len(audited)}/{SAMPLE_ROWS}</div>
<div class="card"><b>Tam doğrulanan</b><br>{passed}</div>
<div class="card"><b>Exact pair</b><br>{exact_pair_pass}</div>
<div class="card"><b>2011 nokta</b><br>{historical_point_pass}</div>
<div class="card"><b>2021 nokta</b><br>{current_point_pass}</div>
<div class="card"><b>HELD / BLOCKED</b><br>{held} / {blocked}</div>
<div class="card"><b>İşlem</b><br>{completed_or_fail_closed}/{total_operations}</div>
<div class="card"><b>Kaynak ailesi</b><br>3/3 resmî</div>
<div class="card"><b>Ana doğruluk</b><br>%{payload['result']['parent_accuracy_percent']}</div>
<div class="card"><b>Artış</b><br>+0.0 yüzde puan</div>
</div>
<p>Exact-fit CSV SHA-256: <code>{html.escape(str(csv_result.get('sha256') or ''))}</code></p>
<table>
<thead><tr>
<th>Parsel</th><th>Tarihsel LSOA</th><th>Güncel LSOA</th><th>Exact pair</th>
<th>2011 nokta</th><th>2021 nokta</th><th>Durum</th><th>Denetim güveni</th>
<th>Resmî hedefler</th><th>2011 SHA-256</th><th>2021 SHA-256</th>
</tr></thead>
<tbody>{''.join(rows_html)}</tbody>
</table>
</body>
</html>
"""
OUTPUT_HTML.write_text(html_text, encoding="utf-8")

print(json.dumps({
    "state": payload["state"],
    "sample_rows": len(audited),
    "fully_confirmed_rows": passed,
    "held_rows": held,
    "blocked_rows": blocked,
    "completed_or_fail_closed_operations": completed_or_fail_closed,
    "total_operations": total_operations,
    "json_sha256": hashlib.sha256(OUTPUT_JSON.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest(),
}, ensure_ascii=False))
