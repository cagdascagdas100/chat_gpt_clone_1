from __future__ import annotations

import hashlib
import html
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
TASK_ID = "security_public_safety_2_lsoa_transition_quality_audit_wave116_20260731"
PARENT_CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"
CONTINUATION_KEY = "69becfee7408d752eb9a84f8627aa3e23337e36628cda4108d3c336ca65b8c7e"
PARENT_JSON = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_30761row_evidence_expansion_latest.json"
STATUS_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/status_latest.json"
OWNERSHIP_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/ownership_latest.json"
OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_transition_quality_audit_wave116_latest.json"
OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_transition_quality_audit_wave116.html"

LOOKUP_LAYER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "LSOA11_LSOA21_LAD22_EW_LU_v5/FeatureServer/0"
)
BOUNDARY_LAYER = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
)
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave116-lsoa-transition-audit/1.0"
MAX_WORKERS = 15
EXPECTED_PARENT_ROWS = 30761
EXPECTED_LOW_ROWS = 394
PARENT_HIGH_CONFIDENCE_ROWS = 30367


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"REQUIRED_FILE_MISSING: {path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"REQUIRED_OBJECT_INVALID: {path}")
    return value


def fetch_json(url: str, params: dict[str, str], *, attempts: int = 3) -> dict[str, Any]:
    target = f"{url}/query?{urllib.parse.urlencode(params)}"
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            target,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read()
                parsed = json.loads(body.decode("utf-8-sig"))
                if not isinstance(parsed, dict):
                    raise RuntimeError("NON_OBJECT_JSON")
                if parsed.get("error"):
                    raise RuntimeError(f"ARCGIS_ERROR:{parsed['error']}")
                return {
                    "reachable": True,
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "attempt": attempt,
                    "parsed": parsed,
                }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    return {
        "reachable": False,
        "http_status": None,
        "final_url": target,
        "content_type": "",
        "bytes": 0,
        "sha256": None,
        "attempt": attempts,
        "error": last_error or "UNKNOWN_FETCH_ERROR",
        "parsed": {},
    }


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    parcel_id = str(row.get("parcel_id") or "")
    historical_code = str(row.get("historical_lsoa_code") or "").strip()
    current_code = str(row.get("ons_lsoa_code") or "").strip()
    longitude = row.get("longitude")
    latitude = row.get("latitude")

    lookup_where = (
        f"LSOA11CD='{historical_code.replace(chr(39), chr(39) * 2)}' "
        f"AND LSOA21CD='{current_code.replace(chr(39), chr(39) * 2)}'"
        if historical_code and current_code
        else "1=0"
    )
    lookup = fetch_json(
        LOOKUP_LAYER,
        {
            "where": lookup_where,
            "outFields": "LSOA11CD,LSOA11NM,LSOA21CD,LSOA21NM,CHGIND,LAD22CD,LAD22NM",
            "returnGeometry": "false",
            "resultRecordCount": "10",
            "f": "json",
        },
    )
    lookup_features = (lookup.get("parsed") or {}).get("features") or []
    lookup_attrs = [
        feature.get("attributes") or {}
        for feature in lookup_features
        if isinstance(feature, dict)
    ]
    exact_transition = any(
        str(item.get("LSOA11CD") or "") == historical_code
        and str(item.get("LSOA21CD") or "") == current_code
        for item in lookup_attrs
    )

    boundary = fetch_json(
        BOUNDARY_LAYER,
        {
            "where": "1=1",
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "LSOA21CD,LSOA21NM",
            "returnGeometry": "false",
            "resultRecordCount": "5",
            "f": "json",
        },
    ) if longitude is not None and latitude is not None else {
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
    boundary_features = (boundary.get("parsed") or {}).get("features") or []
    boundary_attrs = [
        feature.get("attributes") or {}
        for feature in boundary_features
        if isinstance(feature, dict)
    ]
    current_point_confirmed = (
        len(boundary_attrs) == 1
        and str(boundary_attrs[0].get("LSOA21CD") or "") == current_code
    )

    if exact_transition and current_point_confirmed:
        audit_status = "PASS_OFFICIAL_2011_TO_2021_TRANSITION_AND_POINT"
        audit_confidence = 98
    elif exact_transition:
        audit_status = "HELD_POINT_RECHECK_NOT_EXACT"
        audit_confidence = 93
    elif current_point_confirmed:
        audit_status = "HELD_TRANSITION_LOOKUP_NOT_EXACT"
        audit_confidence = 90
    else:
        audit_status = "BLOCKED_OFFICIAL_REVALIDATION_INCOMPLETE"
        audit_confidence = int(row.get("candidate_accuracy_percent") or 0)

    selected_lookup = next(
        (
            item for item in lookup_attrs
            if str(item.get("LSOA11CD") or "") == historical_code
            and str(item.get("LSOA21CD") or "") == current_code
        ),
        None,
    )

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

    return {
        "parcel_id": parcel_id,
        "longitude": longitude,
        "latitude": latitude,
        "historical_lsoa_code": historical_code,
        "current_ons_lsoa_code": current_code,
        "current_ons_lsoa_name": row.get("ons_lsoa_name"),
        "parent_candidate_accuracy_percent": int(row.get("candidate_accuracy_percent") or 0),
        "parent_relative_security_candidate_percent": row.get("relative_security_candidate_percent"),
        "police_response_sha256": (row.get("police_query") or {}).get("sha256"),
        "lookup_exact_transition": exact_transition,
        "lookup_attributes": selected_lookup,
        "current_point_confirmed": current_point_confirmed,
        "boundary_attributes": boundary_attrs,
        "audit_status": audit_status,
        "audit_confidence_percent": audit_confidence,
        "direct_score_input": False,
        "candidate_value_changed": False,
        "lookup_probe": public_meta(lookup),
        "boundary_probe": public_meta(boundary),
    }


status = read_json(STATUS_JSON)
if status.get("state") != "COMPLETED_ACCEPTED_PUBLISHED" or not status.get("final_ready"):
    raise SystemExit("PARENT_SLOT_NOT_TERMINAL_ACCEPTED")
if status.get("continuation_key") != PARENT_CONTINUATION_KEY:
    raise SystemExit("PARENT_CONTINUATION_MISMATCH")
if status.get("owner") not in (None, "", "null"):
    raise SystemExit("LIVE_OWNER_PRESENT")

ownership = read_json(OWNERSHIP_JSON)
if ownership.get("owner_page_session_id") not in (None, "", "null"):
    raise SystemExit("OWNERSHIP_SESSION_PRESENT")
if ownership.get("lease_expires_at") not in (None, "", "null"):
    raise SystemExit("OWNERSHIP_LEASE_PRESENT")

parent = read_json(PARENT_JSON)
rows = parent.get("rows") or []
if not isinstance(rows, list) or len(rows) != EXPECTED_PARENT_ROWS:
    raise SystemExit(f"PARENT_ROW_COUNT_MISMATCH:{len(rows) if isinstance(rows, list) else 'not-list'}")

low_rows = [
    row for row in rows
    if isinstance(row, dict)
    and int(row.get("candidate_accuracy_percent") or 0) < 95
]
if len(low_rows) != EXPECTED_LOW_ROWS:
    raise SystemExit(f"LOW_ROW_COUNT_MISMATCH:{len(low_rows)}")

audited: list[dict[str, Any]] = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="lsoa-audit") as executor:
    future_map = {executor.submit(audit_row, row): str(row.get("parcel_id") or "") for row in low_rows}
    for future in as_completed(future_map):
        parcel_id = future_map[future]
        try:
            audited.append(future.result())
        except Exception as exc:
            audited.append({
                "parcel_id": parcel_id,
                "audit_status": "BLOCKED_WORKER_EXCEPTION",
                "audit_confidence_percent": 0,
                "direct_score_input": False,
                "candidate_value_changed": False,
                "worker_error": f"{type(exc).__name__}: {exc}",
                "lookup_exact_transition": False,
                "current_point_confirmed": False,
                "lookup_probe": {"reachable": False},
                "boundary_probe": {"reachable": False},
            })

