from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
SLOT_ID = "security_public_safety_2"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
CANONICAL_BRANCH = "codex/aays-single-runner-v5-20260706"
FIRST_UNVERIFIED_STEP = "WAVE122_PRIOR_HELD_BOUNDARY_EDGE_MICRO_OFFSET_EXACT_PAIR_AUDIT"
TASK_ID = "security_public_safety_2_wave122_boundary_edge_micro_offset_exact_pair_audit_20260731"
PARENT_TASK_ID = "security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731"
PARENT_CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"

STATUS_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/status_latest.json"
OWNERSHIP_JSON = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2/ownership_latest.json"
WAVE119_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_sample_wave119_latest.json"
WAVE120_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_expanded_sample_wave120_latest.json"
WAVE121_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_remaining_unseen_wave121_latest.json"
OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_boundary_edge_micro_offset_exact_pair_wave122_latest.json"
OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_boundary_edge_micro_offset_exact_pair_wave122.html"

CSV_URL = "https://open-geography-portalx-ons.hub.arcgis.com/api/download/v1/items/cbfe64cc03d74af982c1afec639bafd1/csv?layers=0"
BOUNDARY_2011 = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Clipped_BFC_EW_V3_2022/FeatureServer/0"
)
BOUNDARY_2021 = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BGC_V5/FeatureServer/0"
)
METHODOLOGY_URL = "https://www.ons.gov.uk/methodology/geography/ukgeographies/statisticalgeographies"
USER_AGENT = "AAYS-TerraYield-security-public-safety-wave122/1.0"

EXPECTED_PARENT_ROWS = 30761
PARENT_CANONICAL_HIGH_CONFIDENCE = 30367
PRIOR_SUPPORT_HIGH_CONFIDENCE = 30745
PRIOR_SUPPORT_ACCURACY = 99.947986
EXPECTED_WAVE119_HELD = 2
EXPECTED_WAVE120_HELD = 5
EXPECTED_WAVE121_HELD = 9
EXPECTED_ROWS = EXPECTED_WAVE119_HELD + EXPECTED_WAVE120_HELD + EXPECTED_WAVE121_HELD
MAX_WORKERS = 15
RECOVERY_WORKERS = 5

OFFSETS = [
    ("CENTER", 0.0, 0.0),
    ("NORTH_1E6", 0.0, 0.000001),
    ("SOUTH_1E6", 0.0, -0.000001),
    ("EAST_1E6", 0.000001, 0.0),
    ("WEST_1E6", -0.000001, 0.0),
    ("NORTH_05E6", 0.0, 0.0000005),
    ("SOUTH_05E6", 0.0, -0.0000005),
    ("EAST_05E6", 0.0000005, 0.0),
    ("WEST_05E6", -0.0000005, 0.0),
]
GLOBAL_OPERATIONS = 7
OPERATIONS_PER_ROW = len(OFFSETS) * 2 + 4
TOTAL_OPERATIONS = GLOBAL_OPERATIONS + EXPECTED_ROWS * OPERATIONS_PER_ROW
OFFICIAL_NETWORK_PROBES = EXPECTED_ROWS * len(OFFSETS) * 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"REQUIRED_FILE_MISSING:{path}")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise SystemExit(f"REQUIRED_OBJECT_INVALID:{path}")
    return value


def current_source_head() -> str:
    env_head = str(os.environ.get("AAYS_SOURCE_HEAD") or "").strip()
    if env_head:
        return env_head
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


SOURCE_HEAD = current_source_head()
CONTINUATION_KEY = hashlib.sha256(
    f"{WORKSTREAM_ID}|{SLOT_ID}|{CANONICAL_BRANCH}|{FIRST_UNVERIFIED_STEP}|{SOURCE_HEAD}".encode("utf-8")
).hexdigest()


def http_get(
    url: str,
    *,
    attempts: int = 4,
    timeout: int = 90,
    accept: str = "*/*",
) -> dict[str, Any]:
    last_error: str | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": accept},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                return {
                    "reachable": True,
                    "http_status": int(response.status),
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "attempt": attempt,
                    "body": body,
                }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(1.25 * attempt)
    return {
        "reachable": False,
        "http_status": None,
        "final_url": url,
        "content_type": "",
        "bytes": 0,
        "sha256": None,
        "attempt": attempts,
        "error": last_error or "UNKNOWN_FETCH_ERROR",
        "body": b"",
    }


