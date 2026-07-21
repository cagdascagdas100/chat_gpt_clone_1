#!/usr/bin/env python3
"""Apply externally approved future-growth score decisions to a verified matrix.

This script does not define or infer the scoring formula. It only applies explicit score
decisions that name an approved contract and reference rows with exact verified evidence.
Missing approval, unsupported rows, duplicate decisions, confidence above the geometry
cap, or non-null pre-existing scores fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"matrix line {line_no} is not an object")
            rows.append(row)
    return rows


def evidence_digest(row: dict[str, Any]) -> str:
    evidence = row.get("evidence")
    encoded = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verified-matrix-jsonl", type=Path, required=True)
    parser.add_argument("--approved-score-decisions-json", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--manifest-json", type=Path, required=True)
    args = parser.parse_args()

    matrix_rows = load_jsonl(args.verified_matrix_jsonl.resolve())
    if len(matrix_rows) != 30761:
        raise ValueError(f"expected 30761 matrix rows, received {len(matrix_rows)}")
    by_row: dict[int, dict[str, Any]] = {}
    for row in matrix_rows:
        row_no = int(row.get("row_no"))
        if row_no in by_row:
            raise ValueError(f"duplicate matrix row {row_no}")
        if row.get("future_growth_score") is not None or row.get("future_growth_confidence") not in (0, None):
            raise ValueError(f"matrix row {row_no} is already scored")
        if row.get("nearest_point_promotion_used") is not False:
            raise ValueError(f"matrix row {row_no} does not prove nearest matching disabled")
        by_row[row_no] = row

    decisions_payload = json.loads(args.approved_score_decisions_json.resolve().read_text(encoding="utf-8"))
    contract_id = str(decisions_payload.get("contract_id") or "").strip()
    approved_by = str(decisions_payload.get("approved_by") or "").strip()
    approved_at = str(decisions_payload.get("approved_at") or "").strip()
    if decisions_payload.get("approved") is not True or not contract_id or not approved_by or not approved_at:
        raise ValueError("score decisions lack explicit approval metadata")
    decisions = decisions_payload.get("rows")
    if not isinstance(decisions, list):
        raise ValueError("score decisions lack rows array")

    seen: set[int] = set()
    applied = 0
    for decision in decisions:
        row_no = int(decision.get("row_no"))
        if row_no in seen:
            raise ValueError(f"duplicate score decision for row {row_no}")
        seen.add(row_no)
        row = by_row.get(row_no)
        if row is None:
            raise ValueError(f"score decision outside matrix row {row_no}")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"score decision for row {row_no} has no verified evidence")
        expected_digest = evidence_digest(row)
        if str(decision.get("evidence_sha256") or "") != expected_digest:
            raise ValueError(f"evidence digest mismatch for row {row_no}")
        score = float(decision.get("future_growth_score"))
        confidence = float(decision.get("future_growth_confidence"))
        if not (0.0 <= score <= 100.0):
            raise ValueError(f"score outside 0..100 for row {row_no}")
        if not (0.0 < confidence <= 100.0):
            raise ValueError(f"confidence outside 0..100 for row {row_no}")
        caps = [float(item.get("parcel_match_confidence_cap") or 0) for item in evidence]
        allowed_cap = min(caps) if caps else 0
        if confidence > allowed_cap:
            raise ValueError(f"confidence {confidence} exceeds evidence cap {allowed_cap} for row {row_no}")
        rationale = str(decision.get("rationale") or "").strip()
        if not rationale:
            raise ValueError(f"score decision lacks rationale for row {row_no}")
        row["future_growth_score"] = round(score, 3)
        row["future_growth_confidence"] = round(confidence, 3)
        row["scoring_contract_id"] = contract_id
        row["score_decision_approved_by"] = approved_by
        row["score_decision_approved_at"] = approved_at
        row["score_rationale"] = rationale
        applied += 1

    output_path = args.output_jsonl.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with output_path.open("w", encoding="utf-8") as handle:
        for row_no in sorted(by_row):
            encoded = json.dumps(by_row[row_no], ensure_ascii=False, separators=(",", ":")) + "\n"
            handle.write(encoded)
            digest.update(encoded.encode("utf-8"))

    manifest = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "contract_id": contract_id,
        "approved_by": approved_by,
        "approved_at": approved_at,
        "matrix_rows": len(by_row),
        "score_decisions_applied": applied,
        "output_jsonl": str(output_path),
        "output_sha256": digest.hexdigest(),
        "nearest_point_promotion_used": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    manifest_path = args.manifest_json.resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "applied": applied, "contract_id": contract_id}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
