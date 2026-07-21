from __future__ import annotations

import importlib.util
import json
from pathlib import Path

CORE_PATH = Path(__file__).with_name("security_public_safety_3_sample_hydrate_v4.py")
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
TARGET_IDS = [f"parcel_{value}" for value in range(61523, 61571)]
TASK_VERSION = "5.1-powershell-carrier"
ATTEMPT_ID = "security-public-safety-3-20260721-008"
STATUS_BY_ACCURACY = {
    0: "NO_ACCEPTANCE_GATE_PASSED",
    1: "ONE_OF_FOUR_GATES_PASSED",
    2: "TWO_OF_FOUR_GATES_PASSED",
    3: "THREE_OF_FOUR_GATES_PASSED",
    4: "CANONICAL_APIS_IOD25_V2_VERIFIED",
}


def load_core():
    spec = importlib.util.spec_from_file_location("security_public_safety_3_v5_core", CORE_PATH)
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
    core.TARGET_IDS = list(TARGET_IDS)
    core.TASK_VERSION = TASK_VERSION
    core_return_code = int(core.main())

    core_output_path = core.OUT_ROOT / "security_public_safety_3_sample_candidates_v4_latest.json"
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

    accuracy_ge_3 = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in rows if row.get("accuracy_score_4") == 4)
    chunks = [
        {
            "chunk": index + 1,
            "start": TARGET_IDS[index * 12],
            "end": TARGET_IDS[index * 12 + 11],
            "count": 12,
        }
        for index in range(4)
    ]

    payload.update(
        {
            "schema_version": 5,
            "task_version": TASK_VERSION,
            "attempt_id": ATTEMPT_ID,
            "required_canonical_git_blob_sha": EXPECTED_BLOB_SHA,
            "canonical_source_acceptance_passed": exact_blob_pass,
            "target_identity_acceptance_passed": identity_pass,
            "sample_range": {"start": 61523, "end": 61570, "count": 48},
            "target_parcels": TARGET_IDS,
            "chunks": chunks,
            "rows": rows,
            "sample_count": len(rows),
            "prepared_acceptance_gate_cells": len(rows) * 4,
            "passed_acceptance_gate_cells": passed_gate_cells,
            "accuracy_ge_3_count": accuracy_ge_3,
            "accuracy_score_4_count": accuracy_4,
            "verified_slot_rows": accuracy_4,
            "actual_slot_rows_written": accuracy_4,
            "core_return_code": core_return_code,
            "fake_data": False,
            "final_ready": False,
        }
    )

    output_path = core.OUT_ROOT / "security_public_safety_3_sample_candidates_v5_latest.json"
    runner_web_path = core.WEB_ROOT / "security_public_safety_3_rows_latest.json"
    site_rows_path = core.REPO / "england_map_web" / "data" / "security_public_safety" / "security_public_safety_3_rows_latest.json"
    reconciliation_path = core.OUT_ROOT / "security_public_safety_3_v5_reconciliation_latest.json"

    reconciliation = {
        "schema_version": 1,
        "slot_id": core.SLOT_ID,
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "canonical_source_acceptance_passed": exact_blob_pass,
        "target_identity_acceptance_passed": identity_pass,
        "expected_rows": 48,
        "actual_rows": len(rows),
        "unique_rows": len(set(row_ids)),
        "expected_gate_cells": 192,
        "passed_gate_cells": passed_gate_cells,
        "accuracy_ge_3_count": accuracy_ge_3,
        "accuracy_score_4_count": accuracy_4,
        "all_unverified_published_scores_null": all(
            row.get("accuracy_score_4") == 4 or row.get("security_score_percent") is None
            for row in rows
        ),
        "fake_data": False,
        "final_ready": False,
    }

    for path in (output_path, runner_web_path, site_rows_path):
        write_json(path, payload)
    write_json(reconciliation_path, reconciliation)

    progress_path = core.REPO / "england_map_web" / "data" / "security_public_safety" / "security_public_safety_3_progress_latest.json"
    progress = {}
    if progress_path.is_file():
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
        except Exception:
            progress = {}
    progress.update(
        {
            "schema_version": 5,
            "slot_id": core.SLOT_ID,
            "updated_at": core.utc_now(),
            "status": "V5_FORTY_EIGHT_ROW_EXECUTED" if exact_blob_pass else "V5_EXECUTED_CANONICAL_BLOB_REJECTED",
            "visible_parcel_rows": 48,
            "prepared_acceptance_gate_cells": 192,
            "passed_acceptance_gate_cells": passed_gate_cells,
            "verified_slot_rows": accuracy_4,
            "accuracy_score_4_rows": accuracy_4,
            "actual_slot_rows_written": accuracy_4,
            "expected_output": str(output_path.relative_to(core.REPO)).replace("\\", "/"),
            "expected_output_exists": True,
            "runner_execution_claimed": True,
            "task_version": TASK_VERSION,
            "attempt_id": ATTEMPT_ID,
            "fake_data": False,
            "final_ready": False,
        }
    )
    write_json(progress_path, progress)

    print(f"SLOT_ID={core.SLOT_ID}")
    print(f"TASK_VERSION={TASK_VERSION}")
    print(f"SAMPLE_COUNT={len(rows)}")
    print(f"CANONICAL_SOURCE_ACCEPTANCE_PASSED={exact_blob_pass}")
    print(f"TARGET_IDENTITY_ACCEPTANCE_PASSED={identity_pass}")
    print(f"PASSED_GATE_CELLS={passed_gate_cells}")
    print(f"ACCURACY_GE_3_COUNT={accuracy_ge_3}")
    print(f"ACCURACY_SCORE_4_COUNT={accuracy_4}")
    print(f"OUTPUT={output_path}")
    print(f"RECONCILIATION={reconciliation_path}")
    print("FINAL_READY=false")
    return 0 if exact_blob_pass and identity_pass and accuracy_4 > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
