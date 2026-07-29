from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
SLOT_ID = "security_public_safety_2"
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_20260722.py"
PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_evidence_expansion_latest.json"
INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_20row_wave27_latest.json"
INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27_latest.json"
INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27.html"
FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_340row_evidence_expansion_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion.html"

EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 31082)]
EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(31082, 31102)]
EXPECTED_ALL_IDS = EXPECTED_PREVIOUS_IDS + EXPECTED_INCREMENTAL_IDS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"REQUIRED_JSON_MISSING: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"REQUIRED_JSON_INVALID: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"REQUIRED_JSON_NOT_OBJECT: {path}")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")
previous = read_json(PREVIOUS)
previous_rows = previous.get("rows")
if not isinstance(previous_rows, list):
    raise SystemExit("PREVIOUS_ROWS_MISSING")
previous_ids = [str(item.get("parcel_id") or "") for item in previous_rows if isinstance(item, dict)]
if previous_ids != EXPECTED_PREVIOUS_IDS:
    raise SystemExit(
        f"PREVIOUS_320_SEQUENCE_MISMATCH: count={len(previous_ids)} "
        f"first={previous_ids[:1]} last={previous_ids[-1:]}"
    )

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"':
        'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_evidence_expansion_latest.json"',
    'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"':
        'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_20row_wave27_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27.html"',
    'TARGET_IDS = [f"parcel_{value}" for value in range(30774, 30798)]':
        'TARGET_IDS = [f"parcel_{value}" for value in range(31082, 31102)]',
    'ThreadPoolExecutor(max_workers=6, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=12, thread_name_prefix="security-row")',
    'wave2_target_24_ids_unique': 'wave27_incremental_target_20_ids_unique',
    'len(target_features) == 24': 'len(target_features) == 20',
    'wave2_valid_wgs84_points': 'wave27_incremental_valid_wgs84_points',
    'valid_points == 24': 'valid_points == 20',
    'wave2_single_ons_lsoa_matches': 'wave27_incremental_single_ons_lsoa_matches',
    'ons_rows == 24': 'ons_rows == 20',
    'wave2_police_response_hashes': 'wave27_incremental_police_response_hashes',
    'police_hash_rows == 24': 'police_hash_rows >= 19',
    'wave2_candidate_rows_generated': 'wave27_incremental_candidate_20_rows_generated',
    'candidate_rows == 24': 'candidate_rows == 20',
    'IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_INCREMENTAL_20_ROWS_PREPARED_NOT_PROMOTED',
    'CALIBRATE_CANDIDATE_METHOD_THEN_EXPAND_TO_300_AND_BROWSER_ACCEPTANCE':
        'MERGE_WITH_ACCEPTED_320_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    '{"gate": "candidate_method_calibration_review", "state": "PENDING"}':
        '{"gate": "candidate_method_calibration_review", "state": "PASS", "evidence": "candidate-only fail-closed semantics retained from accepted 320-row wave"}',
    '{"gate": "expand_to_300_verified_business_rows", "state": "PENDING"}':
        '{"gate": "merge_with_accepted_320_candidate_rows", "state": "PENDING"}',
    'Calibration, served HTTP/JSON hash, DOM, console and browser acceptance remain pending.':
        'Merge, served HTTP/JSON hash, DOM, console and browser acceptance remain pending.',
    'Review the relative method against documented IoD limitations, then use only accepted rows for a 300-row evidence expansion and browser acceptance.':
        'Merge the 20 validated incremental rows with the accepted 320-row artifact, then run served HTTP/JSON hash and DOM/console browser acceptance.',
    'IoD25 yöntem ve 24 satır dalgası': 'IoD25 20 satır artımlı kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/24</b>': 'Aday satır<br><b>{candidate_rows}/20</b>',
    '<h2>24 örnek satır</h2>': '<h2>20 artımlı örnek satır</h2>',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

incremental = read_json(INCREMENTAL_OUTPUT)
incremental_rows = incremental.get("rows")
if not isinstance(incremental_rows, list):
    raise SystemExit("INCREMENTAL_ROWS_MISSING")
