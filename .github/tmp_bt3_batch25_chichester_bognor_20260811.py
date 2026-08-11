import collections
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import time
import urllib.parse
import urllib.request

SLOT = "building_type_3"
TASK = "building-type-3-england-classification-v1-20260808"
CONT = "03d44e69b0c48954f68ecf6b86773a0e24affd56956a1cdfee6ccd900658161e"
REGION = "South East"
CITY = "Chichester_Bognor"
BATCH_INDEX = 25
EXPECTED_BEFORE = 5200
ADD_COUNT = 300
TARGET_AFTER = 5500
NEXT_BATCH = 26
NEXT_TARGET = 5800
BBOX = (50.75, -0.90, 50.90, -0.65)  # south, west, north, east
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

GEO = pathlib.Path("england_map_web/data/building_type/shards/building_type_3_latest.geojson")
MAN = pathlib.Path("england_map_web/data/building_type/shards/building_type_3_manifest_latest.json")
STA = pathlib.Path("docs/chatgpt_status/_shared/slots_21/building_type_3/status_latest.json")
CP = pathlib.Path("docs/chatgpt_status/_shared/slots_21/building_type_3/checkpoint_latest.json")
CT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/building_type_3/current_task_latest.json")
RUN = pathlib.Path("docs/chatgpt_status/building_type/slots/building_type_3/runner_outputs/building_type_3_classification_latest.json")

NOW = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def dump(path, obj, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    else:
        text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False)
    path.write_text(text + ("" if compact else "\n"), encoding="utf-8")


def dist(features, field):
    c = collections.Counter()
    for f in features:
        p = f.get("properties") or {}
        v = p.get(field)
        if v is not None:
            c[str(v)] += 1
    return dict(c)


def classified_counts(features):
    classified = 0
    unknown = 0
    for f in features:
        p = f.get("properties") or {}
        bt = str(p.get("building_type_primary") or "unknown")
        if bt == "unknown":
            unknown += 1
        else:
            classified += 1
    return classified, unknown


task = load(CT)
status = load(STA)
checkpoint = load(CP)
geo = load(GEO)
manifest = load(MAN)

# Fail closed against stale continuation or accidental second task/owner.
if task.get("task_id") != TASK or status.get("task_id") != TASK:
    raise SystemExit("task mismatch; refusing second task")
if task.get("owner") not in (None, "") or status.get("owner") not in (None, ""):
    raise SystemExit("owner is non-null; refusing second owner")
for obj, name in ((task, "task"), (status, "status"), (checkpoint, "checkpoint")):
    if obj.get("continuation_key") != CONT:
        raise SystemExit(f"{name} continuation_key moved; refusing stale continuation")
if checkpoint.get("next_batch_index") != BATCH_INDEX:
    raise SystemExit(f"next_batch_index moved: {checkpoint.get('next_batch_index')} != {BATCH_INDEX}")
if checkpoint.get("current_feature_count") != EXPECTED_BEFORE:
    raise SystemExit(f"checkpoint count moved: {checkpoint.get('current_feature_count')} != {EXPECTED_BEFORE}")
if status.get("total_elements") != EXPECTED_BEFORE:
    raise SystemExit(f"status count moved: {status.get('total_elements')} != {EXPECTED_BEFORE}")
if task.get("progress", {}).get("completed_count") != EXPECTED_BEFORE:
    raise SystemExit("task completed_count moved")

features = geo.get("features")
if not isinstance(features, list):
    raise SystemExit("invalid GeoJSON FeatureCollection")
before = len(features)
if before != EXPECTED_BEFORE:
    raise SystemExit(f"shard count moved: {before} != {EXPECTED_BEFORE}")

# Treat every existing feature.id, parcel_id and osm_id as already processed.
already = set()
for feat in features:
    fid = feat.get("id")
    if fid not in (None, ""):
        already.add(str(fid))
    props = feat.get("properties") or {}
    for key in ("parcel_id", "osm_id"):
        val = props.get(key)
        if val not in (None, ""):
            already.add(str(val))

attempted = checkpoint.get("attempted_cities") or []
if CITY in attempted or checkpoint.get("attempted_new_city_batch") == CITY or checkpoint.get("last_batch_name") == CITY:
    raise SystemExit(f"{CITY} already attempted; choose another batch")

