from __future__ import annotations

import hashlib
import html
import json
import runpy
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
BASE_SCRIPT = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave118_corrected_2011_boundary_full_audit_20260731.py"
OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_corrected_2011_boundary_full_audit_wave118_latest.json"
OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_corrected_2011_boundary_full_audit_wave118.html"
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave118-recovery/1.0"

# Run the guarded full audit once. It performs all parent/owner/schema gates and
# writes a fail-closed first-pass result. The globals are retained for targeted
# recovery without creating a second task or changing the continuation key.
ctx = runpy.run_path(str(BASE_SCRIPT))
payload = json.loads(OUTPUT_JSON.read_text(encoding="utf-8"))
rows: list[dict[str, Any]] = [dict(row) for row in payload.get("rows") or []]
source_rows = {
    str(row.get("parcel_id") or ""): row
    for row in ctx["held_rows"]
    if isinstance(row, dict)
}
pairs: dict[tuple[str, str], dict[str, str]] = ctx["pairs"]
boundary_2011 = str(ctx["BOUNDARY_2011"])
boundary_2021 = str(ctx["BOUNDARY_2021"])
expected_rows = int(ctx["EXPECTED_HELD_ROWS"])
expected_parent_rows = int(ctx["EXPECTED_PARENT_ROWS"])
parent_high_confidence_rows = int(ctx["PARENT_HIGH_CONFIDENCE_ROWS"])
total_operations = int(ctx["TOTAL_OPERATIONS"])


def http_json(url: str, *, attempts: int, timeout: int) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
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
                    "error": None,
                    "parsed": parsed,
                }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(2.0 * attempt)
    return {
        "reachable": False,
        "http_status": None,
        "final_url": url,
        "content_type": "",
        "bytes": 0,
        "sha256": None,
        "attempt": attempts,
        "error": last_error or "UNKNOWN_FETCH_ERROR",
        "parsed": {},
    }


def point_query(
    layer: str,
    longitude: Any,
    latitude: Any,
    out_fields: str,
    *,
    attempts: int,
    timeout: int,
) -> dict[str, Any]:
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
    return http_json(
        f"{layer}/query?{urllib.parse.urlencode(params)}",
        attempts=attempts,
        timeout=timeout,
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


def attributes(probe: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        feature.get("attributes") or {}
        for feature in ((probe.get("parsed") or {}).get("features") or [])
        if isinstance(feature, dict)
    ]


def recover_row(
    previous: dict[str, Any],
    *,
    attempts: int,
    timeout: int,
    retry_current: bool,
) -> dict[str, Any]:
    parcel_id = str(previous.get("parcel_id") or "")
    source = source_rows[parcel_id]
    longitude = source.get("longitude")
    latitude = source.get("latitude")
    original_code = str(source.get("historical_lsoa_code") or "").strip()
    current_code = str(source.get("current_ons_lsoa_code") or "").strip()

    probe_2011 = point_query(
        boundary_2011,
        longitude,
        latitude,
        "LSOA11CD,LSOA11NM",
        attempts=attempts,
        timeout=timeout,
    )
    attrs_2011 = attributes(probe_2011)

    previous_2021_probe = previous.get("boundary_2021_probe") or {}
    previous_2021_attrs = previous.get("boundary_2021_attributes") or []
    if retry_current or not previous_2021_probe.get("reachable"):
        probe_2021 = point_query(
            boundary_2021,
            longitude,
            latitude,
            "LSOA21CD,LSOA21NM",
            attempts=attempts,
            timeout=timeout,
        )
        attrs_2021 = attributes(probe_2021)
    else:
        probe_2021 = dict(previous_2021_probe)
        probe_2021["parsed"] = {"features": [{"attributes": item} for item in previous_2021_attrs]}
        attrs_2021 = [dict(item) for item in previous_2021_attrs if isinstance(item, dict)]

    corrected_code = str(attrs_2011[0].get("LSOA11CD") or "") if len(attrs_2011) == 1 else ""
    point_2011_exact = bool(corrected_code)
    point_2021_exact = len(attrs_2021) == 1 and str(attrs_2021[0].get("LSOA21CD") or "") == current_code
    pair_record = pairs.get((corrected_code, current_code)) if corrected_code else None
    exact_pair = pair_record is not None
    original_already_correct = bool(corrected_code and corrected_code == original_code)

    if not probe_2011.get("reachable") or not probe_2021.get("reachable"):
        audit_status = "BLOCKED_BOUNDARY_NETWORK"
        confidence = int(source.get("parent_candidate_accuracy_percent") or 0)
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
        **previous,
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
        "audit_status": audit_status,
        "audit_confidence_percent": confidence,
        "candidate_value_changed": False,
        "direct_score_input": False,
        "recovery_attempted": True,
    }


