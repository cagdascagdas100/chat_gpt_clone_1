import json
import hashlib
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import subprocess

SLOT = "building_type_9"
CITY = "Ripon"
GRID = "RIPON_CENTRAL_02"
LOCAL_AUTHORITY = "North Yorkshire"
BATCH = 46
EXPECTED_BEFORE = 2250
TARGET_AFTER = 2300
NEXT_TARGET = 2350
BASE_URL = "https://api.openstreetmap.org/api/0.6/map"

geo_path = Path("england_map_web/data/building_type/shards/building_type_9_latest.geojson")
manifest_path = Path("england_map_web/data/building_type/shards/building_type_9_manifest_latest.json")
runner_path = Path("docs/chatgpt_status/building_type/slots/building_type_9/runner_outputs/building_type_9_classification_latest.json")
status_path = Path("docs/chatgpt_status/_shared/slots_21/building_type_9/status_latest.json")
checkpoint_path = Path("docs/chatgpt_status/_shared/slots_21/building_type_9/checkpoint_latest.json")
task_path = Path("docs/chatgpt_status/_shared/slots_21/building_type_9/current_task_latest.json")

def read_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

geo = read_json(geo_path)
features = geo.get("features") or []
if len(features) != EXPECTED_BEFORE:
    raise SystemExit("FAIL_CLOSED feature_count expected=%d actual=%d" % (EXPECTED_BEFORE, len(features)))

checkpoint = read_json(checkpoint_path)
if checkpoint.get("slot_id") != SLOT:
    raise SystemExit("FAIL_CLOSED wrong slot")
if int(checkpoint.get("current_feature_count", -1)) != EXPECTED_BEFORE:
    raise SystemExit("FAIL_CLOSED checkpoint current_feature_count changed")
if int(checkpoint.get("next_batch_index", -1)) != BATCH:
    raise SystemExit("FAIL_CLOSED checkpoint next_batch_index changed")
if bool(checkpoint.get("final_ready")):
    raise SystemExit("FAIL_CLOSED final_ready unexpectedly true")

task = read_json(task_path)
continuation_key = task.get("continuation_key")
if not continuation_key:
    raise SystemExit("FAIL_CLOSED missing continuation_key")
if task.get("owner") not in (None, ""):
    raise SystemExit("FAIL_CLOSED live owner exists: %r" % (task.get("owner"),))
if task.get("blocker") not in (None, ""):
    raise SystemExit("FAIL_CLOSED blocker exists: %r" % (task.get("blocker"),))

manifest = read_json(manifest_path)
sources = manifest.get("sources")
if not isinstance(sources, list):
    raise SystemExit("FAIL_CLOSED manifest sources is not list")
for s in sources:
    text = " ".join(str(s.get(k, "")) for k in ("name", "grid_id", "url")).lower()
    if CITY.lower() in text or GRID.lower() in text:
        raise SystemExit("FAIL_CLOSED city/grid already present in manifest")
if str(manifest.get("last_batch_city", "")).lower() == CITY.lower():
    raise SystemExit("FAIL_CLOSED city already last_batch_city")

processed = set()
for ft in features:
    p = ft.get("properties") or {}
    for v in (ft.get("id"), p.get("parcel_id"), p.get("osm_id")):
        if v is not None and str(v):
            processed.add(str(v))
processed_before = len(processed)

xs = [-1.5650, -1.5350, -1.5050, -1.4750]
ys = [54.1100, 54.1320, 54.1540, 54.1760]
urls = []
for yi in range(len(ys) - 1):
    for xi in range(len(xs) - 1):
        urls.append(
            "%s?bbox=%.4f,%.4f,%.4f,%.4f"
            % (BASE_URL, xs[xi], ys[yi], xs[xi + 1], ys[yi + 1])
        )
query_sha = hashlib.sha256("\n".join(urls).encode("utf-8")).hexdigest()

raw_parts = []
failed = []
nodes = {}
ways = {}
for url in urls:
    data = None
    error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TerraYield-AAYS-building_type_9/1.0 (+evidence batch 46)"},
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            break
        except Exception as exc:
            error = repr(exc)
            time.sleep(2 + attempt * 2)
    if data is None:
        failed.append({"url": url, "error": error})
        continue
    raw_parts.append(data)
    root = ET.fromstring(data)
    for n in root.findall("node"):
        try:
            nodes[n.attrib["id"]] = (float(n.attrib["lat"]), float(n.attrib["lon"]))
        except Exception:
            pass
    for w in root.findall("way"):
        wid = w.attrib.get("id")
        if not wid:
            continue
        tags = {
            t.attrib.get("k"): t.attrib.get("v")
            for t in w.findall("tag")
            if t.attrib.get("k")
        }
        refs = [
            nd.attrib.get("ref")
            for nd in w.findall("nd")
            if nd.attrib.get("ref")
        ]
        old = ways.get(wid)
        if old is None or len(tags) > len(old["tags"]):
            ways[wid] = {"tags": tags, "refs": refs}
    time.sleep(0.7)