south, west, north, east = BBOX
query = f'''[out:json][timeout:100];
(
  nwr["shop"]({south},{west},{north},{east});
  nwr["office"]({south},{west},{north},{east});
  nwr["tourism"~"hotel|hostel|guest_house|motel"]({south},{west},{north},{east});
  nwr["healthcare"]({south},{west},{north},{east});
  nwr["amenity"~"school|college|university|kindergarten|hospital|clinic|doctors|dentist|pharmacy|place_of_worship|townhall|police|fire_station|library|community_centre|courthouse|restaurant|cafe|pub|bar|fast_food|fuel"]({south},{west},{north},{east});
  nwr["building"~"retail|commercial|office|hotel|industrial|warehouse|school|college|university|church|chapel|hospital|civic|public|train_station|house|detached|semidetached_house|terrace|apartments|bungalow|residential|dormitory|barn|farm|farm_auxiliary|stable|garage|garages"]({south},{west},{north},{east});
);
out body center qt 9000;
'''
query_sha = hashlib.sha256(query.encode("utf-8")).hexdigest()
payload = urllib.parse.urlencode({"data": query}).encode("utf-8")
raw = None
endpoint_used = None
last_error = None
attempt_total = 0
for endpoint in ENDPOINTS:
    for attempt in range(1, 4):
        attempt_total += 1
        try:
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "User-Agent": "TerraYield-AAYS-building_type_3/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=125) as resp:
                raw = resp.read()
            endpoint_used = endpoint
            break
        except Exception as exc:
            last_error = repr(exc)
            if attempt < 3:
                time.sleep(4 * attempt)
    if raw is not None:
        break
if raw is None:
    raise SystemExit(f"Overpass unavailable after bounded retries: {last_error}")

source_sha = hashlib.sha256(raw).hexdigest()
data = json.loads(raw.decode("utf-8"))
elements = data.get("elements") or []
if not isinstance(elements, list):
    raise SystemExit("invalid Overpass response")

# Map only supported, directly evidenced OSM tags. No inference-only rows.
residential_building = {
    "house": ("residential_house", "R_HOUSE"),
    "detached": ("residential_house", "R_DET"),
    "semidetached_house": ("residential_house", "R_SEMI"),
    "terrace": ("residential_terrace", "R_TERRACE"),
    "apartments": ("flat_or_apartment", "R_APARTMENT"),
    "bungalow": ("residential_bungalow", "R_BUNGALOW"),
    "residential": ("residential", "R_RESIDENTIAL"),
    "dormitory": ("residential", "R_RESIDENTIAL"),
}
explicit_building = {
    "retail": ("commercial_retail", "C_RETAIL", "commercial"),
    "commercial": ("commercial_retail", "C_COMMERCIAL", "commercial"),
    "office": ("commercial_office", "C_OFFICE", "commercial"),
    "hotel": ("hotel_or_hospitality", "C_HOTEL", "commercial"),
    "industrial": ("industrial", "I_INDUSTRIAL", "industrial"),
    "warehouse": ("warehouse", "I_WAREHOUSE", "industrial"),
    "school": ("education", "P_SCHOOL", "institutional"),
    "college": ("education", "P_SCHOOL", "institutional"),
    "university": ("education", "P_SCHOOL", "institutional"),
    "church": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "chapel": ("religious_or_community", "P_RELIGIOUS", "institutional"),
    "hospital": ("hospital_or_healthcare", "P_HEALTH", "institutional"),
    "civic": ("public_infrastructure", "P_PUBLIC", "public"),
    "public": ("public_infrastructure", "P_PUBLIC", "public"),
    "train_station": ("public_infrastructure", "P_TRANSPORT", "public"),
    "barn": ("agricultural", "A_AGRICULTURAL", "agricultural"),
    "farm": ("agricultural", "A_AGRICULTURAL", "agricultural"),
    "farm_auxiliary": ("agricultural", "A_AGRICULTURAL", "agricultural"),
    "stable": ("agricultural", "A_AGRICULTURAL", "agricultural"),
    "garage": ("workshop_or_garage", "I_GARAGE", "industrial"),
    "garages": ("workshop_or_garage", "I_GARAGE", "industrial"),
}