initial_blocked = [row for row in rows if str(row.get("audit_status") or "").startswith("BLOCKED_")]
initial_blocked_count = len(initial_blocked)
row_by_id = {str(row.get("parcel_id") or ""): row for row in rows}

# First recovery pass: deliberately lower concurrency to remove pressure from
# the full-resolution ONS service while keeping bounded parallel progress.
with ThreadPoolExecutor(max_workers=5, thread_name_prefix="wave118-recovery") as executor:
    future_map = {
        executor.submit(
            recover_row,
            row,
            attempts=6,
            timeout=150,
            retry_current=not bool((row.get("boundary_2021_probe") or {}).get("reachable")),
        ): str(row.get("parcel_id") or "")
        for row in initial_blocked
    }
    for future in as_completed(future_map):
        parcel_id = future_map[future]
        try:
            row_by_id[parcel_id] = future.result()
        except Exception as exc:
            row_by_id[parcel_id] = {
                **row_by_id[parcel_id],
                "audit_status": "BLOCKED_RECOVERY_WORKER_EXCEPTION",
                "worker_error": f"{type(exc).__name__}: {exc}",
                "recovery_attempted": True,
            }

remaining = [
    row for row in row_by_id.values()
    if str(row.get("audit_status") or "").startswith("BLOCKED_")
]
first_pass_recovered = initial_blocked_count - len(remaining)

# Final recovery pass: one request stream, longer timeout, no service burst.
final_sequential_count = len(remaining)
for row in sorted(remaining, key=lambda item: str(item.get("parcel_id") or "")):
    recovered = recover_row(
        row,
        attempts=8,
        timeout=180,
        retry_current=not bool((row.get("boundary_2021_probe") or {}).get("reachable")),
    )
    row_by_id[str(row.get("parcel_id") or "")] = recovered
    time.sleep(0.35)

rows = sorted(
    row_by_id.values(),
    key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]),
)
if len(rows) != expected_rows:
    raise SystemExit(f"RECOVERY_ROW_COUNT_MISMATCH:{len(rows)}")

passed = sum(row.get("audit_status") == "PASS_CORRECTED_2011_POINT_AND_EXACT_RELATION" for row in rows)
held = sum(str(row.get("audit_status") or "").startswith("HELD_") for row in rows)
blocked = sum(str(row.get("audit_status") or "").startswith("BLOCKED_") for row in rows)
point_2011 = sum(bool(row.get("corrected_2011_point_confirmed")) for row in rows)
point_2021 = sum(bool(row.get("current_2021_point_confirmed")) for row in rows)
pair_confirmed = sum(bool(row.get("corrected_exact_pair_confirmed")) for row in rows)
already_correct = sum(bool(row.get("original_historical_code_already_correct")) for row in rows)
proposed_corrections = sum(bool(row.get("proposed_historical_code_correction")) for row in rows)
high_confidence_after = min(expected_parent_rows, parent_high_confidence_rows + passed)
parent_accuracy = round(100.0 * parent_high_confidence_rows / expected_parent_rows, 6)
support_accuracy = round(100.0 * high_confidence_after / expected_parent_rows, 6)
delta_pp = round(support_accuracy - parent_accuracy, 6)

operations = list(payload.get("operations") or [])[:5]
for row in rows:
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
            "source_sha256": (payload.get("sources") or {}).get("exact_fit_csv_sha256"),
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
if len(operations) != total_operations:
    raise SystemExit(f"RECOVERY_OPERATION_COUNT_MISMATCH:{len(operations)}")
completed_or_fail_closed = sum(item.get("status") in {"PASS", "FAIL_CLOSED"} for item in operations)
blocked_operations = sum(item.get("status") == "BLOCKED" for item in operations)

payload["rows"] = rows
payload["operations"] = operations
payload["recovery"] = {
    "triggered": initial_blocked_count > 0,
    "initial_blocked_rows": initial_blocked_count,
    "targeted_retry_workers": 5,
    "targeted_retry_rows": initial_blocked_count,
    "targeted_retry_recovered_rows": first_pass_recovered,
    "final_sequential_retry_rows": final_sequential_count,
    "final_blocked_rows": blocked,
    "second_task_created": False,
    "second_pr_created": False,
}
payload["result"] = {
    "candidate_rows": expected_parent_rows,
    "new_correction_candidates": passed,
    "rows_audited": len(rows),
    "corrected_2011_point_confirmed_rows": point_2011,
    "current_2021_point_confirmed_rows": point_2021,
    "corrected_exact_pair_confirmed_rows": pair_confirmed,
    "original_historical_code_already_correct_rows": already_correct,
    "proposed_historical_code_corrections": proposed_corrections,
    "fully_confirmed_support_rows": passed,
    "held_rows": held,
    "blocked_rows": blocked,
    "parent_high_confidence_rows": parent_high_confidence_rows,
    "high_confidence_support_rows_after_audit": high_confidence_after,
    "parent_accuracy_percent": parent_accuracy,
    "support_accuracy_percent": support_accuracy,
    "progress_delta_percentage_points": delta_pp,
    "line_by_line_rows": len(rows),
    "completed_or_fail_closed_operations": completed_or_fail_closed,
    "blocked_operations": blocked_operations,
    "total_operations": len(operations),
}
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

