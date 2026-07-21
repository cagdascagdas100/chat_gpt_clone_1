#!/usr/bin/env python3
"""Fail-closed current-period validator for future_growth_2 Planning Data waves.

This validator never assigns a parcel or product score. It verifies that each selected
entity is returned exactly once by the official Planning Data API with period=current,
is authoritative brownfield-land data, has no end date, and matches the expected
entity/reference. Any entity/curie or current/historical ambiguity blocks eligibility.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_BASE = "https://www.planning.data.gov.uk/entity.json"
OFFICIAL_HOST = "www.planning.data.gov.uk"
DEFAULT_TIMEOUT = 30.0


def fetch_current(entity_id: int, timeout: float) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        [("entity", str(entity_id)), ("dataset", "brownfield-land"),
         ("period", "current"), ("limit", "2")]
    )
    url = f"{API_BASE}?{query}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TerraYield-AAYS-future-growth-2/1.0"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Planning Data returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Planning Data response is not an object")
    return payload


def entities_from(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("entities")
    if rows is None:
        rows = payload.get("data")
    if not isinstance(rows, list):
        raise ValueError("Planning Data response lacks an entities/data array")
    return [row for row in rows if isinstance(row, dict)]


def value(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def validate_candidate(candidate: dict[str, Any], timeout: float) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    entity_id = int(candidate["source_entity"])
    expected_reference = str(candidate.get("source_reference") or "").strip()
    eligibility = str(candidate.get("eligibility") or "")
    if not candidate_id or not expected_reference:
        raise ValueError("candidate identity is incomplete")
    if candidate.get("canonical_row_no") is not None or candidate.get("canonical_parcel_id") is not None:
        raise ValueError(f"{candidate_id}: parcel assignment present before exact crosswalk")
    if candidate.get("future_growth_score") is not None or candidate.get("future_growth_confidence") not in (0, None):
        raise ValueError(f"{candidate_id}: score/confidence present before approval")

    if not eligibility.startswith("eligible"):
        return {
            "candidate_id": candidate_id,
            "source_entity": entity_id,
            "state": "SKIPPED_NOT_ELIGIBLE",
            "eligibility": eligibility,
            "parcel_promoted": False,
            "score_written": False,
        }

    payload = fetch_current(entity_id, timeout)
    rows = entities_from(payload)
    exact = [row for row in rows if int(value(row, "entity") or -1) == entity_id]
    if len(exact) != 1:
        raise ValueError(f"{candidate_id}: expected one current entity row, got {len(exact)}")
    row = exact[0]

    dataset = str(value(row, "dataset") or "")
    reference = str(value(row, "reference") or "")
    quality = str(value(row, "quality") or "")
    end_date = str(value(row, "end-date", "end_date") or "").strip()
    point = str(value(row, "point") or "").strip()

    failures: list[str] = []
    if dataset != "brownfield-land":
        failures.append(f"dataset={dataset!r}")
    if reference != expected_reference:
        failures.append(f"reference={reference!r}")
    if quality != "authoritative":
        failures.append(f"quality={quality!r}")
    if end_date:
        failures.append(f"end_date={end_date!r}")
    if not point.startswith("POINT"):
        failures.append("point_missing")
    if failures:
        raise ValueError(f"{candidate_id}: current-period validation failed: {';'.join(failures)}")

    return {
        "candidate_id": candidate_id,
        "source_entity": entity_id,
        "source_reference": reference,
        "state": "CURRENT_AUTHORITATIVE_ENTITY_VALIDATED",
        "quality": quality,
        "end_date": None,
        "point_present": True,
        "parcel_promoted": False,
        "score_written": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-wave", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--delay-seconds", type=float, default=0.25)
    args = parser.parse_args()

    payload = json.loads(args.candidate_wave.resolve().read_text(encoding="utf-8"))
    if payload.get("slot_id") != "future_growth_2":
        raise ValueError("wrong slot_id")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate wave is empty")

    ids = [int(c["source_entity"]) for c in candidates]
    refs = [str(c["source_reference"]) for c in candidates]
    if len(ids) != len(set(ids)) or len(refs) != len(set(refs)):
        raise ValueError("duplicate entity or reference inside wave")

    results: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        results.append(validate_candidate(candidate, args.timeout))
        if index + 1 < len(candidates):
            time.sleep(max(0.0, args.delay_seconds))

    validated = sum(r["state"] == "CURRENT_AUTHORITATIVE_ENTITY_VALIDATED" for r in results)
    output = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "source_contract": "PLANNING_DATA_ENTITY_API_PERIOD_CURRENT",
        "official_host": OFFICIAL_HOST,
        "candidate_count": len(candidates),
        "validated_current_eligible": validated,
        "results": results,
        "actual_parcel_matches": 0,
        "actual_business_data_rows_written": 0,
        "future_growth_scores_produced": 0,
        "nearest_point_promotion_used": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "validated_current_eligible": validated, "matches": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