def classify(tags):
    b = str(tags.get("building") or "").strip().lower()
    if b in residential_building:
        primary, code = residential_building[b]
        return primary, code, "residential", "B", 0.84, 3, f"building={b}", "osm_explicit_building_tag"
    if b in explicit_building:
        primary, code, category = explicit_building[b]
        return primary, code, category, "B", 0.84, 3, f"building={b}", "osm_explicit_building_tag"

    shop = str(tags.get("shop") or "").strip()
    office = str(tags.get("office") or "").strip()
    tourism = str(tags.get("tourism") or "").strip()
    healthcare = str(tags.get("healthcare") or "").strip()
    amenity = str(tags.get("amenity") or "").strip()

    if shop and shop != "no":
        return "commercial_retail", "C_RETAIL", "commercial", "C", 0.66, 2, f"shop={shop}", "osm_semantic_poi_tag"
    if office and office != "no":
        return "commercial_office", "C_OFFICE", "commercial", "C", 0.66, 2, f"office={office}", "osm_semantic_poi_tag"
    if tourism in {"hotel", "hostel", "guest_house", "motel"}:
        return "hotel_or_hospitality", "C_HOTEL", "commercial", "C", 0.66, 2, f"tourism={tourism}", "osm_semantic_poi_tag"
    if healthcare:
        return "hospital_or_healthcare", "P_HEALTH", "institutional", "C", 0.66, 2, f"healthcare={healthcare}", "osm_semantic_poi_tag"
    if amenity in {"school", "college", "university", "kindergarten"}:
        return "education", "P_SCHOOL", "institutional", "C", 0.66, 2, f"amenity={amenity}", "osm_semantic_poi_tag"
    if amenity in {"hospital", "clinic", "doctors", "dentist", "pharmacy"}:
        return "hospital_or_healthcare", "P_HEALTH", "institutional", "C", 0.66, 2, f"amenity={amenity}", "osm_semantic_poi_tag"
    if amenity == "place_of_worship":
        return "religious_or_community", "P_RELIGIOUS", "institutional", "C", 0.66, 2, "amenity=place_of_worship", "osm_semantic_poi_tag"
    if amenity in {"townhall", "police", "fire_station", "library", "community_centre", "courthouse"}:
        return "public_infrastructure", "P_PUBLIC", "public", "C", 0.66, 2, f"amenity={amenity}", "osm_semantic_poi_tag"
    if amenity in {"restaurant", "cafe", "pub", "bar", "fast_food", "fuel"}:
        return "commercial_retail", "C_RETAIL", "commercial", "C", 0.66, 2, f"amenity={amenity}", "osm_semantic_poi_tag"
    return None


def excerpt(tags, reason):
    keys = [
        "building", "amenity", "shop", "office", "tourism", "healthcare", "name",
        "addr:housenumber", "addr:street", "addr:city", "addr:postcode", "industrial", "landuse"
    ]
    parts = []
    for k in keys:
        v = tags.get(k)
        if v not in (None, ""):
            parts.append(f"{k}={v}")
    if reason and reason not in parts:
        parts.insert(0, reason)
    return " | ".join(parts)[:700]

candidates = []
seen_elements = set()
for elem in elements:
    typ = str(elem.get("type") or "")
    oid = elem.get("id")
    if typ not in {"node", "way", "relation"} or oid in (None, ""):
        continue
    element_key = (typ, str(oid))
    if element_key in seen_elements:
        continue
    seen_elements.add(element_key)

    fid = f"ENG_OSM_{typ}_{oid}"
    pid = fid
    osmid = f"{typ}/{oid}"
    alt = {fid, pid, osmid, str(oid), f"{typ}_{oid}"}
    if alt & already:
        continue

    if typ == "node":
        lon, lat = elem.get("lon"), elem.get("lat")
    else:
        center = elem.get("center") or {}
        lon, lat = center.get("lon"), center.get("lat")
    if lon is None or lat is None:
        continue

    tags = elem.get("tags") or {}
    cls = classify(tags)
    if cls is None:
        continue
    primary, code, category, evidence, score, conf, reason, match_method = cls
    candidates.append({
        "typ": typ,
        "oid": int(oid),
        "fid": fid,
        "pid": pid,
        "osmid": osmid,
        "lon": float(lon),
        "lat": float(lat),
        "tags": tags,
        "primary": primary,
        "code": code,
        "category": category,
        "evidence": evidence,
        "score": score,
        "conf": conf,
        "reason": reason,
        "match_method": match_method,
    })

