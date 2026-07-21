#!/usr/bin/env python3
"""Build the 30,761-row future_growth_2 evidence matrix without inventing scores.

Every canonical row is preserved. Candidate evidence is attached only when the exact
crosswalk output contains an explicit canonical row number, parcel ID and HMLR INSPIRE
ID that agree with the canonical shard. No nearest match or inferred identity is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROW_START = 30762
ROW_END = 61522
ROW_COUNT = 30761


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"line {line_no} is not an object")
            rows.append(value)
    return rows


def validate_canonical(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    if len(rows) != ROW_COUNT:
        raise ValueError(f"expected {ROW_COUNT} canonical rows, received {len(rows)}")
    by_row: dict[int, dict[str, Any]] = {}
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    for row in rows:
        row_no = int(row.get("row_no"))
        parcel_id = str(row.get("parcel_id") or "").strip()
        inspire_id = str(row.get("hmlr_inspire_id") or "").strip()
        if not (ROW_START <= row_no <= ROW_END):
            raise ValueError(f"row {row_no} outside shard")
        if not parcel_id or not inspire_id:
            raise ValueError(f"row {row_no} lacks explicit identity")
        if row_no in by_row or parcel_id in parcel_ids or inspire_id in inspire_ids:
            raise ValueError(f"duplicate canonical identity at row {row_no}")
        by_row[row_no] = row
        parcel_ids.add(parcel_id)
        inspire_ids.add(inspire_id)
    if sorted(by_row) != list(range(ROW_START, ROW_END + 1)):
        raise ValueError("canonical shard rows are not exactly contiguous 30762..61522")
    return by_row


def load_candidates(paths: Iterable[Path]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates = payload.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError(f"candidate file lacks candidates array: {path}")
        for candidate in candidates:
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            if not candidate_id or candidate_id in out:
                raise ValueError(f"duplicate or empty candidate_id {candidate_id!r}")
            out[candidate_id] = candidate
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-shard-jsonl", type=Path, required=True)
    parser.add_argument("--exact-crosswalk-json", type=Path, required=True)
    parser.add_argument("--candidate-json", type=Path, action="append", required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--manifest-json", type=Path, required=True)
    args = parser.parse_args()

    canonical_rows = load_jsonl(args.canonical_shard_jsonl.resolve())
    canonical = validate_canonical(canonical_rows)
    candidates = load_candidates([p.resolve() for p in args.candidate_json])
    crosswalk = json.loads(args.exact_crosswalk_json.resolve().read_text(encoding="utf-8"))
    results = crosswalk.get("results")
    if not isinstance(results, list):
        raise ValueError("exact crosswalk payload lacks results")
    if crosswalk.get("nearest_point_promotion_used") is not False:
        raise ValueError("crosswalk does not prove nearest-point promotion was disabled")

    evidence_by_row: dict[int, list[dict[str, Any]]] = {}
    for result in results:
        if result.get("state") != "EXACT_IDENTITY_CROSSWALK_READY_FOR_EVIDENCE_MATRIX":
            continue
        candidate_id = str(result.get("candidate_id") or "")
        candidate = candidates.get(candidate_id)
        if candidate is None:
            raise ValueError(f"crosswalk candidate not found in source waves: {candidate_id}")
        row_no = int(result.get("canonical_row_no"))
        canonical_row = canonical.get(row_no)
        if canonical_row is None:
            raise ValueError(f"crosswalk row outside shard: {row_no}")
        if str(result.get("canonical_parcel_id")) != str(canonical_row.get("parcel_id")):
            raise ValueError(f"parcel ID disagreement at row {row_no}")
        if str(result.get("hmlr_inspire_id")) != str(canonical_row.get("hmlr_inspire_id")):
            raise ValueError(f"INSPIRE ID disagreement at row {row_no}")
        evidence_by_row.setdefault(row_no, []).append({
            "candidate_id": candidate_id,
            "source_entity": candidate.get("source_entity"),
            "source_reference": candidate.get("source_reference"),
            "source_url": candidate.get("source_url"),
            "source_confidence": candidate.get("source_confidence"),
            "relation_type": result.get("relation_type"),
            "parcel_match_confidence_cap": result.get("parcel_match_confidence_cap"),
            "official_geojson_url": result.get("official_geojson_url"),
            "hmlr_inspire_id": result.get("hmlr_inspire_id"),
        })

    output_path = args.output_jsonl.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    matched_rows = 0
    evidence_links = 0
    with output_path.open("w", encoding="utf-8") as handle:
        for row_no in range(ROW_START, ROW_END + 1):
            canonical_row = canonical[row_no]
            evidence = evidence_by_row.get(row_no, [])
            if evidence:
                matched_rows += 1
                evidence_links += len(evidence)
            matrix_row = {
                "row_no": row_no,
                "parcel_id": canonical_row["parcel_id"],
                "hmlr_inspire_id": canonical_row["hmlr_inspire_id"],
                "local_authority_name": canonical_row.get("local_authority_name"),
                "evidence_state": "EXACT_CROSSWALK_EVIDENCE_READY_FOR_APPROVED_SCORER" if evidence else "NO_VERIFIED_FUTURE_GROWTH_EVIDENCE",
                "evidence": evidence,
                "future_growth_score": None,
                "future_growth_confidence": 0,
                "scoring_contract_id": None,
                "nearest_point_promotion_used": False,
            }
            encoded = json.dumps(matrix_row, ensure_ascii=False, separators=(",", ":")) + "\n"
            handle.write(encoded)
            digest.update(encoded.encode("utf-8"))

    manifest = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "matrix_rows": ROW_COUNT,
        "matched_rows": matched_rows,
        "evidence_links": evidence_links,
        "output_jsonl": str(output_path),
        "output_sha256": digest.hexdigest(),
        "scores_written": 0,
        "score_contract_present": False,
        "nearest_point_promotion_used": False,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    manifest_path = args.manifest_json.resolve()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "rows": ROW_COUNT, "matched_rows": matched_rows, "scores": 0}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
