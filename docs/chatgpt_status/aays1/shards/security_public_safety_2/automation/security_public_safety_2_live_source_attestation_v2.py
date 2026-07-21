from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
IOD25_FILE_URL = "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
CACHE_REL = Path("docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/official_source_cache")
PROVENANCE_REL = Path("docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_official_source_provenance_latest.json")
BOOTSTRAP_REL = Path("docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_official_source_manifest_latest.json")
OUTPUT_REL = Path("docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_live_source_attestation_latest.json")
MAX_AGE_SECONDS = 1800
MONTHS = {name.lower(): index for index, name in enumerate(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"), 1)}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def time_monotonic() -> float:
    import time
    return time.monotonic()

def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time_monotonic()
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "elapsed_seconds": round(time_monotonic() - started, 3), "pass": completed.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": command, "returncode": None, "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "elapsed_seconds": round(time_monotonic() - started, 3), "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "elapsed_seconds": round(time_monotonic() - started, 3), "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}

def is_https(url: str | None) -> bool:
    return bool(url and urlparse(url).scheme == "https" and urlparse(url).hostname)

def month_key(text: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\s*([A-Za-z]{3})\s+(\d{4})\s*", text)
    if match and match.group(1).lower() in MONTHS:
        return int(match.group(2)), MONTHS[match.group(1).lower()]
    match = re.fullmatch(r"\s*(\d{4})[-_/ ]?(0[1-9]|1[0-2])\s*", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

def period_bounds(text: str | None) -> tuple[tuple[int, int], tuple[int, int]] | None:
    if not text:
        return None
    match = re.search(r"([A-Za-z]{3}\s+\d{4})\s*[–-]\s*([A-Za-z]{3}\s+\d{4})", text)
    if not match:
        return None
    start, end = month_key(match.group(1)), month_key(match.group(2))
    return (start, end) if start and end else None

def header_bounds(headers: list[str]) -> tuple[tuple[int, int], tuple[int, int]] | None:
    months = sorted({value for header in headers if (value := month_key(str(header))) is not None})
    return (months[0], months[-1]) if months else None

def validate(repo: Path, provenance: dict[str, Any], bootstrap: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    checks: dict[str, bool] = {}
    detail: dict[str, Any] = {}
    checks["provenance_pass"] = provenance.get("pass") is True
    checks["bootstrap_pass"] = bootstrap.get("pass") is True
    checks["provenance_contract"] = (provenance.get("contract") or {}).get("pass") is True
    checks["bootstrap_contract"] = (bootstrap.get("contract") or {}).get("pass") is True
    pt = parse_time(provenance.get("generated_at"))
    bt = parse_time(bootstrap.get("generated_at"))
    checks["timestamps_parse"] = pt is not None and bt is not None
    checks["bootstrap_after_provenance"] = bool(pt and bt and bt >= pt)
    checks["current_run_fresh"] = bool(bt and 0 <= (now - bt).total_seconds() <= MAX_AGE_SECONDS)

    sources = bootstrap.get("sources") or {}
    iod = sources.get("iod25_file7_v2") or {}
    mps = sources.get("mps_lsoa") or {}
    for name, source in (("iod", iod), ("mps", mps)):
        path = Path(str(source.get("path") or ""))
        validation = source.get("validation") or {}
        http = source.get("http") or {}
        checks[f"{name}_source_pass"] = source.get("pass") is True
        checks[f"{name}_live_download"] = source.get("method") == "download"
        checks[f"{name}_path_in_slot_cache"] = path.is_absolute() and CACHE_REL.as_posix().lower() in path.as_posix().lower()
        checks[f"{name}_file_exists"] = path.is_file()
        observed_sha = sha256_file(path) if path.is_file() else None
        detail[f"{name}_observed_sha256"] = observed_sha
        checks[f"{name}_sha_matches_validation"] = bool(observed_sha and observed_sha == validation.get("sha256"))
        checks[f"{name}_sha_matches_http"] = bool(observed_sha and observed_sha == http.get("sha256"))
        checks[f"{name}_http_200"] = http.get("http_status") == 200
        checks[f"{name}_final_https"] = is_https(http.get("final_url"))
        checks[f"{name}_nonempty"] = path.is_file() and path.stat().st_size > 0

    checks["iod_requested_url_exact"] = iod.get("url") == IOD25_FILE_URL
    checks["iod_final_host_official"] = urlparse(str((iod.get("http") or {}).get("final_url") or "")).hostname == "assets.publishing.service.gov.uk"
    discovery = bootstrap.get("mps_discovery") or {}
    checks["mps_discovery_pass"] = discovery.get("pass") is True
    checks["mps_selected_url_bound"] = bool(discovery.get("selected_url") and discovery.get("selected_url") == mps.get("url"))
    checks["mps_selected_https"] = is_https(discovery.get("selected_url"))

    p_sources = provenance.get("sources") or {}
    police_parsed = ((p_sources.get("police_latest") or {}).get("parsed") or {})
    iod_parsed = ((p_sources.get("iod25_page") or {}).get("parsed") or {})
    mps_parsed = ((p_sources.get("mps_page") or {}).get("parsed") or {})
    checks["police_latest_month_parse"] = bool(re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])-01", str(police_parsed.get("latest_date") or "")))
    checks["iod_v2_page_contract"] = iod_parsed.get("v2_required") is True and iod_parsed.get("files_1_9_corrected") is True
    expected_period = period_bounds(mps_parsed.get("latest_period"))
    observed_period = header_bounds(list(((mps.get("validation") or {}).get("headers") or [])))
    detail["expected_mps_period"] = expected_period
    detail["observed_mps_period"] = observed_period
    checks["mps_period_parse"] = expected_period is not None
    checks["mps_csv_month_headers"] = observed_period is not None
    checks["mps_period_matches_current_page"] = expected_period is not None and observed_period == expected_period
    checks["mps_connect_caveat"] = mps_parsed.get("connect_caveat") is True

    passed = all(checks.values())
    return {"pass": passed, "checks": checks, "passed": sum(checks.values()), "total": len(checks), "detail": detail, "blocker": None if passed else "LIVE_OFFICIAL_SOURCE_ATTESTATION_FAILED"}

def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or Path.cwd()).resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    output = repo / OUTPUT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "attestation_version": "2.0-live-source-bound", "generated_at": utc_now(), "steps": [], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now(), "pass": code == 0})
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)

    env = os.environ.copy()
    for name in ("AAYS_IOD25_V2_CSV", "AAYS_IOD25_V2_URL", "AAYS_MPS_LSOA_CSV", "AAYS_MPS_LSOA_URL"):
        env.pop(name, None)
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})
    shard = repo / "docs/chatgpt_status/aays1/shards" / SLOT_ID
    provenance_script = shard / "automation/security_public_safety_2_official_source_provenance.py"
    bootstrap_script = shard / "automation/security_public_safety_2_official_source_bootstrap.py"

    result = run_command([sys.executable, str(provenance_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.timeout)], repo, env, args.timeout + 120)
    receipt["steps"].append({"name": "LIVE_PROVENANCE", **result})
    provenance_path = repo / PROVENANCE_REL
    if not result["pass"] or not provenance_path.is_file():
        return finish("BLOCKED_LIVE_PROVENANCE", "PROVENANCE_FAILED_OR_MISSING", 3)
    provenance = read_json(provenance_path)

    cache = repo / CACHE_REL
    removed: list[dict[str, Any]] = []
    for name in ("File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators_v2.csv", "MPS_LSOA_Level_Crime_latest.csv"):
        path = cache / name
        if path.is_file():
            removed.append({"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
            path.unlink()
    receipt["cache_removed_before_live_download"] = removed

    result = run_command([sys.executable, str(bootstrap_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.timeout)], repo, env, args.timeout * 3 + 180)
    receipt["steps"].append({"name": "LIVE_BOOTSTRAP", **result})
    bootstrap_path = repo / BOOTSTRAP_REL
    if not result["pass"] or not bootstrap_path.is_file():
        return finish("BLOCKED_LIVE_BOOTSTRAP", "BOOTSTRAP_FAILED_OR_MISSING", 4)
    bootstrap = read_json(bootstrap_path)
    attestation = validate(repo, provenance, bootstrap)
    receipt["attestation"] = attestation
    receipt["provenance_manifest"] = provenance
    receipt["bootstrap_manifest"] = bootstrap
    receipt["resolved_env"] = bootstrap.get("resolved_env") or {}
    if not attestation["pass"]:
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION", attestation.get("blocker"), 5)
    return finish("LIVE_SOURCE_ATTESTATION_PASSED", None, 0)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()

if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "attestation_version": "2.0-live-source-bound", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