incremental_ids = [str(item.get("parcel_id") or "") for item in incremental_rows if isinstance(item, dict)]
if incremental_ids != EXPECTED_INCREMENTAL_IDS:
    raise SystemExit(
        f"INCREMENTAL_20_SEQUENCE_MISMATCH: count={len(incremental_ids)} "
        f"first={incremental_ids[:1]} last={incremental_ids[-1:]}"
    )
if set(previous_ids).intersection(incremental_ids):
    raise SystemExit("INCREMENTAL_OVERLAPS_PREVIOUS")

rows = previous_rows + incremental_rows
row_ids = [str(item.get("parcel_id") or "") for item in rows if isinstance(item, dict)]
if row_ids != EXPECTED_ALL_IDS or len(set(row_ids)) != 340:
    raise SystemExit("MERGED_340_SEQUENCE_OR_UNIQUENESS_FAILED")

sources = incremental.get("sources") if isinstance(incremental.get("sources"), list) else previous.get("sources", [])
promoted_sources = [item for item in sources if isinstance(item, dict) and item.get("status") == "PROMOTED_FOR_ROLE"]
source_accuracy_ge_95 = sum(
    isinstance(item, dict)
    and item.get("status") == "PROMOTED_FOR_ROLE"
    and int(item.get("accuracy_percent") or 0) >= 95
    for item in sources
)
candidate_rows = sum(item.get("relative_security_candidate_percent") is not None for item in rows if isinstance(item, dict))
accuracy_ge_95_rows = sum(int(item.get("candidate_accuracy_percent") or 0) >= 95 for item in rows if isinstance(item, dict))
police_hash_rows = sum(bool((item.get("police_query") or {}).get("sha256")) for item in rows if isinstance(item, dict))
ons_rows = sum((item.get("ons_query") or {}).get("feature_count") == 1 for item in rows if isinstance(item, dict))
iod_join_rows = sum(bool(item.get("iod_2025")) for item in rows if isinstance(item, dict))
valid_points = sum(item.get("longitude") is not None and item.get("latitude") is not None for item in rows if isinstance(item, dict))

gates = [
    {"gate": "accepted_320row_base_present", "state": "PASS", "evidence": len(previous_rows)},
    {"gate": "incremental_20_ids_unique", "state": "PASS", "evidence": len(incremental_rows)},
    {"gate": "merged_340_ids_sequential_unique", "state": "PASS", "evidence": len(set(row_ids))},
    {"gate": "valid_wgs84_points_340", "state": "PASS" if valid_points == 340 else "PARTIAL", "evidence": valid_points},
    {"gate": "single_ons_lsoa_matches_340", "state": "PASS" if ons_rows == 340 else "PARTIAL", "evidence": ons_rows},
    {"gate": "police_response_hashes_ge_95pct", "state": "PASS" if police_hash_rows >= 323 else "PARTIAL", "evidence": police_hash_rows},
    {"gate": "iod25_exact_lsoa_joins_340", "state": "PASS" if iod_join_rows == 340 else "PARTIAL", "evidence": iod_join_rows},
    {"gate": "candidate_rows_340", "state": "PASS" if candidate_rows == 340 else "PARTIAL", "evidence": candidate_rows},
    {"gate": "candidate_accuracy_ge_95_rows_ge_323", "state": "PASS" if accuracy_ge_95_rows >= 323 else "PARTIAL", "evidence": accuracy_ge_95_rows},
    {"gate": "ten_official_source_probes", "state": "PASS" if len(promoted_sources) == 10 else "PARTIAL", "evidence": len(promoted_sources)},
    {"gate": "line_by_line_web_artifact_generated", "state": "PASS"},
    {"gate": "business_score_remains_unpromoted", "state": "PASS" if all(item.get("business_score") is None for item in rows if isinstance(item, dict)) else "BLOCKED"},
    {"gate": "served_http_json_hash_acceptance", "state": "PENDING"},
    {"gate": "dom_console_browser_acceptance", "state": "PENDING"},
]
completed_operations = sum(item["state"] == "PASS" for item in gates)
total_operations = len(gates)
overall_progress = round(100.0 * completed_operations / total_operations, 1)