audited.sort(key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]))
transition_confirmed = sum(
    row.get("audit_status") == "PASS_OFFICIAL_2011_TO_2021_TRANSITION_AND_POINT"
    for row in audited
)
held = sum(str(row.get("audit_status") or "").startswith("HELD_") for row in audited)
blocked = sum(str(row.get("audit_status") or "").startswith("BLOCKED_") for row in audited)
lookup_reachable = sum(bool((row.get("lookup_probe") or {}).get("reachable")) for row in audited)
boundary_reachable = sum(bool((row.get("boundary_probe") or {}).get("reachable")) for row in audited)
high_confidence_support_rows = PARENT_HIGH_CONFIDENCE_ROWS + transition_confirmed
support_progress_percent = round(100.0 * high_confidence_support_rows / EXPECTED_PARENT_ROWS, 6)
parent_progress_percent = round(100.0 * PARENT_HIGH_CONFIDENCE_ROWS / EXPECTED_PARENT_ROWS, 6)
delta_pp = round(support_progress_percent - parent_progress_percent, 6)

operation_rows = []
for row in audited:
    operation_rows.append({
        "parcel_id": row.get("parcel_id"),
        "operation": "official_ons_lsoa11_to_lsoa21_transition_lookup",
        "status": "PASS" if row.get("lookup_exact_transition") else (
            "FAIL_CLOSED" if (row.get("lookup_probe") or {}).get("reachable") else "BLOCKED"
        ),
        "source_sha256": (row.get("lookup_probe") or {}).get("sha256"),
    })
    operation_rows.append({
        "parcel_id": row.get("parcel_id"),
        "operation": "official_ons_lsoa21_point_boundary_recheck",
        "status": "PASS" if row.get("current_point_confirmed") else (
            "FAIL_CLOSED" if (row.get("boundary_probe") or {}).get("reachable") else "BLOCKED"
        ),
        "source_sha256": (row.get("boundary_probe") or {}).get("sha256"),
    })

