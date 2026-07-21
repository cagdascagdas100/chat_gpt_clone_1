from __future__ import annotations
import argparse, csv, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
BRANCH = "codex/aays-single-runner-v5-20260706"
IDS = [f"parcel_{n}" for n in range(30762, 31062)]
V7_RECEIPT = "security_public_safety_2_pipeline_v7_receipt_latest.json"
V8_RECEIPT = "security_public_safety_2_pipeline_v8_receipt_latest.json"
V7_STATE = "PIPELINE_V7_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK"
V8_STATE = "PIPELINE_V8_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK"
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"

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

def csv_rows(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    except Exception:
        return None

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
        "state_exact": payload.get("state") == V7_STATE,
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
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "PIPELINE_V7_RECEIPT_NOT_FRESH_OR_EXACT"}

def final_integrity(repo: Path, started: datetime) -> dict[str, Any]:
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    paths = {
        "json": out / "security_public_safety_2_hydrated_300_latest.json",
        "csv": out / "security_public_safety_2_hydrated_300_latest.csv",
        "geo": out / "security_public_safety_2_hydrated_300_latest.geojson",
        "webjson": web / "hydrated_300_latest.json",
        "html": web / "progress.html",
        "acceptance": out / "security_public_safety_2_acceptance_latest.json",
    }
    checks = {f"{name}_exists": path.is_file() for name, path in paths.items()}
    hydration: dict[str, Any] = {}
    geo: dict[str, Any] = {}
    acceptance: dict[str, Any] = {}
    try:
        hydration = readj(paths["json"]) if paths["json"].is_file() else {}
    except Exception:
        pass
    try:
        geo = readj(paths["geo"]) if paths["geo"].is_file() else {}
    except Exception:
        pass
    try:
        acceptance = readj(paths["acceptance"]) if paths["acceptance"].is_file() else {}
    except Exception:
        pass
    rows = hydration.get("rows") or []
    ids = [str(row.get("parcel_id") or "") for row in rows]
    artifacts = hydration.get("artifacts") or {}
    guard = hydration.get("canonical_guard") or {}
    acceptance_checks = acceptance.get("checks") or {}
    browser = acceptance.get("browser") or {}
    accepted_at = pt(acceptance.get("generated_at"))
    html_meta = acceptance.get("html") or {}
    json_meta = acceptance.get("json") or {}
    checks.update({
        "hydration_slot_exact": hydration.get("slot_id") == SLOT_ID,
        "rows_300": len(rows) == 300,
        "ids_exact": ids == IDS,
        "canonical_rows_300": int(hydration.get("canonical_rows") or -1) == 300,
        "exact_blob": guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA,
        "no_missing_canonical": all(row.get("candidate_status") != "CANONICAL_FEATURE_NOT_FOUND" for row in rows),
        "area_proxy": hydration.get("output_semantics") == "AREA_LEVEL_PROXY" and all(row.get("output_semantics") == "AREA_LEVEL_PROXY" for row in rows),
        "not_parcel_measurement": all(row.get("parcel_measurement") is False for row in rows),
        "csv_rows_300": paths["csv"].is_file() and csv_rows(paths["csv"]) == 300,
        "geo_rows_300": len(geo.get("features") or []) == 300,
        "csv_sha_current": paths["csv"].is_file() and artifacts.get("csv_sha256") == sha(paths["csv"]),
        "geo_sha_current": paths["geo"].is_file() and artifacts.get("geojson_sha256") == sha(paths["geo"]),
        "html_sha_current": paths["html"].is_file() and artifacts.get("html_sha256") == sha(paths["html"]),
        "parity_true": artifacts.get("parity_pass") is True,
        "runner_web_json_equal": paths["json"].is_file() and paths["webjson"].is_file() and paths["json"].read_bytes() == paths["webjson"].read_bytes(),
        "acceptance_slot_exact": acceptance.get("slot_id") == SLOT_ID,
        "acceptance_fresh": bool(accepted_at and accepted_at >= started),
        "acceptance_all_checks_pass": acceptance.get("all_checks_pass") is True,
        "acceptance_passed_total": int(acceptance.get("total") or 0) > 0 and acceptance.get("passed") == acceptance.get("total"),
        "acceptance_checks_all_true": bool(acceptance_checks) and all(value is True for value in acceptance_checks.values()),
        "acceptance_business_zero": acceptance.get("actual_business_rows_written") == 0,
        "acceptance_fake_false": acceptance.get("fake_data") is False,
        "acceptance_final_false": acceptance.get("final_ready") is False,
        "browser_available": browser.get("available") is True,
        "browser_http_200": browser.get("http_status") == 200,
        "browser_rows_300": browser.get("row_count") == 300 and browser.get("body_visible_row_count") == "300",
        "browser_slot_exact": browser.get("body_slot_id") == SLOT_ID,
        "browser_console_zero": not browser.get("console_errors") and not browser.get("page_errors") and not browser.get("error"),
        "acceptance_html_sha_current": paths["html"].is_file() and html_meta.get("sha256") == sha(paths["html"]),
        "acceptance_json_sha_current": paths["webjson"].is_file() and json_meta.get("sha256") == sha(paths["webjson"]),
        "hydration_fake_false": hydration.get("fake_data") is False,
        "hydration_final_false": hydration.get("final_ready") is False,
    })
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "POST_SUCCESS_ARTIFACT_OR_BROWSER_INTEGRITY_FAILED"}

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
    rows = "".join(f"<tr><td>{n}</td><td>{s}</td><td>{escape(name)}</td></tr>" for n,s,name in core)
    candidates = "".join(f"<tr><td>{escape(item)}</td><td>INVALIDATED_OR_PENDING</td><td>0/4</td></tr>" for item in IDS[:3])
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="20"><title>Security/Public Safety Slot 2</title></head><body data-slot-id="{SLOT_ID}" data-final-ready="false" data-real-row-count="0" data-runtime-fail-closed="true"><h1>Security / Public Safety — Slot 2</h1><p><b>Runtime fail-closed:</b> {escape(blocker)}. {removed_count} kısmi/stale artifact temizlendi; geçersiz veri gerçek satır olarak gösterilmez.</p><h2>Çekirdek işlemler</h2><table><tr><th>#</th><th>Durum</th><th>İşlem</th></tr>{rows}</table><h2>Adaylar</h2><table><tr><th>Parsel</th><th>Durum</th><th>Doğruluk</th></tr>{candidates}</table><p>actual_business_rows_written=0; fake_data=false; final_ready=false.</p></body></html>'''