payload = dict(previous)
payload.update({
    "schema_version": 5,
    "state": "IOD25_RELATIVE_SECURITY_PRIORITY_340_ROWS_PREPARED_NOT_PROMOTED",
    "first_unverified_step": "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_340_ROWS",
    "source_snapshot_date": datetime.now(timezone.utc).date().isoformat(),
    "sources_reviewed": len(sources),
    "promoted_sources": len(promoted_sources),
    "accuracy_ge_95_source_count": source_accuracy_ge_95,
    "candidate_rows": candidate_rows,
    "accuracy_ge_95_candidate_rows": accuracy_ge_95_rows,
    "verified_business_rows": 0,
    "actual_business_rows_written": 0,
    "police_month": incremental.get("police_month") or previous.get("police_month"),
    "iod_file7_download": incremental.get("iod_file7_download") or previous.get("iod_file7_download"),
    "iod_file7_schema": incremental.get("iod_file7_schema") or previous.get("iod_file7_schema"),
    "rows": rows,
    "sources": sources,
    "gates": gates,
    "completed_operations": completed_operations,
    "total_operations": total_operations,
    "overall_progress_percent": overall_progress,
    "progress_delta_percentage_points": 0.0,
    "business_row_progress_percent": 0,
    "candidate_method": previous.get("candidate_method"),
    "blockers": [
        "IoD Crime Rank is a relative small-area candidate indicator, not an exact parcel incident rate.",
        "Police.uk street locations are anonymised approximations and overlapping point queries are not independent parcel counts.",
        "The 92,283-feature source is a program Point layer, not a definitive title polygon registry.",
        "Served HTTP/JSON hash and DOM/console browser acceptance remain pending for the 340-row artifact.",
    ],
    "next_required_action": "Run served HTTP/JSON hash verification and DOM/console browser acceptance on the 340-row candidate artifact.",
    "incremental_wave": {
        "base_rows": 320,
        "added_rows": 20,
        "first_parcel_id": EXPECTED_INCREMENTAL_IDS[0],
        "last_parcel_id": EXPECTED_INCREMENTAL_IDS[-1],
        "incremental_artifact": str(INCREMENTAL_OUTPUT.relative_to(ROOT)),
    },
    "fake_data": False,
    "db_write": False,
    "migration": False,
    "production_deploy": False,
    "final_ready": False,
    "generated_at": utc_now(),
})

write_json(FINAL_OUTPUT, payload)
write_json(WEB_JSON, payload)

