from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

CORE_PATH = Path(__file__).with_name("security_public_safety_3_sample_hydrate_v4.py")
TASK_VERSION = "5.2.1-smoke-fail-closed"
ATTEMPT_ID = "security-public-safety-3-20260721-010"
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
STATUS_BY_ACCURACY = {
    0: "NO_ACCEPTANCE_GATE_PASSED",
    1: "ONE_OF_FOUR_GATES_PASSED",
    2: "TWO_OF_FOUR_GATES_PASSED",
    3: "THREE_OF_FOUR_GATES_PASSED",
    4: "CANONICAL_APIS_IOD25_V2_VERIFIED",
}


def load_core():
    spec = importlib.util.spec_from_file_location("security_public_safety_3_smoke_core", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load core verifier: {CORE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    core = load_core()
    temp_root = Path(tempfile.gettempdir()) / "aays_security_public_safety_slot3_smoke_v5_2_1"
    temp_out = temp_root / "runner_outputs"
    temp_web = temp_root / "web"
    temp_out.mkdir(parents=True, exist_ok=True)
    temp_web.mkdir(parents=True, exist_ok=True)

    core.TARGET_IDS = list(TARGET_IDS)
    core.TASK_VERSION = TASK_VERSION
    core.OUT_ROOT = temp_out
    core.WEB_ROOT = temp_web

    core_return_code = int(core.main())
    core_output_path = temp_out / "security_public_safety_3_sample_candidates_v4_latest.json"
    payload = json.loads(core_output_path.read_text(encoding="utf-8"))

    materialization = payload.get("historical_source_materialization") or {}
    exact_blob_pass = bool(
        materialization.get("verified")
        and payload.get("source_file_git_blob_sha") == EXPECTED_BLOB_SHA
    )
    rows = payload.get("rows") or []
    row_ids = [row.get("parcel_id") for row in rows]
    identity_pass = (
        len(rows) == len(TARGET_IDS)
        and len(set(row_ids)) == len(TARGET_IDS)
        and row_ids == TARGET_IDS
    )

    passed_gate_cells = 0
    for row in rows:
        candidate_score = row.get("security_score_percent")
        row["candidate_security_score_percent"] = candidate_score
        if not exact_blob_pass or not identity_pass:
            row["canonical_gate"] = False
        accuracy = sum(
            bool(row.get(key))
            for key in ("canonical_gate", "crime_api_gate", "outcomes_api_gate", "iod25_gate")
        )
        passed_gate_cells += accuracy
        row["accuracy_score_4"] = accuracy
        row["candidate_status"] = STATUS_BY_ACCURACY[accuracy]
        row["needs_manual_review"] = accuracy != 4
        row["security_score_percent"] = candidate_score if accuracy == 4 else None
        row["score_publish_rule"] = "published only when all four gates pass"
        row["smoke_task"] = True

    accuracy_ge_3 = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in rows if row.get("accuracy_score_4") == 4)
    api_attempted_count = sum(1 for row in rows if row.get("area_evidence"))
    runtime_acceptance_pass = bool(
        exact_blob_pass
        and identity_pass
        and accuracy_4 > 0
        and core_return_code == 0
    )

    output = {
        "schema_version": 5,
        "slot_id": core.SLOT_ID,
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "generated_at": core.utc_now(),
        "sample_kind": "three-row-priority-smoke",
        "sample_range": {"start": 61523, "end": 61525, "count": 3},
        "target_parcels": TARGET_IDS,
        "required_canonical_git_blob_sha": EXPECTED_BLOB_SHA,
        "canonical_source_acceptance_passed": exact_blob_pass,
        "target_identity_acceptance_passed": identity_pass,
        "historical_source_materialization": materialization,
        "source_file": payload.get("source_file"),
        "source_file_git_blob_sha": payload.get("source_file_git_blob_sha"),
        "source_file_sha256": payload.get("source_file_sha256"),
        "official_api_latest": payload.get("official_api_latest"),
        "iod25_v2_evidence": payload.get("iod25_v2_evidence"),
        "acceptance_gates": payload.get("acceptance_gates"),
        "rows": rows,
        "sample_count": len(rows),
        "prepared_acceptance_gate_cells": len(rows) * 4,
        "passed_acceptance_gate_cells": passed_gate_cells,
        "accuracy_ge_3_count": accuracy_ge_3,
        "accuracy_score_4_count": accuracy_4,
        "verified_slot_rows": accuracy_4,
        "actual_slot_rows_written": accuracy_4,
        "api_attempted_row_count": api_attempted_count,
        "runtime_execution_complete": True,
        "runtime_acceptance_passed": runtime_acceptance_pass,
        "runtime_execution_success": runtime_acceptance_pass,
        "success_rule": "exit zero only when exact blob, exact ordered identity, core success, and at least one 4/4 row are all present",
        "core_return_code": core_return_code,
        "semantic_limits": [
            "Police API locations are anonymised and approximate supporting area evidence, not exact parcel incidents.",
            "IoD2025 Crime fields are relative LSOA context and are not converted directly into an absolute parcel percentage.",
            "The published score is the preexisting canonical score and remains null unless all four gates pass.",
        ],
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "person_level_data": False,
        "final_ready": False,
    }

    output_path = core.REPO / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json"
    reconciliation_path = core.REPO / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
    website_path = core.REPO / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json"

    reconciliation = {
        "schema_version": 1,
        "slot_id": core.SLOT_ID,
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "runtime_execution_complete": True,
        "runtime_acceptance_passed": runtime_acceptance_pass,
        "canonical_source_acceptance_passed": exact_blob_pass,
        "target_identity_acceptance_passed": identity_pass,
        "expected_rows": 3,
        "actual_rows": len(rows),
        "unique_rows": len(set(row_ids)),
        "ordered_identity_match": row_ids == TARGET_IDS,
        "expected_gate_cells": 12,
        "passed_gate_cells": passed_gate_cells,
        "accuracy_ge_3_count": accuracy_ge_3,
        "accuracy_score_4_count": accuracy_4,
        "requires_at_least_one_accuracy_4_for_success": True,
        "all_unverified_published_scores_null": all(
            row.get("accuracy_score_4") == 4 or row.get("security_score_percent") is None
            for row in rows
        ),
        "fake_data": False,
        "final_ready": False,
    }

    write_json(output_path, output)
    write_json(reconciliation_path, reconciliation)
    write_json(website_path, output)

    print(f"SLOT_ID={core.SLOT_ID}")
    print(f"TASK_VERSION={TASK_VERSION}")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print(f"SAMPLE_COUNT={len(rows)}")
    print(f"CANONICAL_SOURCE_ACCEPTANCE_PASSED={exact_blob_pass}")
    print(f"TARGET_IDENTITY_ACCEPTANCE_PASSED={identity_pass}")
    print(f"PASSED_GATE_CELLS={passed_gate_cells}")
    print(f"ACCURACY_SCORE_4_COUNT={accuracy_4}")
    print(f"RUNTIME_ACCEPTANCE_PASSED={runtime_acceptance_pass}")
    print(f"OUTPUT={output_path}")
    print(f"RECONCILIATION={reconciliation_path}")
    print("FINAL_READY=false")

    return 0 if runtime_acceptance_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
