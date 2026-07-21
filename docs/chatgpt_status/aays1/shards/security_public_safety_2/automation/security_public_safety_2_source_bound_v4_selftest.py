from __future__ import annotations

import copy
import csv
import importlib.util
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "security_public_safety_2_runner_pipeline_v4_source_bound.py"
spec = importlib.util.spec_from_file_location("slot2_source_bound_v4", MODULE_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

cases: list[dict[str, object]] = []
def check(name: str, value: object) -> None:
    cases.append({"name": name, "pass": bool(value)})

with tempfile.TemporaryDirectory() as td:
    repo = Path(td)
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    auto = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    out.mkdir(parents=True); auto.mkdir(parents=True); web.mkdir(parents=True)
    iod = out / "official_source_cache/iod.csv"; mps = out / "official_source_cache/mps.csv"
    iod.parent.mkdir(parents=True)
    iod.write_text("lsoa,score\nE1,1\n", encoding="utf-8")
    mps.write_text("lsoa,2026-05\nE1,2\n", encoding="utf-8")
    attestation = {
        "pass": True,
        "state": "LIVE_SOURCE_ATTESTATION_PASSED",
        "resolved_env": {"AAYS_IOD25_V2_CSV": str(iod.resolve()), "AAYS_MPS_LSOA_CSV": str(mps.resolve())},
        "provenance_manifest": {"sources": {"police_latest": {"parsed": {"latest_date": "2026-05-01", "latest_month": "2026-05"}}}},
        "bootstrap_manifest": {},
    }
    bindings = m.attestation_bindings(attestation)
    check("bindings_valid", bindings["pass"])
    check("bindings_police_month", bindings["police_month"] == "2026-05")
    check("bindings_iod_sha", bindings["iod_sha256"] == m.sha256_file(iod))
    check("bindings_mps_sha", bindings["mps_sha256"] == m.sha256_file(mps))
    bad = copy.deepcopy(attestation); bad["pass"] = False; check("bindings_reject_pass", not m.attestation_bindings(bad)["pass"])
    bad = copy.deepcopy(attestation); bad["state"] = "BAD"; check("bindings_reject_state", not m.attestation_bindings(bad)["pass"])
    bad = copy.deepcopy(attestation); bad["resolved_env"]["AAYS_IOD25_V2_CSV"] = str(repo / "missing.csv"); check("bindings_reject_missing_iod", not m.attestation_bindings(bad)["pass"])
    bad = copy.deepcopy(attestation); bad["resolved_env"]["AAYS_MPS_LSOA_CSV"] = str(repo / "missing2.csv"); check("bindings_reject_missing_mps", not m.attestation_bindings(bad)["pass"])
    bad = copy.deepcopy(attestation); bad["provenance_manifest"]["sources"]["police_latest"]["parsed"] = {}; check("bindings_reject_missing_month", not m.attestation_bindings(bad)["pass"])

    sample_rows = [{"parcel_id": pid, "accuracy_score_4": 3, "official_api_http_status": 200, "official_api_sha256": "a", "output_semantics": "AREA_LEVEL_PROXY", "parcel_measurement": False} for pid in m.SAMPLE_IDS]
    sample = {"slot_id": m.SLOT_ID, "rows": sample_rows, "canonical_guard": {"pass": True, "observed_blob_sha": m.REQUIRED_BLOB_SHA}, "official_api_latest": {"month": "2026-05"}, "fake_data": False, "final_ready": False}
    check("sample_valid", m.sample_binding(sample, bindings)["pass"])
    sample_mutations = {
        "wrong_slot": lambda p: p.update(slot_id="other"),
        "wrong_ids": lambda p: p["rows"][0].update(parcel_id="parcel_1"),
        "wrong_blob": lambda p: p["canonical_guard"].update(observed_blob_sha="bad"),
        "stale_month": lambda p: p["official_api_latest"].update(month="2026-04"),
        "missing_api_sha": lambda p: p["rows"][0].update(official_api_sha256=None),
        "parcel_measurement": lambda p: p["rows"][0].update(parcel_measurement=True),
        "wrong_semantics": lambda p: p["rows"][0].update(output_semantics="PARCEL"),
        "fake": lambda p: p.update(fake_data=True),
        "final": lambda p: p.update(final_ready=True),
    }
    for name, mutate in sample_mutations.items():
        bad = copy.deepcopy(sample); mutate(bad)
        check(f"sample_reject_{name}", not m.sample_binding(bad, bindings)["pass"])

    rows = [{"parcel_id": pid, "accuracy_score_4": 4, "official_api_http_status": 200, "official_api_sha256": "api", "iod25_v2_join_pass": True, "mps_lsoa_join_pass": True, "output_semantics": "AREA_LEVEL_PROXY", "parcel_measurement": False} for pid in m.EXPECTED_IDS]
    payload = {
        "slot_id": m.SLOT_ID,
        "rows": rows,
        "canonical_rows": 300,
        "canonical_guard": {"pass": True, "observed_blob_sha": m.REQUIRED_BLOB_SHA},
        "official_api_latest": {"month": "2026-05"},
        "iod25": {"status": "LOADED", "sha256": bindings["iod_sha256"]},
        "mps_lsoa": {"status": "LOADED", "sha256": bindings["mps_sha256"]},
        "output_semantics": "AREA_LEVEL_PROXY",
        "fake_data": False,
        "final_ready": False,
    }
    csv_path = out / "security_public_safety_2_hydrated_300_latest.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["parcel_id"]); writer.writeheader(); writer.writerows([{"parcel_id": value} for value in m.EXPECTED_IDS])
    geo_path = out / "security_public_safety_2_hydrated_300_latest.geojson"
    geo_path.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": None, "properties": {"parcel_id": value}} for value in m.EXPECTED_IDS]}), encoding="utf-8")
    html_path = web / "progress.html"; html_path.write_text("<html><table><tbody></tbody></table></html>", encoding="utf-8")
    payload["artifacts"] = {"csv_sha256": m.sha256_file(csv_path), "geojson_sha256": m.sha256_file(geo_path), "html_sha256": m.sha256_file(html_path), "parity_pass": True}
    json_path = out / "security_public_safety_2_hydrated_300_latest.json"; web_json = web / "hydrated_300_latest.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"; json_path.write_text(text, encoding="utf-8"); web_json.write_text(text, encoding="utf-8")
    good = m.hydration_binding(repo, payload, bindings)
    check("hydration_valid", good["pass"])
    check("hydration_check_count", good["total"] >= 25)
    hydration_mutations = {
        "wrong_slot": lambda p: p.update(slot_id="other"),
        "rows_299": lambda p: p["rows"].pop(),
        "ids_wrong": lambda p: p["rows"][0].update(parcel_id="parcel_1"),
        "canonical_299": lambda p: p.update(canonical_rows=299),
        "wrong_blob": lambda p: p["canonical_guard"].update(observed_blob_sha="bad"),
        "stale_month": lambda p: p["official_api_latest"].update(month="2026-04"),
        "iod_sha": lambda p: p["iod25"].update(sha256="bad"),
        "mps_sha": lambda p: p["mps_lsoa"].update(sha256="bad"),
        "iod_status": lambda p: p["iod25"].update(status="BAD"),
        "mps_status": lambda p: p["mps_lsoa"].update(status="BAD"),
        "parity_false": lambda p: p["artifacts"].update(parity_pass=False),
        "score4_api": lambda p: p["rows"][0].update(official_api_sha256=None),
        "score4_iod": lambda p: p["rows"][0].update(iod25_v2_join_pass=False),
        "score4_mps": lambda p: p["rows"][0].update(mps_lsoa_join_pass=False),
        "semantics": lambda p: p["rows"][0].update(output_semantics="PARCEL"),
        "parcel_measurement": lambda p: p["rows"][0].update(parcel_measurement=True),
        "fake": lambda p: p.update(fake_data=True),
        "final": lambda p: p.update(final_ready=True),
    }
    for name, mutate in hydration_mutations.items():
        bad = copy.deepcopy(payload); mutate(bad)
        check(f"hydration_reject_{name}", not m.hydration_binding(repo, bad, bindings)["pass"])
    original_csv = csv_path.read_bytes(); csv_path.write_bytes(original_csv + b"\n"); check("hydration_reject_csv_hash", not m.hydration_binding(repo, payload, bindings)["pass"]); csv_path.write_bytes(original_csv)
    original_geo = geo_path.read_bytes(); geo_path.write_bytes(original_geo + b" "); check("hydration_reject_geo_hash", not m.hydration_binding(repo, payload, bindings)["pass"]); geo_path.write_bytes(original_geo)
    original_html = html_path.read_bytes(); html_path.write_bytes(original_html + b" "); check("hydration_reject_html_hash", not m.hydration_binding(repo, payload, bindings)["pass"]); html_path.write_bytes(original_html)
    web_json.write_text("{}", encoding="utf-8"); check("hydration_reject_web_json_mismatch", not m.hydration_binding(repo, payload, bindings)["pass"]); web_json.write_text(text, encoding="utf-8")

    now = datetime.now(timezone.utc)
    receipt = {"slot_id": m.SLOT_ID, "state": "PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", "exit_code": 0, "generated_at": now.isoformat(), "completed_at": (now + timedelta(seconds=1)).isoformat(), "steps": [{"name": "ACCEPTANCE_GATE", "pass": True}], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    check("receipt_valid", m.validate_pipeline_receipt(receipt, now - timedelta(seconds=1))["pass"])
    receipt_mutations = {
        "missing_exit": lambda p: p.pop("exit_code"),
        "exit_nonzero": lambda p: p.update(exit_code=1),
        "stale_generated": lambda p: p.update(generated_at=(now - timedelta(hours=1)).isoformat()),
        "stale_completed": lambda p: p.update(completed_at=(now - timedelta(hours=1)).isoformat()),
        "missing_acceptance": lambda p: p.update(steps=[]),
        "missing_business": lambda p: p.pop("actual_business_rows_written"),
        "business_nonzero": lambda p: p.update(actual_business_rows_written=1),
        "fake": lambda p: p.update(fake_data=True),
        "final": lambda p: p.update(final_ready=True),
        "wrong_state": lambda p: p.update(state="BAD"),
        "wrong_slot": lambda p: p.update(slot_id="other"),
    }
    for name, mutate in receipt_mutations.items():
        bad = copy.deepcopy(receipt); mutate(bad)
        check(f"receipt_reject_{name}", not m.validate_pipeline_receipt(bad, now - timedelta(seconds=1))["pass"])
    bad = copy.deepcopy(receipt); bad["steps"][0]["pass"] = False
    check("receipt_reject_failed_acceptance", not m.validate_pipeline_receipt(bad, now - timedelta(seconds=1))["pass"])
    victim = out / "victim.json"; victim.write_text("x", encoding="utf-8")
    removed = m.invalidate([victim, out / "missing"])
    check("invalidate_removed_one", len(removed) == 1)
    check("invalidate_file_absent", not victim.exists())
    check("invalidate_sha_recorded", bool(removed[0].get("sha256")))

result = {"schema_version": 1, "slot_id": m.SLOT_ID, "test_type": "SOURCE_BOUND_RESUME_V4_SELFTEST", "cases": cases, "passed": sum(item["pass"] for item in cases), "total": len(cases), "pass": all(item["pass"] for item in cases), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["pass"] else 1)