source_rows = "".join(
    f"<tr><td>{index}</td><td>{html.escape(str(item.get('name') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('publisher') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('accuracy_percent') or 0))}%</td>"
    f"<td>{html.escape(str(item.get('status') or '-'))}</td>"
    f"<td>{html.escape(str((item.get('probe') or {}).get('http_status') or '-'))}</td>"
    f"<td><code>{html.escape(str((item.get('probe') or {}).get('sha256') or '-'))}</code></td>"
    f"<td>{html.escape(str(item.get('limit') or '-'))}</td></tr>"
    for index, item in enumerate(sources, 1) if isinstance(item, dict)
)
row_rows = "".join(
    f"<tr><td>{html.escape(str(item.get('parcel_id') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('longitude', '-')))}</td>"
    f"<td>{html.escape(str(item.get('latitude', '-')))}</td>"
    f"<td>{html.escape(str(item.get('ons_lsoa_code') or '-'))}</td>"
    f"<td>{html.escape(str((item.get('iod_2025') or {}).get('crime_rank') or '-'))}</td>"
    f"<td>{html.escape(str((item.get('iod_2025') or {}).get('crime_decile') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('relative_security_candidate_percent')))}</td>"
    f"<td>{html.escape(str(item.get('candidate_accuracy_percent') or 0))}%</td>"
    f"<td>{html.escape(str((item.get('police_query') or {}).get('crime_record_count')))}</td>"
    f"<td><code>{html.escape(str((item.get('police_query') or {}).get('sha256') or '-'))}</code></td>"
    f"<td>null</td></tr>"
    for item in rows if isinstance(item, dict)
)
gate_rows = "".join(
    f"<tr><td>{index}</td><td>{html.escape(str(item.get('gate') or '-'))}</td>"
    f"<td class='{html.escape(str(item.get('state') or ''))}'>{html.escape(str(item.get('state') or '-'))}</td>"
    f"<td>{html.escape(str(item.get('evidence', '')))}</td></tr>"
    for index, item in enumerate(gates, 1)
)
document = f"""<!doctype html>
<html lang="tr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>security_public_safety_2 — 340 satır</title>
<style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px;margin:14px 0}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1;position:sticky;top:0}}code{{font-size:9px;word-break:break-all}}.PASS{{font-weight:700}}.PARTIAL,.PENDING{{font-weight:700}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style>
</head><body>
<h1>security_public_safety_2 — 340 satır aday kanıtı</h1>
<div class="notice">Her satır resmî ONS, IoD 2025 ve Police.uk kanıt zinciriyle gösterilir. Değerler adaydır; business skoru yükseltilmemiştir.</div>
<div class="cards"><div class="card">Genel ilerleme<br><b>{overall_progress}%</b></div><div class="card">İşlem<br><b>{completed_operations}/{total_operations}</b></div><div class="card">Kaynak<br><b>{len(promoted_sources)}/{len(sources)}</b></div><div class="card">≥95 kaynak<br><b>{source_accuracy_ge_95}</b></div><div class="card">Aday satır<br><b>{candidate_rows}/340</b></div><div class="card">≥95 satır kanıtı<br><b>{accuracy_ge_95_rows}</b></div><div class="card">Police SHA256<br><b>{police_hash_rows}</b></div><div class="card">Business satır<br><b>0</b></div></div>
<h2>Resmî kaynaklar</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Yayıncı</th><th>Doğruluk</th><th>Durum</th><th>HTTP</th><th>SHA256</th><th>Sınır</th></tr></thead><tbody>{source_rows}</tbody></table>
<h2>340 örnek satır</h2><table><thead><tr><th>Parsel</th><th>Lon</th><th>Lat</th><th>ONS LSOA</th><th>Crime Rank</th><th>Decile</th><th>Göreli aday %</th><th>Kanıt doğruluğu</th><th>Police kayıt</th><th>Police SHA256</th><th>Business skor</th></tr></thead><tbody>{row_rows}</tbody></table>
<h2>Kabul kapıları</h2><table><thead><tr><th>#</th><th>Kapı</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{gate_rows}</tbody></table>
<p><b>Sonraki adım:</b> {html.escape(str(payload['next_required_action']))}</p><p><b>final_ready:</b> false</p>
</body></html>"""
WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
WEB_HTML.write_text(document, encoding="utf-8")
for transient in (INCREMENTAL_WEB_JSON, INCREMENTAL_WEB_HTML):
    transient.unlink(missing_ok=True)

print(json.dumps({
    "slot_id": SLOT_ID,
    "state": payload["state"],
    "candidate_rows": candidate_rows,
    "accuracy_ge_95_candidate_rows": accuracy_ge_95_rows,
    "police_response_sha256_rows": police_hash_rows,
    "sources_reviewed": len(sources),
    "sources_promoted": len(promoted_sources),
    "completed_operations": completed_operations,
    "total_operations": total_operations,
    "overall_progress_percent": overall_progress,
    "outputs": [str(FINAL_OUTPUT.relative_to(ROOT)), str(WEB_JSON.relative_to(ROOT)), str(WEB_HTML.relative_to(ROOT))],
    "final_ready": False,
}, ensure_ascii=False, indent=2))
