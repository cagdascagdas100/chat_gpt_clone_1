#!/usr/bin/env python3
"""Offline selftest for the future_growth_1 supply-chain validator."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

VALIDATOR = Path(__file__).with_name("016_validate_revision7_supply_chain_v1.py")
SPEC = importlib.util.spec_from_file_location("fg1_supply", VALIDATOR)
assert SPEC and SPEC.loader
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)

def write(root: Path, path: str, content: str) -> str:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return V.git_blob_sha(content.encode("utf-8"))

def fixture(root: Path) -> dict:
    queue_path = V.ALLOWED_QUEUE
    script_path = "docs/chatgpt_status/aays1/shards/future_growth_1/test_fixture.py"
    queue = json.dumps({"slot_id": V.SLOT_ID, "contract_revision": V.CONTRACT_REVISION, "state": "pending"})
    script = "SLOT_ID='future_growth_1'\n"
    qsha = write(root, queue_path, queue)
    ssha = write(root, script_path, script)
    files = [
        {"path": queue_path, "git_blob_sha": qsha, "required_text": ["future_growth_1"], "json_assertions": {"slot_id": V.SLOT_ID, "contract_revision": 7}},
        {"path": script_path, "git_blob_sha": ssha, "required_text": ["future_growth_1"]},
    ]
    while len(files) < 12:
        path = f"docs/chatgpt_status/aays1/shards/future_growth_1/fixture_{len(files)}.txt"
        sha = write(root, path, f"future_growth_1 fixture {len(files)}\n")
        files.append({"path": path, "git_blob_sha": sha, "required_text": ["future_growth_1"]})
    return {"slot_id": V.SLOT_ID, "contract_revision": 7, "files": files}

def run_case(name: str, mutate, expected: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        manifest = fixture(root)
        mutate(root, manifest)
        actual = V.validate(root, manifest)["result"]
        return {"name": name, "expected": expected, "actual": actual, "passed": actual == expected}

cases = [
    run_case("exact_manifest", lambda r, m: None, "PASS"),
    run_case("tampered_file", lambda r, m: (r / m["files"][1]["path"]).write_text("tampered\n", encoding="utf-8"), "FAIL"),
    run_case("wrong_slot", lambda r, m: m.__setitem__("slot_id", "other_slot"), "FAIL"),
    run_case("duplicate_path", lambda r, m: m["files"].__setitem__(2, dict(m["files"][1])), "FAIL"),
    run_case("unsafe_path", lambda r, m: m["files"][1].__setitem__("path", "docs/chatgpt_status/aays1/shards/other_slot/file.py"), "FAIL"),
    run_case("queue_pointer_mismatch", lambda r, m: m["files"][0]["json_assertions"].__setitem__("contract_revision", 6), "FAIL"),
]
result = {
    "schema_version": 1,
    "slot_id": V.SLOT_ID,
    "result": "PASS" if all(c["passed"] for c in cases) else "FAIL",
    "checks_passed": sum(c["passed"] for c in cases),
    "checks_total": len(cases),
    "cases": cases,
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["result"] == "PASS" else 2)