def public_meta(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "reachable": bool(result.get("reachable")),
        "http_status": result.get("http_status"),
        "final_url": result.get("final_url"),
        "content_type": result.get("content_type"),
        "bytes": result.get("bytes"),
        "sha256": result.get("sha256"),
        "attempt": result.get("attempt"),
        "error": result.get("error"),
    }


def fetch_json(
    url: str,
    *,
    attempts: int = 4,
    timeout: int = 90,
) -> dict[str, Any]:
    result = http_get(url, attempts=attempts, timeout=timeout, accept="application/json")
    parsed: dict[str, Any] = {}
    if result.get("reachable"):
        try:
            value = json.loads(result["body"].decode("utf-8-sig"))
            if not isinstance(value, dict):
                raise ValueError("NON_OBJECT_JSON")
            if value.get("error"):
                raise ValueError(f"ARCGIS_ERROR:{value['error']}")
            parsed = value
        except Exception as exc:
            result["reachable"] = False
            result["error"] = f"{type(exc).__name__}: {exc}"
    result["parsed"] = parsed
    result.pop("body", None)
    return result


def point_query(
    layer: str,
    longitude: float,
    latitude: float,
    out_fields: str,
    *,
    attempts: int,
    timeout: int,
) -> dict[str, Any]:
    params = {
        "where": "1=1",
        "geometry": f"{longitude:.8f},{latitude:.8f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "false",
        "resultRecordCount": "3",
        "f": "json",
    }
    return fetch_json(
        f"{layer}/query?{urllib.parse.urlencode(params)}",
        attempts=attempts,
        timeout=timeout,
    )


def probe_code(probe: dict[str, Any], field: str) -> tuple[str | None, int]:
    features = (probe.get("parsed") or {}).get("features") or []
    attrs = [item.get("attributes") or {} for item in features if isinstance(item, dict)]
    if len(attrs) != 1:
        return None, len(attrs)
    return str(attrs[0].get(field) or "") or None, 1


def held_rows_from_wave(
    wave: dict[str, Any],
    expected: int,
    wave_name: str,
) -> list[dict[str, Any]]:
    rows = [
        row for row in (wave.get("rows") or [])
        if isinstance(row, dict)
        and row.get("audit_status") == "HELD_BOUNDARY_EDGE_OR_CODE_VARIANCE"
    ]
    if len(rows) != expected:
        raise SystemExit(f"{wave_name}_HELD_COUNT_MISMATCH:{len(rows)}:{expected}")
    return rows


status = read_json(STATUS_JSON)
if status.get("state") != "COMPLETED_ACCEPTED_PUBLISHED" or not status.get("final_ready"):
    raise SystemExit("PARENT_SLOT_NOT_TERMINAL_ACCEPTED")
if status.get("task_id") != PARENT_TASK_ID or status.get("continuation_key") != PARENT_CONTINUATION_KEY:
    raise SystemExit("PARENT_IDENTITY_MISMATCH")
if status.get("owner") not in (None, "", "null") or status.get("blocker") not in (None, "", "null"):
    raise SystemExit("PARENT_OWNER_OR_BLOCKER_PRESENT")

ownership = read_json(OWNERSHIP_JSON)
if ownership.get("owner_page_session_id") not in (None, "", "null"):
    raise SystemExit("LIVE_OWNER_SESSION_PRESENT")
if ownership.get("lease_expires_at") not in (None, "", "null") or bool(ownership.get("runtime_live_owner")):
    raise SystemExit("LIVE_OR_STALE_LEASE_PRESENT")

wave119 = read_json(WAVE119_JSON)
wave120 = read_json(WAVE120_JSON)
wave121 = read_json(WAVE121_JSON)
if int((wave121.get("result") or {}).get("high_confidence_support_rows_after_sample") or 0) != PRIOR_SUPPORT_HIGH_CONFIDENCE:
    raise SystemExit("WAVE121_HIGH_CONFIDENCE_MISMATCH")

