from __future__ import annotations
import csv, datetime, importlib.util, json, shutil, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "security_public_safety_2_runner_pipeline_v8_integrity.py"

def load():
    spec = importlib.util.spec_from_file_location("slot2_v8", TARGET)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main() -> dict:
    m = load()
    temp = Path(tempfile.mkdtemp(prefix="slot2_v8_"))
    cases = []
    def add(name, value): cases.append({"name": name, "pass": bool(value)})
    try:
        out = temp / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
        auto = temp / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation"
        web = temp / "england_map_web/data/aays_18_slots/security_public_safety_2"
        out.mkdir(parents=True); auto.mkdir(parents=True); web.mkdir(parents=True)
        rows = [{"parcel_id": f"parcel_{n}", "candidate_status": "CANONICAL_MATCH", "output_semantics": "AREA_LEVEL_PROXY", "parcel_measurement": False} for n in range(30762, 31062)]
        csv_path = out / "security_public_safety_2_hydrated_300_latest.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["parcel_id"]); writer.writeheader()
            writer.writerows([{"parcel_id": row["parcel_id"]} for row in rows])
        geo_path = out / "security_public_safety_2_hydrated_300_latest.geojson"
        geo_path.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"parcel_id": row["parcel_id"]}, "geometry": None} for row in rows]}), encoding="utf-8")
        html_path = web / "progress.html"
        html_path.write_text('<body data-slot-id="security_public_safety_2" data-visible-row-count="300" data-final-ready="false"><table><tbody>' + "".join("<tr></tr>" for _ in rows) + "</tbody></table></body>", encoding="utf-8")
        hydration = {"slot_id": m.SLOT_ID, "rows": rows, "canonical_rows": 300, "canonical_guard": {"pass": True, "observed_blob_sha": m.REQUIRED_BLOB_SHA}, "artifacts": {}, "output_semantics": "AREA_LEVEL_PROXY", "fake_data": False, "final_ready": False}
        hydration["artifacts"] = {"csv_sha256": m.sha(csv_path), "geojson_sha256": m.sha(geo_path), "html_sha256": m.sha(html_path), "parity_pass": True}
        json_path = out / "security_public_safety_2_hydrated_300_latest.json"
        json_path.write_text(json.dumps(hydration), encoding="utf-8")
        web_json = web / "hydrated_300_latest.json"; web_json.write_bytes(json_path.read_bytes())
        started = datetime.datetime.now(datetime.timezone.utc)
        acceptance = {"slot_id": m.SLOT_ID, "generated_at": (started + datetime.timedelta(seconds=1)).isoformat().replace("+00:00", "Z"), "all_checks_pass": True, "passed": 2, "total": 2, "checks": {"a": True, "b": True}, "actual_business_rows_written": 0, "fake_data": False, "final_ready": False, "browser": {"available": True, "http_status": 200, "row_count": 300, "body_visible_row_count": "300", "body_slot_id": m.SLOT_ID, "console_errors": [], "page_errors": [], "error": None}, "html": {"sha256": m.sha(html_path)}, "json": {"sha256": m.sha(web_json)}}
        acceptance_path = out / "security_public_safety_2_acceptance_latest.json"
        acceptance_path.write_text(json.dumps(acceptance), encoding="utf-8")
        result = m.final_integrity(temp, started)
        add("integrity_valid", result["pass"]); add("integrity_check_count_ge_35", result["total"] >= 35)
        original_acceptance = json.loads(acceptance_path.read_text())
        mutations = [
            ("reject_acceptance_false", lambda item: item.update(all_checks_pass=False)),
            ("reject_browser_error", lambda item: item["browser"].update(error="x")),
            ("reject_console_error", lambda item: item["browser"].update(console_errors=["x"])),
            ("reject_browser_rows", lambda item: item["browser"].update(row_count=299)),
            ("reject_html_sha", lambda item: item["html"].update(sha256="bad")),
            ("reject_json_sha", lambda item: item["json"].update(sha256="bad")),
            ("reject_stale_acceptance", lambda item: item.update(generated_at="2020-01-01T00:00:00Z")),
        ]
        for name, mutate in mutations:
            item = json.loads(json.dumps(original_acceptance)); mutate(item)
            acceptance_path.write_text(json.dumps(item), encoding="utf-8")
            add(name, not m.final_integrity(temp, started)["pass"])
        acceptance_path.write_text(json.dumps(original_acceptance), encoding="utf-8")
        original_hydration = json.loads(json_path.read_text())
        hydration_mutations = [
            ("reject_ids", lambda item: item["rows"][0].update(parcel_id="bad")),
            ("reject_canonical_299", lambda item: item.update(canonical_rows=299)),
            ("reject_blob", lambda item: item["canonical_guard"].update(observed_blob_sha="bad")),
            ("reject_parity", lambda item: item["artifacts"].update(parity_pass=False)),
        ]
        for name, mutate in hydration_mutations:
            item = json.loads(json.dumps(original_hydration)); mutate(item)
            json_path.write_text(json.dumps(item), encoding="utf-8"); web_json.write_bytes(json_path.read_bytes())
            add(name, not m.final_integrity(temp, started)["pass"])
        json_path.write_text(json.dumps(original_hydration), encoding="utf-8"); web_json.write_bytes(json_path.read_bytes())
        web_json.write_text("{}", encoding="utf-8"); add("reject_web_mismatch", not m.final_integrity(temp, started)["pass"]); web_json.write_bytes(json_path.read_bytes())
        csv_path.write_text(csv_path.read_text(encoding="utf-8") + "parcel_extra\n", encoding="utf-8")
        add("reject_csv_tamper", not m.final_integrity(temp, started)["pass"])
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["parcel_id"]); writer.writeheader()
            writer.writerows([{"parcel_id": row["parcel_id"]} for row in rows])
        fresh = (started + datetime.timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        receipt = {"slot_id": m.SLOT_ID, "state": m.V7_STATE, "pass": True, "exit_code": 0, "generated_at": fresh, "completed_at": fresh, "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
        add("receipt_valid", m.receipt_ok(receipt, started)["pass"])
        for name, key, value in [
            ("receipt_wrong_slot", "slot_id", "x"), ("receipt_wrong_state", "state", "x"),
            ("receipt_nonzero", "exit_code", 1), ("receipt_business", "actual_business_rows_written", 1),
            ("receipt_fake", "fake_data", True), ("receipt_final", "final_ready", True),
            ("receipt_stale", "generated_at", "2020-01-01T00:00:00Z"),
        ]:
            item = dict(receipt); item[key] = value
            add(name, not m.receipt_ok(item, started)["pass"])
        (out / "security_public_safety_2_pipeline_v6_receipt_latest.json").write_text("x", encoding="utf-8")
        (out / "security_public_safety_2_pipeline_v7_receipt_latest.json").write_text("x", encoding="utf-8")
        removed = m.cleanup(temp)
        add("cleanup_v6", not (out / "security_public_safety_2_pipeline_v6_receipt_latest.json").exists())
        add("cleanup_v7", not (out / "security_public_safety_2_pipeline_v7_receipt_latest.json").exists())
        add("cleanup_count", len(removed) >= 2)
        fallback = m.failclosed_html("X", 2)
        add("fallback_zero", 'data-real-row-count="0"' in fallback)
        add("fallback_core_rows", "SHARED_RUNNER_PICKUP" in fallback and "BROWSER_ACCEPTANCE" in fallback)
        add("fallback_candidates", "parcel_30762" in fallback and "parcel_30764" in fallback)
        source = TARGET.read_text(encoding="utf-8")
        ps = (HERE / "security_public_safety_2_runner_pipeline_v8.ps1").read_text(encoding="utf-8")
        static = [
            ("static_wraps_v7", "runner_pipeline_v7_failclosed.py" in source),
            ("static_acceptance_revalidation", "acceptance_all_checks_pass" in source),
            ("static_browser_revalidation", "browser_console_zero" in source),
            ("static_csv_hash", "csv_sha_current" in source),
            ("static_geo_hash", "geo_sha_current" in source),
            ("static_html_hash", "html_sha_current" in source),
            ("static_acceptance_html_hash", "acceptance_html_sha_current" in source),
            ("static_acceptance_json_hash", "acceptance_json_sha_current" in source),
            ("static_cleanup_v6", "security_public_safety_2_pipeline_v6_receipt_latest.json" in source),
            ("static_cleanup_v7", "security_public_safety_2_pipeline_v7_receipt_latest.json" in source),
            ("static_no_global", "ai-tasks/current-task.json" not in source),
            ("static_no_push", "git push" not in source.lower()),
            ("static_no_commit", "git commit" not in source.lower()),
            ("static_no_runner_start", "start-process" not in ps.lower()),
            ("static_ps_slot", "WRONG_SLOT" in ps),
            ("static_ps_branch", "WRONG_BRANCH" in ps),
            ("static_ps_root", "AAYS_REPO_ROOT_NOT_RESOLVED" in ps),
        ]
        for name, value in static: add(name, value)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    passed = sum(1 for case in cases if case["pass"])
    return {"schema_version": 1, "slot_id": "security_public_safety_2", "test_type": "PIPELINE_V8_POST_SUCCESS_INTEGRITY_SELFTEST", "cases": cases, "passed": passed, "total": len(cases), "pass": passed == len(cases), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

if __name__ == "__main__":
    result = main()
    output = Path(__file__).resolve().parents[1] / "validation/security_public_safety_2_pipeline_v8_selftest_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slot_id": result["slot_id"], "passed": result["passed"], "total": result["total"], "pass": result["pass"], "final_ready": False}))
    raise SystemExit(0 if result["pass"] else 1)