# Prefer explicit building evidence, then stable canonical feature ID order.
candidates.sort(key=lambda c: (0 if c["evidence"] == "B" else 1, c["fid"]))
if len(candidates) < ADD_COUNT:
    raise SystemExit(f"BLOCKED_NO_NEW_SOURCE_OR_BATCH: only {len(candidates)} new classifiable candidates, need {ADD_COUNT}")
chosen = candidates[:ADD_COUNT]

new_features = []
records = []
for c in chosen:
    source_url = f"https://www.openstreetmap.org/{c['typ']}/{c['oid']}"
    ev_excerpt = excerpt(c["tags"], c["reason"])
    source_obj = {
        "source_name": "OpenStreetMap Overpass API",
        "url_or_local_path": source_url,
        "accessed_at": NOW,
        "sha256": source_sha,
        "licence": "ODbL 1.0",
        "granularity": "building_or_poi_point",
        "fields_used": [k for k in ("building", "amenity", "shop", "office", "tourism", "healthcare") if c["tags"].get(k) not in (None, "")],
        "supports_field": "building_type_primary",
        "match_method": c["match_method"],
        "match_score": c["score"],
    }
    props = {
        "parcel_id": c["pid"],
        "osm_id": c["osmid"],
        "slot_id": SLOT,
        "region": REGION,
        "city_batch": CITY,
        "postcode": c["tags"].get("addr:postcode"),
        "building_type_primary": c["primary"],
        "building_type_code": c["code"],
        "building_category": c["category"],
        "confidence_score": c["score"],
        "confidence_level_1_to_4": c["conf"],
        "evidence_level": c["evidence"],
        "source_count": 1,
        "source_url": source_url,
        "source_hash": source_sha,
        "match_method": c["match_method"],
        "evidence_excerpt": ev_excerpt,
        "sources": [source_obj],
        "geometry_match_method": "osm_node_or_element_center",
        "address_match_method": "osm_addr_tags_or_none",
        "limitations": "OSM-derived building/use classification; no EPC/VOA corroboration in this batch.",
        "needs_manual_review": c["conf"] <= 2,
        "fake_data": False,
        "final_ready": False,
        "updated_at": NOW,
    }
    geom = {"type": "Point", "coordinates": [c["lon"], c["lat"]]}
    new_features.append({"type": "Feature", "id": c["fid"], "geometry": geom, "properties": props})
    records.append({
        "feature_id": c["fid"],
        "parcel_id": c["pid"],
        "osm_id": c["osmid"],
        "building_type_primary": c["primary"],
        "building_type_code": c["code"],
        "building_category": c["category"],
        "confidence_score": c["score"],
        "confidence_level_1_to_4": c["conf"],
        "evidence_level": c["evidence"],
        "source_url": source_url,
        "source_hash": source_sha,
        "match_method": c["match_method"],
        "evidence_excerpt": ev_excerpt,
        "fake_data": False,
        "final_ready": False,
        "geometry": geom,
    })

# Hard uniqueness check against all three existing ID namespaces and within the new batch.
new_id_values = set()
for f in new_features:
    vals = {str(f.get("id")), str(f["properties"].get("parcel_id")), str(f["properties"].get("osm_id"))}
    if vals & already:
        raise SystemExit("dedupe invariant failed against already_processed_ids")
    if new_id_values & vals:
        raise SystemExit("dedupe invariant failed inside new batch")
    new_id_values |= vals

features.extend(new_features)
after = len(features)
if after <= before:
    raise SystemExit(f"NO_PROGRESS: feature_count_after={after} <= feature_count_before={before}")
if after - before < 50:
    raise SystemExit(f"NO_PROGRESS: only {after-before} new features, minimum is 50")
