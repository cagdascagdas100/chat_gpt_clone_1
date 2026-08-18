#!/usr/bin/env python3
import hashlib, html, json, re, subprocess, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = "codex/aays-single-runner-v5-20260706"
SLOT = "future_growth_7"
CONT = "future_growth_7_open_source_v2_20260813"
CP = Path("state/slots/future_growth_7/checkpoint_latest.json")
ST = Path("state/slots/future_growth_7/status_latest.json")
MF = Path("state/slots/future_growth_7/evidence_manifest_latest.json")
RP = Path("state/slots/future_growth_7/report_latest.json")
SHARD = Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")
SOURCE = "https://nationalhighways.co.uk/roads-and-travel/live-travel-updates/the-severn-bridges/"
F_PATH = r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY = "National Highways M48 Severn Bridge resurfacing trial - unused window set 27"
MATCHING = "STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"

BATCHES = [
    (331, "national_highways_severn_bridge_resurfacing:m48_contraflow_20260808_20260918",
     "M48 Severn Bridge contraflow - 8 August to 18 September 2026",
     "current 2026 resurfacing trial window",
     ["From 8pm Saturday 08 August until 8pm Friday 18 September", "single narrow 3m wide lane running in each direction", "westbound carriageway"]),
    (332, "national_highways_severn_bridge_resurfacing:m48_both_full_20260918_20260919",
     "M48 Severn Bridge full closure - 18 to 19 September 2026",
     "forward 2026 resurfacing trial window",
     ["From 8pm Friday 18 September until 8pm Saturday 19 September", "Closure of westbound and eastbound carriageways"]),
    (333, "national_highways_severn_bridge_resurfacing:m48_lane2_overnight_20260919",
     "M48 Severn Bridge lane 2 overnight closure - 19 September 2026",
     "forward 2026 resurfacing trial window",
     ["Saturday 19 September", "Overnight eastbound and westbound lane 2 closure"]),
    (334, "national_highways_severn_bridge_resurfacing:m48_lane2_day_20260920_20260924",
     "M48 Severn Bridge daytime lane 2 closures - 20 to 24 September 2026",
     "forward 2026 resurfacing trial window",
     ["Sunday 20 September", "Thursday 24 September", "Daytime eastbound and westbound lane 2 closure"]),
    (335, "national_highways_severn_bridge_resurfacing:m48_wb_full_overnight_20260920_20260924",
     "M48 Severn Bridge westbound overnight closures - 20 to 24 September 2026",
     "forward 2026 resurfacing trial window",
     ["Sunday 20 September", "Thursday 24 September", "Full overnight closure of westbound carriageway", "lane 2 closure eastbound"]),
    (336, "national_highways_severn_bridge_resurfacing:m48_lane2_day_20260925",
     "M48 Severn Bridge daytime lane 2 closure - 25 September 2026",
     "forward 2026 resurfacing trial window",
     ["Friday 25 September", "midnight", "8pm", "Eastbound and westbound lane 2 closure"]),
    (337, "national_highways_severn_bridge_resurfacing:m48_wb_full_overnight_20260925",
     "M48 Severn Bridge westbound full overnight closure - 25 September 2026",
     "forward 2026 resurfacing trial window",
     ["Friday 25 September", "Full overnight closure of westbound carriageway", "Westbound diversion via M4 Prince of Wales Bridge"]),
    (338, "national_highways_severn_bridge_resurfacing:m48_eb_lane2_day_20260926",
     "M48 Severn Bridge eastbound lane 2 daytime closure - 26 September 2026",
     "forward 2026 resurfacing trial window",
     ["Saturday 26 September", "Eastbound lane 2 closure", "30mph limit in place"]),
    (339, "national_highways_severn_bridge_resurfacing:m48_eb_full_overnight_20260926",
     "M48 Severn Bridge eastbound full overnight closure - 26 September 2026",
     "forward 2026 resurfacing trial window",
     ["Saturday 26 September", "Full overnight closure of eastbound carriageway", "Eastbound diversion via M4 Prince of Wales Bridge"]),
    (340, "national_highways_severn_bridge_resurfacing:m48_wb_full_overnight_20260801",
     "M48 Severn Bridge westbound full overnight closure - 1 August 2026",
     "verified earlier 2026 setup window",
     ["Saturday 01 August", "Full overnight closure of westbound carriageway", "lane 2 closure eastbound"]),
    (341, "national_highways_severn_bridge_resurfacing:m48_eb_full_overnight_20260802",
     "M48 Severn Bridge eastbound full overnight closure - 2 August 2026",
     "verified earlier 2026 setup window",
     ["Sunday 02 August", "Full overnight closure of eastbound carriageway", "lane 2 closure westbound"]),
    (342, "national_highways_severn_bridge_resurfacing:m48_both_full_24h_20260807_20260808",
     "M48 Severn Bridge both carriageways full closure - 7 to 8 August 2026",
     "verified earlier 2026 setup window",
     ["From 8pm Friday 07 August until 8pm Saturday 08 August", "Closure of westbound and eastbound carriageways"]),
]


