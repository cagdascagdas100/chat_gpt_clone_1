from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

CORE_PATH = Path(__file__).with_name("security_public_safety_3_sample_hydrate_v4.py")
TASK_VERSION = "5.2.3-force-coverage-locate-neighbourhood-gate"
ATTEMPT_ID = "security-public-safety-3-20260721-012"
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_IOD25_FILE7_V2_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
LOCATE_NEIGHBOURHOOD_URL = "https://data.police.uk/api/locate-neighbourhood"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
LSOA_RE = re.compile(r"^E01[0-9]{6}$")
MONTH_RE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
FORCE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAY_2026_MISSING_TERRITORIAL_CRIME_FORCE_IDS = {
    "gloucestershire",
    "greater-manchester",
    "lincolnshire",
}
SPECIAL_FORCE_CRIME_GAPS = {"british-transport-police"}
NO_OUTCOME_FORCE_IDS = {"british-transport-police", "northern-ireland"}
STATUS_BY_ACCURACY = {
    0: "NO_ACCEPTANCE_GATE_PASSED",
    1: "ONE_OF_FOUR_GATES_PASSED",
    2: "TWO_OF_FOUR_GATES_PASSED",
    3: "THREE_OF_FOUR_GATES_PASSED",
    4: "STRICT_CANONICAL_FORCE_COVERAGE_APIS_IOD25_V2_VERIFIED",
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


def finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def sha256_ok(value: object) -> bool:
    return bool(SHA256_RE.fullmatch(str(value or "")))


def valid_point_geometry(geometry: object) -> tuple[bool, float | None, float | None]:
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return False, None, None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return False, None, None
    lng = finite_number(coordinates[0])
    lat = finite_number(coordinates[1])
    if lng is None or lat is None or not (-180 <= lng <= 180) or not (-90 <= lat <= 90):
        return False, None, None
    return True, lng, lat


def url_contract_ok(url: object, month: str, lat: float, lng: float, endpoint_fragment: str) -> bool:
    try:
        parsed = urlparse(str(url))
        query = parse_qs(parsed.query)
        if parsed.scheme != "https" or parsed.netloc != "data.police.uk":
            return False
        if endpoint_fragment not in parsed.path:
            return False
        if query.get("date", [None])[0] != month:
            return False
        query_lat = finite_number(query.get("lat", [None])[0])
        query_lng = finite_number(query.get("lng", [None])[0])
        if query_lat is None or query_lng is None:
            return False
        return abs(query_lat - lat) <= 1e-5 and abs(query_lng - lng) <= 1e-5
    except Exception:
        return False


def force_lookup_url_contract_ok(url: object, lat: float, lng: float) -> bool:
    try:
        parsed = urlparse(str(url))
        query = parse_qs(parsed.query)
        if parsed.scheme != "https" or parsed.netloc != "data.police.uk":
            return False
        if parsed.path != "/api/locate-neighbourhood":
            return False
        raw_q = query.get("q", [None])[0]
        if raw_q is None:
            return False
        parts = str(raw_q).split(",")
        if len(parts) != 2:
            return False
        query_lat = finite_number(parts[0])
        query_lng = finite_number(parts[1])
        if query_lat is None or query_lng is None:
            return False
        return abs(query_lat - lat) <= 1e-5 and abs(query_lng - lng) <= 1e-5
    except Exception:
        return False


def locate_force(core, lat: float, lng: float, cache: dict[str, dict]) -> dict:
    key = f"{lat:.6f},{lng:.6f}"
    if key in cache:
        return cache[key]
    url = f"{LOCATE_NEIGHBOURHOOD_URL}?{urlencode({'q': key})}"
    evidence = {
        "url": url,
        "http_status": None,
        "response_sha256": None,
        "payload_is_object": False,
        "force_id": None,
        "neighbourhood_id": None,
        "url_contract_passed": False,
        "error": None,
    }
    try:
        status, body, payload = core.http_json(url)
        evidence.update(
            {
                "http_status": status,
                "response_sha256": hashlib.sha256(body).hexdigest(),
                "payload_is_object": isinstance(payload, dict),
                "force_id": payload.get("force") if isinstance(payload, dict) else None,
                "neighbourhood_id": payload.get("neighbourhood") if isinstance(payload, dict) else None,
                "url_contract_passed": force_lookup_url_contract_ok(url, lat, lng),
            }
        )
    except Exception as exc:
        evidence["error"] = str(exc)
    force_id = str(evidence.get("force_id") or "")
    neighbourhood_id = str(evidence.get("neighbourhood_id") or "")
    evidence["acceptance_passed"] = bool(
        evidence.get("http_status") == 200
        and sha256_ok(evidence.get("response_sha256"))
        and evidence.get("payload_is_object")
        and evidence.get("url_contract_passed")
        and FORCE_ID_RE.fullmatch(force_id)
        and neighbourhood_id
    )
    cache[key] = evidence
    return evidence


def territorial_coverage(force_id: str, latest_month: str) -> dict:
    missing_crime = bool(
        latest_month == "2026-05"
        and force_id in MAY_2026_MISSING_TERRITORIAL_CRIME_FORCE_IDS
    )
    missing_outcomes = force_id in NO_OUTCOME_FORCE_IDS
    return {
        "force_id": force_id,
        "latest_month": latest_month,
        "territorial_crime_coverage_available": not missing_crime,
        "territorial_outcomes_coverage_available": not missing_outcomes,
        "special_force_crime_gap_present": latest_month == "2026-05" and bool(SPECIAL_FORCE_CRIME_GAPS),
        "special_force_outcome_gap_present": bool(NO_OUTCOME_FORCE_IDS),
        "semantic_rule": (
            "Territorial force coverage is checked by the official locate-neighbourhood endpoint. "
            "British Transport Police and other special-force gaps remain disclosed and prevent claims of complete national coverage."
        ),
    }


def strict_api_gate(
    row: dict,
    prefix: str,
    endpoint_fragment: str,
    latest_month: str,
    lat: float,
    lng: float,
    force_lookup: dict,
    coverage_available: bool,
) -> tuple[bool, dict]:
    area = row.get("area_evidence")
    if not isinstance(area, dict):
        return False, {"reason": "AREA_EVIDENCE_MISSING"}
    count = non_negative_int(area.get(f"{prefix}_one_mile_supporting_count"))
    checks = {
        "core_gate": bool(row.get(f"{prefix}_api_gate")),
        "http_200": area.get(f"{prefix}_http_status") == 200,
        "sha256_64_hex": sha256_ok(area.get(f"{prefix}_response_sha256")),
        "response_payload_is_list": count is not None,
        "url_contract": url_contract_ok(
            area.get(f"{prefix}_url"), latest_month, lat, lng, endpoint_fragment
        ),
        "row_month_matches_latest": row.get("official_api_month") == latest_month,
        "force_lookup_accepted": bool(force_lookup.get("acceptance_passed")),
        "territorial_force_coverage_available": coverage_available,
    }
    return all(checks.values()), checks


def strict_iod_gate(row: dict, iod_evidence: object, lsoa_code: str) -> tuple[bool, dict]:
    iod = row.get("iod25_v2")
    evidence = iod_evidence if isinstance(iod_evidence, dict) else {}
    rank = non_negative_int(iod.get("iod25_crime_rank")) if isinstance(iod, dict) else None
    decile = non_negative_int(iod.get("iod25_crime_decile")) if isinstance(iod, dict) else None
    score = finite_number(iod.get("iod25_crime_score")) if isinstance(iod, dict) else None
    checks = {
        "core_gate": bool(row.get("iod25_gate")),
        "official_v2_url_exact": evidence.get("url") == EXPECTED_IOD25_FILE7_V2_URL,
        "http_200": evidence.get("http_status") == 200,
        "sha256_64_hex": sha256_ok(evidence.get("response_sha256")),
        "response_bytes_positive": (non_negative_int(evidence.get("bytes")) or 0) > 0,
        "matched_lsoa_count_positive": (non_negative_int(evidence.get("matched_lsoa_count")) or 0) > 0,
        "lsoa_code_matches": isinstance(iod, dict) and iod.get("lsoa_code_2021") == lsoa_code,
        "crime_score_finite": score is not None,
        "crime_rank_positive": rank is not None and rank >= 1,
        "crime_decile_1_to_10": decile is not None and 1 <= decile <= 10,
    }
    return all(checks.values()), checks


def main() -> int:
    core = load_core()
    temp_root = Path(tempfile.gettempdir()) / "aays_security_public_safety_slot3_smoke_v5_2_3"
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

    latest = payload.get("official_api_latest") or {}
    latest_month = str(latest.get("month") or "")
    official_latest_pass = bool(
        latest.get("http_status") == 200
        and MONTH_RE.fullmatch(latest_month)
        and sha256_ok(latest.get("response_sha256"))
    )
    iod_evidence = payload.get("iod25_v2_evidence") or {}
    force_cache: dict[str, dict] = {}

    passed_gate_cells = 0
    force_lookup_pass_count = 0
    for row in rows:
        candidate_score = row.get("security_score_percent")
        row["candidate_security_score_percent"] = candidate_score
        point_ok, lng, lat = valid_point_geometry(row.get("geometry"))
        lsoa_code = str(row.get("lsoa_code") or "")
        canonical_checks = {
            "core_gate": bool(row.get("canonical_gate")),
            "exact_blob": exact_blob_pass,
            "ordered_identity": identity_pass,
            "target_id": row.get("parcel_id") in TARGET_IDS,
            "point_geometry_and_finite_coordinates": point_ok,
            "preexisting_score_finite": finite_number(candidate_score) is not None,
            "lsoa_code_format": bool(LSOA_RE.fullmatch(lsoa_code)),
        }
        canonical_gate = all(canonical_checks.values())

        force_lookup = {
            "acceptance_passed": False,
            "reason": "POINT_OR_LATEST_MONTH_NOT_READY",
        }
        coverage = territorial_coverage("", latest_month)
        if point_ok and official_latest_pass and lat is not None and lng is not None:
            force_lookup = locate_force(core, lat, lng, force_cache)
            if force_lookup.get("acceptance_passed"):
                force_lookup_pass_count += 1
            force_id = str(force_lookup.get("force_id") or "")
            coverage = territorial_coverage(force_id, latest_month)
            crime_gate, crime_checks = strict_api_gate(
                row,
                "crime",
                "/api/crimes-street/all-crime",
                latest_month,
                lat,
                lng,
                force_lookup,
                bool(coverage["territorial_crime_coverage_available"]),
            )
            outcomes_gate, outcomes_checks = strict_api_gate(
                row,
                "outcomes",
                "/api/outcomes-at-location",
                latest_month,
                lat,
                lng,
                force_lookup,
                bool(coverage["territorial_outcomes_coverage_available"]),
            )
        else:
            crime_gate = False
            outcomes_gate = False
            crime_checks = {"official_latest_and_point_ready": False}
            outcomes_checks = {"official_latest_and_point_ready": False}

        iod_gate, iod_checks = strict_iod_gate(row, iod_evidence, lsoa_code)
        accuracy = sum((canonical_gate, crime_gate, outcomes_gate, iod_gate))
        passed_gate_cells += accuracy

        row["canonical_gate"] = canonical_gate
        row["crime_api_gate"] = crime_gate
        row["outcomes_api_gate"] = outcomes_gate
        row["iod25_gate"] = iod_gate
        row["force_lookup_evidence"] = force_lookup
        row["territorial_coverage"] = coverage
        row["strict_gate_checks"] = {
            "canonical": canonical_checks,
            "crime_api": crime_checks,
            "outcomes_api": outcomes_checks,
            "iod25_v2": iod_checks,
        }
        row["accuracy_score_4"] = accuracy
        row["candidate_status"] = STATUS_BY_ACCURACY[accuracy]
        row["needs_manual_review"] = accuracy != 4
        row["security_score_percent"] = candidate_score if accuracy == 4 else None
        row["score_publish_rule"] = "published only when all four strict gates pass"
        row["smoke_task"] = True

    accuracy_ge_3 = sum(1 for row in rows if row.get("accuracy_score_4", 0) >= 3)
    accuracy_4 = sum(1 for row in rows if row.get("accuracy_score_4") == 4)
    api_attempted_count = sum(1 for row in rows if row.get("area_evidence"))
    all_unverified_scores_null = all(
        row.get("accuracy_score_4") == 4 or row.get("security_score_percent") is None
        for row in rows
    )
    runtime_acceptance_pass = bool(
        exact_blob_pass
        and identity_pass
        and official_latest_pass
        and accuracy_4 > 0
        and core_return_code == 0
        and all_unverified_scores_null
    )

    latest_month_quality_caveats = []
    if latest_month == "2026-05":
        latest_month_quality_caveats = [
            {
                "force": "British Transport Police",
                "force_id": "british-transport-police",
                "issue": "Crime data not provided for May 2026; outcome data is not supplied to data.police.uk.",
                "effect": "Special-force undercoverage remains disclosed and must not be interpreted as zero crime or complete outcome coverage.",
            },
            {
                "force": "Gloucestershire Constabulary",
                "force_id": "gloucestershire",
                "issue": "Crime data not provided for May 2026.",
                "effect": "Territorial crime gate fails when locate-neighbourhood resolves this force.",
            },
            {
                "force": "Greater Manchester Police",
                "force_id": "greater-manchester",
                "issue": "Crime data not provided for May 2026.",
                "effect": "Territorial crime gate fails when locate-neighbourhood resolves this force.",
            },
            {
                "force": "Lincolnshire Police",
                "force_id": "lincolnshire",
                "issue": "Crime data not provided for May 2026.",
                "effect": "Territorial crime gate fails when locate-neighbourhood resolves this force.",
            },
            {
                "force": "Police Service of Northern Ireland",
                "force_id": "northern-ireland",
                "issue": "Outcome data is not supplied to data.police.uk.",
                "effect": "Territorial outcomes gate fails if this force is resolved; slot parcels are expected to be in England.",
            },
        ]

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
        "official_latest_month_acceptance_passed": official_latest_pass,
        "historical_source_materialization": materialization,
        "source_file": payload.get("source_file"),
        "source_file_git_blob_sha": payload.get("source_file_git_blob_sha"),
        "source_file_sha256": payload.get("source_file_sha256"),
        "official_api_latest": latest,
        "iod25_v2_evidence": iod_evidence,
        "force_lookup_endpoint": LOCATE_NEIGHBOURHOOD_URL,
        "force_lookup_attempted_count": len(force_cache),
        "force_lookup_acceptance_pass_count": force_lookup_pass_count,
        "latest_month_quality_caveats": latest_month_quality_caveats,
        "strict_gate_version": "exact-blob-point-numeric-force-lookup-territorial-coverage-list-payload-sha256-iod25-fields-v2",
        "acceptance_gates": [
            "exact canonical Git blob, exact ordered identity, Point geometry, finite coordinates, finite preexisting score and valid LSOA code",
            "latest-month street-crime HTTPS URL contract, HTTP 200, 64-hex SHA256, list payload and accepted territorial force coverage",
            "latest-month outcomes-at-location HTTPS URL contract, HTTP 200, 64-hex SHA256, list payload and accepted territorial force coverage",
            "corrected IoD2025 File 7 v2 exact URL, HTTP 200, 64-hex SHA256 and matching non-empty Crime Score, positive Rank and Decile 1-10",
        ],
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
        "success_rule": "exit zero only when exact blob, ordered identity, valid latest-month metadata, accepted force lookup and territorial coverage, strict API lists, strict IoD fields, core success, null suppression and at least one strict 4/4 row are all present",
        "core_return_code": core_return_code,
        "semantic_limits": [
            "Police API locations are anonymised and approximate supporting area evidence, not exact parcel incidents.",
            "Territorial force lookup does not remove British Transport Police or other special-force undercoverage.",
            "IoD2025 Crime fields are relative LSOA context and are not converted directly into an absolute parcel percentage.",
            "The published score is the preexisting canonical score and remains null unless all four strict gates pass.",
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
        "strict_gate_version": output["strict_gate_version"],
        "runtime_execution_complete": True,
        "runtime_acceptance_passed": runtime_acceptance_pass,
        "canonical_source_acceptance_passed": exact_blob_pass,
        "target_identity_acceptance_passed": identity_pass,
        "official_latest_month_acceptance_passed": official_latest_pass,
        "expected_rows": 3,
        "actual_rows": len(rows),
        "unique_rows": len(set(row_ids)),
        "ordered_identity_match": row_ids == TARGET_IDS,
        "expected_gate_cells": 12,
        "passed_gate_cells": passed_gate_cells,
        "accuracy_ge_3_count": accuracy_ge_3,
        "accuracy_score_4_count": accuracy_4,
        "force_lookup_attempted_count": len(force_cache),
        "force_lookup_acceptance_pass_count": force_lookup_pass_count,
        "requires_at_least_one_accuracy_4_for_success": True,
        "requires_list_payload_for_api_gates": True,
        "requires_force_lookup_for_api_gates": True,
        "requires_territorial_coverage_for_api_gates": True,
        "requires_nonempty_iod25_crime_fields": True,
        "all_unverified_published_scores_null": all_unverified_scores_null,
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
    print(f"OFFICIAL_LATEST_MONTH_ACCEPTANCE_PASSED={official_latest_pass}")
    print(f"FORCE_LOOKUP_ACCEPTANCE_PASS_COUNT={force_lookup_pass_count}")
    print(f"PASSED_GATE_CELLS={passed_gate_cells}")
    print(f"ACCURACY_SCORE_4_COUNT={accuracy_4}")
    print(f"RUNTIME_ACCEPTANCE_PASSED={runtime_acceptance_pass}")
    print(f"OUTPUT={output_path}")
    print(f"RECONCILIATION={reconciliation_path}")
    print("FINAL_READY=false")

    return 0 if runtime_acceptance_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