if not raw_parts:
    raise SystemExit("BLOCKED_NO_NEW_SOURCE_OR_BATCH all OSM API tiles failed")
source_sha = hashlib.sha256(b"".join(raw_parts)).hexdigest()

building_map = {
    "detached": ("residential_detached", "R_DET", "residential"),
    "semidetached_house": ("residential_semi_detached", "R_SEMI", "residential"),
    "semi": ("residential_semi_detached", "R_SEMI", "residential"),
    "terrace": ("residential_other", "R_TERR", "residential"),
    "terraced_house": ("residential_other", "R_TERR", "residential"),
    "apartments": ("residential_apartments", "R_FLAT", "residential"),
    "flats": ("residential_apartments", "R_FLAT", "residential"),
    "house": ("residential_house", "R_HOUSE", "residential"),
    "residential": ("residential_other", "R_OTHER", "residential"),
    "bungalow": ("residential_detached", "R_DET", "residential"),
    "dormitory": ("residential_other", "R_OTHER", "residential"),
    "industrial": ("industrial", "I_FACTORY", "industrial"),
    "warehouse": ("warehouse", "I_WAREHOUSE", "industrial"),
    "retail": ("commercial_retail", "C_RETAIL", "commercial"),
    "commercial": ("commercial_other", "C_OTHER", "commercial"),
    "office": ("office", "C_OFFICE", "commercial"),
    "school": ("education", "P_SCHOOL", "institutional"),
    "college": ("education", "P_SCHOOL", "institutional"),
    "university": ("education", "P_SCHOOL", "institutional"),
    "hospital": ("hospital_or_healthcare", "P_HEALTHCARE", "institutional"),
    "church": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "chapel": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "mosque": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "synagogue": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "temple": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "hotel": ("hotel_or_hospitality", "C_HOSPITALITY", "commercial"),
    "civic": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "public": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "government": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "train_station": ("public_infrastructure", "P_TRANSPORT", "institutional"),
    "fire_station": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "garage": ("industrial", "I_WORKSHOP", "industrial"),
    "garages": ("industrial", "I_WORKSHOP", "industrial"),
}
amenity_map = {
    "school": ("education", "P_SCHOOL", "institutional"),
    "college": ("education", "P_SCHOOL", "institutional"),
    "university": ("education", "P_SCHOOL", "institutional"),
    "kindergarten": ("education", "P_SCHOOL", "institutional"),
    "hospital": ("hospital_or_healthcare", "P_HEALTHCARE", "institutional"),
    "clinic": ("hospital_or_healthcare", "P_HEALTHCARE", "institutional"),
    "doctors": ("hospital_or_healthcare", "P_HEALTHCARE", "institutional"),
    "pharmacy": ("hospital_or_healthcare", "P_HEALTHCARE", "institutional"),
    "place_of_worship": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "community_centre": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "police": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "post_office": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "fire_station": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "townhall": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "library": ("public_infrastructure", "P_GOVERNMENT", "institutional"),
    "bank": ("commercial_retail", "C_RETAIL", "commercial"),
    "restaurant": ("commercial_retail", "C_RETAIL", "commercial"),
    "cafe": ("commercial_retail", "C_RETAIL", "commercial"),
    "pub": ("commercial_retail", "C_RETAIL", "commercial"),
    "fast_food": ("commercial_retail", "C_RETAIL", "commercial"),
}

def classify(tags):
    amen = tags.get("amenity")
    if amen in amenity_map:
        primary, code, category = amenity_map[amen]
        return primary, code, category, "osm_building_plus_amenity_tag"
    tourism = tags.get("tourism")
    if tourism in {"hotel", "hostel", "guest_house"}:
        return "hotel_or_hospitality", "C_HOSPITALITY", "commercial", "osm_building_plus_tourism_tag"
    office = tags.get("office")
    if office not in (None, "", "no"):
        return "office", "C_OFFICE", "commercial", "osm_building_plus_office_tag"
    shop = tags.get("shop")
    if shop not in (None, "", "no"):
        return "commercial_retail", "C_RETAIL", "commercial", "osm_building_plus_shop_tag"
    building = tags.get("building")
    if building in building_map:
        primary, code, category = building_map[building]
        return primary, code, category, "osm_explicit_building_tag"
    return None

