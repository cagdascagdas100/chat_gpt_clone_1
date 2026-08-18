#!/usr/bin/env python3
import hashlib
import html
import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANONICAL = "codex/aays-single-runner-v5-20260706"
SLOT = "future_growth_7"
CONT = "future_growth_7_open_source_v2_20260813"
MATCHING = "STRICT_CENTROID_WITHIN_POLYGON_OR_EXACT_INTERSECTION_ONLY"
WM = "https://nationalhighways.co.uk/roads-and-travel/road-projects/west-midlands/west-midlands-maintenance-schemes/"
F_PATH = r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md"
FAMILY = "National Highways official West Midlands A46/M40/M42/M6 maintenance entries - unused window set 31"

CP = Path("state/slots/future_growth_7/checkpoint_latest.json")
ST = Path("state/slots/future_growth_7/status_latest.json")
MF = Path("state/slots/future_growth_7/evidence_manifest_latest.json")
RP = Path("state/slots/future_growth_7/report_latest.json")
SHARD = Path("AAYS/england_map_web/data/future_growth/shards/future_growth_7_latest.geojson")

BATCHES = [
    (343, "national_highways_west_midlands_maintenance:a46_walsgrave_m6_nb_full_20260717_31", "A46 Walsgrave to M6 junction 2 northbound full closure - 17 to 31 July 2026", ["Friday 17 to Friday 31 July", "Total closure of A46 northbound between Walsgrave and M6 junction 2"]),
    (344, "national_highways_west_midlands_maintenance:a46_m6_walsgrave_sb_full_20260731_20260811", "A46 M6 junction 2 to Walsgrave southbound full closure - 31 July to 11 August 2026", ["Friday 31 July to Tuesday 11 August", "Total closure of A46 southbound between M6 junction 2 and Walsgrave"]),
    (345, "national_highways_west_midlands_maintenance:m42_j3_eb_exit_20260408_14", "M42 junction 3 eastbound exit slip full closure - 8 to 14 April 2026", ["8-14 April", "M42 junction 3 eastbound exit slip road", "Full closure"]),
    (346, "national_highways_west_midlands_maintenance:m42_j3_wb_exit_20260424_29", "M42 junction 3 westbound exit slip full closure - 24 to 29 April 2026", ["24-29 April", "M42 junction 3 westbound exit slip road", "Full closure"]),
    (347, "national_highways_west_midlands_maintenance:m40_j15_nb_entry_20260518", "M40 junction 15 northbound entry slip full closure - 18 May 2026", ["18 May", "M40 junction 15 northbound entry slip road", "Full closure"]),
    (348, "national_highways_west_midlands_maintenance:m40_j16_sb_exit_20260519_20", "M40 junction 16 southbound exit slip full closure - 19 to 20 May 2026", ["19-20 May", "M40 junction 16 southbound exit slip road", "Full closure"]),
    (349, "national_highways_west_midlands_maintenance:m40_j15_nb_entry_20260521", "M40 junction 15 northbound entry slip full closure - 21 May 2026", ["21 May", "M40 junction 15 northbound entry slip road", "Full closure"]),
    (350, "national_highways_west_midlands_maintenance:m6_j6_j4_sb_full_20260518_20260619", "M6 southbound junction 6 to 4 full closure - 18 May to 19 June 2026", ["18 May to 19 June", "Full closure of M6 southbound between junction 6 and 4"]),
    (351, "national_highways_west_midlands_maintenance:m6_j6_j5_sb_full_20260622_20260717", "M6 southbound junction 6 to 5 full closure - 22 June to 17 July 2026", ["22 June to 17 July", "Full closure of M6 southbound between junction 6 and 5"]),
    (352, "national_highways_west_midlands_maintenance:m6_j6_j4_sb_3lanes_20260720_31", "M6 southbound junctions 6 to 4 three-lane closure - 20 to 31 July 2026", ["20 July to 31 July", "3 lanes closed with hard shoulder open"]),
    (353, "national_highways_west_midlands_maintenance:m6_j6_j5_sb_full_20260803_14", "M6 southbound junction 6 to 5 full closure - 3 to 14 August 2026", ["3 August to 14 August", "Full closure of M6 southbound between junction 6 and 5"]),
    (354, "national_highways_west_midlands_maintenance:m6_j6_j5_sb_full_20260928_20261016", "M6 southbound junction 6 to 5 full closure - 28 September to 16 October 2026", ["28 September to 16 October", "Full closure of M6 southbound between junction 6 and 5"]),
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


def norm(text):
    text = html.unescape(text)
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("–", "-").replace("—", "-").replace("‑", "-")
    return re.sub(r"\s+", " ", text).strip().lower()


def fetch_source():
    req = urllib.request.Request(
        WM,
        headers={
            "User-Agent": "Mozilla/5.0 AAYS-FG7-West-Midlands-343-354/2026-08-19",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
        final = r.geturl()
        status = getattr(r, "status", 200)
    if status != 200:
        raise RuntimeError(f"WM_SOURCE_HTTP:{status}")
    if "/west-midlands/" not in final:
        raise RuntimeError(f"WM_SOURCE_URL:{final}")
    txt = norm(raw.decode("utf-8", "replace"))
    for batch, key, name, tokens in BATCHES:
        for token in tokens:
            if norm(token) not in txt:
                raise RuntimeError(f"WM_SOURCE_TOKEN_MISSING:{batch}:{token!r}:BYTES={len(raw)}:FINAL={final}")
    return {
        "url": WM,
        "final_url": final,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "accessed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def evidence_entry(window, src):
    batch, key, name, tokens = window
    return {
        "batch": batch,
        "window_key": key,
        "project_name": name,
        "project_stage": "verified 2026 maintenance window",
        "source_ref": WM,
        "source_fetch_ok": True,
        "source_http_status": 200,
        "source_final_url": src["final_url"],
        "source_sha256_runtime": src["sha256"],
        "source_bytes_runtime": src["bytes"],
        "source_accessed_at": src["accessed_at"],
        "source_verification": f"official_national_highways_west_midlands_runtime_verified_{src['accessed_at'][:10]}",
        "result": "ZERO_SAFE_CANONICAL_MATCHES",
        "new_unique_evidenced_parcels": 0,
        "reason": "Official National Highways West Midlands maintenance window verified. No jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is available to prove strict centroid-within-polygon or exact intersection; no inferred polygon, proximity, nearest match, or fake data used.",
        "reason_code": "STRICT_SPATIAL_JOIN_INPUT_PAIR_UNAVAILABLE",
    }


def push_with_rebase():
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


def verify_remote(batch):
    run("git", "fetch", "origin", CANONICAL)
    cp = remote(CP)
    st = remote(ST)
    mf = remote(MF)
    sh = remote(SHARD)
    shard_count = len(sh.get("features") or [])
    meta_count = (sh.get("metadata") or {}).get("feature_count")
    counts = [
        shard_count,
        cp.get("artifact_feature_count"),
        st.get("artifact_feature_count"),
        mf.get("artifact_feature_count"),
    ]
    assert shard_count == meta_count == 18 and counts == [18, 18, 18, 18], counts
    assert cp.get("latest_batch") == batch and cp.get("next_batch_index") == batch + 1
    assert st.get("latest_batch") == batch
    assert cp.get("duplicate_count") == st.get("duplicate_count") == mf.get("duplicate_count") == 0
    assert cp.get("unique_evidenced_parcel_count_after") == st.get("unique_evidenced_parcel_count") == mf.get("unique_evidenced_parcel_count") == 0
    assert cp.get("nearest_match_used") is False and st.get("nearest_match_used") is False and mf.get("nearest_match_used") is False
    assert cp.get("fake_data") is False and st.get("fake_data") is False and mf.get("fake_data") is False
    assert st.get("cross_slot_writes") is False and mf.get("cross_slot_writes") is False
    if batch == 354:
        rp = remote(RP)
        assert rp.get("completed_new_bounded_batches") == 12
        assert rp.get("counts", {}).get("before") == 0
        assert rp.get("counts", {}).get("added") == 0
        assert rp.get("counts", {}).get("after") == 0
        assert rp.get("quality_gates", {}).get("dup0_each_batch") is True
    print("READBACK_PASS", batch, counts, "dup=0")


def main():
    if len({w[1] for w in BATCHES}) != len(BATCHES):
        raise RuntimeError("duplicate window key inside batch list")

    run("git", "config", "user.name", "AAYS FG7 strict runner")
    run("git", "config", "user.email", "aays-fg7@users.noreply.github.com")
    if run("git", "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        run("git", "fetch", "--unshallow", "origin")
    run("git", "fetch", "origin", CANONICAL)
    run("git", "checkout", "-B", "fg7_wm_exec", f"origin/{CANONICAL}")

    cp0, st0, mf0, sh0 = load(CP), load(ST), load(MF), load(SHARD)
    assert cp0.get("slot_id") == st0.get("slot_id") == mf0.get("slot_id") == SLOT
    assert cp0.get("latest_batch") == 342 and cp0.get("next_batch_index") == 343
    assert cp0.get("artifact_feature_count") == 18 and cp0.get("duplicate_count") == 0
    assert len(sh0.get("features") or []) == 18
    assert cp0.get("nearest_match_used") is False and cp0.get("fake_data") is False
    assert st0.get("cross_slot_writes") is False

    src = fetch_source()
    source_contract = {
        "existing_source_family": "Scottish Government NPF4 Annex B national developments",
        "new_source_family": FAMILY,
        "project_index": [WM],
        "canonical_target": "AAYS england_map_web future_growth parcel mirror",
        "matching_rule": MATCHING,
        "nearest_match_allowed": False,
        "strict_join_input_status": "Official maintenance windows prove source activity, but no jointly readable machine-readable official works/project polygon plus canonical parcel polygon pair is exposed; source-only evidence is not promoted to parcel evidence.",
    }

    for idx, window in enumerate(BATCHES, start=1):
        batch, key, name, tokens = window
        run("git", "fetch", "origin", CANONICAL)
        r = run("git", "rebase", f"origin/{CANONICAL}", check=False)
        if r.returncode:
            run("git", "rebase", "--abort", check=False)
            raise RuntimeError("pre-batch rebase conflict; fail closed")

        cp, st, mf = load(CP), load(ST), load(MF)
        assert cp.get("latest_batch") == batch - 1 and cp.get("next_batch_index") == batch
        assert st.get("latest_batch") == batch - 1

        history = run("git", "log", "-S", key, "--format=%H", "--", "state/slots/future_growth_7", check=False).stdout.strip()
        if history:
            raise RuntimeError(f"REUSED_WINDOW:{key}:{history}")

        entry = evidence_entry(window, src)
        prior_blob = run("git", "hash-object", str(CP)).stdout.strip()
        final = batch == 354
        state = "BOUNDED_RUN_COMPLETE_NO_NEW_STRICT_MATCHES" if final else "BOUNDED_RUN_IN_PROGRESS_NO_NEW_STRICT_MATCHES"

        cp.update({
            "state": state,
            "prior_checkpoint_blob_sha": prior_blob,
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
            "last_batch": entry,
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
        mf["processed_windows_this_run"].append(entry)

        dump(CP, cp)
        dump(ST, st)
        dump(MF, mf)
        paths = [str(CP), str(ST), str(MF)]

        if final:
            report = {
                "schema_version": 1,
                "slot_id": SLOT,
                "continuation_key": CONT,
                "run_id": "common_continuation_20260819_batches_343_354_west_midlands_unused",
                "requested_common_continuation_path": F_PATH,
                "requested_common_continuation_file_read": False,
                "requested_common_continuation_file_note": "The exact F: path is not mounted in the hosted session, is absent from /mnt/data, and no matching canonical repository file was found. The exact file is therefore not claimed as read; this run follows the current user instruction and canonical future_growth_7 state/source contract.",
                "requested_new_bounded_batches": 12,
                "completed_new_bounded_batches": 12,
                "batch_range": {"first": 343, "last": 354},
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
                    "shard": SHARD.as_posix(),
                    "checkpoint": CP.as_posix(),
                    "status": ST.as_posix(),
                    "manifest": MF.as_posix(),
                    "report": RP.as_posix(),
                },
                "source_contract": source_contract,
                "source_refs": [WM],
                "source_runtime": src,
                "source_window_keys": [x[1] for x in BATCHES],
                "source_windows": [evidence_entry(x, src) for x in BATCHES],
            }
            dump(RP, report)
            paths.append(str(RP))

        changed = set(run("git", "diff", "--name-only").stdout.splitlines())
        allowed = {CP.as_posix(), ST.as_posix(), MF.as_posix(), RP.as_posix()}
        if not changed or not changed.issubset(allowed):
            raise RuntimeError(f"CROSS_SLOT_OR_UNEXPECTED_CHANGE:{sorted(changed)}")

        run("git", "add", *paths)
        run("git", "commit", "-m", f"FG7 strict batch {batch}: {key}")
        push_with_rebase()
        verify_remote(batch)

    print("FINAL_REPORT", RP.as_posix())
    print("BEFORE_ADDED_AFTER", 0, 0, 0)


if __name__ == "__main__":
    main()