def run(*args, check=True):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"{' '.join(args)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def remote(path):
    return json.loads(run("git", "show", f"origin/{CANONICAL}:{path.as_posix()}").stdout)


def normalize(raw_text):
    s = html.unescape(raw_text)
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<style\b[^>]*>.*?</style>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def source_verify():
    req = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "Mozilla/5.0 AAYS-FG7-Severn/2026-08-18", "Accept": "text/html,application/xhtml+xml"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        final = r.geturl()
        status = getattr(r, "status", 200)
    assert status == 200
    assert "the-severn-bridges" in final
    txt = normalize(raw.decode("utf-8", "replace"))
    assert "m48 severn bridge" in txt
    assert "saturday 01 august until sunday 27 september 2026" in txt
    for batch, key, name, stage, tokens in BATCHES:
        for token in tokens:
            nt = normalize(token)
            assert nt in txt, (batch, token)
    return hashlib.sha256(raw).hexdigest(), len(raw), datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), final


def entry(window, sha256, nbytes, accessed_at, final_url):
    batch, key, name, stage, tokens = window
    return {
        "batch": batch,
        "window_key": key,
        "project_name": name,
        "project_stage": stage,
        "source_ref": SOURCE,
        "source_fetch_ok": True,
        "source_http_status": 200,
        "source_final_url": final_url,
        "source_sha256_runtime": sha256,
        "source_bytes_runtime": nbytes,
        "source_accessed_at": accessed_at,
        "source_verification": "official_national_highways_severn_bridges_runtime_verified_2026-08-18",
        "result": "ZERO_SAFE_CANONICAL_MATCHES",
        "new_unique_evidenced_parcels": 0,
        "reason": "Official National Highways M48 Severn Bridge resurfacing/traffic-management window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.",
        "reason_code": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE",
    }


def verify(batch):
    run("git", "fetch", "origin", CANONICAL)
    cp, st, mf, shard = remote(CP), remote(ST), remote(MF), remote(SHARD)
    shard_count = len(shard.get("features") or [])
    metadata_count = (shard.get("metadata") or {}).get("feature_count")
    counts = [shard_count, cp.get("artifact_feature_count"), st.get("artifact_feature_count"), mf.get("artifact_feature_count")]
    assert shard_count == metadata_count == 18
    assert counts == [18, 18, 18, 18], counts
    assert cp.get("latest_batch") == batch and cp.get("next_batch_index") == batch + 1
    assert st.get("latest_batch") == batch
    assert cp.get("duplicate_count") == st.get("duplicate_count") == mf.get("duplicate_count") == 0
    assert cp.get("unique_evidenced_parcel_count_after") == st.get("unique_evidenced_parcel_count") == mf.get("unique_evidenced_parcel_count") == 0
    assert cp.get("nearest_match_used") is False and st.get("nearest_match_used") is False and mf.get("nearest_match_used") is False
    assert cp.get("fake_data") is False and st.get("fake_data") is False and mf.get("fake_data") is False
    assert st.get("cross_slot_writes") is False and mf.get("cross_slot_writes") is False
    print("READBACK_PASS", batch, counts, "dup=0")


