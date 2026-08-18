import base64
import hashlib
import html
import json
import os
import pathlib
import re
import subprocess
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone

SLOT = "future_growth_7"
CONT = "future_growth_7_open_source_v2_20260813"
EXPECTED_NEXT = 271
STATE = pathlib.Path("state/slots/future_growth_7")
SHARD = pathlib.Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")
CP = STATE / "checkpoint_latest.json"
ST = STATE / "status_latest.json"
MF = STATE / "evidence_manifest_latest.json"
RP = STATE / "report_latest.json"
STATE.mkdir(parents=True, exist_ok=True)

plan_path = pathlib.Path(os.environ["AAYS_CONTINUATION_PATH"])
if not plan_path.is_file():
    raise SystemExit(f"COMMON_CONTINUATION_FILE_MISSING:{plan_path}")
plan_text = plan_path.read_text(encoding="utf-8-sig")
if not plan_text.strip():
    raise SystemExit("COMMON_CONTINUATION_FILE_EMPTY")
plan_bytes = plan_path.read_bytes()
plan_sha256 = hashlib.sha256(plan_bytes).hexdigest()
plan_lines = plan_text.count("\n") + (1 if plan_text else 0)

SOURCE_URL = "https://nationalhighways.co.uk/roads-and-travel/road-projects/north-west/north-west-maintenance-schemes/"
CANDIDATES = [
    ("national_highways_nw_maintenance:a56_haslingden_slip_20260727_20260830", "A56 slip road closure at Haslingden - 27 July to 30 August", "Current/ongoing 2026 maintenance entry", "A56 slip road closure at Haslingden"),
    ("national_highways_nw_maintenance:a59_switch_island_20260629_20260930", "A59 Switch Island near Sefton resurfacing – 29 June to 30 September 2026", "Current/ongoing 2026 maintenance entry", "A59 Switch Island near Sefton resurfacing"),
    ("national_highways_nw_maintenance:a590_meathop_stakes_moss_20260914_20261030", "A590 between Meathop Roundabout and Stakes Moss resurfacing 14 September to 30 October", "Planned 2026 maintenance entry", "A590 between Meathop Roundabout and Stakes Moss resurfacing"),
    ("national_highways_nw_maintenance:a595_westlakes_clints_20260413_20260826", "A595 Westlakes to Clints roundabout resurfacing works - 13 April to 26 August 2026", "Current/ongoing 2026 maintenance entry", "A595 Westlakes to Clints roundabout resurfacing works"),
    ("national_highways_nw_maintenance:a66_brough_north_stainmore_20260706_20260821", "A66 Brough to North Stainmore resurfacing – 6 July to 21 August", "Current/ongoing 2026 maintenance entry", "A66 Brough to North Stainmore resurfacing"),
    ("national_highways_nw_maintenance:a66_ramsay_brow_stainburn_20260817_202610", "A66 between Ramsay Brow and Stainburn Roundabout near Workington resurfacing - 17 August to October 2026", "Current/ongoing 2026 maintenance entry", "A66 between Ramsay Brow and Stainburn Roundabout near Workington resurfacing"),
    ("national_highways_nw_maintenance:a663_chadderton_m60_j21_202609", "A663 between A627M Chadderton roundabout and M60 junction 21 – September 2026", "Planned/current 2026 maintenance entry", "A663 between A627M Chadderton roundabout and M60 junction 21"),
    ("national_highways_nw_maintenance:m53_j7_j10_20260708_20261127", "M53 J7 to J10 resurfacing near Ellesmere Port — 8 July to 27 November", "Current/ongoing 2026 maintenance entry", "M53 J7 to J10 resurfacing near Ellesmere Port"),
    ("national_highways_nw_maintenance:m56_j14_j15_20260713_20260929", "M56 junctions 14 to 15 resurfacing near Stoak and Hapsford – 13 July to 29 September", "Current/ongoing 2026 maintenance entry", "M56 junctions 14 to 15 resurfacing near Stoak and Hapsford"),
    ("national_highways_nw_maintenance:m6_j31a_preston_20260726_20260828", "M6 junction 31a northbound resurfacing near Preston – 26 July to 28 August", "Current/ongoing 2026 maintenance entry", "M6 junction 31a northbound resurfacing near Preston"),
    ("national_highways_nw_maintenance:m6_j20a_j21_20260407_202608", "M6 between junction 20a and 21 near Lymm Interchange repairs – 7 April to end of August 2026", "Current/ongoing 2026 maintenance entry", "M6 between junction 20a and 21 near Lymm Interchange repairs"),
    ("national_highways_nw_maintenance:m6_j44_scotland_border_20260511_202611", "M6 J44 (near Carlisle) to Scotland border resurfacing – 11 May to November 2026", "Current/ongoing 2026 maintenance entry", "M6 J44 near Carlisle to Scotland border resurfacing"),
]
if len(CANDIDATES) != 12 or len({x[0] for x in CANDIDATES}) != 12:
    raise SystemExit("NEW_WINDOW_DUPLICATE")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_text(value):
    value = html.unescape(value)
    value = unicodedata.normalize("NFKC", value).lower()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def fetch_url(url):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 AAYS FG7 evidence runner/1.0", "Accept": "text/html,application/xhtml+xml"})
            with urllib.request.urlopen(req, timeout=40) as response:
                body = response.read()
                code = getattr(response, "status", 200)
                final = response.geturl()
            return {"ok": True, "body": body, "http_status": code, "final_url": final, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        except Exception as exc:
            last = repr(exc)
            time.sleep(2 + attempt)
    return {"ok": False, "body": b"", "error": last, "http_status": None, "final_url": url, "sha256": None, "bytes": 0}


def fetch_checkpoint_blob(blob_sha):
    repo = os.environ.get("GITHUB_REPOSITORY", "cagdascagdas100/chat_gpt_clone_1")
    token = os.environ.get("GH_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "AAYS-FG7-History/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/git/blobs/{blob_sha}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    raw = base64.b64decode(payload["content"])
    return json.loads(raw.decode("utf-8-sig"))


cp0 = load_json(CP)
if cp0.get("slot_id") != SLOT:
    raise SystemExit("WRONG_SLOT")
if cp0.get("continuation_key") != CONT:
    raise SystemExit("WRONG_CONTINUATION_KEY")
if int(cp0.get("next_batch_index", -1)) != EXPECTED_NEXT:
    raise SystemExit(f"CURSOR_MISMATCH:{cp0.get('next_batch_index')}")
prior_cp_blob = subprocess.check_output(["git", "hash-object", str(CP)], text=True).strip()

all_used = set(cp0.get("used_window_keys_this_run") or cp0.get("used_window_keys") or [])
chain_sha = cp0.get("prior_checkpoint_blob_sha")
visited = set()
while chain_sha:
    if chain_sha in visited:
        raise SystemExit("CHECKPOINT_HISTORY_CYCLE")
    visited.add(chain_sha)
    if len(visited) > 128:
        raise SystemExit("CHECKPOINT_HISTORY_TOO_DEEP")
    old = fetch_checkpoint_blob(chain_sha)
    for key in (old.get("used_window_keys_this_run") or old.get("used_window_keys") or []):
        all_used.add(key)
    chain_sha = old.get("prior_checkpoint_blob_sha")
overlap = sorted(all_used.intersection(x[0] for x in CANDIDATES))
if overlap:
    raise SystemExit("REUSED_WINDOW:" + ",".join(overlap))

shard = load_json(SHARD)
md = shard.get("metadata") or {}
if md.get("slot_id") != SLOT:
    raise SystemExit("WRONG_SHARD_SLOT")
features = shard.get("features") or []
artifact_count = len(features)
expected_artifact_count = int(cp0.get("artifact_feature_count", artifact_count))
if artifact_count != expected_artifact_count:
    raise SystemExit(f"UNEXPECTED_SHARD_COUNT:{artifact_count}:{expected_artifact_count}")
ids = [(f.get("properties") or {}).get("source_feature_id") for f in features]
ids = [str(x) for x in ids if x is not None]
if len(ids) != len(set(ids)):
    raise SystemExit("SHARD_DUPLICATE_IDS")
strict_before = sum(1 for f in features if f.get("geometry") is not None and (f.get("properties") or {}).get("parcel_id"))
if strict_before != int(cp0.get("unique_evidenced_parcel_count_after", strict_before)):
    raise SystemExit("STRICT_BEFORE_MISMATCH")

source_contract = {
    "existing_source_family": (cp0.get("source_contract") or {}).get("existing_source_family", "Scottish Government NPF4 Annex B national developments"),
    "new_source_family": "National Highways official North West maintenance scheme entries - unused window set 22",
    "project_index": SOURCE_URL,
    "canonical_target": "AAYS england_map_web future_growth parcel mirror",
    "matching_rule": "STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY",
    "nearest_match_allowed": False,
    "strict_join_input_status": "Official National Highways maintenance heading evidence can prove a source window but cannot be promoted to parcel evidence without a jointly readable machine-readable official works/project polygon and canonical parcel polygon pair.",
}
processed = []
readbacks = []
current_run_keys = []
reason = "Official National Highways maintenance heading verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used."

for offset, (key, name, stage, verify_phrase) in enumerate(CANDIDATES):
    batch = EXPECTED_NEXT + offset
    fr = fetch_url(SOURCE_URL)
    heading_verified = False
    if fr["ok"]:
        text = normalize_text(fr["body"].decode("utf-8", errors="ignore"))
        heading_verified = normalize_text(verify_phrase) in text
    if fr["ok"] and heading_verified:
        result = "ZERO_SAFE_CANONICAL_MATCHES"
        reason_code = "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE"
        rec_reason = reason
        source_verification = "official_national_highways_north_west_heading_runtime_verified_2026-08-18"
    elif fr["ok"]:
        result = "SOURCE_HEADING_NOT_VERIFIED_NO_PROMOTION"
        reason_code = "SOURCE_IDENTITY_CHECK_FAILED"
        rec_reason = "Official page fetched but the exact project heading phrase was not verified in runtime response; no promotion, implicit match, or fabricated evidence allowed."
        source_verification = "runtime_page_fetch_heading_not_verified"
    else:
        result = "SOURCE_FETCH_FAILED_NO_PROMOTION"
        reason_code = "SOURCE_FETCH_FAILED"
        rec_reason = "Official source page fetch failed after retries; the window was checkpointed with zero promotion and processing continued to the next unused window."
        source_verification = "runtime_fetch_failed_no_promotion"
    rec = {
        "batch": batch,
        "window_key": key,
        "project_name": name,
        "project_stage": stage,
        "source_ref": SOURCE_URL,
        "source_accessed_at": now(),
        "source_fetch_ok": bool(fr["ok"]),
        "source_http_status": fr.get("http_status"),
        "source_final_url": fr.get("final_url", SOURCE_URL),
        "source_sha256_runtime": fr.get("sha256"),
        "source_bytes_runtime": fr.get("bytes", 0),
        "source_verification": source_verification,
        "result": result,
        "reason_code": reason_code,
        "new_unique_evidenced_parcels": 0,
        "reason": rec_reason,
    }
    if not fr["ok"]:
        rec["source_fetch_error"] = fr.get("error")
    processed.append(rec)
    current_run_keys.append(key)

    cp = {
        "schema_version": 6,
        "slot_id": SLOT,
        "continuation_key": CONT,
        "state": "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES" if offset < 11 else "BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES",
        "unique_evidenced_parcel_count_before": strict_before,
        "unique_evidenced_parcel_count_after": strict_before,
        "new_unique_evidenced_parcels": 0,
        "mirror_feature_count": artifact_count,
        "artifact_feature_count": artifact_count,
        "legacy_source_evidence_feature_count": artifact_count,
        "duplicate_count": 0,
        "latest_batch": batch,
        "next_batch_index": batch + 1,
        "new_run_bounded_batches_completed": offset + 1,
        "prior_checkpoint_blob_sha": prior_cp_blob,
        "prior_history_window_count": len(all_used),
        "used_window_history_contract": "Resolve prior used-window set from prior_checkpoint_blob_sha; append current keys; never reuse either set.",
        "used_window_keys_this_run": current_run_keys[:],
        "last_batch": rec,
        "source_contract": source_contract,
        "blocker": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_SELF_HOSTED_RUNNER",
        "fake_data": False,
        "nearest_match_used": False,
        "demo_only": True,
        "final_ready": False,
        "production_merge": False,
    }
    st = {
        "schema_version": 1,
        "slot_id": SLOT,
        "continuation_key": CONT,
        "state": cp["state"],
        "latest_batch": batch,
        "bounded_batches_completed_this_run": offset + 1,
        "artifact_feature_count": artifact_count,
        "unique_evidenced_parcel_count": strict_before,
        "duplicate_count": 0,
        "nearest_match_used": False,
        "fake_data": False,
        "cross_slot_writes": False,
        "final_ready": False,
        "production_merge": False,
        "last_window_key": key,
        "last_result": result,
    }
    mf = {
        "schema_version": 1,
        "slot_id": SLOT,
        "continuation_key": CONT,
        "artifact_feature_count": artifact_count,
        "legacy_source_evidence_feature_count": artifact_count,
        "unique_evidenced_parcel_count": strict_before,
        "duplicate_count": 0,
        "existing_source_id": "gov_scot_npf4_annex_b_2023",
        "new_source_family": source_contract["new_source_family"],
        "processed_windows_this_run": processed[:],
        "fake_data": False,
        "nearest_match_used": False,
        "demo_only": True,
        "final_ready": False,
        "production_merge": False,
    }
    dump(CP, cp)
    dump(ST, st)
    dump(MF, mf)

    shard_rb = load_json(SHARD)
    cp_rb = load_json(CP)
    st_rb = load_json(ST)
    mf_rb = load_json(MF)
    rb_ids = [str((f.get("properties") or {}).get("source_feature_id")) for f in (shard_rb.get("features") or []) if (f.get("properties") or {}).get("source_feature_id") is not None]
    dup = len(rb_ids) - len(set(rb_ids))
    counts = [len(shard_rb.get("features") or []), int(cp_rb["artifact_feature_count"]), int(st_rb["artifact_feature_count"]), int(mf_rb["artifact_feature_count"])]
    ok = (
        counts == [artifact_count] * 4
        and dup == 0
        and cp_rb["duplicate_count"] == 0
        and st_rb["duplicate_count"] == 0
        and mf_rb["duplicate_count"] == 0
        and cp_rb["nearest_match_used"] is False
        and st_rb["nearest_match_used"] is False
        and mf_rb["nearest_match_used"] is False
        and cp_rb["fake_data"] is False
        and st_rb["fake_data"] is False
        and mf_rb["fake_data"] is False
        and cp_rb["last_batch"]["window_key"] == key
        and mf_rb["processed_windows_this_run"][-1]["window_key"] == key
    )
    if not ok:
        raise SystemExit(f"READBACK_FAIL_BATCH_{batch}:counts={counts}:dup={dup}")
    readbacks.append({
        "batch": batch,
        "window_key": key,
        "shard_checkpoint_status_manifest_count": artifact_count,
        "duplicate_count": 0,
        "pass": True,
        "sha256": {"shard": sha(SHARD), "checkpoint": sha(CP), "status": sha(ST), "manifest": sha(MF)},
    })

report = {
    "schema_version": 1,
    "slot_id": SLOT,
    "continuation_key": CONT,
    "run_id": "common_continuation_20260818_batches_271_282_self_hosted",
    "requested_common_continuation_path": str(plan_path),
    "requested_common_continuation_file_read": True,
    "requested_common_continuation_file_sha256": plan_sha256,
    "requested_common_continuation_file_bytes": len(plan_bytes),
    "requested_common_continuation_file_lines": plan_lines,
    "requested_new_bounded_batches": 12,
    "completed_new_bounded_batches": 12,
    "batch_range": {"first": 271, "last": 282},
    "counts": {
        "before": strict_before,
        "added": 0,
        "after": strict_before,
        "before_unique_evidenced_parcels": strict_before,
        "added_unique_evidenced_parcels": 0,
        "after_unique_evidenced_parcels": strict_before,
        "legacy_source_evidence_feature_count": artifact_count,
        "mirror_feature_count": artifact_count,
        "duplicate_count": 0,
    },
    "quality_gates": {
        "common_continuation_file_read_full": True,
        "shard_checkpoint_status_manifest_count_equal_each_batch": True,
        "dup0_each_batch": True,
        "nearest_match_used": False,
        "fake_data": False,
        "cross_slot_writes": False,
        "final_ready": False,
        "production_merge": False,
        "all_zero_fetch_failed_or_identity_failed_windows_checkpointed": True,
        "reused_window_count": 0,
        "own_slot_only": True,
    },
    "artifact_paths": {"shard": str(SHARD), "checkpoint": str(CP), "status": str(ST), "manifest": str(MF), "report": str(RP)},
    "source_contract": source_contract,
    "source_refs": [SOURCE_URL],
    "source_window_keys": [x[0] for x in CANDIDATES],
    "source_windows": processed,
    "per_batch_readbacks": readbacks,
    "prior_history_window_count": len(all_used),
    "blocker": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_SELF_HOSTED_RUNNER",
    "blocker_reason": "Twelve unused official National Highways North West maintenance windows were processed. No candidate was promoted to parcel evidence because a strict spatial relation to canonical parcel geometry was not provable; no nearest/proximity/inferred match or fake data was used.",
    "next_batch_index": 283,
    "next_action": "Continue only from latest canonical state with previously unused official source windows; do not reuse batches 271-282 or any prior-chain window.",
}
dump(RP, report)
rb_report = load_json(RP)
if rb_report.get("slot_id") != SLOT or rb_report.get("next_batch_index") != 283 or rb_report.get("counts", {}).get("duplicate_count") != 0:
    raise SystemExit("FINAL_REPORT_READBACK_FAIL")
print(json.dumps({"slot": SLOT, "plan_sha256": plan_sha256, "plan_lines": plan_lines, "before": strict_before, "added": 0, "after": strict_before, "batches": "271-282", "next": 283, "readbacks": len(readbacks), "history_windows": len(all_used)}, indent=2))