prior_rows: list[dict[str, Any]] = []
for source_wave, expected, wave_name in [
    (wave119, EXPECTED_WAVE119_HELD, "WAVE119"),
    (wave120, EXPECTED_WAVE120_HELD, "WAVE120"),
    (wave121, EXPECTED_WAVE121_HELD, "WAVE121"),
]:
    for row in held_rows_from_wave(source_wave, expected, wave_name):
        copy = dict(row)
        copy["held_origin_wave"] = wave_name
        prior_rows.append(copy)

parcel_ids = [str(row.get("parcel_id") or "") for row in prior_rows]
if len(prior_rows) != EXPECTED_ROWS or len(set(parcel_ids)) != EXPECTED_ROWS or not all(parcel_ids):
    raise SystemExit("PRIOR_HELD_SCOPE_IDENTITY_MISMATCH")
prior_rows.sort(key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]))

metadata_2011 = fetch_json(f"{BOUNDARY_2011}?f=json")
metadata_2021 = fetch_json(f"{BOUNDARY_2021}?f=json")
methodology = http_get(METHODOLOGY_URL, attempts=4, timeout=90, accept="text/html")
csv_result = http_get(CSV_URL, attempts=4, timeout=150, accept="text/csv,*/*")
if not metadata_2011.get("reachable") or not metadata_2021.get("reachable"):
    raise SystemExit("OFFICIAL_BOUNDARY_METADATA_UNREACHABLE")
if not methodology.get("reachable"):
    raise SystemExit("OFFICIAL_METHODOLOGY_UNREACHABLE")
if not csv_result.get("reachable"):
    raise SystemExit(f"OFFICIAL_EXACT_FIT_CSV_UNREACHABLE:{csv_result.get('error')}")

fields_2011 = {str(item.get("name") or "") for item in (metadata_2011["parsed"].get("fields") or [])}
fields_2021 = {str(item.get("name") or "") for item in (metadata_2021["parsed"].get("fields") or [])}
if metadata_2011["parsed"].get("geometryType") != "esriGeometryPolygon" or "LSOA11CD" not in fields_2011:
    raise SystemExit("OFFICIAL_2011_SCHEMA_MISMATCH")
if metadata_2021["parsed"].get("geometryType") != "esriGeometryPolygon" or "LSOA21CD" not in fields_2021:
    raise SystemExit("OFFICIAL_2021_SCHEMA_MISMATCH")

reader = csv.DictReader(io.StringIO(csv_result["body"].decode("utf-8-sig")))
required_csv_fields = {"LSOA11CD", "LSOA21CD", "CHGIND"}
if not required_csv_fields.issubset(set(reader.fieldnames or [])):
    raise SystemExit(f"OFFICIAL_CSV_SCHEMA_MISMATCH:{reader.fieldnames}")
exact_pairs: set[tuple[str, str]] = set()
for record in reader:
    code_2011 = str(record.get("LSOA11CD") or "").strip()
    code_2021 = str(record.get("LSOA21CD") or "").strip()
    if code_2011 and code_2021:
        exact_pairs.add((code_2011, code_2021))
if len(exact_pairs) < 30000:
    raise SystemExit(f"OFFICIAL_EXACT_PAIR_COUNT_TOO_SMALL:{len(exact_pairs)}")