if after != TARGET_AFTER:
    raise SystemExit(f"unexpected final count {after} != {TARGET_AFTER}")

# Persist canonical shard first; raw Overpass payload is never written to disk/Git.
dump(GEO, geo, compact=True)
geo_sha = hashlib.sha256(GEO.read_bytes()).hexdigest()

classified, unknown = classified_counts(features)
evidence_dist = dist(features, "evidence_level")
confidence_dist = dist(features, "confidence_level_1_to_4")
type_dist = dist(features, "building_type_primary")
last_evidence = dict(collections.Counter(r["evidence_level"] for r in records))
last_conf = dict(collections.Counter(str(r["confidence_level_1_to_4"]) for r in records))
last_types = dict(collections.Counter(r["building_type_primary"] for r in records))
new_ids = [r["feature_id"] for r in records]

batch_meta = {
    "batch_index": BATCH_INDEX,
    "batch_name": CITY,
    "city": CITY,
    "bbox_south_west_north_east": f"{south},{west},{north},{east}",
    "grid_bbox": f"{south},{west},{north},{east}",
    "source": "OpenStreetMap via Overpass API",
    "endpoint": endpoint_used,
    "source_url": endpoint_used,
    "response_sha256": source_sha,
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "returned_elements": len(elements),
    "classified_unprocessed_candidates": len(candidates),
    "features_used": len(records),
    "added_feature_count": after - before,
    "accessed_at": NOW,
    "evidence_level_distribution": last_evidence,
    "confidence_level_distribution": last_conf,
    "building_type_distribution": last_types,
    "new_feature_ids": new_ids,
}

sources = manifest.get("sources")
if not isinstance(sources, list):
    sources = []
sources.append({
    "name": f"OpenStreetMap Overpass API - {CITY} batch {BATCH_INDEX}",
    "url": endpoint_used,
    "features_used": len(records),
    "accessed_at": NOW,
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "source_hash_method": "sha256_raw_overpass_json",
    "license": "ODbL 1.0",
    "evidence_level_distribution": last_evidence,
    "confidence_level_distribution": last_conf,
    "grid_bbox": batch_meta["grid_bbox"],
    "note": "Append-only batch after feature.id/parcel_id/osm_id exclusion; raw response runtime-only and not committed.",
})
manifest.update({
    "generated_at": NOW,
    "continuation_key": CONT,
    "total_features": after,
    "classified": classified,
    "unknown": unknown,
    "feature_count": after,
    "feature_count_before": before,
    "feature_count_after": after,
    "added_feature_count": after - before,
    "evidence_distribution": evidence_dist,
    "type_distribution": type_dist,
    "confidence_level_distribution": confidence_dist,
    "sources": sources,
    "latest_batch": batch_meta,
})
dump(MAN, manifest)

run = {
    "schema_version": 3,
    "slot_id": SLOT,
    "region": REGION,
    "continuation_key": CONT,
    "updated_at": NOW,
    "state": "IN_PROGRESS",
    "feature_count_before": before,
    "feature_count_after": after,
    "new_features_added": after - before,
    "batch_index": BATCH_INDEX,
    "batch_name": CITY,
    "source": "OpenStreetMap via Overpass API",
    "source_url": endpoint_used,
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "returned_elements": len(elements),
    "classified_unprocessed_candidates": len(candidates),
    "evidence_level_distribution": last_evidence,
    "confidence_level_distribution": last_conf,
    "building_type_distribution": last_types,
    "records": records,
    "fake_data": False,
    "final_ready": False,
}
dump(RUN, run)