global_operations = [
    {"operation": "parent_terminal_acceptance_gate", "status": "PASS"},
    {"operation": "owner_and_lease_absence_gate", "status": "PASS"},
    {"operation": "exact_parent_row_count_gate", "status": "PASS"},
    {"operation": "exact_low_confidence_scope_gate", "status": "PASS"},
]
all_operations = global_operations + operation_rows
completed_or_fail_closed = sum(item["status"] in {"PASS", "FAIL_CLOSED"} for item in all_operations)
blocked_operations = sum(item["status"] == "BLOCKED" for item in all_operations)

payload = {
    "schema_version": 1,
    "architecture_version": 3,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": SLOT_ID,
    "task_id": TASK_ID,
    "continuation_key": CONTINUATION_KEY,
    "parent_task_id": status.get("task_id"),
    "parent_continuation_key": PARENT_CONTINUATION_KEY,
    "state": "COMPLETED_SUPPORT_AUDIT_PUBLISHED",
    "scope": {
        "parent_candidate_rows": EXPECTED_PARENT_ROWS,
        "parent_accuracy_ge_95_rows": PARENT_HIGH_CONFIDENCE_ROWS,
        "rows_below_95_audited": len(audited),
        "candidate_values_changed": 0,
        "business_rows_written": 0,
    },
    "parallelism": {
        "maximum_simultaneous_workers": MAX_WORKERS,
        "official_probe_types": 2,
    },
    "sources": {
        "reviewed_official_source_families": 2,
        "promoted_official_source_families": 2,
        "official_source_confirmations": lookup_reachable + boundary_reachable,
        "lookup_layer": LOOKUP_LAYER,
        "boundary_layer": BOUNDARY_LAYER,
    },
    "result": {
        "candidate_rows": EXPECTED_PARENT_ROWS,
        "new_candidates": 0,
        "transition_confirmed_rows": transition_confirmed,
        "held_rows": held,
        "blocked_rows": blocked,
        "high_confidence_support_rows_after_audit": high_confidence_support_rows,
        "support_accuracy_percent": support_progress_percent,
        "parent_accuracy_percent": parent_progress_percent,
        "progress_delta_percentage_points": delta_pp,
        "line_by_line_rows": len(audited),
        "completed_or_fail_closed_operations": completed_or_fail_closed,
        "blocked_operations": blocked_operations,
        "total_operations": len(all_operations),
    },
    "quality_policy": {
        "direct_score_input": False,
        "parent_candidate_value_changed": False,
        "parent_candidate_accuracy_mutated": False,
        "transition_confidence_rule": (
            "98 only when the official ONS LSOA11-to-LSOA21 lookup contains the exact pair "
            "and the official 2021 boundary service independently returns the current code at the point"
        ),
        "fail_closed": True,
    },
    "operations": all_operations,
    "rows": audited,
    "fake_data": False,
    "db_write": False,
    "migration": False,
    "production_deploy": False,
    "final_ready": blocked == 0,
    "updated_at": utc_now(),
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
OUTPUT_JSON.write_text(json_text, encoding="utf-8")
json_sha = hashlib.sha256(json_text.encode("utf-8")).hexdigest()

table_rows = []
for item in audited:
    lookup = item.get("lookup_attributes") or {}
    table_rows.append(
        "<tr>"
        f"<td>{html.escape(str(item.get('parcel_id') or ''))}</td>"
        f"<td>{html.escape(str(item.get('historical_lsoa_code') or ''))}</td>"
        f"<td>{html.escape(str(item.get('current_ons_lsoa_code') or ''))}</td>"
        f"<td>{html.escape(str(lookup.get('CHGIND') or ''))}</td>"
        f"<td>{'PASS' if item.get('lookup_exact_transition') else '—'}</td>"
        f"<td>{'PASS' if item.get('current_point_confirmed') else '—'}</td>"
        f"<td>{html.escape(str(item.get('audit_status') or ''))}</td>"
        f"<td>{html.escape(str(item.get('audit_confidence_percent') or ''))}</td>"
        f"<td><code>{html.escape(str((item.get('lookup_probe') or {}).get('sha256') or ''))}</code></td>"
        f"<td><code>{html.escape(str((item.get('boundary_probe') or {}).get('sha256') or ''))}</code></td>"
        "</tr>"
    )

html_text = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{SLOT_ID} — Wave116 LSOA geçiş doğruluk denetimi</title>
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
<h1>{SLOT_ID} — Wave116 resmî ONS LSOA geçiş denetimi</h1>
<p>Bu görünüm, ana 30.761 aday satırını değiştirmeden yalnız %95 altındaki 394 satırı resmî ONS
2011→2021 lookup ve 2021 nokta-poligon servisiyle yeniden doğrular.</p>
<div class="cards">
<div class="card"><b>Denetlenen satır</b><br>{len(audited)}/{EXPECTED_LOW_ROWS}</div>
<div class="card"><b>Geçiş doğrulandı</b><br>{transition_confirmed}</div>
<div class="card"><b>Destek yüksek güven</b><br>{high_confidence_support_rows}/{EXPECTED_PARENT_ROWS}</div>
<div class="card"><b>Destek doğruluğu</b><br>%{support_progress_percent}</div>
<div class="card"><b>Artış</b><br>+{delta_pp} yüzde puan</div>
<div class="card"><b>İşlem</b><br>{completed_or_fail_closed}/{len(all_operations)}</div>
<div class="card"><b>Kaynak ailesi</b><br>2/2 resmî</div>
<div class="card"><b>Bloklu satır</b><br>{blocked}</div>
</div>
<p>JSON SHA-256: <code>{json_sha}</code></p>
<table>
<thead><tr>
<th>Parsel</th><th>Tarihsel LSOA</th><th>Güncel ONS LSOA</th><th>CHGIND</th>
<th>Lookup</th><th>Nokta</th><th>Durum</th><th>Denetim güveni</th>
<th>Lookup SHA-256</th><th>Boundary SHA-256</th>
</tr></thead>
<tbody>{''.join(table_rows)}</tbody>
</table>
</body>
</html>
"""
OUTPUT_HTML.write_text(html_text, encoding="utf-8")
print(json.dumps({
    "state": payload["state"],
    "rows_audited": len(audited),
    "transition_confirmed_rows": transition_confirmed,
    "held_rows": held,
    "blocked_rows": blocked,
    "support_accuracy_percent": support_progress_percent,
    "progress_delta_percentage_points": delta_pp,
    "completed_or_fail_closed_operations": completed_or_fail_closed,
    "total_operations": len(all_operations),
    "json_sha256": json_sha,
}, ensure_ascii=False))
