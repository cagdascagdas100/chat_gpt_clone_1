from __future__ import annotations

import concurrent.futures
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
ROOT = Path.cwd()
OUT_JSON = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/light_official_source_expansion_wave3_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/source_expansion_wave3_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/source_expansion_wave3.html"
USER_AGENT = "AAYS-TerraYield-security-public-safety-source-expansion/3.0"
SNAPSHOT_DATE = datetime.now(timezone.utc).date().isoformat()

if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
    raise SystemExit(f"WRONG_SLOT: {os.environ.get('AAYS_SLOT_ID')}")
if os.environ.get("AAYS_CHILD_DIRECT_PUSH_FORBIDDEN", "true").lower() != "true":
    raise SystemExit("DIRECT_PUSH_GUARD_MISSING")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(spec: dict[str, Any]) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(
                spec["url"],
                headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,text/csv,*/*"},
            )
            with urllib.request.urlopen(request, timeout=35) as response:
                body = response.read()
                parsed_summary: dict[str, Any] = {}
                content_type = response.headers.get("Content-Type", "")
                if "json" in content_type.lower():
                    try:
                        parsed = json.loads(body.decode("utf-8-sig"))
                        if isinstance(parsed, list):
                            parsed_summary = {"json_type": "list", "json_item_count": len(parsed)}
                        elif isinstance(parsed, dict):
                            parsed_summary = {"json_type": "object", "json_keys": sorted(parsed.keys())[:30]}
                            for key in ("date", "count", "name", "geometryType", "objectIdField"):
                                if key in parsed:
                                    parsed_summary[key] = parsed[key]
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        parsed_summary = {"json_parse": "FAILED"}
                return {
                    **spec,
                    "status": "PROMOTED_FOR_ROLE" if 200 <= int(response.status) < 400 else "HELD_HTTP",
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": content_type,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "retrieved_at": utc_now(),
                    "attempts": attempt,
                    "parsed_summary": parsed_summary,
                }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 3:
                time.sleep(attempt)
    return {
        **spec,
        "status": "HELD_UNREACHABLE",
        "http_status": None,
        "bytes": 0,
        "sha256": None,
        "attempts": 3,
        "error": last_error,
        "retrieved_at": utc_now(),
        "parsed_summary": {},
    }


SOURCES = [
    {"source_id":"hmlr_inspire_download","name":"HM Land Registry INSPIRE download","publisher":"HM Land Registry","url":"https://use-land-property-data.service.gov.uk/datasets/inspire/download","role":"indicative_freehold_geometry_route","source_role_confidence_percent":95,"limit":"Indicative freehold extents; not definitive title boundaries and not complete leasehold coverage."},
    {"source_id":"hmlr_inspire_metadata","name":"INSPIRE Index Polygons metadata","publisher":"HM Land Registry / data.gov.uk","url":"https://www.data.gov.uk/dataset/811bcf4c-fbbf-4597-aa9c-3d5bd3bfd455/inspire-index-polygons-spatial-data","role":"publisher_update_metadata","source_role_confidence_percent":95,"limit":"Metadata and access route only."},
    {"source_id":"ons_lsoa_layer","name":"LSOA 2021 BGC V5 layer","publisher":"Office for National Statistics","url":"https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0?f=json","role":"official_lsoa_point_intersection","source_role_confidence_percent":98,"limit":"Area geography; not a parcel boundary."},
    {"source_id":"ons_lsoa_count","name":"LSOA 2021 feature count","publisher":"Office for National Statistics","url":"https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json","role":"boundary_completeness_probe","source_role_confidence_percent":98,"limit":"Integrity count only."},
    {"source_id":"police_last_updated","name":"Police.uk last updated","publisher":"Home Office / Police.uk","url":"https://data.police.uk/api/crime-last-updated","role":"explicit_month_selector","source_role_confidence_percent":98,"limit":"Month selector only."},
    {"source_id":"police_forces","name":"Police.uk forces endpoint","publisher":"Home Office / Police.uk","url":"https://data.police.uk/api/forces","role":"api_reference_integrity","source_role_confidence_percent":96,"limit":"Force directory; not parcel evidence."},
    {"source_id":"police_categories","name":"Police.uk crime categories","publisher":"Home Office / Police.uk","url":"https://data.police.uk/api/crime-categories?date=2026-05","role":"category_schema_for_explicit_month","source_role_confidence_percent":96,"limit":"Category schema only."},
    {"source_id":"police_street_contract","name":"Police.uk street crime contract","publisher":"Home Office / Police.uk","url":"https://data.police.uk/docs/method/crime-street/","role":"official_event_api_contract","source_role_confidence_percent":95,"limit":"Published locations are anonymised approximations; not exact parcel incidents."},
    {"source_id":"police_availability","name":"Police.uk data availability","publisher":"Home Office / Police.uk","url":"https://data.police.uk/docs/method/crime-last-updated/","role":"coverage_and_refresh_contract","source_role_confidence_percent":95,"limit":"Availability documentation only."},
    {"source_id":"home_office_tables","name":"Police recorded crime open data tables","publisher":"Home Office","url":"https://www.gov.uk/government/statistical-data-sets/police-recorded-crime-and-outcomes-open-data-tables","role":"official_area_benchmark","source_role_confidence_percent":95,"limit":"Benchmark geography cannot be copied to parcels."},
    {"source_id":"home_office_user_guide","name":"Police recorded crime open data user guide","publisher":"Home Office","url":"https://www.gov.uk/government/statistics/police-recorded-crime-open-data-tables/police-recorded-crime-and-outcomes-open-data-tables-user-guide","role":"field_and_quality_documentation","source_role_confidence_percent":95,"limit":"Method documentation only."},
    {"source_id":"data_gov_local_crime","name":"Local police recorded crime data","publisher":"Home Office / data.gov.uk","url":"https://www.data.gov.uk/dataset/0e26ee1b-26b7-406e-a3b1-f3481b324977/local-police-recorded-crime-data","role":"official_bulk_data_route","source_role_confidence_percent":95,"limit":"Bulk route; geography and month must be retained."},
    {"source_id":"iod_2025_main","name":"English indices of deprivation 2025","publisher":"MHCLG","url":"https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025","role":"official_lsoa_crime_domain_candidate","source_role_confidence_percent":98,"limit":"Relative deprivation domain; not a live monthly incident count."},
    {"source_id":"iod_2025_faq","name":"IoD 2025 FAQ","publisher":"MHCLG","url":"https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025/english-indices-of-deprivation-2025-frequently-asked-questions","role":"interpretation_limits","source_role_confidence_percent":98,"limit":"Interpretation and comparison guidance only."},
    {"source_id":"iod_2025_technical","name":"IoD 2025 technical report","publisher":"MHCLG","url":"https://www.gov.uk/government/publications/english-indices-of-deprivation-2025-technical-report","role":"methodology_and_domain_definition","source_role_confidence_percent":98,"limit":"Relative index methodology; calibration required before any security percentage."},
    {"source_id":"ons_lsoa_population","name":"LSOA mid-year population estimates","publisher":"Office for National Statistics","url":"https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/lowersuperoutputareamidyearpopulationestimatesnationalstatistics","role":"official_population_denominator_route","source_role_confidence_percent":98,"limit":"Edition and LSOA-code compatibility must be verified before rate calculation."},
]

with concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="security-light-source") as executor:
    rows = list(executor.map(fetch, SOURCES))

promoted = [row for row in rows if row["status"] == "PROMOTED_FOR_ROLE"]
confidence_ge_95 = sum(row["status"] == "PROMOTED_FOR_ROLE" and row["source_role_confidence_percent"] >= 95 for row in rows)
confidence_ge_98 = sum(row["status"] == "PROMOTED_FOR_ROLE" and row["source_role_confidence_percent"] >= 98 for row in rows)
operations = [
    {"operation":"parallel_official_source_probe_16","state":"PASS" if len(rows) == 16 else "BLOCKED","evidence":len(rows)},
    {"operation":"promoted_official_roles","state":"PASS" if len(promoted) >= 12 else "PARTIAL","evidence":len(promoted)},
    {"operation":"source_sha256_inventory","state":"PASS" if all(row.get("sha256") for row in promoted) else "PARTIAL","evidence":sum(bool(row.get("sha256")) for row in rows)},
    {"operation":"source_role_limits_recorded","state":"PASS","evidence":16},
    {"operation":"line_by_line_web_artifact","state":"PASS","evidence":"source_expansion_wave3.html"},
    {"operation":"canonical_12_row_wave","state":"PENDING","evidence":"queued separately"},
    {"operation":"iod_relative_24_row_wave","state":"PENDING","evidence":"queued separately"},
    {"operation":"business_score_promotion","state":"PENDING","evidence":"method and browser acceptance required"},
]
completed = sum(item["state"] == "PASS" for item in operations)
payload = {
    "schema_version":3,
    "architecture_version":3,
    "workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id":SLOT_ID,
    "base_slot_id":"security_public_safety",
    "shard_index":2,
    "state":"LIGHT_OFFICIAL_SOURCE_EXPANSION_COMPLETE_NO_BUSINESS_PROMOTION",
    "source_snapshot_date":SNAPSHOT_DATE,
    "sources_reviewed":len(rows),
    "promoted_sources":len(promoted),
    "held_sources":len(rows)-len(promoted),
    "source_role_confidence_ge_95_count":confidence_ge_95,
    "source_role_confidence_ge_98_count":confidence_ge_98,
    "completed_operations":completed,
    "total_operations":len(operations),
    "operations":operations,
    "sources":rows,
    "candidate_business_rows":0,
    "verified_business_rows":0,
    "progress_note":"Source-role coverage only; the canonical geometry, LSOA, rate methodology and browser gates remain authoritative for overall progress.",
    "fake_data":False,
    "db_write":False,
    "migration":False,
    "production_deploy":False,
    "final_ready":False,
    "generated_at":utc_now(),
}
for path in (OUT_JSON, WEB_JSON):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

source_rows = "".join(
    f"<tr><td>{i}</td><td>{html.escape(row['name'])}</td><td>{html.escape(row['publisher'])}</td><td>{row['source_role_confidence_percent']}%</td><td>{html.escape(row['status'])}</td><td>{row.get('http_status') or '-'}</td><td>{row.get('bytes') or 0}</td><td><code>{html.escape(str(row.get('sha256') or '-'))}</code></td><td>{html.escape(row['role'])}</td><td>{html.escape(row['limit'])}</td></tr>"
    for i,row in enumerate(rows,1)
)
operation_rows = "".join(
    f"<tr><td>{i}</td><td>{html.escape(item['operation'])}</td><td>{html.escape(item['state'])}</td><td>{html.escape(str(item['evidence']))}</td></tr>"
    for i,item in enumerate(operations,1)
)
doc = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Security Source Expansion Wave 3</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:white;border:1px solid #cfd8dc;padding:10px;min-width:145px}}table{{border-collapse:collapse;width:100%;background:white;font-size:11px;margin:14px 0}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}code{{font-size:9px;word-break:break-all}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c}}</style></head><body><h1>security_public_safety_2 — resmî kaynak genişletme dalgası 3</h1><div class='notice'>Bu sayfa kaynak rolü ve erişilebilirlik kanıtıdır. Parsel business skoru üretmez.</div><div class='cards'><div class='card'>Kaynak<br><b>{len(rows)}</b></div><div class='card'>Yükseltilen<br><b>{len(promoted)}</b></div><div class='card'>≥95 rol güveni<br><b>{confidence_ge_95}</b></div><div class='card'>≥98 rol güveni<br><b>{confidence_ge_98}</b></div><div class='card'>İşlem<br><b>{completed}/{len(operations)}</b></div><div class='card'>Business satırı<br><b>0</b></div></div><h2>Kaynak satırları</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Yayıncı</th><th>Rol güveni</th><th>Durum</th><th>HTTP</th><th>Bayt</th><th>SHA256</th><th>Rol</th><th>Sınır</th></tr></thead><tbody>{source_rows}</tbody></table><h2>İşlemler</h2><table><thead><tr><th>#</th><th>İşlem</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody>{operation_rows}</tbody></table><p><b>final_ready:</b> false</p></body></html>"""
WEB_HTML.parent.mkdir(parents=True, exist_ok=True)
WEB_HTML.write_text(doc, encoding="utf-8")
print(json.dumps({"slot_id":SLOT_ID,"state":payload["state"],"sources":len(rows),"promoted":len(promoted),"operations":f"{completed}/{len(operations)}","final_ready":False}, ensure_ascii=False))
