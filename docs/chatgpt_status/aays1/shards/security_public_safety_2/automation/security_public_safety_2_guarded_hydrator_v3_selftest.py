from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"


def run_command(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def fixture_repo(worker_text: str, *, ignore_override: bool = False) -> tuple[Path, str, Path]:
    root = Path(tempfile.mkdtemp(prefix="aays_slot2_guarded_v3_"))
    automation = root / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation"
    automation.mkdir(parents=True)
    shared = root / "docs/chatgpt_status/_shared/slots_18/security_public_safety_2"
    shared.mkdir(parents=True)
    for name in ("current_task_latest.json", "status_latest.json", "ownership_latest.json"):
        (shared / name).write_text("{}\n", encoding="utf-8")

    source = root / "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
    source.parent.mkdir(parents=True)
    source.write_text(
        '{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"security_parcel_id":"parcel_30762"},"geometry":{"type":"Point","coordinates":[0,0]}}]}',
        encoding="utf-8",
    )
    run_command(["git", "init"], cwd=root)
    run_command(["git", "config", "user.email", "selftest@example.com"], cwd=root)
    run_command(["git", "config", "user.name", "selftest"], cwd=root)
    run_command(["git", "add", "."], cwd=root)
    commit = run_command(["git", "commit", "-m", "fixture"], cwd=root)
    if commit.returncode != 0:
        raise RuntimeError(commit.stderr)
    run_command(["git", "branch", TARGET_BRANCH], cwd=root)
    blob = run_command(["git", "hash-object", str(source)], cwd=root).stdout.strip()
    source.unlink()

    worker = worker_text.replace("bb48164e7a0af78df875f30421a6a3068c43edb8", blob)
    worker_path = automation / "security_public_safety_2_batch_hydrate_v3_guarded.py"
    worker_path.write_text(worker, encoding="utf-8")

    fake_core = '''
from pathlib import Path
import argparse, os
REPO = Path(os.environ["AAYS_REPO_ROOT"])
OUT = REPO / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
WEB = REPO / "england_map_web/data/aays_18_slots/security_public_safety_2"
IGNORE_OVERRIDE = __IGNORE_OVERRIDE__
def load_base():
    class Base:
        SOURCES=[REPO/"wrong.geojson"]
    return Base
def parse_args():
    parser=argparse.ArgumentParser()
    return parser.parse_args()
def run(arguments):
    OUT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)
    base=load_base()
    source=(REPO/"wrong.geojson") if IGNORE_OVERRIDE else base.SOURCES[0]
    for path in [OUT/"security_public_safety_2_hydrated_300_latest.csv", OUT/"security_public_safety_2_hydrated_300_latest.geojson", WEB/"hydrated_300_latest.json"]:
        path.write_text("fixture", encoding="utf-8")
    return {"source_file":str(source),"canonical_rows":300,"accuracy_ge_3_count":300,"accuracy_4_count":300,"rows":[],"artifacts":{"parity_pass":True},"final_ready":False}
'''.replace("__IGNORE_OVERRIDE__", "True" if ignore_override else "False")
    (automation / "security_public_safety_2_batch_hydrate_v2.py").write_text(fake_core, encoding="utf-8")
    return root, blob, worker_path


def main() -> int:
    automation = Path(__file__).resolve().parent
    worker_path = automation / "security_public_safety_2_batch_hydrate_v3_guarded.py"
    worker_text = worker_path.read_text(encoding="utf-8")
    cases: list[dict[str, object]] = []

    def add(name: str, passed: bool, detail: str | None = None) -> None:
        item: dict[str, object] = {"name": name, "pass": bool(passed)}
        if detail is not None:
            item["detail"] = detail
        cases.append(item)

    compiled = run_command([sys.executable, "-m", "py_compile", str(worker_path)], cwd=automation)
    add("worker_py_compile", compiled.returncode == 0, None if compiled.returncode == 0 else compiled.stderr[-500:])

    add("uses_repo_root_resolver", "def resolve_repo_root()" in worker_text)
    add("sets_repo_env_before_core_import", 'os.environ["AAYS_REPO_ROOT"] = str(repo)' in worker_text)
    add("uses_core_parse_args", "core.parse_args()" in worker_text and "core.args()" not in worker_text)
    add("monkeypatches_core_load_base", "core.load_base = load_base_exact" in worker_text)
    add("sets_exact_base_sources", "base.SOURCES = [source]" in worker_text)
    add("streams_git_show_to_file", "def git_show_to_file" in worker_text and "stdout=output" in worker_text)
    add("does_not_capture_git_show_blob", 'git(repo, "show"' not in worker_text)
    add("verifies_runtime_source_override", "source_override_observed" in worker_text)
    add("clears_hydrated_outputs_on_failure", "clear_hydrated_outputs(repo)" in worker_text)
    add("no_git_push", '"push"' not in worker_text and "git push" not in worker_text.lower())
    add("no_git_commit", '"commit"' not in worker_text and "git commit" not in worker_text.lower())
    add("no_runner_start", "start-process" not in worker_text.lower() and "new_runner" not in worker_text.lower())
    add("final_ready_false", '"final_ready": False' in worker_text)

    root, blob, fixture_worker = fixture_repo(worker_text, ignore_override=False)
    env = os.environ.copy()
    env["AAYS_REPO_ROOT"] = str(root / "nonexistent")
    env["AAYS_SLOT_ID"] = SLOT_ID
    env["AAYS_TARGET_BRANCH"] = TARGET_BRANCH
    good = run_command([sys.executable, str(fixture_worker)], cwd=root, env=env)
    guard_path = root / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_exact_blob_guard_latest.json"
    guard = json.loads(guard_path.read_text(encoding="utf-8")) if guard_path.is_file() else {}
    canonical_guard = guard.get("canonical_guard") or {}
    add("dynamic_success_exit_zero", good.returncode == 0, None if good.returncode == 0 else (good.stdout + good.stderr)[-500:])
    add("dynamic_git_show_blob_exact", canonical_guard.get("observed_blob_sha") == blob)
    add("dynamic_stream_method", canonical_guard.get("materialization_method") == "git_show_stream_exact_blob")
    add("dynamic_source_override_observed", canonical_guard.get("source_override_observed") is True)
    add("dynamic_repo_root_falls_back_to_script", good.returncode == 0)

    bad_root, _, bad_worker = fixture_repo(worker_text, ignore_override=True)
    bad_env = os.environ.copy()
    bad_env["AAYS_REPO_ROOT"] = str(bad_root)
    bad_env["AAYS_SLOT_ID"] = SLOT_ID
    bad_env["AAYS_TARGET_BRANCH"] = TARGET_BRANCH
    bad = run_command([sys.executable, str(bad_worker)], cwd=bad_root, env=bad_env)
    bad_out = bad_root / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    bad_web = bad_root / "england_map_web/data/aays_18_slots/security_public_safety_2"
    add("dynamic_wrong_source_rejected", bad.returncode == 5, None if bad.returncode == 5 else (bad.stdout + bad.stderr)[-500:])
    add("dynamic_wrong_source_json_removed", not (bad_out / "security_public_safety_2_hydrated_300_latest.json").exists())
    add("dynamic_wrong_source_csv_removed", not (bad_out / "security_public_safety_2_hydrated_300_latest.csv").exists())
    add("dynamic_wrong_source_geojson_removed", not (bad_out / "security_public_safety_2_hydrated_300_latest.geojson").exists())
    add("dynamic_wrong_source_web_json_removed", not (bad_web / "hydrated_300_latest.json").exists())

    passed = sum(bool(item["pass"]) for item in cases)
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "test_type": "GUARDED_HYDRATOR_V3_EXECUTION_SELFTEST",
        "cases": cases,
        "passed": passed,
        "total": len(cases),
        "pass": passed == len(cases),
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    output = automation.parent / "validation/security_public_safety_2_guarded_hydrator_v3_selftest_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slot_id": SLOT_ID, "passed": passed, "total": len(cases), "pass": payload["pass"], "final_ready": False}))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