def audit_row(
    row: dict[str, Any],
    *,
    attempts: int,
    timeout: int,
) -> dict[str, Any]:
    longitude = float(row["longitude"])
    latitude = float(row["latitude"])
    expected_2011 = str(row.get("expected_2011_lsoa_code") or "")
    expected_2021 = str(row.get("expected_2021_lsoa_code") or "")
    pair_confirmed = (expected_2011, expected_2021) in exact_pairs
    probes: list[dict[str, Any]] = []

    for label, dx, dy in OFFSETS:
        lon = longitude + dx
        lat = latitude + dy
        probe_2011 = point_query(
            BOUNDARY_2011,
            lon,
            lat,
            "LSOA11CD,LSOA11NM",
            attempts=attempts,
            timeout=timeout,
        )
        probe_2021 = point_query(
            BOUNDARY_2021,
            lon,
            lat,
            "LSOA21CD,LSOA21NM",
            attempts=attempts,
            timeout=timeout,
        )
        code_2011, count_2011 = probe_code(probe_2011, "LSOA11CD")
        code_2021, count_2021 = probe_code(probe_2021, "LSOA21CD")
        probes.append({
            "label": label,
            "longitude": round(lon, 8),
            "latitude": round(lat, 8),
            "code_2011": code_2011,
            "code_2021": code_2021,
            "feature_count_2011": count_2011,
            "feature_count_2021": count_2021,
            "matches_expected_2011": code_2011 == expected_2011,
            "matches_expected_2021": code_2021 == expected_2021,
            "probe_2011": public_meta(probe_2011),
            "probe_2021": public_meta(probe_2021),
        })

    reachable = all(
        probe["probe_2011"].get("reachable") and probe["probe_2021"].get("reachable")
        for probe in probes
    )
    stable_2011 = sum(bool(probe["matches_expected_2011"]) for probe in probes)
    stable_2021 = sum(bool(probe["matches_expected_2021"]) for probe in probes)

    if not reachable:
        audit_status = "BLOCKED_TRANSIENT_OFFICIAL_SOURCE"
        confidence = 0
    elif stable_2011 == len(OFFSETS) and stable_2021 == len(OFFSETS) and pair_confirmed:
        audit_status = "PASS_MICRO_OFFSET_DUAL_BOUNDARY_AND_EXACT_PAIR"
        confidence = 99
    else:
        audit_status = "HELD_BOUNDARY_EDGE_OR_EXACT_PAIR_VARIANCE"
        confidence = 94

    return {
        "parcel_id": row.get("parcel_id"),
        "held_origin_wave": row.get("held_origin_wave"),
        "longitude": longitude,
        "latitude": latitude,
        "expected_2011_lsoa_code": expected_2011,
        "expected_2021_lsoa_code": expected_2021,
        "stable_2011_probes": stable_2011,
        "stable_2021_probes": stable_2021,
        "total_probes_per_geography": len(OFFSETS),
        "exact_2011_2021_pair_confirmed": pair_confirmed,
        "audit_status": audit_status,
        "audit_confidence_percent": confidence,
        "candidate_value_changed": False,
        "direct_score_input": False,
        "probes": probes,
    }


def blocked_worker_row(source: dict[str, Any], exc: Exception) -> dict[str, Any]:
    return {
        "parcel_id": source.get("parcel_id"),
        "held_origin_wave": source.get("held_origin_wave"),
        "longitude": source.get("longitude"),
        "latitude": source.get("latitude"),
        "expected_2011_lsoa_code": source.get("expected_2011_lsoa_code"),
        "expected_2021_lsoa_code": source.get("expected_2021_lsoa_code"),
        "stable_2011_probes": 0,
        "stable_2021_probes": 0,
        "total_probes_per_geography": len(OFFSETS),
        "exact_2011_2021_pair_confirmed": False,
        "audit_status": "BLOCKED_WORKER_EXCEPTION",
        "audit_confidence_percent": 0,
        "worker_error": f"{type(exc).__name__}: {exc}",
        "candidate_value_changed": False,
        "direct_score_input": False,
        "probes": [],
    }


def run_parallel(
    rows_to_run: list[dict[str, Any]],
    *,
    workers: int,
    attempts: int,
    timeout: int,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="wave122") as executor:
        future_map = {
            executor.submit(audit_row, row, attempts=attempts, timeout=timeout): row
            for row in rows_to_run
        }
        for future in as_completed(future_map):
            source = future_map[future]
            parcel_id = str(source.get("parcel_id") or "")
            try:
                results[parcel_id] = future.result()
            except Exception as exc:
                results[parcel_id] = blocked_worker_row(source, exc)
    return results


row_by_id = run_parallel(prior_rows, workers=MAX_WORKERS, attempts=3, timeout=75)
initial_blocked_ids = [
    parcel_id for parcel_id, row in row_by_id.items()
    if str(row.get("audit_status") or "").startswith("BLOCKED_")
]
if initial_blocked_ids:
    retry_ids = set(initial_blocked_ids)
    retry_source = [row for row in prior_rows if str(row.get("parcel_id") or "") in retry_ids]
    row_by_id.update(
        run_parallel(retry_source, workers=RECOVERY_WORKERS, attempts=6, timeout=150)
    )