candidates = []
for wid, obj in ways.items():
    tags = obj["tags"]
    if not tags.get("building"):
        continue
    classification = classify(tags)
    if classification is None:
        continue
    fid = "ENG_OSM_way_" + wid
    oid = "way/" + wid
    if fid in processed or oid in processed or wid in processed:
        continue
    pts = [nodes[r] for r in obj["refs"] if r in nodes]
    if not pts:
        continue
    lat = sum(p[0] for p in pts) / len(pts)
    lon = sum(p[1] for p in pts) / len(pts)
    candidates.append((int(wid), wid, tags, lat, lon, classification))

candidates.sort(key=lambda row: row[0])
if len(candidates) < 50:
    raise SystemExit(
        "BLOCKED_NO_NEW_SOURCE_OR_BATCH only %d new semantic OSM building ways found"
        % len(candidates)
    )
chosen = candidates[:50]

now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
region = checkpoint.get("region") or "North East & Yorkshire"
new_features = []
records = []
keep_keys = [
    "building", "amenity", "shop", "office", "tourism", "name",
    "addr:postcode", "addr:street", "addr:housenumber", "addr:city"
]
for _, wid, tags, lat, lon, classification in chosen:
    primary, code, category, method = classification
    fid = "ENG_OSM_way_" + wid
    oid = "way/" + wid
    excerpt = {k: tags[k] for k in keep_keys if tags.get(k)}
    excerpt_text = " | ".join(
        ["OSM way/" + wid] + ["%s=%s" % (k, v) for k, v in excerpt.items()]
    )
    src = {
        "source_name": "OpenStreetMap API 0.6",
        "url_or_local_path": "https://www.openstreetmap.org/way/" + wid,
        "accessed_at": now,
        "sha256": source_sha,
        "licence": "ODbL 1.0",
        "granularity": "building_way_center",
        "fields_used": [
            k for k in ("building", "amenity", "shop", "office", "tourism")
            if tags.get(k)
        ],
        "supports_field": "building_type_primary",
        "match_method": method,
        "match_score": 0.85,
        "evidence_excerpt": excerpt,
    }
    props = {
        "parcel_id": fid,
        "osm_id": oid,
        "slot_id": SLOT,
        "region": region,
        "local_authority": LOCAL_AUTHORITY,
        "area": CITY,
        "postcode": tags.get("addr:postcode", ""),
        "building_type_primary": primary,
        "building_type_code": code,
        "building_category": category,
        "evidence_level": "B",
        "confidence_score": 0.85,
        "confidence_level_1_to_4": 3,
        "source_count": 1,
        "match_method": method,
        "source": "OpenStreetMap API 0.6",
        "source_url": "https://www.openstreetmap.org/way/" + wid,
        "source_hash": source_sha,
        "query_sha256": query_sha,
        "evidence_excerpt": excerpt_text,
        "osm_tags_summary": excerpt,
        "fake_data": False,
        "final_ready": False,
        "needs_manual_review": False,
        "updated_at": now,
        "sources": [src],
        "source_evidence_excerpt": excerpt,
        "building_type_secondary": "",
        "geometry_match_method": "osm_way_centroid",
        "address_match_method": "osm_address_tags" if tags.get("addr:postcode") else "none",
        "limitations": "OSM explicit/tag-based classification; independent EPC/VOA/HMLR corroboration still pending.",
    }
    new_features.append({
        "type": "Feature",
        "id": fid,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    })
    records.append({
        "id": fid,
        "parcel_id": fid,
        "osm_id": oid,
        "building_type_primary": primary,
        "source": "OpenStreetMap API 0.6",
        "source_url": "https://www.openstreetmap.org/way/" + wid,
        "source_hash": source_sha,
        "query_sha256": query_sha,
        "sources": [src],
        "evidence_excerpt": excerpt_text,
        "evidence_level": "B",
        "confidence_level_1_to_4": 3,
        "match_method": method,
    })

geo["features"].extend(new_features)
if len(geo["features"]) != TARGET_AFTER:
    raise SystemExit("FAIL_CLOSED feature_count_after invariant failed")
