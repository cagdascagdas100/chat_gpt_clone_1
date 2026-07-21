#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOST = "www.planning.data.gov.uk"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def entity_set(payload: dict) -> set[int]:
    result: set[int] = set()
    for candidate in payload.get("candidates") or []:
        value = candidate.get("source_entity")
        if value not in (None, ""):
            result.add(int(value))
    return result

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--wave", type=Path, required=True)
    p.add_argument("--previous-wave", type=Path, action="append", default=[])
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()

    payload = load_json(a.wave)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate array missing or empty")
    previous: set[int] = set()
    for path in a.previous_wave:
        previous |= entity_set(load_json(path))

    ids = [c["candidate_id"] for c in candidates]
    entities = [int(c["source_entity"]) for c in candidates]
    references = [str(c["source_reference"]).strip() for c in candidates]

    checks = []
    def record(name: str, passed: bool, detail: str):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    record("candidate_count_matches_summary",
           len(candidates) == payload["candidate_summary"]["researched"],
           f"{len(candidates)} candidates")
    record("candidate_ids_unique", len(ids) == len(set(ids)), f"{len(set(ids))}/{len(ids)} unique")
    record("source_entities_unique", len(entities) == len(set(entities)), f"{len(set(entities))}/{len(entities)} unique")
    record("source_references_unique", len(references) == len(set(references)), f"{len(set(references))}/{len(references)} unique")
    overlap = sorted(set(entities) & previous)
    record("no_previous_entity_overlap", not overlap, f"overlap={overlap}")
    official = all(urlparse(c["source_url"]).hostname == ALLOWED_HOST for c in candidates)
    record("official_source_domain", official, ALLOWED_HOST)
    record("authoritative_quality", all(c.get("source_quality") == "authoritative" for c in candidates), "all authoritative")
    record("current_end_date_empty", all(c.get("end_date") in (None, "") for c in candidates), "all current-ended empty")
    record("coordinates_present", all(isinstance(c.get("longitude"), (int,float)) and isinstance(c.get("latitude"), (int,float)) for c in candidates), "all points present")
    record("fail_closed_product_fields", all(
        c.get("canonical_row_no") is None and c.get("canonical_parcel_id") is None
        and c.get("future_growth_score") is None and c.get("future_growth_confidence") == 0
        for c in candidates), "all parcel/score fields null or zero")
    record("source_confidence_threshold", all(90 <= int(c.get("source_confidence", -1)) <= 100 for c in candidates), "all 90..100")
    record("eligible_count_matches_summary", sum(str(c.get("eligibility","")).startswith("eligible") for c in candidates) == payload["candidate_summary"]["eligible"], "eligible count checked")

    passed = sum(1 for c in checks if c["passed"])
    result = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "wave_id": payload.get("wave_id"),
        "executed": True,
        "test_type": "actual_wave_registry_invariant_validation",
        "checks_passed": passed,
        "checks_total": len(checks),
        "all_passed": passed == len(checks),
        "checks": checks,
        "canonical_parcel_matches": 0,
        "future_growth_scores_produced": 0,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "total": len(checks), "all_passed": result["all_passed"]}))
    return 0 if result["all_passed"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