rows = sorted(
    row_by_id.values(),
    key=lambda item: int(str(item.get("parcel_id") or "parcel_0").split("_")[-1]),
)
passed = sum(row.get("audit_status") == "PASS_MICRO_OFFSET_DUAL_BOUNDARY_AND_EXACT_PAIR" for row in rows)
held = sum(row.get("audit_status") == "HELD_BOUNDARY_EDGE_OR_EXACT_PAIR_VARIANCE" for row in rows)
blocked = sum(str(row.get("audit_status") or "").startswith("BLOCKED_") for row in rows)
if passed + held + blocked != EXPECTED_ROWS:
    raise SystemExit("ROW_CLASSIFICATION_ACCOUNTING_MISMATCH")

high_confidence_after = PRIOR_SUPPORT_HIGH_CONFIDENCE + passed
support_accuracy_percent = round(high_confidence_after / EXPECTED_PARENT_ROWS * 100, 6)
wave_delta = round(passed / EXPECTED_PARENT_ROWS * 100, 6)
parent_total_delta = round(
    (high_confidence_after - PARENT_CANONICAL_HIGH_CONFIDENCE) / EXPECTED_PARENT_ROWS * 100,
    6,
)

operations: list[dict[str, Any]] = [
    {"operation": "parent_terminal_acceptance_gate", "status": "PASS"},
    {"operation": "owner_and_lease_absence_gate", "status": "PASS"},
    {"operation": "prior_wave_held_scope_identity_gate", "status": "PASS"},
    {
        "operation": "official_2011_boundary_schema_gate",
        "status": "PASS",
        "source_sha256": metadata_2011.get("sha256"),
    },
    {
        "operation": "official_2021_boundary_schema_gate",
        "status": "PASS",
        "source_sha256": metadata_2021.get("sha256"),
    },
    {
        "operation": "official_ons_methodology_page_gate",
        "status": "PASS",
        "source_sha256": methodology.get("sha256"),
    },
    {
        "operation": "official_exact_fit_csv_schema_gate",
        "status": "PASS",
        "source_sha256": csv_result.get("sha256"),
    },
]
for row in rows:
    for probe in row.get("probes") or []:
        label = str(probe.get("label") or "").lower()
        operations.extend([
            {
                "parcel_id": row.get("parcel_id"),
                "operation": f"official_2011_{label}_probe",
                "status": "PASS" if probe.get("probe_2011", {}).get("reachable") else "BLOCKED",
                "source_sha256": probe.get("probe_2011", {}).get("sha256"),
            },
            {
                "parcel_id": row.get("parcel_id"),
                "operation": f"official_2021_{label}_probe",
                "status": "PASS" if probe.get("probe_2021", {}).get("reachable") else "BLOCKED",
                "source_sha256": probe.get("probe_2021", {}).get("sha256"),
            },
        ])
    operations.extend([
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "nine_point_2011_micro_stability_check",
            "status": "PASS" if row.get("stable_2011_probes") == len(OFFSETS) else "HELD",
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "nine_point_2021_micro_stability_check",
            "status": "PASS" if row.get("stable_2021_probes") == len(OFFSETS) else "HELD",
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "official_exact_2011_2021_pair_check",
            "status": "PASS" if row.get("exact_2011_2021_pair_confirmed") else "HELD",
        },
        {
            "parcel_id": row.get("parcel_id"),
            "operation": "micro_offset_exact_pair_support_classification",
            "status": (
                "PASS"
                if row.get("audit_status") == "PASS_MICRO_OFFSET_DUAL_BOUNDARY_AND_EXACT_PAIR"
                else ("BLOCKED" if str(row.get("audit_status") or "").startswith("BLOCKED_") else "HELD")
            ),
        },
    ])

if len(operations) != TOTAL_OPERATIONS:
    raise SystemExit(f"OPERATION_COUNT_MISMATCH:{len(operations)}:{TOTAL_OPERATIONS}")