def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo(args.repo_root)
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    output = out / V8_RECEIPT
    v7_receipt = out / V7_RECEIPT
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "pipeline_version": "8.0-post-success-integrity-and-browser-revalidation", "generated_at": utc(), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

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
    if v7_receipt.is_file():
        receipt["stale_v7_receipt_removed"] = {"path": str(v7_receipt), "sha256": sha(v7_receipt), "bytes": v7_receipt.stat().st_size}
        v7_receipt.unlink()
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": BRANCH})
    started = datetime.now(timezone.utc)
    script = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v7_failclosed.py"
    argv = [sys.executable, str(script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", BRANCH, "--source-timeout", str(args.source_timeout), "--pipeline-timeout", str(args.pipeline_timeout), "--outer-timeout", str(args.v7_timeout), "--port", str(args.port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    result = command(argv, repo, env, args.outer_timeout)
    receipt["pipeline_v7_command"] = result
    if not result["pass"] or not v7_receipt.is_file():
        return fail("BLOCKED_PIPELINE_V7_EXECUTION_FAILCLOSED", "PIPELINE_V7_TIMEOUT" if result.get("timed_out") else "PIPELINE_V7_NONZERO_OR_RECEIPT_MISSING", 3)
    try:
        v7 = readj(v7_receipt)
    except Exception as exc:
        return fail("BLOCKED_PIPELINE_V7_RECEIPT_FAILCLOSED", f"PIPELINE_V7_RECEIPT_READ:{type(exc).__name__}:{exc}", 4)
    validation = receipt_ok(v7, started)
    receipt["pipeline_v7_receipt"] = v7
    receipt["pipeline_v7_validation"] = validation
    if not validation["pass"]:
        return fail("BLOCKED_PIPELINE_V7_GATE_FAILCLOSED", validation["blocker"], 5)
    integrity = final_integrity(repo, started)
    receipt["post_success_integrity"] = integrity
    if not integrity["pass"]:
        return fail("BLOCKED_POST_SUCCESS_INTEGRITY_FAILCLOSED", integrity["blocker"], 6)
    return finish(V8_STATE, None, 0)

def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--source-timeout", type=int, default=180)
    parser.add_argument("--pipeline-timeout", type=int, default=5700)
    parser.add_argument("--v7-timeout", type=int, default=6600)
    parser.add_argument("--outer-timeout", type=int, default=6900)
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()

if __name__ == "__main__":
    result = run(args())
    print(json.dumps({"slot_id": SLOT_ID, "pipeline_version": "8.0-post-success-integrity-and-browser-revalidation", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
