from __future__ import annotations

import csv
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry.py"
SOURCE_CSV = ROOT / "england_map_web" / "data" / "security_public_safety" / "parcel_security_scores_verified.csv"
CANDIDATE_EXAMPLE_LIMIT = 20


def parcel_number(value: Any) -> int | None:
    match = re.search(r"(\d+)$", str(value or ""))
    return int(match.group(1)) if match else None


def load_base_entry():
    spec = importlib.util.spec_from_file_location("security_public_safety_1_worker_entry_base", BASE_ENTRY)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_ENTRY_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def candidate_examples() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            number = parcel_number(row.get("parcel_id"))
            if number is None or not 1 <= number <= 30761:
                continue
            examples.append(
                {
                    "parcel_id": row.get("parcel_id"),
                    "security_score_percent": row.get("security_score_percent"),
                    "security_level": row.get("security_level"),
                    "accuracy_score_4": int(row.get("accuracy_score_4") or 0),
                    "accuracy_label_4": row.get("accuracy_label_4"),
                    "confidence_score": row.get("confidence_score"),
                    "spatial_score": row.get("spatial_score"),
                    "source_geography_level": row.get("source_geography_level"),
                    "official_api_latest_month": row.get("official_api_latest_month"),
                    "official_api_validation_status": row.get("official_api_validation_status"),
                    "matching_method": row.get("matching_method"),
                    "output_semantics": "AREA_LEVEL_PROXY",
                    "parcel_measurement": False,
                }
            )
            if len(examples) >= CANDIDATE_EXAMPLE_LIMIT:
                break
    if len(examples) != CANDIDATE_EXAMPLE_LIMIT:
        raise RuntimeError(f"EXPECTED_20_CANDIDATE_EXAMPLES_GOT_{len(examples)}")
    return examples


def main() -> int:
    base = load_base_entry()
    exit_code = int(base.main() or 0)

    progress_path = Path(base.PROGRESS_JSON)
    if not progress_path.is_file():
        raise RuntimeError("BASE_PROGRESS_JSON_NOT_CREATED")
    payload = json.loads(progress_path.read_text(encoding="utf-8"))
    examples = candidate_examples()
    payload["candidate_examples"] = examples
    payload["candidate_examples_count"] = len(examples)
    payload["candidate_example_limit"] = CANDIDATE_EXAMPLE_LIMIT
    payload["web_display_contract"] = {
        "line_item_events": True,
        "candidate_examples": CANDIDATE_EXAMPLE_LIMIT,
        "official_source_checks": int(payload.get("source_check_count") or 0),
        "show_http_status": True,
        "show_extracted_date": True,
        "show_measurement_scope": True,
        "show_area_level_proxy_disclaimer": True,
    }
    payload["accuracy_summary"] = {
        "verified_rows": int(payload.get("hydrated_rows") or 0),
        "accuracy_score_4_rows": int(payload.get("accuracy_score_4_rows") or 0),
        "candidate_accuracy_score_4_rows": sum(item.get("accuracy_score_4") == 4 for item in examples),
        "parcel_measurement_rows": 0,
        "output_semantics": "AREA_LEVEL_PROXY",
    }
    base.publish_progress(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
