#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path.cwd() / "canonical"
BRANCH = "codex/aays-single-runner-v5-20260706"
SLOT = "future_growth_9"
CONTINUATION = "future_growth_9_open_source_v2_20260813"
STATE_DIR = Path("docs/chatgpt_status/_shared/slots_21/future_growth_9")
CHECKPOINT = STATE_DIR / "checkpoint_latest.json"
STATUS = STATE_DIR / "status_latest.json"
CURRENT_TASK = STATE_DIR / "current_task_latest.json"
RECOVERY = STATE_DIR / "recovery_latest.json"
REPORTS = STATE_DIR / "reports"
MANIFEST = Path("state/slots/future_growth_9/evidence_manifest_latest.json")
BATCH_BASE = Path("AAYS/england_map_web/data/future_growth/shards/future_growth_9_batches")
LATEST = Path("AAYS/england_map_web/data/future_growth/shards/future_growth_9_latest.geojson")
API = "https://www.planning.data.gov.uk/entity.json"
EXPECTED_ANCHORS = {84: ("KY/162", 1713284), 90: ("BU/011", 1712077)}
QUERY_VARIANTS = [
    ("geometry_within_default", {"dataset": "brownfield-land", "geometry_entity": 626068, "geometry_relation": "within", "limit": 1}),
    ("geometry_within_current", {"dataset": "brownfield-land", "geometry_entity": 626068, "geometry_relation": "within", "period": "current", "limit": 1}),
    ("organisation_default", {"dataset": "brownfield-land", "organisation_entity": 58, "limit": 1}),
    ("organisation_current", {"dataset": "brownfield-land", "organisation_entity": 58, "period": "current", "limit": 1}),
]
ALLOWED_PREFIXES = (
    "AAYS/england_map_web/data/future_growth/shards/future_growth_9_batches/",
    "docs/chatgpt_status/_shared/slots_21/future_growth_9/",
    "state/slots/future_growth_9/",
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AAYS-future-growth-9-strict-bounded/1.0"})


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(*args, check=True, capture=False):
    p = subprocess.run(list(args), cwd=REPO, text=True, check=check,
                       stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.STDOUT if capture else None)
    return p.stdout if capture else ""


def load(path):
    with (REPO / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def dump(path, obj):
    p = REPO / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def api_entities(offset, params):
    q = dict(params)
    q["offset"] = int(offset)
    last = None
    for attempt in range(4):
        try:
            r = SESSION.get(API, params=q, timeout=60)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                return data, r.url
            for key in ("entities", "entity", "results"):
                v = data.get(key) if isinstance(data, dict) else None
                if isinstance(v, list):
                    return v, r.url
            return [], r.url
        except Exception as exc:
            last = exc
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise last


def ref_entity(e):
    ref = e.get("reference") or e.get("name")
    ent = e.get("entity")
    try:
        ent = int(ent) if ent is not None else None
    except Exception:
        pass
    return ref, ent


def choose_query_variant():
    diagnostics = []
    for name, params in QUERY_VARIANTS:
        ok = True
        got = {}
        for offset, expected in EXPECTED_ANCHORS.items():
            entities, url = api_entities(offset, params)
            pair = ref_entity(entities[0]) if entities else (None, None)
            got[offset] = {"got": pair, "expected": expected, "url": url}
            if pair != expected:
                ok = False
        diagnostics.append({"name": name, "ok": ok, "anchors": got})
        if ok:
            return name, params, diagnostics
    raise RuntimeError("SOURCE_SEQUENCE_UNRESOLVED: no official API query variant reproduces historical windows 84 and 90: " + json.dumps(diagnostics, ensure_ascii=False))


def parse_point(e):
    point = e.get("point") or ""
    m = re.match(r"^POINT\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)$", str(point).strip())
    if not m:
        return None
    lon, lat = float(m.group(1)), float(m.group(2))
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return [lon, lat]


def num(v):
    if v in (None, ""):
        return None
    try:
        x = float(v)
        return int(x) if x.is_integer() else x
    except Exception:
        return None


def canonical_hash(e):
    payload = json.dumps(e, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_feature(e, query_name):
    ref, ent = ref_entity(e)
    point = parse_point(e)
    if not ref or ent is None or point is None:
        return None, "MISSING_REFERENCE_ENTITY_OR_WGS84_POINT"
    status = e.get("planning-permission-status")
    direct = status == "permissioned"
    notes = e.get("notes") or ""
    props = {
        "slot_id": SLOT,
        "continuation_key": CONTINUATION,
        "source_family": "planning_data_brownfield_land_direct_identity",
        "source_name": "Planning Data Brownfield Land — City of Bradford Metropolitan District Council",
        "source_publisher": "City of Bradford Metropolitan District Council via Planning Data",
        "source_feature_id": ref,
        "planning_data_entity": ent,
        "source_url": f"https://www.planning.data.gov.uk/entity/{ent}",
        "source_dataset_url": "https://www.planning.data.gov.uk/dataset/brownfield-land",
        "source_entry_date": e.get("entry-date"),
        "source_start_date": e.get("start-date"),
        "source_sha256": canonical_hash(e),
        "source_sha256_scope": "canonical JSON of official API entity payload used in this bounded batch",
        "license": "Open Government Licence v3.0",
        "planning_status": status,
        "future_growth_evidence_type": "direct_project" if direct else "area_proxy",
        "direct_project_evidence": bool(direct),
        "evidence_summary": notes,
        "matching_method": "direct official brownfield-land reference identity plus published WGS84 point; no nearest matching, no cross-parcel identity inference",
        "source_query_variant": query_name,
        "accuracy_scale_1_4": 4 if direct else 3,
        "future_growth_value": None,
        "future_growth_probability": None,
        "unknown_reason": "Numeric value/probability withheld because no approved scoring rule exists.",
        "site_name": e.get("site-address"),
        "hectares": num(e.get("hectares")),
        "net_dwellings_range_from": num(e.get("minimum-net-dwellings")),
        "net_dwellings_range_to": num(e.get("maximum-net-dwellings")),
        "planning_permission_date": e.get("planning-permission-date"),
        "planning_permission_type": e.get("planning-permission-type"),
        "deliverable": e.get("deliverable"),
        "fake_data": False,
        "final_ready": False,
        "production_merge": False,
        "demo_only": True,
    }
    fid = "future_growth_9:planning_data_bradford:" + re.sub(r"[^a-z0-9]+", "-", ref.lower()).strip("-")
    return {"type": "Feature", "id": fid, "geometry": {"type": "Point", "coordinates": point}, "properties": props}, None


def existing_identity_sets():
    refs, entities = set(), set()
    paths = list((REPO / BATCH_BASE).glob("**/*.geojson"))
    if (REPO / LATEST).exists():
        paths.append(REPO / LATEST)
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            ref = props.get("source_feature_id")
            ent = props.get("planning_data_entity")
            if ref:
                refs.add(str(ref))
            if ent is not None:
                try:
                    entities.add(int(ent))
                except Exception:
                    entities.add(str(ent))
    return refs, entities


def verify_allowed_changes():
    out = run("git", "status", "--porcelain", capture=True)
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        p = line[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        paths.append(p)
        if not p.startswith(ALLOWED_PREFIXES):
            raise RuntimeError(f"WRITE_OWNERSHIP_VIOLATION: {p}")
    return paths


def push_commit(message):
    changed = verify_allowed_changes()
    if not changed:
        raise RuntimeError("NO_CHANGES_TO_COMMIT")
    run("git", "add", "--", *changed)
    run("git", "commit", "-m", message)
    for attempt in range(4):
        p = subprocess.run(["git", "push", "origin", f"HEAD:{BRANCH}"], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.returncode == 0:
            return run("git", "rev-parse", "HEAD", capture=True).strip()
        if attempt == 3:
            raise RuntimeError("PUSH_FAILED: " + p.stdout)
        run("git", "pull", "--rebase", "origin", BRANCH)


def remote_json(path):
    run("git", "fetch", "origin", BRANCH)
    text = run("git", "show", f"origin/{BRANCH}:{path.as_posix()}", capture=True)
    return json.loads(text)


def batch_readback(batch_path, expected_count):
    shard = remote_json(batch_path)
    cp = remote_json(CHECKPOINT)
    st = remote_json(STATUS)
    mf = remote_json(MANIFEST)
    vals = {
        "shard": shard.get("metadata", {}).get("feature_count_after"),
        "checkpoint": cp.get("feature_count_after"),
        "status": st.get("feature_count_after"),
        "manifest": mf.get("feature_count_after"),
        "dup": max(
            int(shard.get("metadata", {}).get("duplicate_count", 0)),
            int(cp.get("duplicate_count", 0)),
            int(st.get("duplicate_count", 0)),
            int(mf.get("duplicate_count", 0)),
        ),
    }
    if vals != {"shard": expected_count, "checkpoint": expected_count, "status": expected_count, "manifest": expected_count, "dup": 0}:
        raise RuntimeError("READBACK_MISMATCH: " + json.dumps(vals))
    return vals


def main():
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "pull", "--rebase", "origin", BRANCH)

    cp0 = load(CHECKPOINT)
    st0 = load(STATUS)
    mf0 = load(MANIFEST)
    if cp0.get("slot_id") != SLOT or cp0.get("continuation_key") != CONTINUATION:
        raise RuntimeError("SLOT_OR_CONTINUATION_MISMATCH")
    start_window = int(cp0.get("next_unused_window", {}).get("window_index", -1))
    before = int(cp0.get("feature_count_after", -1))
    if start_window < 91 or before < 91:
        raise RuntimeError(f"STALE_OR_INVALID_START checkpoint_window={start_window} before={before}")
    if not (st0.get("feature_count_after") == before == mf0.get("feature_count_after")):
        raise RuntimeError("PRE_RUN_STATE_READBACK_MISMATCH")
    if any(int(x.get("duplicate_count", 0)) != 0 for x in (cp0, st0, mf0)):
        raise RuntimeError("PRE_RUN_DUPLICATE_COUNT_NONZERO")
    if any(bool(x.get("nearest_match_used", False)) for x in (cp0, st0, mf0)):
        raise RuntimeError("PRE_RUN_NEAREST_MATCH_FLAG_TRUE")

    used_refs, used_entities = existing_identity_sets()
    if len(used_refs) != before:
        raise RuntimeError(f"IDENTITY_COUNT_MISMATCH repo_unique_refs={len(used_refs)} checkpoint={before}")

    query_name, query_params, sequence_diagnostics = choose_query_variant()
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"future_growth_9_bounded12_{run_stamp}"
    batch_root = BATCH_BASE / run_stamp
    windows = list(range(start_window, start_window + 12))
    added_refs, added_entities, zero_windows, skipped_duplicates, skipped_invalid = [], [], [], [], []
    readbacks = {}
    added_direct = 0
    added_area = 0
    current_count = before
    last_ref = cp0.get("current_source_feature_id")
    last_ent = cp0.get("current_source_entity")

    base_direct = int(st0.get("evidence_distribution", {}).get("direct_project_or_site", mf0.get("classification_counts", {}).get("direct_project_or_site", 0)))
    base_area = int(st0.get("evidence_distribution", {}).get("area_proxy", mf0.get("classification_counts", {}).get("area_proxy", 0)))
    zero_total_before = int(cp0.get("zero_result_windows", 0))

    for window in windows:
        run("git", "pull", "--rebase", "origin", BRANCH)
        live_cp = load(CHECKPOINT)
        live_next = int(live_cp.get("next_unused_window", {}).get("window_index", -1))
        if live_next != window:
            raise RuntimeError(f"CONCURRENT_SLOT_ADVANCE expected_window={window} observed={live_next}")

        entities, source_url = api_entities(window, query_params)
        features = []
        result = "ZERO_RESULT"
        ref = None
        ent = None
        if not entities:
            zero_windows.append(window)
        else:
            e = entities[0]
            ref, ent = ref_entity(e)
            last_ref, last_ent = ref, ent
            if (ref and str(ref) in used_refs) or (ent is not None and ent in used_entities):
                skipped_duplicates.append({"window_index": window, "reference": ref, "entity": ent})
                result = "DUPLICATE_CANDIDATE_SKIPPED_NOT_EMITTED"
            else:
                feat, reason = make_feature(e, query_name)
                if feat is None:
                    skipped_invalid.append({"window_index": window, "reference": ref, "entity": ent, "reason": reason})
                    result = reason
                else:
                    features = [feat]
                    result = "ADDED"
                    used_refs.add(str(ref))
                    used_entities.add(ent)
                    added_refs.append(ref)
                    added_entities.append(ent)
                    current_count += 1
                    if feat["properties"]["direct_project_evidence"]:
                        added_direct += 1
                    else:
                        added_area += 1

        batch_index = window + 1
        batch_path = batch_root / f"batch_{batch_index}.geojson"
        batch_obj = {
            "type": "FeatureCollection",
            "name": f"future_growth_9_batch_{batch_index}",
            "demo_only": True,
            "metadata": {
                "schema_version": 3,
                "slot_id": SLOT,
                "continuation_key": CONTINUATION,
                "run_id": run_id,
                "batch_index": batch_index,
                "feature_count_before": current_count - len(features),
                "feature_count_added": len(features),
                "feature_count_after": current_count,
                "source_window": {"dataset": "brownfield-land", "window_index": window, "window_size": 1, "entity": ent},
                "source_query_variant": query_name,
                "source_request_url": source_url,
                "source_result": result,
                "fake_data": False,
                "final_ready": False,
                "production_merge": False,
                "duplicate_count": 0,
                "duplicate_candidate_skipped": result == "DUPLICATE_CANDIDATE_SKIPPED_NOT_EMITTED",
                "nearest_match_used": False,
            },
            "features": features,
        }
        dump(batch_path, batch_obj)

        now = utcnow()
        common = {
            "schema_version": 3,
            "slot_id": SLOT,
            "continuation_key": CONTINUATION,
            "run_id": run_id,
            "updated_at": now,
            "state": "IN_PROGRESS_BOUNDED_SOURCE_EXPANSION",
            "fake_data": False,
            "final_ready": False,
            "production_merge": False,
            "demo_only": True,
            "feature_count_before": before,
            "feature_count_after": current_count,
            "logical_mirror_feature_count": current_count,
            "processed_window_range": [0, window],
            "zero_result_windows": zero_total_before + len(zero_windows),
            "current_batch_index": batch_index,
            "current_source_feature_id": ref,
            "current_source_entity": ent,
            "duplicate_count": 0,
            "nearest_match_used": False,
            "readback_expected": {"shard": current_count, "checkpoint": current_count, "status": current_count, "manifest": current_count, "dup": 0},
        }
        cp = dict(common)
        cp.update({
            "new_features_added": current_count - before,
            "already_processed_ids_count": current_count,
            "already_processed_ids_tail": (list(used_refs)[-5:] if used_refs else []),
            "next_unused_window": {"dataset": "brownfield-land", "window_index": window + 1, "window_size": 1},
            "current_batch_shard_path": batch_path.as_posix(),
            "source_query_variant": query_name,
            "duplicate_candidates_skipped_this_run": len(skipped_duplicates),
            "invalid_source_records_skipped_this_run": len(skipped_invalid),
        })
        status = dict(common)
        status.update({
            "new_records_added": current_count - before,
            "evidence_distribution": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area},
            "scoring_rule_status": "NOT_APPROVED_IN_AUTHORIZED_STATE",
            "source_query_variant": query_name,
            "duplicate_candidates_skipped_this_run": len(skipped_duplicates),
            "invalid_source_records_skipped_this_run": len(skipped_invalid),
        })
        manifest = dict(common)
        manifest.update({
            "emitted_feature_count_this_run": current_count - before,
            "already_processed_ids_count": current_count,
            "already_processed_ids_tail": (list(used_refs)[-5:] if used_refs else []),
            "classification_counts": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area},
            "matching_method": "direct official brownfield-land reference identity plus published WGS84 point; no nearest matching, no cross-parcel identity inference",
            "batch_shard_root": batch_root.as_posix(),
            "current_batch_shard_path": batch_path.as_posix(),
            "source_query_variant": query_name,
            "duplicate_candidates_skipped_this_run": len(skipped_duplicates),
            "invalid_source_records_skipped_this_run": len(skipped_invalid),
        })
        dump(CHECKPOINT, cp)
        dump(STATUS, status)
        dump(MANIFEST, manifest)

        sha = push_commit(f"aays: fg9 window {window} batch {batch_index} strict readback")
        readbacks[f"batch_{batch_index}"] = {"verified": True, "values": batch_readback(batch_path, current_count), "commit": sha, "window_index": window, "result": result}

    finished = utcnow()
    next_window = windows[-1] + 1
    report_path = REPORTS / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_report.json"
    report = {
        "schema_version": 1,
        "slot_id": SLOT,
        "slot_family": "future_growth",
        "continuation_key": CONTINUATION,
        "run_id": run_id,
        "state": "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED",
        "source_family": "planning_data_brownfield_land_direct_identity",
        "source_authority": "City of Bradford Metropolitan District Council",
        "source_query_variant": query_name,
        "source_sequence_anchor_validation": sequence_diagnostics,
        "source_dataset_url": "https://www.planning.data.gov.uk/dataset/brownfield-land",
        "source_quality": "authoritative source records; individual record quality retained from API",
        "source_license": "Open Government Licence v3.0",
        "bounded_batches_requested": 12,
        "bounded_batches_completed": 12,
        "new_processed_window_indices": windows,
        "processed_window_range": [0, windows[-1]],
        "zero_result_windows_this_run": zero_windows,
        "zero_result_windows_total": zero_total_before + len(zero_windows),
        "reprocessed_window_count": 0,
        "next_unused_window": {"dataset": "brownfield-land", "window_index": next_window, "window_size": 1},
        "source_feature_ids_added": added_refs,
        "source_entities_added": added_entities,
        "duplicate_candidates_skipped_not_emitted": skipped_duplicates,
        "invalid_source_records_skipped_not_emitted": skipped_invalid,
        "feature_counts": {"before": before, "added": current_count - before, "after_logical_mirror": current_count},
        "unique_evidenced_parcel_counts": {"before": before, "added": current_count - before, "after": current_count, "identity_basis": "unique direct official brownfield-land reference; no inferred parcel crosswalk"},
        "evidence_distribution": {"before": {"direct_project_or_site": base_direct, "area_proxy": base_area}, "added": {"direct_project_or_site": added_direct, "area_proxy": added_area}, "after": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area}},
        "duplicate_count_new": 0,
        "duplicate_definition": "no duplicate feature emitted; exact official source_feature_id/reference and entity uniqueness checked against all future_growth_9 batch shards plus canonical latest mirror",
        "nearest_match_used": False,
        "cross_parcel_identity_inference_used": False,
        "fake_data": False,
        "future_growth_value": None,
        "future_growth_probability": None,
        "scoring_rule_status": "METHODOLOGY_APPROVAL_REQUIRED",
        "batch_readback_verified": readbacks,
        "final_readback_verified": {"shard": current_count, "checkpoint": current_count, "status": current_count, "manifest": current_count, "dup": 0},
        "batch_shard_root": batch_root.as_posix(),
        "mirror_only": True,
        "other_slot_writes": 0,
        "demo_only": True,
        "final_ready": False,
        "production_merge": False,
        "finished_at": finished,
    }
    dump(report_path, report)

    cp = load(CHECKPOINT)
    st = load(STATUS)
    mf = load(MANIFEST)
    for obj in (cp, st, mf):
        obj["state"] = "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED"
        obj["updated_at"] = finished
    cp["report_path"] = report_path.as_posix()
    st["report_path"] = report_path.as_posix()
    mf["report_path"] = report_path.as_posix()
    dump(CHECKPOINT, cp)
    dump(STATUS, st)
    dump(MANIFEST, mf)

    task = load(CURRENT_TASK)
    task.update({
        "updated_at": finished,
        "state": "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED",
        "feature_count_before": before,
        "new_records_added": current_count - before,
        "feature_count_after": current_count,
        "processed_window_range": [0, windows[-1]],
        "next_batch_index": next_window + 1,
        "next_unused_window": {"dataset": "brownfield-land", "window_index": next_window, "window_size": 1},
        "source_contract_in_use": "Planning Data Brownfield Land direct official reference identity plus published WGS84 point; no nearest matching or cross-parcel identity inference",
        "source_query_variant": query_name,
        "duplicate_count": 0,
        "nearest_match_used": False,
        "report_path": report_path.as_posix(),
        "bounded_next_work": f"Continue from next unused brownfield-land window_index {next_window}; checkpoint zero-result windows and advance without replay.",
        "next_action": "Remain on the same task and continuation_key; do not create a new owner, replay a processed window, infer parcel identity, use nearest matching, or invent a scoring rule.",
        "prompt_contract_unchanged": True,
    })
    dump(CURRENT_TASK, task)

    recovery = load(RECOVERY)
    recovery.update({
        "updated_at": finished,
        "state": "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED",
        "recovery_decision": "RESUME_FROM_NEXT_UNUSED_WINDOW",
        "feature_count_before": before,
        "new_features_added": current_count - before,
        "feature_count_after": current_count,
        "processed_window_range": [0, windows[-1]],
        "next_batch_index": next_window + 1,
        "next_unused_window": {"dataset": "brownfield-land", "window_index": next_window, "window_size": 1},
        "last_processed_source_feature_id": last_ref,
        "last_processed_source_entity": last_ent,
        "duplicate_count": 0,
        "nearest_match_used": False,
        "fake_data": False,
        "final_ready": False,
        "production_merge": False,
        "demo_only": True,
        "report_path": report_path.as_posix(),
        "prompt_contract_unchanged": True,
    })
    dump(RECOVERY, recovery)

    final_sha = push_commit(f"aays: fg9 strict next-12 report {before} to {current_count}")
    run("git", "fetch", "origin", BRANCH)
    rcp = remote_json(CHECKPOINT)
    rst = remote_json(STATUS)
    rmf = remote_json(MANIFEST)
    rreport = remote_json(report_path)
    final_vals = {"checkpoint": rcp.get("feature_count_after"), "status": rst.get("feature_count_after"), "manifest": rmf.get("feature_count_after"), "report": rreport.get("unique_evidenced_parcel_counts", {}).get("after"), "dup": max(int(rcp.get("duplicate_count", 0)), int(rst.get("duplicate_count", 0)), int(rmf.get("duplicate_count", 0)))}
    if final_vals != {"checkpoint": current_count, "status": current_count, "manifest": current_count, "report": current_count, "dup": 0}:
        raise RuntimeError("FINAL_REMOTE_READBACK_MISMATCH: " + json.dumps(final_vals))
    print(json.dumps({"ok": True, "slot_id": SLOT, "start_window": start_window, "windows": windows, "before": before, "added": current_count - before, "after": current_count, "zero_windows": zero_windows, "duplicate_candidates_skipped": skipped_duplicates, "invalid_source_records_skipped": skipped_invalid, "next_unused_window": next_window, "report_path": report_path.as_posix(), "final_commit": final_sha, "query_variant": query_name, "final_readback": final_vals}, ensure_ascii=False))


if __name__ == "__main__":
    main()