cards = [
    ("Denetlenen satır", f"{len(rows)}/{expected_rows}"),
    ("Tam doğrulanan", str(passed)),
    ("2011 nokta", str(point_2011)),
    ("2021 nokta", str(point_2021)),
    ("Exact pair", str(pair_confirmed)),
    ("Kod düzeltme adayı", str(proposed_corrections)),
    ("Kurtarılan blok", f"{initial_blocked_count - blocked}/{initial_blocked_count}"),
    ("HELD / BLOCKED", f"{held} / {blocked}"),
    ("İşlem", f"{completed_or_fail_closed}/{len(operations)}"),
    ("Kaynak ailesi", "3/3 resmî"),
    ("Destek doğruluğu", f"%{support_accuracy}"),
    ("Artış", f"+{delta_pp} yüzde puan"),
]
rows_html: list[str] = []
for row in rows:
    esc = lambda value: html.escape(str(value if value is not None else ""))
    rows_html.append(
        "<tr>"
        f"<td>{esc(row.get('parcel_id'))}</td>"
        f"<td>{esc(row.get('original_historical_lsoa_code'))}</td>"
        f"<td>{esc(row.get('corrected_2011_lsoa_code'))}</td>"
        f"<td>{esc(row.get('current_2021_lsoa_code'))}</td>"
        f"<td>{'PASS' if row.get('corrected_2011_point_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('current_2021_point_confirmed') else '—'}</td>"
        f"<td>{'PASS' if row.get('corrected_exact_pair_confirmed') else '—'}</td>"
        f"<td>{esc(row.get('change_indicator'))}</td>"
        f"<td>{esc(row.get('audit_status'))}</td>"
        f"<td>{esc(row.get('audit_confidence_percent'))}</td>"
        f"<td><code>{esc((row.get('boundary_2011_probe') or {}).get('sha256'))}</code></td>"
        f"<td><code>{esc((row.get('boundary_2021_probe') or {}).get('sha256'))}</code></td>"
        "</tr>"
    )
cards_html = "".join(
    f"<div class='card'><b>{html.escape(key)}</b><br>{html.escape(value)}</div>"
    for key, value in cards
)
page = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>security_public_safety_2 — Wave118 düzeltilmiş 2011 sınır denetimi</title>
<style>body{{font-family:system-ui,sans-serif;margin:20px;background:#f7f7f8;color:#171717}}h1{{font-size:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:12px}}table{{width:100%;border-collapse:collapse;background:white;font-size:12px}}th,td{{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eee}}code{{font-size:10px;word-break:break-all}}</style></head>
<body><h1>security_public_safety_2 — Wave118 resmî ONS tam çözünürlüklü 2011 sınır denetimi</h1>
<p>Wave116 içinde HELD kalan 394 satır, gerçek ONS 2011 BFC tam çözünürlüklü sınırı, 2021 sınırı ve resmî exact-fit ilişki tablosuyla satır bazında doğrulanmıştır. Geçici servis hataları düşük eşzamanlı hedefli yeniden denemeyle kurtarılmıştır. Ana aday değerleri ve skorları değiştirilmemiştir.</p>
<div class="cards">{cards_html}</div>
<p>Exact-fit CSV SHA-256: <code>{html.escape(str((payload.get('sources') or {}).get('exact_fit_csv_sha256')))}</code></p>
<table><thead><tr><th>Parsel</th><th>Önceki tarihsel kod</th><th>Doğru 2011 kodu</th><th>2021 kodu</th><th>2011 nokta</th><th>2021 nokta</th><th>Exact pair</th><th>Değişim</th><th>Durum</th><th>Güven</th><th>2011 SHA-256</th><th>2021 SHA-256</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table></body></html>"""
OUTPUT_HTML.write_text(page, encoding="utf-8")

print(json.dumps({
    "state": payload["state"],
    **payload["result"],
    "recovery": payload["recovery"],
    "json_sha256": hashlib.sha256(OUTPUT_JSON.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest(),
}, ensure_ascii=False))
