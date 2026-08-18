#!/usr/bin/env python3
import csv
import hashlib
import io
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import requests
from pyproj import Transformer

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
FUTURE_GROWTH_ROOT = Path("AAYS/england_map_web/data/future_growth")
SOURCE_FAMILY = "local_planning_authority_brownfield_land_register"
SOURCE_SNAPSHOT = "bradford_brownfield_register_2025_csv"
SOURCE_PAGE = "https://datahub.bradford.gov.uk/datasets/planning/bradford-brownfield-register/"
SOURCE_URL = "https://datahub.bradford.gov.uk/opendata/Brownfield_Register/Brownfield%20register%202025.csv"
SOURCE_PUBLISHER = "City of Bradford Metropolitan District Council"
SWITCH_REASON = "PRIMARY_PLANNING_DATA_API_OFFSET_SEQUENCE_UNRESOLVED_NO_SORT_CONTRACT"
ALLOWED_PREFIXES = (
    "AAYS/england_map_web/data/future_growth/shards/future_growth_9_batches/",
    "docs/chatgpt_status/_shared/slots_21/future_growth_9/",
    "state/slots/future_growth_9/",
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AAYS-future-growth-9-bounded-snapshot/1.0"})
TRANSFORMER = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


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


def canon_key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def row_get(row, *names):
    keyed = {canon_key(k): v for k, v in row.items() if k is not None}
    for name in names:
        v = keyed.get(canon_key(name))
        if v is not None:
            return str(v).strip()
    return ""


def source_snapshot():
    r = SESSION.get(SOURCE_URL, timeout=90)
    r.raise_for_status()
    raw = r.content
    if len(raw) < 1000:
        raise RuntimeError(f"SOURCE_SNAPSHOT_TOO_SMALL bytes={len(raw)} status={r.status_code}")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = [dict(x) for x in reader]
    if not rows:
        raise RuntimeError("SOURCE_SNAPSHOT_EMPTY")
    headers = {canon_key(x) for x in (reader.fieldnames or [])}
    required = {"sitereference", "geox", "geoy"}
    if not required.issubset(headers):
        raise RuntimeError("SOURCE_SCHEMA_MISMATCH headers=" + json.dumps(reader.fieldnames))
    return raw, rows, r.url


def coord_from_row(row):
    sx, sy = row_get(row, "GeoX"), row_get(row, "GeoY")
    try:
        x, y = float(sx), float(sy)
    except Exception:
        return None, None
    if -180 <= x <= 180 and -90 <= y <= 90:
        return [x, y], "published_GeoX_GeoY_WGS84"
    if 0 <= x <= 800000 and 0 <= y <= 1400000:
        lon, lat = TRANSFORMER.transform(x, y)
        if -180 <= lon <= 180 and -90 <= lat <= 90:
            return [round(lon, 7), round(lat, 7)], "published_GeoX_GeoY_EPSG27700_to_EPSG4326"
    return None, None


def num(v):
    if v in (None, "", "Not set", "not set"):
        return None
    try:
        x = float(str(v).replace(",", ""))
        return int(x) if x.is_integer() else x
    except Exception:
        return None


def own_slot_refs():
    refs = set()
    paths = list((REPO / BATCH_BASE).glob("**/*.geojson"))
    if (REPO / LATEST).exists():
        paths.append(REPO / LATEST)
    for p in paths:
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for feat in obj.get("features", []):
            ref = (feat.get("properties") or {}).get("source_feature_id")
            if ref:
                refs.add(str(ref).strip())
    return refs


def repo_future_growth_refs():
    refs = set()
    root = REPO / FUTURE_GROWTH_ROOT
    for p in root.rglob("*.geojson"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for feat in obj.get("features", []):
            props = feat.get("properties") or {}
            ref = props.get("source_feature_id") or props.get("site_reference")
            if ref:
                refs.add(str(ref).strip())
    for p in root.rglob("*.jsonl"):
        try:
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    if "source_feature_id" not in line and "site_reference" not in line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    props = obj.get("properties") if isinstance(obj, dict) else None
                    if not isinstance(props, dict):
                        props = obj if isinstance(obj, dict) else {}
                    ref = props.get("source_feature_id") or props.get("site_reference")
                    if ref:
                        refs.add(str(ref).strip())
        except Exception:
            continue
    return refs


def canonical_row_hash(row):
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def feature_from_row(row, snapshot_sha):
    ref = row_get(row, "SiteReference")
    coords, coord_method = coord_from_row(row)
    if not ref or coords is None:
        return None
    planning_status_raw = row_get(row, "PlanningStatus")
    permissioned = "permissioned" in planning_status_raw.lower() and "not permissioned" not in planning_status_raw.lower()
    notes = row_get(row, "Notes")
    site = row_get(row, "SiteNameAddress")
    evidence = notes or site or "Official Bradford Brownfield Register site suitable for residential development."
    props = {
        "slot_id": SLOT,
        "continuation_key": CONTINUATION,
        "source_family": SOURCE_FAMILY,
        "source_snapshot": SOURCE_SNAPSHOT,
        "source_name": "Bradford Council Brownfield Register 2025",
        "source_publisher": SOURCE_PUBLISHER,
        "source_feature_id": ref,
        "source_url": SOURCE_PAGE,
        "source_download_url": SOURCE_URL,
        "source_snapshot_sha256": snapshot_sha,
        "source_row_sha256": canonical_row_hash(row),
        "source_entry_date": row_get(row, "LastUpdatedDate", "FirstAddedDate") or None,
        "source_first_added_date": row_get(row, "FirstAddedDate") or None,
        "license": "Open Government Licence v3.0",
        "planning_status": planning_status_raw or None,
        "future_growth_evidence_type": "direct_project" if permissioned else "area_proxy",
        "direct_project_evidence": bool(permissioned),
        "evidence_summary": evidence,
        "matching_method": "direct official Bradford Brownfield Register SiteReference plus published GeoX/GeoY coordinate; no nearest matching, no cross-parcel identity inference",
        "coordinate_method": coord_method,
        "accuracy_scale_1_4": 4 if permissioned else 3,
        "future_growth_value": None,
        "future_growth_probability": None,
        "unknown_reason": "Numeric value/probability withheld because no approved scoring rule exists.",
        "site_name": site or None,
        "hectares": num(row_get(row, "Hectares")),
        "net_dwellings_range_from": num(row_get(row, "NetDwellingsRangeFrom")),
        "net_dwellings_range_to": num(row_get(row, "NetDwellingsRangeTo")),
        "planning_permission_date": row_get(row, "PermissionDate") or None,
        "planning_permission_type": row_get(row, "PermissionType") or None,
        "planning_history": row_get(row, "PlanningHistory") or None,
        "deliverable": row_get(row, "Deliverable") or None,
        "fake_data": False,
        "final_ready": False,
        "production_merge": False,
        "demo_only": True,
    }
    fid = "future_growth_9:bradford_brownfield_2025:" + re.sub(r"[^a-z0-9]+", "-", ref.lower()).strip("-")
    return {"type": "Feature", "id": fid, "geometry": {"type": "Point", "coordinates": coords}, "properties": props}


def select_candidates(rows, repo_refs, snapshot_sha):
    ordered = sorted(rows, key=lambda r: (row_get(r, "SiteReference").casefold(), row_get(r, "SiteNameAddress").casefold(), canonical_row_hash(r)))
    selected = []
    seen_source = set()
    skipped_existing = []
    skipped_invalid = []
    skipped_ended = []
    for source_index, row in enumerate(ordered):
        ref = row_get(row, "SiteReference")
        if not ref:
            skipped_invalid.append({"source_index": source_index, "reason": "MISSING_SITE_REFERENCE"})
            continue
        if ref in seen_source:
            skipped_invalid.append({"source_index": source_index, "reference": ref, "reason": "DUPLICATE_REFERENCE_WITHIN_SNAPSHOT"})
            continue
        seen_source.add(ref)
        end_date = row_get(row, "EndDate")
        if end_date and end_date.lower() not in {"not set", "n/a", "na", "none"}:
            skipped_ended.append({"source_index": source_index, "reference": ref, "end_date": end_date})
            continue
        if ref in repo_refs:
            skipped_existing.append({"source_index": source_index, "reference": ref})
            continue
        feat = feature_from_row(row, snapshot_sha)
        if feat is None:
            skipped_invalid.append({"source_index": source_index, "reference": ref, "reason": "INVALID_OR_MISSING_COORDINATE"})
            continue
        selected.append({"source_index": source_index, "row": row, "feature": feat, "reference": ref})
        if len(selected) == 12:
            break
    if len(selected) < 12:
        raise RuntimeError(f"INSUFFICIENT_NEW_VALID_UNIQUE_SOURCE_RECORDS selected={len(selected)} existing_skips={len(skipped_existing)} invalid={len(skipped_invalid)} ended={len(skipped_ended)}")
    return selected, skipped_existing, skipped_invalid, skipped_ended


def changed_paths():
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
    paths = changed_paths()
    if not paths:
        raise RuntimeError("NO_CHANGES_TO_COMMIT")
    run("git", "add", "--", *paths)
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


def verify_remote(batch_path, expected):
    shard = remote_json(batch_path)
    cp = remote_json(CHECKPOINT)
    st = remote_json(STATUS)
    mf = remote_json(MANIFEST)
    vals = {
        "shard": int(shard.get("metadata", {}).get("feature_count_after", -1)),
        "checkpoint": int(cp.get("feature_count_after", -1)),
        "status": int(st.get("feature_count_after", -1)),
        "manifest": int(mf.get("feature_count_after", -1)),
        "dup": max(int(shard.get("metadata", {}).get("duplicate_count", 0)), int(cp.get("duplicate_count", 0)), int(st.get("duplicate_count", 0)), int(mf.get("duplicate_count", 0))),
    }
    wanted = {"shard": expected, "checkpoint": expected, "status": expected, "manifest": expected, "dup": 0}
    if vals != wanted:
        raise RuntimeError("READBACK_MISMATCH actual=" + json.dumps(vals) + " expected=" + json.dumps(wanted))
    return vals


def main():
    run("git", "config", "user.name", "github-actions[bot]")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "pull", "--rebase", "origin", BRANCH)

    cp0, st0, mf0 = load(CHECKPOINT), load(STATUS), load(MANIFEST)
    if cp0.get("slot_id") != SLOT or cp0.get("continuation_key") != CONTINUATION:
        raise RuntimeError("SLOT_OR_CONTINUATION_MISMATCH")
    before = int(cp0.get("feature_count_after", -1))
    start_window = int((cp0.get("next_unused_window") or {}).get("window_index", -1))
    if before != 91 or start_window != 91:
        raise RuntimeError(f"LIVE_STATE_CHANGED expected_before=91 actual_before={before} expected_window=91 actual_window={start_window}")
    if int(st0.get("feature_count_after", -1)) != before or int(mf0.get("feature_count_after", -1)) != before:
        raise RuntimeError("PRE_RUN_STATE_READBACK_MISMATCH")
    if any(int(x.get("duplicate_count", 0)) != 0 for x in (cp0, st0, mf0)):
        raise RuntimeError("PRE_RUN_DUPLICATE_COUNT_NONZERO")
    if any(bool(x.get("nearest_match_used", False)) for x in (cp0, st0, mf0)):
        raise RuntimeError("PRE_RUN_NEAREST_MATCH_TRUE")

    slot_refs = own_slot_refs()
    if len(slot_refs) != before:
        raise RuntimeError(f"SLOT_IDENTITY_COUNT_MISMATCH slot_refs={len(slot_refs)} checkpoint={before}")
    repo_refs = repo_future_growth_refs()

    raw, rows, resolved_url = source_snapshot()
    snapshot_sha = hashlib.sha256(raw).hexdigest()
    selected, skipped_existing, skipped_invalid, skipped_ended = select_candidates(rows, repo_refs, snapshot_sha)

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"future_growth_9_bounded12_{run_stamp}"
    batch_root = BATCH_BASE / run_stamp
    base_direct = int((st0.get("evidence_distribution") or {}).get("direct_project_or_site", 0))
    base_area = int((st0.get("evidence_distribution") or {}).get("area_proxy", 0))
    zero_total_before = int(cp0.get("zero_result_windows", 0))
    prior_tail = list(cp0.get("already_processed_ids_tail") or [])
    added_refs = []
    readbacks = {}
    added_direct = 0
    added_area = 0
    current_count = before

    for i, candidate in enumerate(selected):
        global_window = start_window + i
        batch_index = global_window + 1
        run("git", "pull", "--rebase", "origin", BRANCH)
        live = load(CHECKPOINT)
        observed = int((live.get("next_unused_window") or {}).get("window_index", -1))
        if observed != global_window:
            raise RuntimeError(f"CONCURRENT_SLOT_ADVANCE expected_window={global_window} observed={observed}")

        feat = candidate["feature"]
        ref = candidate["reference"]
        if ref in slot_refs or ref in repo_refs:
            raise RuntimeError(f"DUPLICATE_APPEARED_DURING_RUN reference={ref}")
        slot_refs.add(ref)
        repo_refs.add(ref)
        added_refs.append(ref)
        current_count += 1
        if feat["properties"]["direct_project_evidence"]:
            added_direct += 1
        else:
            added_area += 1

        batch_path = batch_root / f"batch_{batch_index}.geojson"
        batch = {
            "type": "FeatureCollection",
            "name": f"future_growth_9_batch_{batch_index}",
            "demo_only": True,
            "metadata": {
                "schema_version": 3,
                "slot_id": SLOT,
                "continuation_key": CONTINUATION,
                "run_id": run_id,
                "batch_index": batch_index,
                "feature_count_before": current_count - 1,
                "feature_count_added": 1,
                "feature_count_after": current_count,
                "source_window": {
                    "source_family": SOURCE_FAMILY,
                    "snapshot": SOURCE_SNAPSHOT,
                    "continuation_window_index": global_window,
                    "family_window_index": i,
                    "snapshot_sorted_source_index": candidate["source_index"],
                    "window_size": 1,
                    "reference": ref,
                },
                "source_request_url": resolved_url,
                "source_snapshot_sha256": snapshot_sha,
                "source_family_switch_reason": SWITCH_REASON,
                "source_result": "ADDED",
                "fake_data": False,
                "final_ready": False,
                "production_merge": False,
                "duplicate_count": 0,
                "nearest_match_used": False,
            },
            "features": [feat],
        }
        dump(batch_path, batch)

        now = utcnow()
        next_window = global_window + 1
        common_updates = {
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
            "processed_window_range": [0, global_window],
            "zero_result_windows": zero_total_before,
            "current_batch_index": batch_index,
            "current_source_feature_id": ref,
            "current_source_entity": None,
            "duplicate_count": 0,
            "nearest_match_used": False,
            "source_family": SOURCE_FAMILY,
            "source_snapshot": SOURCE_SNAPSHOT,
            "source_snapshot_sha256": snapshot_sha,
            "source_family_switch_reason": SWITCH_REASON,
            "readback_expected": {"shard": current_count, "checkpoint": current_count, "status": current_count, "manifest": current_count, "dup": 0},
        }

        cp = load(CHECKPOINT)
        cp.update(common_updates)
        cp.update({
            "new_features_added": current_count - before,
            "already_processed_ids_count": current_count,
            "already_processed_ids_tail": (prior_tail + added_refs)[-5:],
            "next_unused_window": {"dataset": "bradford-brownfield-register-2025", "source_family": SOURCE_FAMILY, "window_index": next_window, "family_window_index": i + 1, "window_size": 1, "snapshot_sha256": snapshot_sha},
            "current_batch_shard_path": batch_path.as_posix(),
        })

        st = load(STATUS)
        st.update(common_updates)
        st.update({
            "new_records_added": current_count - before,
            "evidence_distribution": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area},
            "scoring_rule_status": "NOT_APPROVED_IN_AUTHORIZED_STATE",
        })

        mf = load(MANIFEST)
        mf.update(common_updates)
        mf.update({
            "emitted_feature_count_this_run": current_count - before,
            "already_processed_ids_count": current_count,
            "already_processed_ids_tail": (prior_tail + added_refs)[-5:],
            "classification_counts": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area},
            "matching_method": "direct official Bradford Brownfield Register SiteReference plus published GeoX/GeoY coordinate; no nearest matching, no cross-parcel identity inference",
            "batch_shard_root": batch_root.as_posix(),
            "current_batch_shard_path": batch_path.as_posix(),
            "source_contract": {
                "primary_sources": ["planning_data_brownfield_land_lpa_membership"],
                "fallback_sources_allowable": ["local_planning_authority_brownfield_land_register"],
                "active_source": SOURCE_FAMILY,
                "nearest_match_forbidden": True,
            },
        })
        dump(CHECKPOINT, cp)
        dump(STATUS, st)
        dump(MANIFEST, mf)

        sha = push_commit(f"aays: fg9 fallback window {global_window} batch {batch_index} strict readback")
        vals = verify_remote(batch_path, current_count)
        readbacks[f"batch_{batch_index}"] = {"verified": True, "values": vals, "commit": sha, "continuation_window_index": global_window, "family_window_index": i, "reference": ref}

    finished = utcnow()
    next_window = start_window + 12
    report_path = REPORTS / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_report.json"
    report = {
        "schema_version": 1,
        "slot_id": SLOT,
        "slot_family": "future_growth",
        "continuation_key": CONTINUATION,
        "run_id": run_id,
        "state": "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED",
        "source_family": SOURCE_FAMILY,
        "source_snapshot": SOURCE_SNAPSHOT,
        "source_authority": SOURCE_PUBLISHER,
        "source_page": SOURCE_PAGE,
        "source_download_url": resolved_url,
        "source_snapshot_sha256": snapshot_sha,
        "source_quality": "authoritative Bradford Council annual Brownfield Register snapshot",
        "source_license": "Open Government Licence v3.0",
        "source_family_switch_reason": SWITCH_REASON,
        "primary_source_sequence_status": "UNRESOLVED_NOT_REPLAYED",
        "bounded_batches_requested": 12,
        "bounded_batches_completed": 12,
        "new_processed_window_indices": list(range(start_window, next_window)),
        "source_family_window_indices": list(range(12)),
        "processed_window_range": [0, next_window - 1],
        "zero_result_windows_this_run": [],
        "zero_result_windows_total": zero_total_before,
        "reprocessed_window_count": 0,
        "next_unused_window": {"dataset": "bradford-brownfield-register-2025", "source_family": SOURCE_FAMILY, "window_index": next_window, "family_window_index": 12, "window_size": 1, "snapshot_sha256": snapshot_sha},
        "source_feature_ids_added": added_refs,
        "source_snapshot_indices_added": [x["source_index"] for x in selected],
        "preselection_existing_references_skipped_not_emitted": skipped_existing,
        "preselection_invalid_rows_skipped_not_emitted": skipped_invalid,
        "preselection_ended_rows_skipped_not_emitted": skipped_ended,
        "feature_counts": {"before": before, "added": current_count - before, "after_logical_mirror": current_count},
        "unique_evidenced_parcel_counts": {"before": before, "added": current_count - before, "after": current_count, "identity_basis": "unique direct Bradford Council SiteReference; no inferred parcel crosswalk"},
        "evidence_distribution": {"before": {"direct_project_or_site": base_direct, "area_proxy": base_area}, "added": {"direct_project_or_site": added_direct, "area_proxy": added_area}, "after": {"direct_project_or_site": base_direct + added_direct, "area_proxy": base_area + added_area}},
        "duplicate_count_new": 0,
        "duplicate_definition": "no duplicate feature emitted; exact SiteReference uniqueness checked against slot batch shards and repo future_growth evidence before selection and before each write",
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

    cp, st, mf = load(CHECKPOINT), load(STATUS), load(MANIFEST)
    for obj in (cp, st, mf):
        obj["state"] = "TWELVE_NEW_BOUNDED_BATCHES_MIRRORED_AND_READBACK_VERIFIED"
        obj["updated_at"] = finished
        obj["report_path"] = report_path.as_posix()
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
        "processed_window_range": [0, next_window - 1],
        "next_source_index": 1,
        "next_batch_index": next_window + 1,
        "next_unused_window": {"dataset": "bradford-brownfield-register-2025", "source_family": SOURCE_FAMILY, "window_index": next_window, "family_window_index": 12, "window_size": 1, "snapshot_sha256": snapshot_sha},
        "source_contract_in_use": "Bradford Council annual Brownfield Register 2025 official SiteReference plus published GeoX/GeoY; deterministic snapshot order; no nearest matching or cross-parcel identity inference",
        "source_family_switch_reason": SWITCH_REASON,
        "duplicate_count": 0,
        "nearest_match_used": False,
        "report_path": report_path.as_posix(),
        "bounded_next_work": f"Continue from logical window_index {next_window}; do not replay primary API offsets whose sequence was unresolved. Resume this deterministic snapshot family from family_window_index 12 or move to the next unused permitted source family if exhausted.",
        "next_action": "Remain on the same task and continuation_key; do not create a new owner, replay processed windows, infer parcel identity, use nearest matching, or invent a scoring rule.",
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
        "processed_window_range": [0, next_window - 1],
        "next_source_index": 1,
        "next_batch_index": next_window + 1,
        "next_unused_window": {"dataset": "bradford-brownfield-register-2025", "source_family": SOURCE_FAMILY, "window_index": next_window, "family_window_index": 12, "window_size": 1, "snapshot_sha256": snapshot_sha},
        "last_processed_source_feature_id": added_refs[-1],
        "last_processed_source_entity": None,
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

    final_sha = push_commit(f"aays: fg9 fallback strict next-12 report {before} to {current_count}")
    final_vals = verify_remote(batch_root / f"batch_{next_window}.geojson", current_count)
    remote_report = remote_json(report_path)
    if remote_report.get("feature_counts") != {"before": before, "added": 12, "after_logical_mirror": current_count}:
        raise RuntimeError("REMOTE_REPORT_COUNT_MISMATCH")
    print(json.dumps({"ok": True, "slot_id": SLOT, "before": before, "added": 12, "after": current_count, "report_path": report_path.as_posix(), "final_commit": final_sha, "final_readback": final_vals, "source_feature_ids_added": added_refs}, ensure_ascii=False))


if __name__ == "__main__":
    raise SystemExit(main())