def push():
    for _ in range(30):
        p = run("git", "push", "origin", f"HEAD:{CANONICAL}", check=False)
        if p.returncode == 0:
            return
        run("git", "fetch", "origin", CANONICAL)
        r = run("git", "rebase", f"origin/{CANONICAL}", check=False)
        if r.returncode:
            run("git", "rebase", "--abort", check=False)
            raise RuntimeError("overlapping/FG7 rebase conflict; fail closed")
        time.sleep(1)
    raise RuntimeError("push retry limit")


def main():
    run("git", "config", "user.name", "AAYS FG7 strict runner")
    run("git", "config", "user.email", "aays-fg7@users.noreply.github.com")
    if run("git", "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        run("git", "fetch", "--unshallow", "origin")
    run("git", "fetch", "origin", CANONICAL)
    run("git", "checkout", "-B", "fg7_severn_exec", f"origin/{CANONICAL}")

    cp0, st0, mf0, shard0 = load(CP), load(ST), load(MF), load(SHARD)
    assert cp0.get("slot_id") == SLOT and st0.get("slot_id") == SLOT and mf0.get("slot_id") == SLOT
    assert cp0.get("continuation_key") == CONT
    assert cp0.get("latest_batch") == 330 and cp0.get("next_batch_index") == 331
    assert cp0.get("artifact_feature_count") == 18 and cp0.get("duplicate_count") == 0
    assert len(shard0.get("features") or []) == 18
    assert cp0.get("nearest_match_used") is False and cp0.get("fake_data") is False

    sha256, nbytes, accessed_at, final_url = source_verify()

    source_contract = {
        "existing_source_family": "Scottish Government NPF4 Annex B national developments",
        "new_source_family": FAMILY,
        "project_index": SOURCE,
        "canonical_target": "AAYS england_map_web future_growth parcel mirror",
        "matching_rule": MATCHING,
        "nearest_match_allowed": False,
        "strict_join_input_status": "Official Severn Bridge resurfacing/traffic-management windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence.",
    }

    for idx, window in enumerate(BATCHES, start=1):
        batch, key, name, stage, tokens = window
        run("git", "fetch", "origin", CANONICAL)
        r = run("git", "rebase", f"origin/{CANONICAL}", check=False)
        if r.returncode:
            run("git", "rebase", "--abort", check=False)
            raise RuntimeError("pre-batch rebase conflict")

        cp, st, mf = load(CP), load(ST), load(MF)
        assert cp.get("latest_batch") == batch - 1 and cp.get("next_batch_index") == batch
        assert st.get("latest_batch") == batch - 1
        hist = run("git", "log", "-S", key, "--format=%H", "--", "state/slots/future_growth_7", check=False).stdout.strip()
        assert not hist, ("reused window", key, hist)

        e = entry(window, sha256, nbytes, accessed_at, final_url)
        prior = run("git", "hash-object", str(CP)).stdout.strip()
        cp.update({
            "state": "BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if batch == 342 else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES",
            "prior_checkpoint_blob_sha": prior,
            "used_window_keys_this_run": [x[1] for x in BATCHES[:idx]],
            "unique_evidenced_parcel_count_before": 0,
            "unique_evidenced_parcel_count_after": 0,
            "new_unique_evidenced_parcels": 0,
            "mirror_feature_count": 18,
            "artifact_feature_count": 18,
            "legacy_source_evidence_feature_count": 18,
            "duplicate_count": 0,
            "latest_batch": batch,
            "next_batch_index": batch + 1,
            "new_run_bounded_batches_completed": idx,
            "last_batch": e,
            "source_contract": source_contract,
            "blocker": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER",
            "fake_data": False,
            "nearest_match_used": False,
            "demo_only": True,
            "final_ready": False,
            "production_merge": False,
        })
        st.update({
            "state": cp["state"],
            "latest_batch": batch,
            "bounded_batches_completed_this_run": idx,
            "artifact_feature_count": 18,
            "unique_evidenced_parcel_count": 0,
            "duplicate_count": 0,
            "nearest_match_used": False,
            "fake_data": False,
            "cross_slot_writes": False,
            "final_ready": False,
            "production_merge": False,
            "last_window_key": key,
            "last_result": "ZERO_SAFE_CANONICAL_MATCHES",
        })
        mf.update({
            "artifact_feature_count": 18,
            "legacy_source_evidence_feature_count": 18,
            "unique_evidenced_parcel_count": 0,
            "duplicate_count": 0,
            "new_source_family": FAMILY,
            "matching_rule": MATCHING,
            "nearest_match_allowed": False,
            "nearest_match_used": False,
            "fake_data": False,
            "cross_slot_writes": False,
            "processed_windows_this_run": [] if idx == 1 else mf.get("processed_windows_this_run", []),
        })
        mf["processed_windows_this_run"].append(e)

        dump(CP, cp)
        dump(ST, st)
        dump(MF, mf)
        paths = [str(CP), str(ST), str(MF)]

        if batch == 342:
            report = {
                "schema_version": 1,
                "slot_id": SLOT,
                "continuation_key": CONT,
                "run_id": "common_continuation_20260818_batches_331_342_severn_bridge",
                "requested_common_continuation_path": F_PATH,
                "requested_common_continuation_file_read": False,
                "requested_common_continuation_file_note": "The exact F: path is not mounted in the hosted session, is absent from /mnt/data, and no matching canonical repository file was found. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.",
                "requested_new_bounded_batches": 12,
                "completed_new_bounded_batches": 12,
                "batch_range": {"first": 331, "last": 342},
                "counts": {
                    "before": 0,
                    "added": 0,
                    "after": 0,
                    "before_unique_evidenced_parcels": 0,
                    "added_unique_evidenced_parcels": 0,
                    "after_unique_evidenced_parcels": 0,
                    "legacy_source_evidence_feature_count": 18,
                    "mirror_feature_count": 18,
                    "duplicate_count": 0,
                },
                "quality_gates": {
                    "shard_checkpoint_status_manifest_count_equal_each_batch": True,
                    "dup0_each_batch": True,
                    "nearest_match_used": False,
                    "fake_data": False,
                    "cross_slot_writes": False,
                    "own_slot_only": True,
                    "reused_window_count": 0,
                    "final_ready": False,
                    "production_merge": False,
                    "all_zero_or_verification_failed_windows_checkpointed": True,
                },
                "artifact_paths": {
                    "shard": str(SHARD),
                    "checkpoint": str(CP),
                    "status": str(ST),
                    "manifest": str(MF),
                    "report": str(RP),
                },
                "source_contract": source_contract,
                "source_refs": [SOURCE],
                "source_runtime": {"sha256": sha256, "bytes": nbytes, "accessed_at": accessed_at, "final_url": final_url},
                "source_window_keys": [x[1] for x in BATCHES],
                "source_windows": mf["processed_windows_this_run"],
                "next_batch_index": 343,
                "blocker": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE_TO_HOSTED_RUNNER",
            }
            dump(RP, report)
            paths.append(str(RP))

        run("git", "add", "--", *paths)
        changed = run("git", "diff", "--cached", "--name-only").stdout.splitlines()
        allowed = {str(CP), str(ST), str(MF), str(RP)}
        assert changed and set(changed) <= allowed, changed
        run("git", "commit", "-m", f"future_growth_7 batch {batch} Severn Bridge strict zero-window checkpoint")
        push()
        verify(batch)

    rp = remote(RP)
    assert rp.get("completed_new_bounded_batches") == 12
    assert rp.get("batch_range") == {"first": 331, "last": 342}
    assert rp.get("quality_gates", {}).get("reused_window_count") == 0
    print("FINAL_REPORT", RP)
    print("BEFORE_ADDED_AFTER", rp["counts"]["before"], rp["counts"]["added"], rp["counts"]["after"])


if __name__ == "__main__":
    main()