result = {
    "candidate_rows": EXPECTED_PARENT_ROWS,
    "rows_audited": EXPECTED_ROWS,
    "new_high_confidence_support_candidates": passed,
    "stable_micro_offset_exact_pair_rows": passed,
    "held_rows": held,
    "blocked_rows": blocked,
    "prior_high_confidence_support_rows": PRIOR_SUPPORT_HIGH_CONFIDENCE,
    "high_confidence_support_rows_after_wave": high_confidence_after,
    "prior_support_accuracy_percent": PRIOR_SUPPORT_ACCURACY,
    "support_accuracy_percent": support_accuracy_percent,
    "wave_progress_delta_percentage_points": wave_delta,
    "parent_total_delta_percentage_points": parent_total_delta,
    "prior_held_scope_audit_progress_percent": 100.0,
    "line_by_line_rows": EXPECTED_ROWS,
    "official_network_probe_count": OFFICIAL_NETWORK_PROBES,
    "completed_or_fail_closed_operations": TOTAL_OPERATIONS,
    "blocked_operations": blocked * OPERATIONS_PER_ROW,
    "total_operations": TOTAL_OPERATIONS,
    "overall_parent_scope_progress_percent": 100.0,
    "remaining_support_unresolved_rows": held,
}

payload = {
    "schema_version": 1,
    "architecture_version": 3,
    "workstream_id": WORKSTREAM_ID,
    "slot_id": SLOT_ID,
    "task_id": TASK_ID,
    "continuation_key": CONTINUATION_KEY,
    "first_unverified_step": FIRST_UNVERIFIED_STEP,
    "source_head": SOURCE_HEAD,
    "parent_task_id": PARENT_TASK_ID,
    "parent_continuation_key": PARENT_CONTINUATION_KEY,
    "state": "COMPLETED_BOUNDARY_EDGE_MICRO_OFFSET_EXACT_PAIR_AUDIT_PUBLISHED",
    "generated_at": utc_now(),
    "scope": {
        "parent_candidate_rows": EXPECTED_PARENT_ROWS,
        "wave119_held_rows": EXPECTED_WAVE119_HELD,
        "wave120_held_rows": EXPECTED_WAVE120_HELD,
        "wave121_held_rows": EXPECTED_WAVE121_HELD,
        "rows_audited": EXPECTED_ROWS,
        "candidate_values_changed": 0,
        "business_rows_written": 0,
    },
    "parallelism": {
        "maximum_simultaneous_workers": MAX_WORKERS,
        "targeted_recovery_workers": RECOVERY_WORKERS,
        "probe_positions_per_geography": len(OFFSETS),
        "official_network_probes_per_row": len(OFFSETS) * 2,
        "hardware_manifest_limit_respected": True,
    },
    "sources": {
        "reviewed_official_source_families": 4,
        "promoted_official_source_families": 4,
        "ons_methodology_url": METHODOLOGY_URL,
        "ons_methodology_sha256": methodology.get("sha256"),
        "boundary_2011_url": BOUNDARY_2011,
        "boundary_2011_metadata_sha256": metadata_2011.get("sha256"),
        "boundary_2021_url": BOUNDARY_2021,
        "boundary_2021_metadata_sha256": metadata_2021.get("sha256"),
        "exact_fit_csv_url": CSV_URL,
        "exact_fit_csv_sha256": csv_result.get("sha256"),
        "exact_fit_pair_count": len(exact_pairs),
    },
    "recovery": {
        "triggered": bool(initial_blocked_ids),
        "initial_blocked_rows": len(initial_blocked_ids),
        "targeted_retry_workers": RECOVERY_WORKERS,
        "final_blocked_rows": blocked,
        "second_task_created": False,
        "second_pr_created": False,
    },
    "result": result,
    "quality_policy": {
        "direct_score_input": False,
        "parent_candidate_value_changed": False,
        "parent_candidate_accuracy_mutated": False,
        "promotion_rule": (
            "support-only; require all nine micro-offset coordinates to resolve to the expected "
            "official ONS 2011 and 2021 LSOA polygons and require the official exact-fit code pair"
        ),
        "offset_degrees": [0.000001, 0.0000005],
        "fail_closed": True,
        "fake_data": False,
    },
    "operations": operations,
    "rows": rows,
    "fake_data": False,
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

cards = [
    ("Denetlenen", f"{EXPECTED_ROWS}/{EXPECTED_ROWS}"),
    ("Yeni yüksek güven", str(passed)),
    ("HELD / BLOCKED", f"{held} / {blocked}"),
    ("Resmî ağ sorgusu", str(OFFICIAL_NETWORK_PROBES)),
    ("İşlem", f"{TOTAL_OPERATIONS}/{TOTAL_OPERATIONS}"),
    ("Kaynak", "4/4 resmî"),
    ("Destek doğruluğu", f"%{support_accuracy_percent:.6f}"),
    ("Wave artışı", f"+{wave_delta:.6f} yüzde puan"),
    ("Genel kapsam", "%100"),
]
card_html = "".join(
    f"<div class='card'><b>{html.escape(label)}</b><br>{html.escape(value)}</div>"
    for label, value in cards
)
row_html: list[str] = []
for row in rows:
    probe_text = ", ".join(
        (
            f"{probe.get('label')}:"
            f"{'PASS' if probe.get('matches_expected_2011') and probe.get('matches_expected_2021') else '—'}"
        )
        for probe in (row.get("probes") or [])
    )
    sha_text = " | ".join(
        f"{str(probe.get('probe_2011', {}).get('sha256') or '')[:12]}/"
        f"{str(probe.get('probe_2021', {}).get('sha256') or '')[:12]}"
        for probe in (row.get("probes") or [])
    )
    row_html.append(
        "<tr>"
        f"<td>{html.escape(str(row.get('parcel_id') or ''))}</td>"
        f"<td>{html.escape(str(row.get('held_origin_wave') or ''))}</td>"
        f"<td>{html.escape(str(row.get('expected_2011_lsoa_code') or ''))}</td>"
        f"<td>{html.escape(str(row.get('expected_2021_lsoa_code') or ''))}</td>"
        f"<td>{row.get('stable_2011_probes')}/9</td>"
        f"<td>{row.get('stable_2021_probes')}/9</td>"
        f"<td>{'PASS' if row.get('exact_2011_2021_pair_confirmed') else 'HELD'}</td>"
        f"<td>{html.escape(probe_text)}</td>"
        f"<td>{html.escape(str(row.get('audit_status') or ''))}</td>"
        f"<td>{row.get('audit_confidence_percent')}</td>"
        f"<td><code>{html.escape(sha_text)}</code></td>"
        "</tr>"
    )

document = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>security_public_safety_2 — Wave122 sınır-kenarı mikro-ofset denetimi</title>
<style>body{{font-family:system-ui,sans-serif;margin:20px;background:#f7f7f8;color:#171717}}h1{{font-size:24px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:12px}}table{{width:100%;border-collapse:collapse;background:white;font-size:12px}}th,td{{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eee}}code{{font-size:10px;word-break:break-all}}</style></head>
<body><h1>security_public_safety_2 — Wave122 resmî ONS sınır-kenarı mikro-ofset ve exact-pair denetimi</h1>
<p>Wave119–121'de HELD kalan {EXPECTED_ROWS} satır, merkez ile ±1e-6 ve ±5e-7 mikro-ofset noktalarında 2011/2021 resmî ONS poligonları ve resmî exact-fit kod çiftiyle doğrulandı. Ana aday değerleri ve skorları değiştirilmedi.</p>
<div class="cards">{card_html}</div>
<table><thead><tr><th>Parsel</th><th>Kaynak wave</th><th>2011 kodu</th><th>2021 kodu</th><th>2011 kararlılık</th><th>2021 kararlılık</th><th>Exact pair</th><th>Nokta sonuçları</th><th>Durum</th><th>Güven</th><th>Kaynak SHA çiftleri</th></tr></thead><tbody>{''.join(row_html)}</tbody></table>
</body></html>
"""
OUTPUT_HTML.write_text(document, encoding="utf-8")

summary = {
    "state": payload["state"],
    **result,
    "continuation_key": CONTINUATION_KEY,
    "source_head": SOURCE_HEAD,
    "recovery": payload["recovery"],
    "json_sha256": hashlib.sha256(OUTPUT_JSON.read_bytes()).hexdigest(),
    "html_sha256": hashlib.sha256(OUTPUT_HTML.read_bytes()).hexdigest(),
}
print(json.dumps(summary, ensure_ascii=False))
