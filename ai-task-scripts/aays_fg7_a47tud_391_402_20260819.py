#!/usr/bin/env python3
import hashlib, html, json, re, subprocess, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = "codex/aays-single-runner-v5-20260706"
SLOT = "future_growth_7"
CONT = "future_growth_7_open_source_v2_20260813"
MATCHING = "STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"
SRC = "https://nationalhighways.co.uk/roads-and-travel/road-projects/east/a47-north-tuddenham-to-easton-improvements/"
F_PATH = r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY = "National Highways official A47 North Tuddenham to Easton project updates - unused window set 35"
CP = Path("state/slots/future_growth_7/checkpoint_latest.json")
ST = Path("state/slots/future_growth_7/status_latest.json")
MF = Path("state/slots/future_growth_7/evidence_manifest_latest.json")
RP = Path("state/slots/future_growth_7/report_latest.json")
SHARD = Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")

BATCHES = [
    (391, "national_highways_a47_tuddenham_project:a47_eb_norwich_longwater_20260815", "A47 eastbound Norwich Road junction to Longwater junction overnight closure - 15 August 2026", ["Overnight closure eastbound", "Saturday 15 August", "Norwich Road junction and Longwater junction"]),
    (392, "national_highways_a47_tuddenham_project:a47_woodlane_longwater_weekend_20260731_20260803", "A47 Wood Lane Junction to Longwater Interchange full weekend closure - 31 July to 3 August 2026", ["Full weekend road closure", "31 July to 3 August 2026", "Wood Lane Junction and Longwater Interchange"]),
    (393, "national_highways_a47_tuddenham_project:a47_lyng_fox_both_20260801_02", "A47 Lyng Road to Fox Lane junction both-directions overnight closure - 1 to 2 August 2026", ["1 August - A47 between Lyng Road and Fox Lane junction overnight closure", "8pm 1 August to 6am 2 August"]),
    (394, "national_highways_a47_tuddenham_project:a47_woodlane_longwater_both_20260630_20260701", "A47 Wood Lane Junction to Longwater Interchange full overnight closures - 30 June and 1 July 2026", ["A47 full overnight road closures", "30 June and 1 July 2026", "Wood Lane Junction to Longwater Interchange"]),
    (395, "national_highways_a47_tuddenham_project:a47_longwater_dereham_weekend_20260529_20260601", "A47 Longwater Interchange to Dereham Interchange full weekend closure - 29 May to 1 June 2026", ["A47 Tuddenham full weekend closure", "8pm Friday 29 May to 6am Monday 1 June", "Longwater Interchange and Dereham Interchange"]),
    (396, "national_highways_a47_tuddenham_project:a47_dereham_easton_weekend_20260424_27", "A47 Dereham Interchange to Easton Roundabout full weekend closure - 24 to 27 April 2026", ["A47 Dereham interchange to Easton Roundabout full weekend closure", "8pm Friday 24 to 6am Monday 27 April"]),
    (397, "national_highways_a47_tuddenham_project:lyng_road_north_tuddenham_20260427_20260601", "Lyng Road North Tuddenham full closure - 27 April to 1 June 2026", ["Lyng Road in North Tuddenham closure", "27 April to 1 June 2026", "Hall Lane and Stone Road"]),
    (398, "national_highways_a47_tuddenham_project:a47_fox_easton_lane_20260328_29", "A47 Fox Lane junction to Easton Roundabout daytime lane closures - 28 and 29 March 2026", ["Daytime lane closures", "28 and 29 March 2026", "Fox Lane junction and Easton Roundabout"]),
    (399, "national_highways_a47_tuddenham_project:a47_longwater_dereham_weekend_20260213_16", "A47 Longwater Junction to Dereham Interchange full weekend closure - 13 to 16 February 2026", ["8pm Friday 13 February", "6am Monday 16 February 2026", "Longwater Junction to Dereham interchange"]),
    (400, "national_highways_a47_tuddenham_project:a47_honingham_easton_directional_20260126_29", "A47 Honingham to Easton directional overnight closures - 26 to 29 January 2026", ["26 to 29 January 2026", "closing one direction of the A47 overnight between the roundabouts"]),
    (401, "national_highways_a47_tuddenham_project:a47_honingham_easton_full_20260130", "A47 Honingham to Easton full overnight closure - 30 January 2026", ["On 30 January 2026", "A47 will be fully closed in both directions"]),
    (402, "national_highways_a47_tuddenham_project:a47_honingham_easton_lane_20260131", "A47 Honingham to Easton daytime lane closure - 31 January 2026", ["On 31 January 2026", "closing one lane of the A47 during the day between the roundabouts"]),
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


def norm(s):
    s = html.unescape(s)
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<style\b[^>]*>.*?</style>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def fetch_source():
    req = urllib.request.Request(SRC, headers={"User-Agent": "Mozilla/5.0 AAYS-FG7-A47TUD/2026-08-19", "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        final = r.geturl()
        status = getattr(r, "status", 200)
    if status != 200:
        raise RuntimeError(f"SOURCE_HTTP:{status}")
    if "/a47-north-tuddenham-to-easton-improvements/" not in final:
        raise RuntimeError(f"SOURCE_URL:{final}")
    txt = norm(raw.decode("utf-8", "replace"))
    for b, key, name, tokens in BATCHES:
        for token in tokens:
            if norm(token) not in txt:
                raise RuntimeError(f"SOURCE_TOKEN_MISSING:{b}:{token!r}:BYTES={len(raw)}:FINAL={final}")
    return {
        "url": SRC,
        "final_url": final,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "accessed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def entry(window, src):
    b, key, name, tokens = window
    return {
        "batch": b,
        "window_key": key,
        "project_name": name,
        "project_stage": "verified 2026 project closure window",
        "source_ref": SRC,
        "source_fetch_ok": True,
        "source_http_status": 200,
        "source_final_url": src["final_url"],
        "source_sha256_runtime": src["sha256"],
        "source_bytes_runtime": src["bytes"],
        "source_accessed_at": src["accessed_at"],
        "source_verification": f"official_national_highways_a47_tuddenham_runtime_verified_{src['accessed_at'][:10]}",
        "result": "ZERO_SAFE_CANONICAL_MATCHES",
        "new_unique_evidenced_parcels": 0,
        "reason": "Official National Highways A47 North Tuddenham to Easton project closure window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.",
        "reason_code": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE",
    }


def push_canonical():
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


def verify(batch):
    run("git", "fetch", "origin", CANONICAL)
    cp, st, mf, sh = remote(CP), remote(ST), remote(MF), remote(SHARD)
    shard_count = len(sh.get("features") or [])
    metadata_count = (sh.get("metadata") or {}).get("feature_count")
    counts = [shard_count, cp.get("artifact_feature_count"), st.get("artifact_feature_count"), mf.get("artifact_feature_count")]
    assert shard_count == metadata_count == 18 and counts == [18, 18, 18, 18], counts
    assert cp.get("latest_batch") == batch and cp.get("next_batch_index") == batch + 1 and st.get("latest_batch") == batch
    assert cp.get("duplicate_count") == st.get("duplicate_count") == mf.get("duplicate_count") == 0
    assert cp.get("unique_evidenced_parcel_count_after") == st.get("unique_evidenced_parcel_count") == mf.get("unique_evidenced_parcel_count") == 0
    assert cp.get("nearest_match_used") is False and st.get("nearest_match_used") is False and mf.get("nearest_match_used") is False
    assert cp.get("fake_data") is False and st.get("fake_data") is False and mf.get("fake_data") is False
    assert st.get("cross_slot_writes") is False and mf.get("cross_slot_writes") is False
    if batch == 402:
        rp = remote(RP)
        assert rp["completed_new_bounded_batches"] == 12
        assert rp["counts"]["before"] == rp["counts"]["added"] == rp["counts"]["after"] == 0
        assert rp["quality_gates"]["dup0_each_batch"] is True
        assert rp["quality_gates"]["reused_window_count"] == 0
    print("READBACK_PASS", batch, counts, "dup=0")


def main():
    if len(BATCHES) != 12 or len({x[1] for x in BATCHES}) != 12:
        raise RuntimeError("invalid or duplicate batch key list")
    run("git", "config", "user.name", "AAYS FG7 strict runner")
    run("git", "config", "user.email", "aays-fg7@users.noreply.github.com")
    if run("git", "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        run("git", "fetch", "--unshallow", "origin")
    run("git", "fetch", "origin", CANONICAL)
    run("git", "checkout", "-B", "fg7_a47tud_exec", f"origin/{CANONICAL}")
    cp0, st0, mf0, sh0 = load(CP), load(ST), load(MF), load(SHARD)
    assert cp0.get("slot_id") == st0.get("slot_id") == mf0.get("slot_id") == SLOT
    assert cp0.get("latest_batch") == 390 and cp0.get("next_batch_index") == 391
    assert cp0.get("artifact_feature_count") == 18 and cp0.get("duplicate_count") == 0
    assert len(sh0.get("features") or []) == 18
    assert cp0.get("nearest_match_used") is False and cp0.get("fake_data") is False and st0.get("cross_slot_writes") is False

    src = fetch_source()
    source_contract = {
        "existing_source_family": "Scottish Government NPF4 Annex B national developments",
        "new_source_family": FAMILY,
        "project_index": [SRC],
        "canonical_target": "AAYS england_map_web future_growth parcel mirror",
        "matching_rule": MATCHING,
        "nearest_match_allowed": False,
        "strict_join_input_status": "Official project closure windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence.",
    }

    for idx, window in enumerate(BATCHES, start=1):
        b, key, name, tokens = window
        run("git", "fetch", "origin", CANONICAL)
        r = run("git", "rebase", f"origin/{CANONICAL}", check=False)
        if r.returncode:
            run("git", "rebase", "--abort", check=False)
            raise RuntimeError("pre-batch rebase conflict")
        cp, st, mf = load(CP), load(ST), load(MF)
        assert cp.get("latest_batch") == b - 1 and cp.get("next_batch_index") == b and st.get("latest_batch") == b - 1
        hist = run("git", "log", "-S", key, "--format=%H", "--", "state/slots/future_growth_7", check=False).stdout.strip()
        if hist:
            raise RuntimeError(f"REUSED_WINDOW:{key}:{hist}")

        e = entry(window, src)
        prior = run("git", "hash-object", str(CP)).stdout.strip()
        final = b == 402
        state = "BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if final else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES"
        cp.update({
            "state": state,
            "prior_checkpoint_blob_sha": prior,
            "used_window_keys_this_run": [x[1] for x in BATCHES[:idx]],
            "unique_evidenced_parcel_count_before": 0,
            "unique_evidenced_parcel_count_after": 0,
            "new_unique_evidenced_parcels": 0,
            "mirror_feature_count": 18,
            "artifact_feature_count": 18,
            "legacy_source_evidence_feature_count": 18,
            "duplicate_count": 0,
            "latest_batch": b,
            "next_batch_index": b + 1,
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
            "state": state,
            "latest_batch": b,
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
        if idx == 1:
            mf["processed_windows_this_run"] = []
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
        })
        mf["processed_windows_this_run"].append(e)
        dump(CP, cp); dump(ST, st); dump(MF, mf)
        paths = [CP.as_posix(), ST.as_posix(), MF.as_posix()]

        if final:
            report = {
                "schema_version": 1,
                "slot_id": SLOT,
                "continuation_key": CONT,
                "run_id": "common_continuation_20260819_batches_391_402_a47_tuddenham_unused",
                "requested_common_continuation_path": F_PATH,
                "requested_common_continuation_file_read": False,
                "requested_common_continuation_file_note": "The exact F: path is not mounted in the hosted session, is absent from /mnt/data, and no matching canonical repository file was found. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.",
                "requested_new_bounded_batches": 12,
                "completed_new_bounded_batches": 12,
                "batch_range": {"first": 391, "last": 402},
                "counts": {
                    "before": 0, "added": 0, "after": 0,
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
                    "shard": SHARD.as_posix(), "checkpoint": CP.as_posix(), "status": ST.as_posix(),
                    "manifest": MF.as_posix(), "report": RP.as_posix(),
                },
                "source_contract": source_contract,
                "source_refs": [SRC],
                "source_runtime": src,
                "source_window_keys": [x[1] for x in BATCHES],
                "source_windows": [entry(x, src) for x in BATCHES],
            }
            dump(RP, report)
            paths.append(RP.as_posix())

        changed = set(run("git", "diff", "--name-only").stdout.splitlines())
        allowed = {CP.as_posix(), ST.as_posix(), MF.as_posix(), RP.as_posix()}
        if not changed or not changed.issubset(allowed):
            raise RuntimeError(f"OWNERSHIP_GATE:{sorted(changed)}")
        run("git", "add", *paths)
        run("git", "commit", "-m", f"FG7 strict batch {b}: checkpoint unused A47 Tuddenham window")
        push_canonical()
        verify(b)

    print("FINAL_REPORT", RP.as_posix())
    print("BEFORE_ADDED_AFTER", 0, 0, 0)


if __name__ == "__main__":
    main()
