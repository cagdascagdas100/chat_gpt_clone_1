import collections
import datetime
import hashlib
import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

SLOT = "building_type_7"
TASK = "building-type-7-england-classification-v1-20260808"
BRANCH = "codex/aays-single-runner-v5-20260706"
BATCH = 183
TARGET = 50
EXPECTED_BEFORE = 9063
EXPECTED_NEXT_BATCH = 183
EXPECTED_AFTER = 9113
EXPECTED_AFTER_NEXT_BATCH = 184

AREAS = [
    ("Coventry_East_A", "uk-grid-coventry_east_a-001", [-1.450, 52.400, -1.425, 52.415]),
    ("Coventry_East_B", "uk-grid-coventry_east_b-001", [-1.425, 52.400, -1.400, 52.415]),
    ("Coventry_South_D", "uk-grid-coventry_south_d-001", [-1.450, 52.385, -1.425, 52.400]),
    ("Coventry_East_C", "uk-grid-coventry_east_c-001", [-1.400, 52.400, -1.375, 52.415]),
    ("Coventry_South_E", "uk-grid-coventry_south_e-001", [-1.425, 52.385, -1.400, 52.400]),
]

shard_path = f"england_map_web/data/building_type/shards/{SLOT}_latest.geojson"
manifest_path = f"england_map_web/data/building_type/shards/{SLOT}_manifest_latest.json"
class_path = f"docs/chatgpt_status/building_type/slots/{SLOT}/runner_outputs/{SLOT}_classification_latest.json"
status_path = f"docs/chatgpt_status/_shared/slots_21/{SLOT}/status_latest.json"
cp_path = f"docs/chatgpt_status/_shared/slots_21/{SLOT}/checkpoint_latest.json"
task_path = f"docs/chatgpt_status/_shared/slots_21/{SLOT}/current_task_latest.json"
write_paths = [shard_path, manifest_path, class_path, status_path, cp_path, task_path]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run(args, check=True, capture=False):
    return subprocess.run(
        args,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def git(*args, check=True, capture=False):
    return run(["git", *args], check=check, capture=capture)


def fetch_branch():
    git("fetch", "origin", BRANCH)


def remote_json(path):
    raw = subprocess.check_output(
        ["git", "show", f"origin/{BRANCH}:{path}"]
    )
    return json.loads(raw), raw


def assert_remote_slot(expected_current, expected_next, label):
    cp, _ = remote_json(cp_path)
    cur = cp.get("current_feature_count")
    nxt = int(cp.get("next_batch_index", -1))
    if cur != expected_current or nxt != expected_next:
        raise SystemExit(
            f"{label} current={cur} next={nxt} expected_current={expected_current} expected_next={expected_next}"
        )


def rebase_and_push(expected_current, expected_next, label):
    for attempt in range(1, 6):
        fetch_branch()
        assert_remote_slot(expected_current, expected_next, label)
        rr = git("rebase", f"origin/{BRANCH}", check=False)
        if rr.returncode != 0:
            git("rebase", "--abort", check=False)
            raise SystemExit(f"{label}_REBASE_FAILED attempt={attempt}")
        pr = git("push", "origin", f"HEAD:{BRANCH}", check=False)
        if pr.returncode == 0:
            return
        if attempt == 5:
            raise SystemExit(f"{label}_PUSH_RETRY_EXHAUSTED")
    raise SystemExit(f"{label}_UNREACHABLE")


def classify(tags):
    b = (tags.get("building") or "").lower()
    direct = {
        "house": ("residential_house", "R_HOUSE", "residential", 0.86, 3, "B", False),
        "detached": ("residential_house", "R_HOUSE", "residential", 0.86, 3, "B", False),
        "semidetached_house": ("residential_house", "R_HOUSE", "residential", 0.86, 3, "B", False),
        "bungalow": ("residential_house", "R_HOUSE", "residential", 0.86, 3, "B", False),
        "terrace": ("residential", "R_RES", "residential", 0.84, 3, "B", False),
        "residential": ("residential", "R_RES", "residential", 0.83, 3, "B", False),
        "apartments": ("residential", "R_APT", "residential", 0.86, 3, "B", False),
        "garage": ("ancillary_or_storage", "A_STORE", "ancillary", 0.80, 3, "B", False),
        "garages": ("ancillary_or_storage", "A_STORE", "ancillary", 0.80, 3, "B", False),
        "shed": ("ancillary_or_storage", "A_STORE", "ancillary", 0.79, 3, "B", False),
        "carport": ("ancillary_or_storage", "A_STORE", "ancillary", 0.79, 3, "B", False),
        "outbuilding": ("ancillary_or_storage", "A_STORE", "ancillary", 0.79, 3, "B", False),
        "barn": ("agricultural_outbuilding", "A_OUT", "agricultural", 0.83, 3, "B", False),
        "farm_auxiliary": ("agricultural_outbuilding", "A_OUT", "agricultural", 0.83, 3, "B", False),
        "cowshed": ("agricultural_outbuilding", "A_OUT", "agricultural", 0.83, 3, "B", False),
        "stable": ("agricultural_outbuilding", "A_OUT", "agricultural", 0.80, 3, "B", False),
        "greenhouse": ("agricultural_outbuilding", "A_OUT", "agricultural", 0.80, 3, "B", False),
        "retail": ("commercial_retail", "C_RETAIL", "commercial", 0.86, 3, "B", False),
        "supermarket": ("commercial_retail", "C_RETAIL", "commercial", 0.86, 3, "B", False),
        "commercial": ("commercial_other", "C_OTHER", "commercial", 0.82, 3, "B", False),
        "office": ("commercial_office", "C_OFFICE", "commercial", 0.86, 3, "B", False),
        "hotel": ("hotel_or_hospitality", "C_HOTEL", "commercial", 0.86, 3, "B", False),
        "industrial": ("industrial", "I_IND", "industrial", 0.86, 3, "B", False),
        "warehouse": ("warehouse", "I_WARE", "industrial", 0.86, 3, "B", False),
        "school": ("education", "P_EDU", "public", 0.86, 3, "B", False),
        "hospital": ("healthcare_care", "P_HEALTH", "public", 0.86, 3, "B", False),
        "church": ("religious", "P_REL", "public", 0.86, 3, "B", False),
        "chapel": ("religious", "P_REL", "public", 0.84, 3, "B", False),
        "civic": ("government_civic", "P_CIVIC", "public", 0.84, 3, "B", False),
        "public": ("public_infrastructure", "P_PUBLIC", "public", 0.80, 3, "B", False),
    }
    if b in direct:
        return direct[b]
    if tags.get("shop"):
        return ("commercial_retail", "C_RETAIL", "commercial", 0.68, 2, "C", True)
    if tags.get("office"):
        return ("commercial_office", "C_OFFICE", "commercial", 0.68, 2, "C", True)
    if tags.get("tourism") == "hotel":
        return ("hotel_or_hospitality", "C_HOTEL", "commercial", 0.68, 2, "C", True)
    amenity = (tags.get("amenity") or "").lower()
    if amenity in {"school", "college", "university", "kindergarten"}:
        return ("education", "P_EDU", "public", 0.68, 2, "C", True)
    if amenity in {"hospital", "clinic", "doctors", "dentist", "care_home"}:
        return ("healthcare_care", "P_HEALTH", "public", 0.68, 2, "C", True)
    if amenity == "place_of_worship":
        return ("religious", "P_REL", "public", 0.66, 2, "C", True)
    return ("unknown", "UNKNOWN", "unknown", 0.35, 1, "U", True)


shard = load(shard_path)
manifest = load(manifest_path)
cp = load(cp_path)
status = load(status_path)
task = load(task_path)
features = shard.get("features", [])
before = len(features)
if before != EXPECTED_BEFORE or int(cp.get("next_batch_index", -1)) != EXPECTED_NEXT_BATCH:
    raise SystemExit(f"STALE_STATE before={before} next_batch={cp.get('next_batch_index')}")
continuation = cp.get("continuation_key") or TASK
if continuation != TASK:
    raise SystemExit(f"CONTINUATION_MISMATCH {continuation}")
if task.get("owner") not in (None, ""):
    raise SystemExit(f"OWNER_PRESENT {task.get('owner')}")

used_areas = {(f.get("properties") or {}).get("area") for f in features}
processed = set()
for feature in features:
    p = feature.get("properties", {})
    for value in (
        feature.get("id"),
        p.get("feature_id"),
        p.get("parcel_id"),
        p.get("osm_id"),
        p.get("source_ref"),
    ):
        if value is not None and str(value):
            processed.add(str(value))

candidate_checks = []
chosen = None
for city, grid, bbox in AREAS:
    if city in used_areas:
        candidate_checks.append(
            {"city": city, "grid_id": grid, "bbox_wgs84": bbox, "result": "AREA_ALREADY_PROCESSED_SKIPPED"}
        )
        continue
    west, south, east, north = bbox
    mx = (west + east) / 2
    my = (south + north) / 2
    tiles = [
        (west, south, mx, my),
        (mx, south, east, my),
        (west, my, mx, north),
        (mx, my, east, north),
    ]
    elements = {}
    raw_parts = []
    source_urls = []
    errors = []
    for tw, ts, te, tn in tiles:
        url = f"https://api.openstreetmap.org/api/0.6/map?bbox={tw},{ts},{te},{tn}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/1.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read()
            raw_parts.append(raw)
            source_urls.append(url)
            root = ET.fromstring(raw)
            nodes = {
                n.attrib["id"]: (float(n.attrib["lon"]), float(n.attrib["lat"]))
                for n in root.findall("node")
            }
            for way in root.findall("way"):
                tags = {t.attrib.get("k"): t.attrib.get("v") for t in way.findall("tag")}
                if not tags.get("building"):
                    continue
                refs = [nd.attrib.get("ref") for nd in way.findall("nd")]
                pts = [nodes[r] for r in refs if r in nodes]
                if not pts:
                    continue
                lon = sum(p[0] for p in pts) / len(pts)
                lat = sum(p[1] for p in pts) / len(pts)
                eid = int(way.attrib["id"])
                elements[eid] = {"id": eid, "tags": tags, "center": {"lon": lon, "lat": lat}}
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
    if not raw_parts:
        candidate_checks.append(
            {"city": city, "grid_id": grid, "bbox_wgs84": bbox, "result": "OSM_API_UNAVAILABLE", "errors": errors}
        )
        continue
    source_sha = hashlib.sha256(b"\n--TILE--\n".join(raw_parts)).hexdigest()
    candidates = []
    prefix = city.upper()
    for eid, element in elements.items():
        osm = f"way/{eid}"
        fid = f"{prefix}_OSM_way_{eid}"
        if osm in processed or fid in processed or str(eid) in processed:
            continue
        cls = classify(element["tags"])
        candidates.append((cls[4], eid, element, osm, fid, element["center"]["lon"], element["center"]["lat"], cls))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    candidate_checks.append(
        {
            "city": city,
            "grid_id": grid,
            "bbox_wgs84": bbox,
            "candidate_count_after_dedupe": len(candidates),
            "result": "SELECTED" if len(candidates) >= TARGET else "OSM_LT_50_NO_WRITE",
            "errors": errors,
        }
    )
    if len(candidates) >= TARGET:
        chosen = (city, grid, bbox, candidates, source_urls, source_sha, errors)
        break

if chosen is None:
    raise SystemExit("NO_UNUSED_GRID_WITH_50_OSM_CANDIDATES " + json.dumps(candidate_checks))

city, grid, bbox, candidates, source_urls, source_sha, errors = chosen
now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
selected = candidates[:TARGET]
new_records = []
new_features = []
for _, _, element, osm, fid, lon, lat, cls in selected:
    tags = element["tags"]
    primary, code, category, score, level, evidence, review = cls
    fields_used = [
        key
        for key in (
            "building",
            "amenity",
            "shop",
            "office",
            "tourism",
            "landuse",
            "addr:housenumber",
            "addr:street",
            "addr:city",
            "addr:postcode",
        )
        if tags.get(key)
    ]
    summary = {key: tags[key] for key in fields_used}
    excerpt = f"OSM {osm} | " + "; ".join(f"{key}={tags[key]}" for key in fields_used)
    rec = {
        "feature_id": fid,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "parcel_id": fid,
        "parcel_id_semantics": "stable OSM element-derived slot identifier; not a cadastral parcel ID",
        "osm_id": osm,
        "source_ref": osm,
        "slot_id": SLOT,
        "region": "West Midlands",
        "area": city,
        "grid_id": grid,
        "local_authority": "Coventry",
        "postcode": tags.get("addr:postcode", ""),
        "building_type_primary": primary,
        "building_type_code": code,
        "building_category": category,
        "building_type_confidence": level,
        "confidence_score": score,
        "confidence_level_1_to_4": level,
        "evidence_level": evidence,
        "source_count": 1,
        "source": "OpenStreetMap API 0.6",
        "source_url": f"https://www.openstreetmap.org/way/{element['id']}",
        "source_path": " | ".join(source_urls),
        "accessed_at": now,
        "fields_used": fields_used,
        "source_hash": source_sha,
        "source_hash_method": "sha256_concatenated_osm_api_tiles",
        "match_method": f"building={tags.get('building')}",
        "classification_method": "deterministic_osm_building_use_tag_rules_v2",
        "evidence_excerpt": excerpt,
        "evidence_excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
        "osm_tags_summary": summary,
        "source_evidence_excerpt": summary,
        "sources": [
            {
                "source_name": "OpenStreetMap API 0.6",
                "url_or_path": " | ".join(source_urls),
                "object_url": f"https://www.openstreetmap.org/way/{element['id']}",
                "accessed_at": now,
                "sha256": source_sha,
                "sha256_scope": "concatenated_osm_api_tiles",
                "licence": "ODbL 1.0",
                "granularity": "building_element",
                "fields_used": fields_used,
                "supports_field": "building_type_primary",
                "match_method": f"building={tags.get('building')}",
                "match_score": score,
            }
        ],
        "geometry_match_method": "osm_way_node_mean_point",
        "address_match_method": "osm_tags_when_present",
        "limitations": "OSM building/use-tag evidence only; OSM element is a building proxy, not a cadastral parcel; no EPC/VOA corroboration needed because selected grid yielded 50 evidence-bearing OSM proxies.",
        "needs_manual_review": review,
        "fake_data": False,
        "final_ready": False,
        "updated_at": now,
    }
    new_records.append(rec)
    new_features.append(
        {
            "type": "Feature",
            "id": fid,
            "geometry": rec["geometry"],
            "properties": {key: value for key, value in rec.items() if key != "geometry"},
        }
    )

features.extend(new_features)
shard["features"] = features
after = len(features)
added = after - before
if added != TARGET or after <= before:
    raise SystemExit(f"PROGRESS_CONDITION_FAILED before={before} after={after} added={added}")

unknown_new = sum(1 for rec in new_records if rec["evidence_level"] == "U")
no_evidence = unknown_new
evidence_dist = collections.Counter()
type_dist = collections.Counter()
confidence_dist = collections.Counter()
classified = 0
unknown = 0
processed_after = set()
for feature in features:
    p = feature.get("properties", {})
    evidence_dist[str(p.get("evidence_level", "U"))] += 1
    type_dist[str(p.get("building_type_primary", "unknown"))] += 1
    confidence_dist[str(p.get("confidence_level_1_to_4", 1))] += 1
    unknown += int(p.get("building_type_primary") == "unknown")
    classified += int(p.get("building_type_primary") != "unknown")
    for value in (
        feature.get("id"),
        p.get("feature_id"),
        p.get("parcel_id"),
        p.get("osm_id"),
        p.get("source_ref"),
    ):
        if value is not None and str(value):
            processed_after.add(str(value))

manifest.update(
    {
        "generated_at": now,
        "total_features": after,
        "classified": classified,
        "unknown": unknown,
        "evidence_distribution": dict(evidence_dist),
        "type_distribution": dict(type_dist),
        "confidence_level_distribution": dict(confidence_dist),
        "final_ready": False,
        "fake_data": False,
    }
)
manifest.setdefault("sources", []).append(
    {
        "name": "OpenStreetMap API 0.6 - " + city,
        "url": " | ".join(source_urls),
        "license": "ODbL 1.0",
        "features_used": added,
        "accessed_at": now,
        "source_sha256": source_sha,
        "source_hash_method": "sha256_concatenated_osm_api_tiles",
        "note": "OSM building footprint/use tag; building proxy, not cadastral parcel. Raw tiles not stored in Git. READ_FALLBACK_USED because connector could not return full shard content.",
    }
)

report = {
    "slot_id": SLOT,
    "task_id": TASK,
    "continuation_key": continuation,
    "generated_at": now,
    "accessed_at": now,
    "batch_index": BATCH,
    "city": city,
    "local_authority": "Coventry",
    "region": "West Midlands",
    "grid_id": grid,
    "bbox_wgs84": bbox,
    "feature_count_before": before,
    "attempted_parcels": TARGET,
    "candidate_count_after_dedupe": len(candidates),
    "feature_count_after": after,
    "new_feature_count": added,
    "target_new_feature_count": TARGET,
    "no_evidence_this_batch": no_evidence,
    "read_fallback_used": True,
    "fallback_candidate_checks": candidate_checks,
    "source_name": "OpenStreetMap API 0.6",
    "source_url": " | ".join(source_urls),
    "source_path": " | ".join(source_urls),
    "source_sha256": source_sha,
    "source_hash_method": "sha256_concatenated_osm_api_tiles",
    "source_fetch_errors": errors,
    "raw_source_committed": False,
    "fake_data": False,
    "final_ready": False,
    "evidence_distribution_new": dict(collections.Counter(rec["evidence_level"] for rec in new_records)),
    "confidence_distribution_new": dict(collections.Counter(str(rec["confidence_level_1_to_4"]) for rec in new_records)),
    "type_distribution_new": dict(collections.Counter(rec["building_type_primary"] for rec in new_records)),
    "records": new_records,
}

batch_summary = {
    "batch_index": BATCH,
    "batch_name": city,
    "city": city,
    "grid_id": grid,
    "grid_bbox": ",".join(str(value) for value in bbox),
    "source": "OpenStreetMap API 0.6",
    "endpoint": " | ".join(source_urls),
    "source_url": " | ".join(source_urls),
    "source_sha256": source_sha,
    "features_used": added,
    "added_feature_count": added,
    "accessed_at": now,
    "evidence_level_distribution": report["evidence_distribution_new"],
    "confidence_level_distribution": report["confidence_distribution_new"],
    "building_type_distribution": report["type_distribution_new"],
    "new_feature_ids": [rec["feature_id"] for rec in new_records],
    "raw_source_stored_in_git": False,
    "read_fallback_used": True,
    "fallback_candidate_checks": candidate_checks,
}

keys_sorted = "\n".join(sorted(processed_after)).encode()
cp.update(
    {
        "slot_id": SLOT,
        "task_id": TASK,
        "continuation_key": continuation,
        "updated_at": now,
        "phase": "APPEND_NEW_BATCH_TO_LATEST_SHARD",
        "feature_count_before": before,
        "feature_count_after": after,
        "current_feature_count": after,
        "next_batch_index": BATCH + 1,
        "next_city_index": BATCH + 1,
        "next_target_feature_count": after + TARGET,
        "target_feature_count_after_next_batch": after + TARGET,
        "last_batch_index": BATCH,
        "last_batch_name": city,
        "last_city": city,
        "last_grid_id": grid,
        "last_bbox_wgs84": bbox,
        "last_new_feature_count": added,
        "last_batch_new_features": added,
        "last_batch": batch_summary,
        "last_batch_evidence": batch_summary,
        "first_unverified_step": f"APPEND_NEW_BATCH_{BATCH + 1}_AFTER_FEATURE_{after}",
        "next_required_action": f"CONTINUE_BATCH_{BATCH + 1}_FROM_{after}_USING_ALREADY_PROCESSED_IDS_DO_NOT_REPROCESS_EXISTING_FEATURES",
        "remote_readback_verified": False,
        "blocker": None,
        "blocker_reason": "",
        "no_progress_reason": None,
        "final_ready": False,
        "fake_data": False,
    }
)
cp["summary"] = {
    "osm_pilot_classified": classified,
    "new_slot": False,
    "pipeline_stage": 1,
    "new_features_appended": added,
    "current_feature_count": after,
    "note": f"PROGRESS: feature_count {before} -> {after}. Batch {BATCH} {city} persisted via READ_FALLBACK_USED; remote readback pending. final_ready remains false.",
    "new_features_added_this_attempt": added,
    "progress_counted": after > before,
    "unknown": unknown,
}
cp["remaining_items"] = {
    "osm_building_tag_scan_pending": True,
    "epc_residential_pending": True,
    "note": f"Next batch {BATCH + 1}: treat all {after} canonical feature.id/feature_id/parcel_id/osm_id/source_ref values as already_processed_ids and append 50 genuinely new West Midlands records; do not replay prior batches.",
}
cp["already_processed_ids"] = {
    "strategy": "derived_from_latest_shard_feature.id_plus_feature_id_plus_parcel_id_plus_osm_id_plus_source_ref",
    "unique_key_count": len(processed_after),
    "sha256_sorted_newline_keys": hashlib.sha256(keys_sorted).hexdigest(),
    "sample": sorted(processed_after)[-20:],
}

status.update(
    {
        "slot_id": SLOT,
        "task_id": TASK,
        "continuation_key": continuation,
        "updated_at": now,
        "owner": None,
        "classified_count": classified,
        "unknown_count": unknown,
        "total_elements": after,
        "total_features": after,
        "classified": classified,
        "unknown": unknown,
        "confidence_distribution": dict(confidence_dist),
        "confidence_level_distribution": dict(confidence_dist),
        "evidence_distribution": dict(evidence_dist),
        "feature_count_before": before,
        "feature_count_after": after,
        "current_feature_count": after,
        "feature_count": after,
        "last_batch_index": BATCH,
        "next_batch_index": BATCH + 1,
        "next_target_feature_count": after + TARGET,
        "last_batch_name": city,
        "last_batch_city": city,
        "last_batch_added_feature_count": added,
        "last_new_feature_count": added,
        "new_feature_count": added,
        "new_features_added": added,
        "no_evidence_this_batch": no_evidence,
        "last_batch_source": "OpenStreetMap API 0.6",
        "last_batch_evidence_distribution": report["evidence_distribution_new"],
        "last_batch_confidence_distribution": report["confidence_distribution_new"],
        "last_batch": batch_summary,
        "progress_count_delta": added,
        "progress_counted": after > before,
        "progress_reason": f"{added} new {city} OSM records appended after processed-ID exclusion via READ_FALLBACK_USED",
        "no_progress_reason": None,
        "blocker": None,
        "blocker_reason": "",
        "remote_readback_verified": False,
        "final_ready": False,
        "fake_data": False,
    }
)

task["task_id"] = TASK
task["slot_id"] = SLOT
task["continuation_key"] = continuation
task["owner"] = None
task["updated_at"] = now
task["first_unverified_step"] = f"APPEND_NEW_BATCH_{BATCH + 1}_AFTER_FEATURE_{after}"
task["blocker"] = None
task["final_ready"] = False
task["fake_data"] = False
task["progress"] = {
    "completed_count": after,
    "target_count": after + TARGET,
    "previous_percent": 100.0 * before / (after + TARGET),
    "current_percent": 100.0 * after / (after + TARGET),
    "percent_increase": 100.0 * (after - before) / (after + TARGET),
}

for path, obj in [
    (shard_path, shard),
    (manifest_path, manifest),
    (class_path, report),
    (cp_path, cp),
    (status_path, status),
    (task_path, task),
]:
    dump(path, obj)

print(
    "CLASSIFY_RESULT="
    + json.dumps(
        {
            "before": before,
            "attempted": TARGET,
            "after": after,
            "added": added,
            "city": city,
            "grid": grid,
            "candidates": len(candidates),
            "unknown_new": unknown_new,
            "no_evidence": no_evidence,
            "confidence_new": report["confidence_distribution_new"],
            "types_new": report["type_distribution_new"],
            "sha256": source_sha,
            "source_tiles": len(source_urls),
            "errors": errors,
            "candidate_checks": candidate_checks,
        }
    ),
    flush=True,
)

fetch_branch()
assert_remote_slot(EXPECTED_BEFORE, EXPECTED_NEXT_BATCH, "REMOTE_SLOT_ADVANCED_BEFORE_COMMIT")
git("config", "user.name", "TerraYield AAYS Bot")
git("config", "user.email", "aays-bot@users.noreply.github.com")
for path in write_paths:
    git("add", path)
if git("diff", "--cached", "--quiet", check=False).returncode != 0:
    git("commit", "-m", f"data(aays): {SLOT} batch {BATCH}")
rebase_and_push(EXPECTED_BEFORE, EXPECTED_NEXT_BATCH, "DATA_PUSH")
data_commit = git("rev-parse", "HEAD", capture=True).stdout.strip()

fetch_branch()
remote_report, remote_report_raw = remote_json(class_path)
remote_cp, _ = remote_json(cp_path)
remote_manifest, _ = remote_json(manifest_path)
if (
    remote_report.get("batch_index") != BATCH
    or remote_report.get("feature_count_after") != EXPECTED_AFTER
    or remote_report.get("new_feature_count") != TARGET
    or remote_manifest.get("total_features") != EXPECTED_AFTER
    or remote_cp.get("current_feature_count") != EXPECTED_AFTER
    or int(remote_cp.get("next_batch_index", -1)) != EXPECTED_AFTER_NEXT_BATCH
):
    raise SystemExit("REMOTE_READBACK_MISMATCH")

cp = load(cp_path)
status = load(status_path)
task = load(task_path)
verify_now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
output_sha = hashlib.sha256(remote_report_raw).hexdigest()
cp["remote_readback_verified"] = True
cp["remote_data_commit"] = data_commit
cp["remote_head"] = data_commit
cp["updated_at"] = verify_now
cp["summary"]["note"] = f"PROGRESS: feature_count {before} -> {after}. Batch {BATCH} {city} persisted via READ_FALLBACK_USED and remote readback verified; continue at batch {BATCH + 1}. final_ready remains false."
status["remote_readback_verified"] = True
status["remote_data_commit"] = data_commit
status["remote_head"] = data_commit
status["updated_at"] = verify_now
status["output_sha256"] = output_sha
status["note"] = f"Appended {added} unique {city} OSM building elements after processed-ID exclusion via READ_FALLBACK_USED; remote readback verified; no second task/owner created."
task["updated_at"] = verify_now
for path, obj in [(cp_path, cp), (status_path, status), (task_path, task)]:
    dump(path, obj)
for path in [cp_path, status_path, task_path]:
    git("add", path)
if git("diff", "--cached", "--quiet", check=False).returncode != 0:
    git("commit", "-m", f"chore(aays): verify {SLOT} batch {BATCH} state")
rebase_and_push(EXPECTED_AFTER, EXPECTED_AFTER_NEXT_BATCH, "VERIFY_PUSH")
verify_commit = git("rev-parse", "HEAD", capture=True).stdout.strip()

fetch_branch()
final_cp, _ = remote_json(cp_path)
final_status, _ = remote_json(status_path)
if (
    final_cp.get("current_feature_count") != EXPECTED_AFTER
    or int(final_cp.get("next_batch_index", -1)) != EXPECTED_AFTER_NEXT_BATCH
    or final_cp.get("remote_readback_verified") is not True
    or final_cp.get("remote_data_commit") != data_commit
    or final_status.get("remote_readback_verified") is not True
):
    raise SystemExit("FINAL_REMOTE_VERIFY_MISMATCH")

print(
    "FINAL_RESULT="
    + json.dumps(
        {
            "verified": True,
            "feature_count_before": before,
            "attempted": TARGET,
            "feature_count_after": after,
            "added": added,
            "city": city,
            "grid": grid,
            "no_evidence": no_evidence,
            "confidence_new": report["confidence_distribution_new"],
            "evidence_new": report["evidence_distribution_new"],
            "types_new": report["type_distribution_new"],
            "source_sha256": source_sha,
            "accessed_at": now,
            "data_commit": data_commit,
            "verify_commit": verify_commit,
            "next_batch": BATCH + 1,
            "next_target": after + TARGET,
            "output_sha256": output_sha,
            "candidate_checks": candidate_checks,
        }
    ),
    flush=True,
)
