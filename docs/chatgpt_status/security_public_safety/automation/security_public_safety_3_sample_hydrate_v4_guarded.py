from __future__ import annotations

import importlib.util
import json
from pathlib import Path

CORE_PATH = Path(__file__).with_name("security_public_safety_3_sample_hydrate_v4.py")
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
STATUS_BY_ACCURACY = {
    0: "NO_ACCEPTANCE_GATE_PASSED",
    1: "ONE_OF_FOUR_GATES_PASSED",
    2: "TWO_OF_FOUR_GATES_PASSED",
    3: "THREE_OF_FOUR_GATES_PASSED",
    4: "CANONICAL_APIS_IOD25_V2_VERIFIED",
}


def load_core():
    spec = importlib.util.spec_from_file_location("security_public_safety_3_v4_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load core verifier: {CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    core = load_core()
    core_return_code = int(core.main())
    output_path = core.OUT_ROOT / "security_public_safety_3_sample_candidates_v4_latest.json"
    website_path = core.WEB_ROOT / "security_public_safety_3_rows_latest.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    materialization = payload.get("historical_source_materialization") or {}
    exact_blob_pass = bool(
        materialization.get("verified")
        and payload.get("source_file_git_blob_sha") == EXPECTED_BLOB_SHA
    )

    for row in payload.get("rows", []):
        if not exact_blob_pass:
            row["canonical_gate"] = False
        accuracy = sum(
            bool(row.get(key))
            for key in ("canonical_gate", "crime_api_gate", "outcomes_api_gate", "iod25_gate")
        )
        row["accuracy_score_4"] = accuracy
        row["candidate_status"] = STATUS_BY_ACCURACY[accuracy]
        row["needs_manual_review"] = accuracy != 4

    accuracy_ge_3 = sum(1 for row in payload.get("rows", []) if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in payload.get("rows", []) if row.get("accuracy_score_4") == 4)
    payload.update(
        {
            "task_version": "4.2-guarded",
            "guard_version": "exact-canonical-git-blob-v1",
            "required_canonical_git_blob_sha": EXPECTED_BLOB_SHA,
            "canonical_source_acceptance_passed": exact_blob_pass,
            "core_return_code": core_return_code,
            "accuracy_ge_3_count": accuracy_ge_3,
            "accuracy_score_4_count": accuracy_4,
            "verified_slot_rows": accuracy_4,
            "actual_slot_rows_written": accuracy_4,
            "final_ready": False,
        }
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    output_path.write_text(text, encoding="utf-8")
    website_path.write_text(text, encoding="utf-8")

    print(f"SLOT_ID={payload.get('slot_id')}")
    print("TASK_VERSION=4.2-guarded")
    print(f"CANONICAL_SOURCE_ACCEPTANCE_PASSED={exact_blob_pass}")
    print(f"ACCURACY_GE_3_COUNT={accuracy_ge_3}")
    print(f"ACCURACY_SCORE_4_COUNT={accuracy_4}")
    print(f"OUTPUT={output_path}")
    print(f"WEB_OUTPUT={website_path}")
    print("FINAL_READY=false")
    return 0 if exact_blob_pass and accuracy_4 > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
