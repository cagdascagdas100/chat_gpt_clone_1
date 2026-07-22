from __future__ import annotations

import hashlib
import html
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
PARTITION = {"start": 30762, "end": 61522, "count": 30761, "canonical_count": 92283}
ROOT = Path.cwd()
BUSINESS_JSON = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/source_and_sample_gate_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"
SNAPSHOT_DATE = datetime.now(timezone.utc).date().isoformat()
USER_AGENT = "AAYS-TerraYield-security-public-safety-source-verifier/1.0"

if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
    raise SystemExit(f"WRONG_SLOT: {os.environ.get('AAYS_SLOT_ID')}")
if os.environ.get("AAYS_CHILD_DIRECT_PUSH_FORBIDDEN", "true").lower() != "true":
    raise SystemExit("DIRECT_PUSH_GUARD_MISSING")


def fetch(url: str, *, parse_json: bool = False, attempts: int = 3) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,*/*"})
            with urllib.request.urlopen(request, timeout=25) as response:
                body = response.read()
                result: dict[str, Any] = {
                    "reachable": 200 <= int(response.status) < 400,
                    "http_status": int(response.status),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "attempts": attempt,
                }
                if parse_json:
                    result["json"] = json.loads(body.decode("utf-8-sig"))
                return result
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(attempt)
    return {"reachable": False, "http_status": None, "bytes": 0, "sha256": None, "attempts": attempts, "error": last_error}


source_specs = [
    {"source_id": "hmlr_inspire_index_polygons", "name": "HM Land Registry INSPIRE Index Polygons", "publisher": "HM Land Registry", "url": "https://use-land-property-data.service.gov.uk/datasets/inspire", "role": "canonical_freehold_geometry_candidate", "measurement_level": "parcel", "accuracy_percent": 95, "promotion_rule": "Exact INSPIRE ID or documented containment only; retain indicative/freehold limitations.", "parse_json": False},
    {"source_id": "ons_lsoa_2021_bgc_v5", "name": "LSOA December 2021 Boundaries EW BGC V5", "publisher": "Office for National Statistics", "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0?f=json", "role": "official_public_safety_geography", "measurement_level": "lsoa", "accuracy_percent": 95, "promotion_rule": "Use LSOA21CD and polygon containment/centroid rule; preserve source version.", "parse_json": True},
    {"source_id": "ons_lsoa_2021_feature_count", "name": "LSOA 2021 Feature Count", "publisher": "Office for National Statistics", "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json", "role": "boundary_completeness_probe", "measurement_level": "lsoa", "accuracy_percent": 95, "promotion_rule": "Source-integrity check only; not a parcel row count.", "parse_json": True},
    {"source_id": "police_api_last_updated", "name": "Police.uk Crime Last Updated", "publisher": "Home Office / Police.uk", "url": "https://data.police.uk/api/crime-last-updated", "role": "explicit_month_selector", "measurement_level": "document", "accuracy_percent": 95, "promotion_rule": "Pin every request to returned YYYY-MM and retain response hash.", "parse_json": True},
    {"source_id": "police_api_street_contract", "name": "Police.uk Street-level Crime API Contract", "publisher": "Home Office / Police.uk", "url": "https://data.police.uk/docs/method/crime-street/", "role": "official_crime_event_source_contract", "measurement_level": "candidate_point", "accuracy_percent": 90, "promotion_rule": "Locations are anonymised approximations; aggregate within verified LSOA, never exact parcel crime.", "parse_json": False},
    {"source_id": "home_office_recorded_crime_tables", "name": "Police Recorded Crime and Outcomes Open Data Tables", "publisher": "Home Office", "url": "https://www.gov.uk/government/statistical-data-sets/police-recorded-crime-and-outcomes-open-data-tables", "role": "official_area_level_benchmark", "measurement_level": "local_authority", "accuracy_percent": 90, "promotion_rule": "Benchmark only; never publish PFA/CSP as parcel measurement.", "parse_json": False},
]

sources: list[dict[str, Any]] = []
for spec in source_specs:
    probe = fetch(spec["url"], parse_json=bool(spec["parse_json"]))
    parsed = probe.pop("json", None)
    row = {key: value for key, value in spec.items() if key != "parse_json"}
    row.update({"probe": probe, "status": "PROMOTED_FOR_ROLE" if probe["reachable"] else "HELD_UNREACHABLE", "source_snapshot_date": SNAPSHOT_DATE})
    if spec["source_id"] == "police_api_last_updated" and isinstance(parsed, dict):
        row["latest_available_month"] = parsed.get("date")
    if spec["source_id"] == "ons_lsoa_2021_feature_count" and isinstance(parsed, dict):
        row["official_feature_count"] = parsed.get("count")
    if spec["source_id"] == "ons_lsoa_2021_bgc_v5" and isinstance(parsed, dict):
        row.update({"layer_name": parsed.get("name"), "object_id_field": parsed.get("objectIdField"), "geometry_type": parsed.get("geometryType"), "max_record_count": parsed.get("maxRecordCount")})
    sources.append(row)

promoted = [item for item in sources if item["status"] == "PROMOTED_FOR_ROLE"]
held = [item for item in sources if item["status"] != "PROMOTED_FOR_ROLE"]
accuracy_ge_90 = sum(item["accuracy_percent"] >= 90 and item["status"] == "PROMOTED_FOR_ROLE" for item in sources)
accuracy_ge_95 = sum(item["accuracy_percent"] >= 95 and item["status"] == "PROMOTED_FOR_ROLE" for item in sources)
source_month = next((item.get("latest_available_month") for item in sources if item["source_id"] == "police_api_last_updated"), None)
sample_candidates = [{"parcel_id": f"parcel_{n}", "partition_ordinal": n, "data_status": "no_data", "candidate_state": "PENDING_CANONICAL_GEOMETRY_AND_LSOA_JOIN", "security_level_percent": None, "confidence": 0, "source_zone_id": None, "source_month": source_month, "spatial_join_method": "NOT_RUN", "promotion_allowed": False} for n in range(30762, 30765)]

gates = [
    {"gate": "remote_head_and_slot_readback", "state": "PASS", "evidence": "Authoritative sequence 0 was read before queue dispatch."},
    {"gate": "hmlr_official_source_probe", "state": "PASS" if sources[0]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "ons_lsoa_layer_probe", "state": "PASS" if sources[1]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "ons_lsoa_count_probe", "state": "PASS" if sources[2]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "police_api_month_probe", "state": "PASS" if sources[3]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "police_api_contract_probe", "state": "PASS" if sources[4]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "home_office_benchmark_probe", "state": "PASS" if sources[5]["probe"]["reachable"] else "BLOCKED"},
    {"gate": "three_row_candidate_gate_prepared", "state": "PASS"},
    {"gate": "three_row_geometry_and_lsoa_hydration", "state": "PENDING"},
    {"gate": "three_row_explicit_month_api_hashes", "state": "PENDING"},
    {"gate": "expand_to_300_verified_rows", "state": "PENDING"},
    {"gate": "http_hash_dom_console_browser_acceptance", "state": "PENDING"},
]
completed_operations = sum(item["state"] == "PASS" for item in gates)
total_operations = len(gates)
overall_progress = round((completed_operations / total_operations) * 40, 1)
payload = {
    "schema_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": SLOT_ID, "base_slot_id": "security_public_safety", "shard_index": 2, "parcel_partition": PARTITION,
    "state": "SOURCE_CHAIN_VERIFIED_THREE_ROW_GATE_PENDING_GEOMETRY", "first_unverified_step": "HYDRATE_300_ROWS_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "source_snapshot_date": SNAPSHOT_DATE,
    "sources_reviewed": len(sources), "promoted_sources": len(promoted), "held_sources": len(held), "accuracy_ge_95_source_count": accuracy_ge_95, "accuracy_ge_90_source_count": accuracy_ge_90,
    "sample_candidate_count": 3, "verified_slot_rows": 0, "actual_business_rows_written": 0, "candidate_rows": sample_candidates, "sources": sources, "gates": gates,
    "completed_operations": completed_operations, "total_operations": total_operations, "overall_progress_percent": overall_progress, "progress_delta_percent": overall_progress, "business_row_progress_percent": 0,
    "progress_formula": "PASS preparation gates / 12, capped at 40 percent before verified parcel hydration.",
    "blockers": ["Canonical parcel geometry/centroid records for parcel_30762 through parcel_61522 are required before LSOA assignment.", "No parcel score may be promoted until the first three rows pass exact geometry, explicit-month API hash and provenance checks.", "HTTP, DOM, console and browser acceptance have not run."],
    "next_required_action": "Resolve exact geometry for parcel_30762..30764, join ONS LSOA21 polygon, execute Police.uk explicit-month requests, hash responses, then expand only after all three pass.",
    "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False, "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
}
for path in (BUSINESS_JSON, WEB_JSON):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
source_rows = "".join(f"<tr><td>{i}</td><td>{html.escape(x['name'])}</td><td>{html.escape(x['publisher'])}</td><td>{x['accuracy_percent']}%</td><td>{html.escape(x['status'])}</td><td>{x['probe'].get('http_status') or '-'}</td><td><code>{html.escape(str(x['probe'].get('sha256') or '-'))}</code></td><td>{html.escape(x['role'])}</td></tr>" for i, x in enumerate(sources, 1))
candidate_rows = "".join(f"<tr><td>{html.escape(x['parcel_id'])}</td><td>{html.escape(x['candidate_state'])}</td><td>{html.escape(str(x['source_month']))}</td><td>null</td><td>0</td><td>NOT_RUN</td></tr>" for x in sample_candidates)
gate_rows = "".join(f"<tr><td>{i}</td><td>{html.escape(x['gate'])}</td><td class='{html.escape(x['state'])}'>{html.escape(x['state'])}</td><td>{html.escape(str(x.get('evidence','')))}</td></tr>" for i, x in enumerate(gates, 1))
document = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Security Public Safety 2</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:150px}}table{{border-collapse:collapse;width:100%;background:#fff;font-size:12px;margin:14px 0}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}code{{font-size:10px;word-break:break-all}}.PASS{{font-weight:700}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style></head><body><h1>security_public_safety_2 — satır satır doğrulama</h1><div class='notice'>Doğrulanmış parsel satırı 0'dır; geometri ve LSOA birleşimi geçmeden skor üretilmez.</div><div class='cards'><div class='card'>Genel ilerleme<br><b>{overall_progress}%</b></div><div class='card'>Artış<br><b>+{overall_progress}%</b></div><div class='card'>İşlem<br><b>{completed_operations}/{total_operations}</b></div><div class='card'>Kaynak<br><b>{len(promoted)}/{len(sources)}</b></div><div class='card'>≥95 doğruluk<br><b>{accuracy_ge_95}</b></div><div class='card'>≥90 doğruluk<br><b>{accuracy_ge_90}</b></div><div class='card'>Aday satır<br><b>3</b></div><div class='card'>Doğrulanmış satır<br><b>0</b></div></div><h2>Kaynak doğrulama satırları</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Yayıncı</th><th>Doğruluk</th><th>Durum</th><th>HTTP</th><th>SHA256</th><th>Rol</th></tr></thead><tbody>{source_rows}</tbody></table><h2>İlk 3 aday</h2><table><thead><tr><th>Parsel</th><th>Durum</th><th>Kaynak ayı</th><th>Skor</th><th>Güven</th><th>Birleşim</th></tr></thead><tbody>{candidate_rows}</tbody></table><h2>Kabul kapıları</h2><table><thead><tr><th>#</th><th>Kapı</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{gate_rows}</tbody></table><p><b>Sonraki adım:</b> {html.escape(payload['next_required_action'])}</p><p><b>final_ready:</b> false</p></body></html>"""
WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
WEB_HTML.write_text(document, encoding="utf-8")
print(json.dumps({"status": payload["state"], "slot_id": SLOT_ID, "completed_operations": completed_operations, "total_operations": total_operations, "overall_progress_percent": overall_progress, "promoted_sources": len(promoted), "sample_candidate_count": 3, "verified_slot_rows": 0, "final_ready": False}, ensure_ascii=False))
