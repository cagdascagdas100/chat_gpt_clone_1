#!/usr/bin/env python3
"""Bounded exact-site scan of the official 2024 UK PRTR CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-csv", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_km = 6371.0088
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2.0) ** 2
    return radius_km * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def parse_float(value: Any) -> float | None:
    try:
        text = str(value).strip()
        if not text or normalize(text) in {"not set", "none", "na"}:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def extract_pollutants(row: dict[str, str]) -> list[dict[str, Any]]:
    prefixes: set[str] = set()
    pattern = re.compile(r"^(FacilityReport_\d+_PollutantRelease_)")
    for key in row:
        match = pattern.match(key)
        if match:
            prefixes.add(match.group(1))
    out: list[dict[str, Any]] = []
    for prefix in sorted(prefixes):
        medium = row.get(prefix + "MediumCode")
        pollutant = row.get(prefix + "PollutantCode")
        total = row.get(prefix + "TotalQuantity")
        accidental = row.get(prefix + "AccidentalQuantity")
        if normalize(medium) in {"", "not set"} and normalize(pollutant) in {"", "not set"}:
            continue
        out.append(
            {
                "release_index": int(re.search(r"FacilityReport_(\d+)_", prefix).group(1)),
                "medium_code": medium,
                "pollutant_code": pollutant,
                "total_quantity": total,
                "accidental_quantity": accidental,
                "method_basis_code": row.get(prefix + "MethodBasisCode"),
                "method_type_code": row.get(prefix + "MethodUsed_MethodTypeCode"),
                "method_designation": row.get(prefix + "MethodUsed_Designation"),
                "confidential_indicator": row.get(prefix + "ConfidentialIndicator"),
                "remark_text": row.get(prefix + "RemarkText"),
            }
        )
    return out


def facility_projection(row: dict[str, str], distance_km: float) -> dict[str, Any]:
    return {
        "national_id": row.get("FacilityReport_NationalID"),
        "parent_company_name": row.get("FacilityReport_ParentCompanyName"),
        "facility_name": row.get("FacilityReport_FacilityName"),
        "street_name": row.get("FacilityReport_Address_StreetName"),
        "building_number": row.get("FacilityReport_Address_BuildingNumber"),
        "city_name": row.get("FacilityReport_Address_CityName"),
        "postcode": row.get("FacilityReport_Address_PostcodeCode"),
        "longitude": parse_float(row.get("FacilityReport_GeographicalCoordinate_LongitudeMeasure")),
        "latitude": parse_float(row.get("FacilityReport_GeographicalCoordinate_LatitudeMeasure")),
        "distance_km_to_locator": round(distance_km, 6),
        "main_economic_activity_code": row.get("FacilityReport_NACEMainEconomicActivityCode"),
        "main_economic_activity_name": row.get("FacilityReport_MainEconomicActivityName"),
        "competent_authority": row.get("FacilityReport_CompetentAuthorityPartyName"),
        "activities": [
            {
                "ranking": row.get("FacilityReport_Activity_RankingNumeric"),
                "annex_i_activity_code": row.get("FacilityReport_Activity_AnnexIActivityCode"),
            }
        ],
        "pollutant_releases": extract_pollutants(row),
    }


def match_target(rows: list[dict[str, str]], target: dict[str, Any], dataset_error: str | None) -> dict[str, Any]:
    aliases = [normalize(item) for item in target["exact_aliases"]]
    locator = target["locator"]
    max_distance = float(target["maximum_distance_km"])
    accepted: list[dict[str, Any]] = []
    alias_candidates = 0
    coordinate_rejections = 0

    for row in rows:
        identity_text = normalize(
            " ".join(
                str(row.get(field) or "")
                for field in (
                    "FacilityReport_ParentCompanyName",
                    "FacilityReport_FacilityName",
                    "FacilityReport_Address_StreetName",
                    "FacilityReport_Address_BuildingNumber",
                    "FacilityReport_Address_CityName",
                    "FacilityReport_Address_PostcodeCode",
                )
            )
        )
        matched_aliases = [alias for alias in aliases if alias and alias in identity_text]
        if not matched_aliases:
            continue
        alias_candidates += 1
        lon = parse_float(row.get("FacilityReport_GeographicalCoordinate_LongitudeMeasure"))
        lat = parse_float(row.get("FacilityReport_GeographicalCoordinate_LatitudeMeasure"))
        if lon is None or lat is None:
            coordinate_rejections += 1
            continue
        distance = haversine_km(float(locator["longitude"]), float(locator["latitude"]), lon, lat)
        if distance > max_distance:
            coordinate_rejections += 1
            continue
        projected = facility_projection(row, distance)
        projected["matched_exact_aliases"] = matched_aliases
        accepted.append(projected)
        require(len(accepted) <= int(target["maximum_matches"]), "target match limit exceeded")

    return {
        "target_id": target["target_id"],
        "site_name": target["site_name"],
        "attempt_completed": True,
        "locator": locator,
        "exact_aliases": target["exact_aliases"],
        "maximum_distance_km": max_distance,
        "alias_candidate_rows": alias_candidates,
        "coordinate_rejected_rows": coordinate_rejections,
        "matched_facility_rows": len(accepted),
        "matches": accepted,
        "decision": "EXACT_SITE_MATCH_VERIFIED" if accepted else "NO_DATA_CONTINUE",
        "error": dataset_error,
    }


def load_dataset(contract: dict[str, Any], fixture_csv: Path | None) -> tuple[bytes | None, list[dict[str, str]], str | None, int | None]:
    policy = contract["network_policy"]
    try:
        if fixture_csv:
            raw = fixture_csv.read_bytes()
            status = 200
        else:
            url = contract["source_evidence_manifest"]["source_url"]
            parsed = urllib.parse.urlparse(url)
            require(parsed.scheme == "https", "dataset URL must use HTTPS")
            require(parsed.netloc == "assets.publishing.service.gov.uk", "dataset host mismatch")
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "AAYS-UK-PRTR-Exact-Site-Gate/1.0",
                    "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.5",
                },
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=int(policy["dataset_timeout_seconds"])) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read(int(policy["maximum_dataset_bytes"]) + 1)
        require(status == 200, f"unexpected HTTP status {status}")
        require(len(raw) <= int(policy["maximum_dataset_bytes"]), "dataset exceeds byte limit")
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        required_headers = set(contract["required_csv_headers"])
        actual_headers = set(reader.fieldnames or [])
        missing = sorted(required_headers - actual_headers)
        require(not missing, "missing required CSV headers: " + ", ".join(missing))
        rows = list(reader)
        require(len(rows) <= int(policy["maximum_csv_rows"]), "dataset exceeds row limit")
        return raw, rows, None, status
    except urllib.error.HTTPError as exc:
        return None, [], f"HTTPError: {exc.code} {exc.reason}"[:500], int(exc.code)
    except Exception as exc:
        return None, [], f"{type(exc).__name__}: {exc}"[:500], None


def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)

    require(contract.get("schema_version") == 3, "contract schema mismatch")
    require(contract.get("slot_id") == "gas_emissions_3", "slot mismatch")
    require(contract.get("state") == "READY", "contract must be READY")
    require(contract.get("status") == "ready", "contract status must be ready")
    require(contract.get("claimable") is True and contract.get("ready_for_claim") is True, "contract not claimable")

    precondition = contract["precondition"]
    require(sha256_bytes(prior_bytes) == precondition["prior_output_sha256"], "prior output SHA mismatch")
    require(prior.get("task_id") == precondition["required_prior_task_id"], "unexpected prior task")
    require(prior.get("state") == precondition["required_prior_state"], "unexpected prior state")
    require(prior.get("next_unverified_step") == precondition["required_prior_next_unverified_step"], "unexpected prior next step")

    manifest = contract["source_evidence_manifest"]
    for field in (
        "source_url",
        "accessed_at",
        "content_sha256",
        "supports_fields",
        "relevant_record_ids_or_excerpt",
        "license_or_terms_url",
    ):
        require(manifest.get(field), f"missing source evidence field: {field}")

    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 2, "exactly two targets required")

    raw, rows, dataset_error, http_status = load_dataset(contract, args.fixture_csv)
    results = [match_target(rows, target, dataset_error) for target in targets]
    completed = sum(bool(item["attempt_completed"]) for item in results)
    target_count = len(targets)
    matched_targets = sum(bool(item["matched_facility_rows"]) for item in results)
    matched_rows = sum(int(item["matched_facility_rows"]) for item in results)
    pollutant_records = sum(
        len(match["pollutant_releases"])
        for item in results
        for match in item["matches"]
    )

    if matched_targets == target_count:
        state = "MATCHES_VERIFIED"
        next_step = "VALIDATE_UK_PRTR_MATCHED_RELEASE_RECORDS_FOR_GAS_EMISSIONS_BINDING"
    elif matched_targets:
        state = "PARTIAL_MATCH_CONTINUE"
        next_step = "ADVANCE_UNMATCHED_TARGET_TO_NEXT_SOURCE_AND_VALIDATE_MATCHED_UK_PRTR_RELEASES"
    else:
        state = "NO_DATA_CONTINUE"
        next_step = "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_UK_PRTR_NO_DATA"

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_csv else "LIVE_NETWORK",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": args.contract.as_posix(),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": args.prior.as_posix(),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "dataset_url": manifest["source_url"],
            "dataset_http_status": http_status,
            "dataset_sha256": sha256_bytes(raw) if raw is not None else None,
            "dataset_bytes": len(raw) if raw is not None else 0,
            "dataset_error": dataset_error,
        },
        "counts": {
            "completed_count": completed,
            "target_count": target_count,
            "dataset_fetch_attempts": 1,
            "dataset_rows_scanned": len(rows),
            "matched_targets": matched_targets,
            "matched_facility_rows": matched_rows,
            "pollutant_release_records": pollutant_records,
            "produced_business_rows": matched_rows,
            "produced_source_evidence_records": target_count,
        },
        "progress_percent": round(completed / target_count * 100, 6),
        "targets": results,
        "decision": {
            "exact_alias_and_coordinate_gate_required": True,
            "preview_absence_not_treated_as_full_dataset_absence": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }

    require(completed == target_count, "not all target assessments completed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
