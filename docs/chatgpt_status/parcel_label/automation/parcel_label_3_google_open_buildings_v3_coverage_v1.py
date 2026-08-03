#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile
from datetime import datetime, timezone

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/google_open_buildings_v3_coverage_source_manifest_20260803.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/google_open_buildings_v3_coverage_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/google_open_buildings_v3_coverage_latest.json"),
]

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp = pathlib.Path(handle.name)
    tmp.replace(path)

def load_rows() -> list[dict]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("records", [])
    if len(rows) != 3:
        raise RuntimeError(f"EXPECTED_3_ROWS:{len(rows)}")
    required = {"parcel_id", "UPRN", "FULLADDRESS", "longitude", "latitude"}
    result = []
    for row in rows:
        missing = sorted(required - set(row))
        if missing or not row.get("exact_uprn_bound"):
            raise RuntimeError(f"INVALID_INPUT_ROW:{row.get('parcel_id')}:{missing}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-8.7 <= lon <= 2.1 and 49.8 <= lat <= 60.9):
            raise RuntimeError(f"TARGET_OUTSIDE_GBR_BOUNDS:{row['parcel_id']}:{lon}:{lat}")
        result.append({
            "parcel_id": str(row["parcel_id"]),
            "UPRN": str(row["UPRN"]),
            "FULLADDRESS": str(row["FULLADDRESS"]),
            "longitude": lon,
            "latitude": lat,
            "exact_uprn_bound": True,
        })
    return result

def load_manifest() -> dict:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    excerpt = str(payload.get("retained_evidence_excerpt", ""))
    expected = str(payload.get("retained_evidence_excerpt_sha256", ""))
    actual = sha256_text(excerpt)
    if not excerpt or actual != expected:
        raise RuntimeError(f"MANIFEST_EVIDENCE_SHA_MISMATCH:{actual}:{expected}")
    codes = payload.get("coverage_country_codes")
    if not isinstance(codes, list) or not all(isinstance(code, str) and len(code) == 3 for code in codes):
        raise RuntimeError("INVALID_COVERAGE_COUNTRY_CODES")
    if payload.get("target_country_code") != "GBR":
        raise RuntimeError("TARGET_COUNTRY_NOT_GBR")
    if "GBR" in codes or payload.get("target_country_listed") is not False:
        raise RuntimeError("GBR_UNEXPECTEDLY_LISTED")
    return payload

def coverage_decision(codes: list[str], target: str) -> bool:
    return target in set(codes)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--synthetic-test", action="store_true")
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 300:
        raise RuntimeError(f"INVALID_TIMEOUT:{args.timeout}")
    rows = load_rows()
    manifest = load_manifest()
    codes = list(manifest["coverage_country_codes"])
    if args.synthetic_test:
        if coverage_decision(codes, "GBR"):
            raise RuntimeError("SYNTHETIC_GBR_EXCLUSION_FAILED")
        if not coverage_decision(codes, "GHA"):
            raise RuntimeError("SYNTHETIC_INCLUDED_COUNTRY_FAILED")
        print(json.dumps({
            "valid": True,
            "gbr_covered": False,
            "gha_covered": True,
            "coverage_country_count": len(codes),
            "input_count": len(rows),
        }, sort_keys=True))
        return 0
    validation = {
        "valid": True,
        "input_count": len(rows),
        "target_country_code": "GBR",
        "target_country_covered": coverage_decision(codes, "GBR"),
        "coverage_country_count": len(codes),
        "resource_class": "geometry",
        "source_url": manifest["source_url"],
        "write_paths": [str(path) for path in OUTPUTS],
    }
    if args.validate_only:
        print(json.dumps(validation, sort_keys=True))
        return 0
    reason = "GOOGLE_OPEN_BUILDINGS_V3_COUNTRY_NOT_COVERED:GBR"
    records = [{
        **row,
        "source_url": manifest["source_url"],
        "earth_engine_catalog_url": manifest["earth_engine_catalog_url"],
        "dataset_version": manifest["dataset_version"],
        "target_country_code": "GBR",
        "target_country_covered": False,
        "candidate_count": 0,
        "state": "NO_DATA",
        "reason": reason,
        "inferred": False,
    } for row in rows]
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-google-open-buildings-v3-coverage-v1-20260803",
        "state": "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_exact_building_rows": 0,
        "evidence_records": len(records),
        "source_evidence": {
            "source_url": manifest["source_url"],
            "earth_engine_catalog_url": manifest["earth_engine_catalog_url"],
            "license_urls": manifest["license_urls"],
            "accessed_at": manifest["accessed_at"],
            "dataset_version": manifest["dataset_version"],
            "coverage_country_count": len(codes),
            "coverage_country_codes_sha256": sha256_text(",".join(codes)),
            "retained_evidence_excerpt_sha256": manifest["retained_evidence_excerpt_sha256"],
            "target_country_code": "GBR",
            "target_country_listed": False,
            "reason": reason,
        },
        "records": records,
        "large_raw_files_committed": False,
        "fake_data": False,
        "generated_at": utc_now(),
    }
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(json.dumps({
        "completed_count": len(records),
        "target_count": 3,
        "matched_exact_building_rows": 0,
        "state": "NO_DATA_CONTINUE",
        "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
