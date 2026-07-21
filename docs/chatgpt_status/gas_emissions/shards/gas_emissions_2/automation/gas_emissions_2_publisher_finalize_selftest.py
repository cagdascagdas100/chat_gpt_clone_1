from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"


def load(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("publisher_finalize", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def check(value: bool, name: str, detail: str, rows: list[dict[str, Any]]) -> None:
    rows.append({"name": name, "pass": bool(value), "detail": detail})


def fixture(repo: Path, module: Any) -> dict[str, str]:
    (repo / module.OUTPUT_REL).mkdir(parents=True)
    served = "a" * 40
    write_json(repo / module.ARTIFACTS["guard_receipt"], {"state":"LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK","runtime_executed":True,"exit_code":0})
    write_json(repo / module.ARTIFACTS["pipeline_receipt"], {"state":"LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK","exit_code":0})
    write_json(repo / module.ARTIFACTS["local_evidence"], {"slot_id":SLOT_ID,"served_commit_sha":served,"checks_summary":{"passed":21,"total":21,"http_passed":6,"http_total":6,"interaction_passed":5,"interaction_total":5,"overall":"PASS"},"dataset_summary":{"candidate_rows":100,"unique_candidate_ids":100,"unique_preview_lines":100,"qa_pass":100,"qa_review":0,"dom_rows":100,"console_errors":0,"parcel_bound_rows":0},"runner_metadata_summary":{"passed":8,"total":9,"missing":["remote_commit_and_readback"]},"proof_complete":False,"remote_commit_and_readback":False,"final_ready":False})
    write_json(repo / module.ARTIFACTS["console"], {"console_events":[],"page_errors":[]})
    (repo / module.ARTIFACTS["screenshot"]).write_bytes(b"png-fixture")
    (repo / module.ARTIFACTS["dom"]).write_text("<html>fixture</html>", encoding="utf-8")
    (repo / module.ARTIFACTS["http_log"]).write_text("http fixture\n", encoding="utf-8")
    return {"served_commit": served}


def run(repo: Path) -> dict[str, Any]:
    module_path = repo / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_2/automation/gas_emissions_2_publisher_finalize.py"
    module = load(module_path)
    rows: list[dict[str, Any]] = []
    text = module_path.read_text(encoding="utf-8")
    tokens = ['SLOT_ID = "gas_emissions_2"','TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"','PUBLISHER_VERSION = "20260721_25"',"PREPARE_PUBLISHER_BUNDLE","VERIFY_REMOTE_ARTIFACT_READBACK","MUST_MATCH_ALL_7_LOCAL_ARTIFACTS","LOCAL_RUNTIME_PASS_AWAITING_PUBLISHER_COMMIT_READBACK","proof_complete_candidate","final_proof_commit_and_readback_pending",'"browser_acceptance_recorded": 66','"counted_toward_browser_acceptance": False','"direct_push_performed": False','"proof_complete": False','"final_ready": False','"fake_data": False','"db_write": False','"migration": False','"production_deploy": False']
    check(module_path.is_file(), "script_exists", str(module_path), rows)
    for token in tokens:
        check(token in text, "token", token, rows)
    check("git push" not in text.lower(), "no_git_push", "git push absent", rows)

    with tempfile.TemporaryDirectory() as tmp:
        test_repo = Path(tmp)
        context = fixture(test_repo, module)
        local = module.validate_local_runtime(test_repo)
        check(local["pass"], "valid_local_runtime_pass", str(local.get("failures")), rows)
        check(len(local["artifacts"]) == 7, "seven_artifacts", str(len(local["artifacts"])), rows)
        check(all(len(item["sha256"]) == 64 for item in local["artifacts"].values()), "all_artifact_hashes", "64 hex", rows)
        bundle = module.prepare(test_repo, test_repo / "bundle.json")
        check(bundle["ready_for_publisher_commit"], "prepare_pass", "ready", rows)
        check(bundle["browser_acceptance_after"] == 66, "prepare_keeps_66", "66", rows)
        check(bundle["proof_complete"] is False, "prepare_proof_false", "false", rows)
        sha_map = {item["path"]: item["sha256"] for item in local["artifacts"].values()}
        readback = {"slot_id":SLOT_ID,"branch":TARGET_BRANCH,"commit_sha":"b"*40,"served_commit_sha":context["served_commit"],"remote_readback_complete":True,"artifact_sha256_map":sha_map}
        write_json(test_repo / "readback.json", readback)
        verified = module.verify(test_repo, test_repo / "readback.json", test_repo / "verified.json")
        check(verified["remote_artifact_readback_verified"], "verify_pass", str(verified["failures"]), rows)
        check(verified["proof_complete_candidate"], "candidate_true", "true", rows)
        check(verified["browser_acceptance_candidate"] == 100, "candidate_100", "100", rows)
        check(verified["browser_acceptance_recorded"] == 66, "recorded_stays_66", "66", rows)
        check(verified["counted_toward_browser_acceptance"] is False, "not_counted", "false", rows)
        check(verified["proof_complete"] is False, "verify_proof_false", "false", rows)
        check(verified["final_ready"] is False, "verify_final_false", "false", rows)
        bad = dict(readback); bad["branch"] = "wrong"; write_json(test_repo / "bad_branch.json", bad)
        check(not module.verify(test_repo,test_repo/"bad_branch.json",test_repo/"bad_branch_out.json")["remote_artifact_readback_verified"], "wrong_branch_rejected", "rejected", rows)
        bad = dict(readback); bad["commit_sha"] = "short"; write_json(test_repo / "bad_commit.json", bad)
        check(not module.verify(test_repo,test_repo/"bad_commit.json",test_repo/"bad_commit_out.json")["remote_artifact_readback_verified"], "bad_commit_rejected", "rejected", rows)
        bad = json.loads(json.dumps(readback)); first = next(iter(bad["artifact_sha256_map"])); bad["artifact_sha256_map"][first] = "0"*64; write_json(test_repo / "bad_hash.json", bad)
        check(not module.verify(test_repo,test_repo/"bad_hash.json",test_repo/"bad_hash_out.json")["remote_artifact_readback_verified"], "bad_hash_rejected", "rejected", rows)
        (test_repo / module.ARTIFACTS["screenshot"]).unlink()
        check(not module.validate_local_runtime(test_repo)["pass"], "missing_artifact_rejected", "rejected", rows)

    passed = sum(1 for row in rows if row["pass"])
    return {"schema_version":1,"slot_id":SLOT_ID,"validation_scope":"STATIC_AND_FUNCTIONAL_PUBLISHER_FINALIZER_SELFTEST","checks":rows,"passed":passed,"total":len(rows),"all_checks_pass":passed==len(rows),"canonical_runner_runtime_executed":False,"browser_acceptance_changed":False,"final_ready":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True); parser.add_argument("--output"); args = parser.parse_args()
    result = run(Path(args.repo_root).resolve())
    if args.output: Path(args.output).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"total":result["total"],"all_checks_pass":result["all_checks_pass"]}))
    raise SystemExit(0 if result["all_checks_pass"] else 1)