status.update({
    "state": "IN_PROGRESS",
    "updated_at": NOW,
    "owner": None,
    "continuation_key": CONT,
    "final_ready": False,
    "classified_count": classified,
    "unknown_count": unknown,
    "total_elements": after,
    "feature_count_before": before,
    "feature_count_after": after,
    "new_features_added": after - before,
    "progress_counted": after > before,
    "next_batch_index": NEXT_BATCH,
    "next_target_feature_count": NEXT_TARGET,
    "confidence_distribution": confidence_dist,
    "evidence_distribution": evidence_dist,
    "output_sha256": geo_sha,
    "blocker": None,
    "blocker_reason": "",
    "note": f"Batch {BATCH_INDEX} appended {after-before} new {CITY} OSM evidence-backed elements outside all prior feature.id/parcel_id/osm_id values; same task/continuation retained.",
    "current_feature_count": after,
    "fake_data": False,
    "total_features": after,
    "classified": classified,
    "unknown": unknown,
    "confidence_level_distribution": confidence_dist,
    "progress_count_delta": after - before,
    "new_feature_count": after - before,
    "last_batch_city": CITY,
    "last_batch_added_feature_count": after - before,
    "last_batch_source": "OpenStreetMap via Overpass API",
    "last_batch_evidence_distribution": last_evidence,
    "last_batch_confidence_distribution": last_conf,
    "last_batch_index": BATCH_INDEX,
    "candidate_batch": None,
    "no_progress_reason": None,
    "progress_reason": f"{after-before} new {CITY} OSM records appended after feature.id/parcel_id/osm_id exclusion",
    "last_batch": batch_meta,
})
dump(STA, status)

attempted2 = list(attempted)
if CITY not in attempted2:
    attempted2.append(CITY)
checkpoint.update({
    "first_unverified_step_status": f"BATCH_{BATCH_INDEX}_APPENDED_{after-before}_{CITY.upper()}_OSM_CONTINUATION_REQUIRED",
    "continuation_key": CONT,
    "terminal_status": "IN_PROGRESS",
    "updated_at": NOW,
    "final_ready": False,
    "state": "IN_PROGRESS",
    "feature_count_before": before,
    "feature_count_after": after,
    "current_feature_count": after,
    "next_batch_index": NEXT_BATCH,
    "next_target_feature_count": NEXT_TARGET,
    "last_processed_ids_sample": new_ids[-20:],
    "attempted_new_city_batch": CITY,
    "attempted_cities": attempted2,
    "source_access_evidence": {
        "overpass_api": "Live OSM Overpass explicit/semantic building-use query succeeded",
        "endpoint": endpoint_used,
        "source_sha256": source_sha,
        "raw_source_stored_in_git": False,
    },
    "blocker": None,
    "blocker_reason": "",
    "next_required_action": f"APPEND_ONLY_BATCH_{NEXT_BATCH}_NEW_SOUTH_EAST_CITY_GRID_DO_NOT_REPROCESS_EXISTING_IDS",
    "fake_data": False,
    "last_batch_name": CITY,
    "last_batch_new_features": after - before,
    "last_batch_evidence": batch_meta,
})
summary = checkpoint.get("summary") or {}
summary.update({
    "current_feature_count": after,
    "new_features_added_this_attempt": after - before,
    "progress_counted": after > before,
})
checkpoint["summary"] = summary
dump(CP, checkpoint)

task["updated_at"] = NOW
task["owner"] = None
task["final_ready"] = False
task["fake_data"] = False
task["last_batch_index"] = BATCH_INDEX
task["last_batch_name"] = CITY
task["last_batch_added_feature_count"] = after - before
task["next_batch_index"] = NEXT_BATCH
task["next_target_feature_count"] = NEXT_TARGET
progress = task.get("progress") or {}
progress["completed_count"] = after
progress["target_count"] = NEXT_TARGET
task["progress"] = progress
dump(CT, task)

# Final local validation.
for path in (GEO, MAN, STA, CP, CT, RUN):
    load(path)
if any((f.get("properties") or {}).get("fake_data") is True for f in new_features):
    raise SystemExit("fake_data invariant failed")
if any((f.get("properties") or {}).get("final_ready") is True for f in new_features):
    raise SystemExit("final_ready invariant failed")
print(json.dumps({
    "slot": SLOT,
    "batch": BATCH_INDEX,
    "city": CITY,
    "feature_count_before": before,
    "feature_count_after": after,
    "new_features": after-before,
    "classified_after": classified,
    "unknown_after": unknown,
    "evidence": last_evidence,
    "confidence": last_conf,
    "source_sha256": source_sha,
    "query_sha256": query_sha,
    "endpoint": endpoint_used,
}, ensure_ascii=False))
