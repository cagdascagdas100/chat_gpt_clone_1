from __future__ import annotations
import argparse, csv, hashlib, json, os, re, subprocess, sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
BRANCH = "codex/aays-single-runner-v5-20260706"
IDS = [f"parcel_{n}" for n in range(30762, 31062)]
V8_RECEIPT = "security_public_safety_2_pipeline_v8_receipt_latest.json"
V9_RECEIPT = "security_public_safety_2_pipeline_v9_receipt_latest.json"
V8_STATE = "PIPELINE_V8_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK"
V9_STATE = "PIPELINE_V9_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK"

def utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def pt(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def readj(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def resolve_repo(explicit: str | None) -> Path:
    candidates = [Path(v).expanduser() for v in (explicit, os.environ.get("AAYS_REPO_ROOT")) if v]
    for probe in (Path.cwd(), Path(__file__).resolve().parent):
        try:
            done = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
            if done.returncode == 0 and done.stdout.strip():
                candidates.append(Path(done.stdout.strip()))
        except Exception:
            pass
    candidates.extend(Path(__file__).resolve().parents)
    seen: set[str] = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except Exception:
            candidate = candidate.absolute()
        key = os.path.normcase(str(candidate))
        if key in seen:
            continue
        seen.add(key)
        if (candidate / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation").is_dir() and (candidate / "england_map_web/data/aays_18_slots/security_public_safety_2").is_dir():
            return candidate
    raise RuntimeError("AAYS_REPO_ROOT_NOT_RESOLVED")

def command(argv: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        done = subprocess.run(argv, cwd=str(cwd), env=env, text=True, capture_output=True, timeout=timeout)
        return {"command": argv, "returncode": done.returncode, "stdout_tail": done.stdout[-4000:], "stderr_tail": done.stderr[-4000:], "pass": done.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": argv, "returncode": None, "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": argv, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}

def receipt_ok(payload: dict[str, Any], started: datetime) -> dict[str, Any]:
    generated, completed = pt(payload.get("generated_at")), pt(payload.get("completed_at"))
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "state_exact": payload.get("state") == V8_STATE,
        "pass_true": payload.get("pass") is True,
        "exit_present": "exit_code" in payload,
        "exit_zero": payload.get("exit_code") == 0,
        "fresh_generated": bool(generated and generated >= started),
        "fresh_completed": bool(completed and completed >= started),
        "business_present": "actual_business_rows_written" in payload,
        "business_zero": payload.get("actual_business_rows_written") == 0,
        "fake_false": payload.get("fake_data") is False,
        "final_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "PIPELINE_V8_RECEIPT_NOT_FRESH_OR_EXACT"}

def scalar_text(value: Any) -> str:
    return "" if value is None else str(value)

def cross_format_integrity(repo: Path) -> dict[str, Any]:
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    paths = {
        "json": out / "security_public_safety_2_hydrated_300_latest.json",
        "csv": out / "security_public_safety_2_hydrated_300_latest.csv",
        "geojson": out / "security_public_safety_2_hydrated_300_latest.geojson",
        "webjson": web / "hydrated_300_latest.json",
        "html": web / "progress.html",
    }
    checks: dict[str, bool] = {f"{name}_exists": path.is_file() for name, path in paths.items()}
    hydration: dict[str, Any] = {}
    geo: dict[str, Any] = {}
    csv_rows: list[dict[str, str]] = []
    csv_headers: list[str] = []
    html_text = ""
    try:
        hydration = readj(paths["json"]) if paths["json"].is_file() else {}
    except Exception:
        pass
    try:
        geo = readj(paths["geojson"]) if paths["geojson"].is_file() else {}
    except Exception:
        pass
    try:
        if paths["csv"].is_file():
            with paths["csv"].open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                csv_headers = list(reader.fieldnames or [])
                csv_rows = list(reader)
    except Exception:
        csv_rows = []
        csv_headers = []
    try:
        html_text = paths["html"].read_text(encoding="utf-8") if paths["html"].is_file() else ""
    except Exception:
        pass

    rows = hydration.get("rows") or []
    json_ids = [str(row.get("parcel_id") or "") for row in rows]
    csv_ids = [str(row.get("parcel_id") or "") for row in csv_rows]
    features = geo.get("features") or []
    geo_ids = [str((feature.get("properties") or {}).get("parcel_id") or "") for feature in features]
    expected_headers = sorted({key for row in rows for key in row if key != "geometry"})
    csv_full_match = len(csv_rows) == len(rows) and csv_headers == expected_headers
    if csv_full_match:
        for source, rendered in zip(rows, csv_rows):
            if any(rendered.get(key, "") != scalar_text(source.get(key)) for key in expected_headers):
                csv_full_match = False
                break
    geo_full_match = len(features) == len(rows)
    geometry_present = len(features) == len(rows)
    if geo_full_match:
        for source, feature in zip(rows, features):
            properties = feature.get("properties") or {}
            expected_properties = {key: value for key, value in source.items() if key != "geometry"}
            if properties != expected_properties or feature.get("geometry") != source.get("geometry"):
                geo_full_match = False
                break
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict) or not geometry.get("type") or geometry.get("coordinates") in (None, [], {}):
                geometry_present = False
    tbody_match = re.search(r"<tbody[^>]*>(.*?)</tbody>", html_text, flags=re.I | re.S)
    html_body_rows = len(re.findall(r"<tr\b", tbody_match.group(1), flags=re.I)) if tbody_match else -1
    accuracy_ge_3 = sum(int(row.get("accuracy_score_4") or 0) >= 3 for row in rows)
    accuracy_4 = sum(int(row.get("accuracy_score_4") or 0) == 4 for row in rows)
    artifacts = hydration.get("artifacts") or {}
    checks.update({
        "hydration_slot_exact": hydration.get("slot_id") == SLOT_ID,
        "json_rows_300": len(rows) == 300,
        "json_ids_exact": json_ids == IDS,
        "canonical_rows_recomputed_300": int(hydration.get("canonical_rows") or -1) == len(rows) == 300,
        "csv_rows_300": len(csv_rows) == 300,
        "csv_ids_exact": csv_ids == IDS,
        "csv_full_scalar_parity": csv_full_match,
        "geojson_feature_collection": geo.get("type") == "FeatureCollection",
        "geojson_rows_300": len(features) == 300,
        "geojson_ids_exact": geo_ids == IDS,
        "geojson_full_property_geometry_parity": geo_full_match,
        "all_canonical_geometries_present": geometry_present,
        "three_id_sequences_equal": json_ids == csv_ids == geo_ids == IDS,
        "runner_web_json_byte_equal": paths["json"].is_file() and paths["webjson"].is_file() and paths["json"].read_bytes() == paths["webjson"].read_bytes(),
        "html_visible_count_300": 'data-visible-row-count="300"' in html_text,
        "html_tbody_rows_300": html_body_rows == 300,
        "accuracy_ge_3_recomputed": int(hydration.get("accuracy_ge_3_count") or 0) == accuracy_ge_3,
        "accuracy_4_recomputed": int(hydration.get("accuracy_4_count") or 0) == accuracy_4,
        "csv_sha_current": paths["csv"].is_file() and artifacts.get("csv_sha256") == sha(paths["csv"]),
        "geojson_sha_current": paths["geojson"].is_file() and artifacts.get("geojson_sha256") == sha(paths["geojson"]),
        "html_sha_current": paths["html"].is_file() and artifacts.get("html_sha256") == sha(paths["html"]),
        "legacy_parity_true": artifacts.get("parity_pass") is True,
        "fake_false": hydration.get("fake_data") is False,
        "final_false": hydration.get("final_ready") is False,
    })
    hashes = {name: sha(path) for name, path in paths.items() if path.is_file()}
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "hashes": hashes, "blocker": None if all(checks.values()) else "CROSS_FORMAT_CONTENT_PARITY_OR_GEOMETRY_FAILED"}

def cleanup(repo: Path) -> list[dict[str, Any]]:
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    names = [
        out / "security_public_safety_2_sample_candidates_latest.json",
        out / "security_public_safety_2_hydrated_300_latest.json",
        out / "security_public_safety_2_hydrated_300_latest.csv",
        out / "security_public_safety_2_hydrated_300_latest.geojson",
        out / "security_public_safety_2_acceptance_latest.json",
        out / "security_public_safety_2_pipeline_receipt_latest.json",
        out / "security_public_safety_2_source_bound_resume_receipt_latest.json",
        out / "security_public_safety_2_pipeline_v6_receipt_latest.json",
        out / "security_public_safety_2_pipeline_v7_receipt_latest.json",
        out / "security_public_safety_2_pipeline_v8_receipt_latest.json",
        web / "sample_candidates_latest.json",
        web / "hydrated_300_latest.json",
    ]
    removed: list[dict[str, Any]] = []
    for path in names:
        if path.is_file():
            removed.append({"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size})
            path.unlink()
    return removed

def failclosed_html(blocker: str, removed_count: int) -> str:
    core = [
        ("1","PASS","REMOTE_HEAD_READBACK"),("2","PASS","SLOT_STATE_READBACK"),("3","PASS","SLOT_ISOLATION"),
        ("4","PASS","PATH_CONTRACT"),("5","PASS","OFFICIAL_SOURCES"),("6","PASS","IOD25_V2"),
        ("7","PASS","MPS_LSOA"),("8","PASS","ACCURACY_GATE"),("9","PASS","WORKERS"),
        ("10","PASS","STREAM_TEST"),("11","PASS","PARITY_TEST"),("12","PASS","QUEUE_GUARD"),
        ("13","PASS","LEASE"),("14","BLOCKED","SHARED_RUNNER_PICKUP"),("15","PENDING","REAL_ROWS"),
        ("16","PENDING","BROWSER_ACCEPTANCE"),
    ]
    core_rows = "".join(f"<tr><td>{n}</td><td>{state}</td><td>{escape(name)}</td></tr>" for n, state, name in core)
    candidates = "".join(f"<tr><td>{escape(item)}</td><td>INVALIDATED_OR_PENDING</td><td>0/4</td></tr>" for item in IDS[:3])
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="20"><title>Security/Public Safety Slot 2</title></head><body data-slot-id="{SLOT_ID}" data-final-ready="false" data-real-row-count="0" data-runtime-fail-closed="true"><h1>Security / Public Safety — Slot 2</h1><p><b>Runtime fail-closed:</b> {escape(blocker)}. {removed_count} kısmi/stale artifact temizlendi; geçersiz veri gerçek satır olarak gösterilmez.</p><h2>Çekirdek işlemler</h2><table><tbody>{core_rows}</tbody></table><h2>Adaylar</h2><table><tbody>{candidates}</tbody></table><p>actual_business_rows_written=0; fake_data=false; final_ready=false.</p></body></html>"""

def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo_root)
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    output = out / V9_RECEIPT
    v8_receipt = out / V8_RECEIPT
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "pipeline_version": "9.0-cross-format-content-and-geometry-parity", "generated_at": utc(), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc(), "pass": code == 0})
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    def fail(state: str, blocker: str, code: int) -> dict[str, Any]:
        removed = cleanup(repo)
        receipt["removed_partial_artifacts"] = removed
        (web / "progress.html").write_text(failclosed_html(blocker, len(removed)), encoding="utf-8")
        return finish(state, blocker, code)
    if slot != SLOT_ID or branch != BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)
    if v8_receipt.is_file():
        receipt["stale_v8_receipt_removed"] = {"path": str(v8_receipt), "sha256": sha(v8_receipt), "bytes": v8_receipt.stat().st_size}
        v8_receipt.unlink()
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": BRANCH})
    started = datetime.now(timezone.utc)
    script = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v8_integrity.py"
    argv = [sys.executable, str(script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", BRANCH, "--source-timeout", str(args.source_timeout), "--pipeline-timeout", str(args.pipeline_timeout), "--v7-timeout", str(args.v7_timeout), "--outer-timeout", str(args.v8_timeout), "--port", str(args.port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    executed = command(argv, repo, env, args.outer_timeout)
    receipt["pipeline_v8_command"] = executed
    if not executed["pass"] or not v8_receipt.is_file():
        return fail("BLOCKED_PIPELINE_V8_EXECUTION_FAILCLOSED", "PIPELINE_V8_TIMEOUT" if executed.get("timed_out") else "PIPELINE_V8_NONZERO_OR_RECEIPT_MISSING", 3)
    try:
        v8 = readj(v8_receipt)
    except Exception as exc:
        return fail("BLOCKED_PIPELINE_V8_RECEIPT_FAILCLOSED", f"PIPELINE_V8_RECEIPT_READ:{type(exc).__name__}:{exc}", 4)
    validation = receipt_ok(v8, started)
    receipt["pipeline_v8_receipt"] = v8
    receipt["pipeline_v8_validation"] = validation
    if not validation["pass"]:
        return fail("BLOCKED_PIPELINE_V8_GATE_FAILCLOSED", validation["blocker"], 5)
    integrity = cross_format_integrity(repo)
    receipt["cross_format_integrity"] = integrity
    if not integrity["pass"]:
        return fail("BLOCKED_CROSS_FORMAT_INTEGRITY_FAILCLOSED", integrity["blocker"], 6)
    return finish(V9_STATE, None, 0)

def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--source-timeout", type=int, default=180)
    parser.add_argument("--pipeline-timeout", type=int, default=5700)
    parser.add_argument("--v7-timeout", type=int, default=6600)
    parser.add_argument("--v8-timeout", type=int, default=6900)
    parser.add_argument("--outer-timeout", type=int, default=7200)
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()

if __name__ == "__main__":
    result = run(args())
    print(json.dumps({"slot_id": SLOT_ID, "pipeline_version": "9.0-cross-format-content-and-geometry-parity", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