if TARGET_AFTER <= EXPECTED_BEFORE:
    raise SystemExit("FAIL_CLOSED no progress")

seen_fid = set()
seen_parcel = set()
seen_osm = set()
for ft in geo["features"]:
    p = ft.get("properties") or {}
    triples = [
        ("feature.id", str(ft.get("id") or ""), seen_fid),
        ("parcel_id", str(p.get("parcel_id") or ""), seen_parcel),
        ("osm_id", str(p.get("osm_id") or ""), seen_osm),
    ]
    for label, value, seen in triples:
        if not value:
            continue
        if value in seen:
            raise SystemExit("FAIL_CLOSED duplicate %s %s" % (label, value))
        seen.add(value)

if any((ft.get("properties") or {}).get("fake_data") is not False for ft in new_features):
    raise SystemExit("FAIL_CLOSED fake_data invariant failed")
if any((ft.get("properties") or {}).get("final_ready") is not False for ft in new_features):
    raise SystemExit("FAIL_CLOSED final_ready invariant failed")

geo_path.write_text(json.dumps(geo, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
geo_sha = hashlib.sha256(geo_path.read_bytes()).hexdigest()

evidence_dist = Counter()
type_dist = Counter()
conf_dist = Counter()
for ft in geo["features"]:
    p = ft.get("properties") or {}
    evidence_dist[str(p.get("evidence_level", "U"))] += 1
    type_dist[str(p.get("building_type_primary", "unknown"))] += 1
    conf_dist[str(p.get("confidence_level_1_to_4", 1))] += 1
unknown = type_dist.get("unknown", 0)
classified = TARGET_AFTER - unknown

sources.append({
    "name": "OpenStreetMap API 0.6 - Ripon batch 46",
    "url": BASE_URL,
    "license": "ODbL 1.0",
    "features_used": 50,
    "accessed_at": now,
    "source_sha256": source_sha,
    "source_hash_method": "sha256_concatenated_successful_osm_xml_tiles",
    "query_sha256": query_sha,
    "query_urls": urls,
    "failed_tile_count": len(failed),
    "grid_id": GRID,
    "note": "50 new evidence-backed semantic building records from runtime-only OSM XML tiles; no raw source committed.",
})
manifest.update({
    "slot_id": SLOT,
    "generated_at": now,
    "total_features": TARGET_AFTER,
    "classified": classified,
    "unknown": unknown,
    "evidence_distribution": dict(sorted(evidence_dist.items())),
    "type_distribution": dict(sorted(type_dist.items())),
    "confidence_level_distribution": dict(sorted(conf_dist.items())),
    "sources": sources,
    "fake_data": False,
    "final_ready": False,
    "note": "Existing %d-feature shard preserved; appended 50 Ripon OSM API records outside feature.id/parcel_id/osm_id already_processed_ids." % EXPECTED_BEFORE,
    "feature_count": TARGET_AFTER,
    "geojson_sha256": geo_sha,
    "geojson_path": str(geo_path),
    "manifest_updated_at": now,
    "feature_count_before": EXPECTED_BEFORE,
    "feature_count_after": TARGET_AFTER,
    "added_feature_count": 50,
    "last_batch_city": CITY,
    "last_batch_source": "OpenStreetMap API 0.6 map endpoint",
    "last_batch_source_sha256": source_sha,
    "last_batch_query_sha256": query_sha,
    "last_batch_grid": GRID,
})
write_json(manifest_path, manifest)

runner = {
    "slot_id": SLOT,
    "continuation_key": continuation_key,
    "batch_index": BATCH,
    "city": CITY,
    "grid_id": GRID,
    "generated_at": now,
    "feature_count_before": EXPECTED_BEFORE,
    "feature_count_after": TARGET_AFTER,
    "added_feature_count": 50,
    "progress": True,
    "already_processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id"],
    "already_processed_id_count_before": processed_before,
    "source": "OpenStreetMap API 0.6 map endpoint",
    "source_url": BASE_URL,
    "source_urls": urls,
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "failed_tile_count": len(failed),
    "evidence_level_new_features": {"B": 50},
    "confidence_level_new_features": {"3": 50},
    "new_feature_ids": [ft["id"] for ft in new_features],
    "records": records,
    "fake_data": False,
    "final_ready": False,
}
write_json(runner_path, runner)

status = read_json(status_path)
status.update({
    "state": "IN_PROGRESS",
    "updated_at": now,
    "final_ready": False,
    "classified_count": classified,
    "unknown_count": unknown,
    "total_elements": TARGET_AFTER,
    "confidence_distribution": dict(sorted(conf_dist.items())),
    "evidence_distribution": dict(sorted(evidence_dist.items())),
    "output_sha256": geo_sha,
    "note": "Batch 46 appended 50 new Ripon OSM API evidence-backed building features; no fake rows.",
    "fake_data": False,
    "feature_count_before": EXPECTED_BEFORE,
    "feature_count_after": TARGET_AFTER,
    "current_feature_count": TARGET_AFTER,
    "next_batch_index": BATCH + 1,
    "next_target_feature_count": NEXT_TARGET,
    "last_batch_city": CITY,
    "last_batch_grid": GRID,
    "last_batch_source_sha256": source_sha,
    "last_batch_query_sha256": query_sha,
    "owner_claim_created": False,
    "progress": True,
})
write_json(status_path, status)

checkpoint.update({
    "hydration_state": "REMOTE_HEAD_HYDRATED_FIRST_UNVERIFIED_PRESERVED",
    "first_unverified_step": "AŞAMA_1_OSM_GENISLETME_APPEND_NEW_BATCH_THEN_OPTIONAL_EPC_VOA_HMLR_UPGRADE",
    "first_unverified_step_status": "BATCH_046_APPENDED_50_RIPON_OSM_FEATURES_CONTINUATION_REQUIRED",
    "updated_at": now,
    "final_ready": False,
    "state": "IN_PROGRESS",
    "feature_count_before": EXPECTED_BEFORE,
    "feature_count_after": TARGET_AFTER,
    "current_feature_count": TARGET_AFTER,
    "next_batch_index": BATCH + 1,
    "next_target_feature_count": NEXT_TARGET,
    "last_processed_ids_sample": [ft["id"] for ft in new_features[-20:]],
    "next_required_action": "APPEND_ONLY_NEW_BATCH_DO_NOT_REPROCESS_EXISTING_FEATURES; OPTIONAL EPC/VOA/HMLR CORROBORATION",
    "fake_data": False,
    "processed_id_basis": ["feature.id", "properties.parcel_id", "properties.osm_id"],
    "last_batch": {
        "batch_index": BATCH,
        "city": CITY,
        "grid_id": GRID,
        "source": "OpenStreetMap API 0.6 map endpoint",
        "source_url": BASE_URL,
        "source_sha256": source_sha,
        "query_sha256": query_sha,
        "evidence_level": "B",
        "confidence_level_1_to_4": 3,
        "added_feature_count": 50,
        "new_feature_ids": [ft["id"] for ft in new_features],
    },
    "next_city_index": BATCH + 1,
})
summary = checkpoint.get("summary")
if isinstance(summary, dict):
    summary["new_features_appended"] = int(summary.get("new_features_appended", 0)) + 50
write_json(checkpoint_path, checkpoint)

task.update({
    "state": "READY",
    "status": "ready",
    "panel_status": "HAZIR",
    "updated_at": now,
    "first_unverified_step": "APPEND_NEW_BATCH_047_AFTER_FEATURE_2300",
    "continuation_key": continuation_key,
    "owner": None,
    "blocker": None,
    "claimable": True,
    "ready_for_claim": True,
    "fake_data": False,
    "final_ready": False,
    "progress": {
        "completed_count": TARGET_AFTER,
        "target_count": NEXT_TARGET,
        "previous_percent": round(EXPECTED_BEFORE / TARGET_AFTER * 100, 4),
        "current_percent": round(TARGET_AFTER / NEXT_TARGET * 100, 4),
        "percent_increase": round(
            TARGET_AFTER / NEXT_TARGET * 100 - EXPECTED_BEFORE / TARGET_AFTER * 100, 4
        ),
    },
})
write_json(task_path, task)

head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
print(json.dumps({
    "slot_id": SLOT,
    "batch_index": BATCH,
    "city": CITY,
    "grid_id": GRID,
    "feature_count_before": EXPECTED_BEFORE,
    "feature_count_after": TARGET_AFTER,
    "added_feature_count": 50,
    "already_processed_id_count_before": processed_before,
    "candidate_count": len(candidates),
    "new_feature_ids": [ft["id"] for ft in new_features],
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "failed_tile_count": len(failed),
    "geojson_sha256": geo_sha,
    "fake_data": False,
    "final_ready": False,
    "continuation_key": continuation_key,
    "checkout_head": head,
}, ensure_ascii=False))
