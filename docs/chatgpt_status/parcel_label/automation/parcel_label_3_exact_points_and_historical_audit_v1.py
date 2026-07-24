from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "parcel_label_3"
TASK_VERSION = "1.0-guarded"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
CACHE_ROOT = Path(tempfile.gettempdir()) / "aays_parcel_label_slot3"

CANONICAL_BRANCH = "codex/aays-single-runner-v5-20260706"
CANONICAL_REPO_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
CANONICAL_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
CANONICAL_CACHE_PATH = CACHE_ROOT / "parcel_security_scores_rechecked_0_120m_spatial.geojson"

HISTORICAL_ARTIFACT_REPO_PATH = "england_map_web/data/distance_property_types/parcel_label_3_historical_198_quarantine.json"
HISTORICAL_ARTIFACT_BLOB_SHA = "bda76aee331acc0b9f33cccdf968c4314fe433a9"
HISTORICAL_ARTIFACT_CACHE_PATH = CACHE_ROOT / "parcel_label_3_historical_198_quarantine.json"

RUNNER_OUTPUT = REPO / "docs/chatgpt_status/parcel_label/runner_outputs/parcel_label_3_exact_points_and_historical_audit_latest.json"
WEBSITE_OUTPUT = REPO / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"

DISTANCE_FIELDS = [
    "nearest_industrial_unit_distance_m",
    "nearest_detached_home_distance_m",
    "nearest_retail_property_distance_m",
    "nearest_apartment_building_distance_m",
    "nearest_office_building_distance_m",
    "nearest_mixed_building_distance_m",
    "selected_match_distance_m",
]
REQUIRED_SCHEMA_FIELDS = [
    "parcel_id",
    "geometry_wkt",
    "centroid_lat",
    "centroid_lon",
    "selected_property_type",
    "source_url",
    "accuracy_score_4",
    "geometry_status",
    "candidate_status",
    "fake_data",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_git(args: list[str], timeout: int = 600, stdout_handle=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        check=False,
        stdout=stdout_handle if stdout_handle is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def git_hash_object(path: Path) -> str | None:
    try:
        result = run_git(["hash-object", str(path)], timeout=120)
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace").strip() or None


def export_blob_by_sha(blob_sha: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_suffix(destination.suffix + ".part")
    part.unlink(missing_ok=True)
    evidence = {"route": "git_cat_file_blob", "blob_sha": blob_sha, "returncode": None, "stderr": None, "verified": False}
    try:
        with part.open("wb") as handle:
            result = run_git(["cat-file", "blob", blob_sha], stdout_handle=handle)
        evidence["returncode"] = result.returncode
        evidence["stderr"] = result.stderr.decode("utf-8", errors="replace")[-2000:]
        if result.returncode != 0:
            part.unlink(missing_ok=True)
            return evidence
        actual_sha = git_hash_object(part)
        evidence["actual_blob_sha"] = actual_sha
        evidence["verified"] = actual_sha == blob_sha
        if not evidence["verified"]:
            part.unlink(missing_ok=True)
            return evidence
        os.replace(part, destination)
        return evidence
    except Exception as exc:
        part.unlink(missing_ok=True)
        evidence["stderr"] = str(exc)
        return evidence


def export_path_from_ref(ref: str, repo_path: str, expected_blob_sha: str, destination: Path) -> dict:
    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_suffix(destination.suffix + ".part")
    part.unlink(missing_ok=True)
    evidence = {"route": "git_show_ref_path", "ref": ref, "repo_path": repo_path, "returncode": None, "stderr": None, "verified": False}
    try:
        with part.open("wb") as handle:
            result = run_git(["show", f"{ref}:{repo_path}"], stdout_handle=handle)
        evidence["returncode"] = result.returncode
        evidence["stderr"] = result.stderr.decode("utf-8", errors="replace")[-2000:]
        if result.returncode != 0:
            part.unlink(missing_ok=True)
            return evidence
        actual_sha = git_hash_object(part)
        evidence["actual_blob_sha"] = actual_sha
        evidence["verified"] = actual_sha == expected_blob_sha
        if not evidence["verified"]:
            part.unlink(missing_ok=True)
            return evidence
        os.replace(part, destination)
        return evidence
    except Exception as exc:
        part.unlink(missing_ok=True)
        evidence["stderr"] = str(exc)
        return evidence


def materialize_exact_blob(branch: str, repo_path: str, blob_sha: str, cache_path: Path) -> tuple[Path | None, dict]:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "branch": branch,
        "repo_path": repo_path,
        "expected_blob_sha": blob_sha,
        "cache_path": str(cache_path),
        "cache_hit": False,
        "fetch_attempted": False,
        "fetch_returncode": None,
        "fetch_stderr": None,
        "attempts": [],
        "verified": False,
        "error": None,
    }
    if cache_path.is_file() and git_hash_object(cache_path) == blob_sha:
        evidence.update({"cache_hit": True, "verified": True, "actual_blob_sha": blob_sha})
        return cache_path, evidence
    cache_path.unlink(missing_ok=True)

    attempt = export_blob_by_sha(blob_sha, cache_path)
    evidence["attempts"].append(attempt)
    if attempt["verified"]:
        evidence.update({"verified": True, "source_route": "local_git_object"})
        return cache_path, evidence

    for ref in (f"origin/{branch}", branch):
        attempt = export_path_from_ref(ref, repo_path, blob_sha, cache_path)
        evidence["attempts"].append(attempt)
        if attempt["verified"]:
            evidence.update({"verified": True, "source_route": ref})
            return cache_path, evidence

    evidence["fetch_attempted"] = True
    try:
        fetch = run_git(["fetch", "origin", branch], timeout=900)
        evidence["fetch_returncode"] = fetch.returncode
        evidence["fetch_stderr"] = fetch.stderr.decode("utf-8", errors="replace")[-2000:]
    except Exception as exc:
        evidence["error"] = str(exc)
        return None, evidence

    if evidence["fetch_returncode"] == 0:
        for route in (
            lambda: export_blob_by_sha(blob_sha, cache_path),
            lambda: export_path_from_ref("FETCH_HEAD", repo_path, blob_sha, cache_path),
        ):
            attempt = route()
            evidence["attempts"].append(attempt)
            if attempt["verified"]:
                evidence.update({"verified": True, "source_route": attempt.get("route")})
                return cache_path, evidence

    evidence["error"] = "Exact Git blob could not be materialized and verified."
    return None, evidence


def is_nonempty(value) -> bool:
    return value is not None and str(value).strip() != ""


def parse_canonical_points(path: Path | None) -> tuple[list[dict], dict]:
    evidence = {"target_ids": TARGET_IDS, "feature_count": None, "targets_found": [], "all_points_valid": False, "error": None}
    rows: list[dict] = []
    if path is None:
        evidence["error"] = "Canonical source path unavailable."
        return rows, evidence
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            raise ValueError("Canonical source does not contain a features array.")
        evidence["feature_count"] = len(features)
        found: dict[str, dict] = {}
        for feature in features:
            props = feature.get("properties") or {}
            parcel_id = props.get("security_parcel_id") or props.get("parcel_id")
            if parcel_id not in TARGET_IDS:
                continue
            geometry = feature.get("geometry") or {}
            coordinates = geometry.get("coordinates")
            valid = (
                geometry.get("type") == "Point"
                and isinstance(coordinates, list)
                and len(coordinates) >= 2
                and isinstance(coordinates[0], (int, float))
                and isinstance(coordinates[1], (int, float))
            )
            found[parcel_id] = {
                "parcel_id": parcel_id,
                "geometry_type": geometry.get("type"),
                "longitude": coordinates[0] if valid else None,
                "latitude": coordinates[1] if valid else None,
                "point_valid": valid,
                "source_git_blob_sha": CANONICAL_BLOB_SHA,
                "security_score_fields_copied": False,
                "property_type_bound": False,
            }
        rows = [found[target] for target in TARGET_IDS if target in found]
        evidence["targets_found"] = [row["parcel_id"] for row in rows]
        evidence["all_points_valid"] = len(rows) == len(TARGET_IDS) and all(row["point_valid"] for row in rows)
        return rows, evidence
    except Exception as exc:
        evidence["error"] = str(exc)
        return rows, evidence


def parse_historical_artifact(path: Path | None) -> dict:
    audit = {
        "row_count": 0,
        "unique_id_count": 0,
        "duplicate_id_count": 0,
        "duplicate_ids": [],
        "source_placeholder_id_count": 0,
        "canonical_parcel_id_count": 0,
        "geometry_wkt_nonempty_count": 0,
        "centroid_complete_count": 0,
        "selected_match_distance_nonempty_count": 0,
        "any_distance_nonempty_count": 0,
        "all_distance_fields_nonempty_count": 0,
        "fake_data_true_count": 0,
        "final_ready_true_count": 0,
        "geometry_status_counts": {},
        "property_type_counts": {},
        "schema_field_coverage": {},
        "checkpoint_row_count_match": False,
        "full_parse_complete": False,
        "error": None,
    }
    if path is None:
        audit["error"] = "Historical artifact path unavailable."
        return audit
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise ValueError("Historical artifact does not contain a rows array.")
        ids = [str(row.get("parcel_id") or "").strip() for row in rows]
        id_counts = Counter(ids)
        duplicates = sorted(parcel_id for parcel_id, count in id_counts.items() if parcel_id and count > 1)
        audit.update(
            {
                "row_count": len(rows),
                "unique_id_count": len({parcel_id for parcel_id in ids if parcel_id}),
                "duplicate_id_count": len(duplicates),
                "duplicate_ids": duplicates,
                "source_placeholder_id_count": sum(parcel_id.startswith("SOURCE_") for parcel_id in ids),
                "canonical_parcel_id_count": sum(bool(re.fullmatch(r"parcel_\d+", parcel_id)) for parcel_id in ids),
                "geometry_wkt_nonempty_count": sum(is_nonempty(row.get("geometry_wkt")) for row in rows),
                "centroid_complete_count": sum(is_nonempty(row.get("centroid_lat")) and is_nonempty(row.get("centroid_lon")) for row in rows),
                "selected_match_distance_nonempty_count": sum(is_nonempty(row.get("selected_match_distance_m")) for row in rows),
                "any_distance_nonempty_count": sum(any(is_nonempty(row.get(field)) for field in DISTANCE_FIELDS) for row in rows),
                "all_distance_fields_nonempty_count": sum(all(is_nonempty(row.get(field)) for field in DISTANCE_FIELDS) for row in rows),
                "fake_data_true_count": sum(row.get("fake_data") is True for row in rows),
                "final_ready_true_count": sum(row.get("final_ready") is True for row in rows),
                "geometry_status_counts": dict(sorted(Counter(str(row.get("geometry_status") or "MISSING") for row in rows).items())),
                "property_type_counts": dict(sorted(Counter(str(row.get("selected_property_type") or "MISSING") for row in rows).items())),
                "schema_field_coverage": {field: sum(field in row for row in rows) for field in REQUIRED_SCHEMA_FIELDS},
                "checkpoint_row_count_match": len(rows) == 198,
                "full_parse_complete": True,
            }
        )
        return audit
    except Exception as exc:
        audit["error"] = str(exc)
        return audit


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(part, path)


def main() -> int:
    canonical_path, canonical_materialization = materialize_exact_blob(
        CANONICAL_BRANCH, CANONICAL_REPO_PATH, CANONICAL_BLOB_SHA, CANONICAL_CACHE_PATH
    )
    historical_main_path = REPO / HISTORICAL_ARTIFACT_REPO_PATH
    if historical_main_path.is_file() and git_hash_object(historical_main_path) == HISTORICAL_ARTIFACT_BLOB_SHA:
        historical_path = historical_main_path
        historical_materialization = {
            "verified": True,
            "source_route": "main_quarantine_path",
            "repo_path": HISTORICAL_ARTIFACT_REPO_PATH,
            "expected_blob_sha": HISTORICAL_ARTIFACT_BLOB_SHA,
            "actual_blob_sha": HISTORICAL_ARTIFACT_BLOB_SHA,
        }
    else:
        historical_path, historical_materialization = materialize_exact_blob(
            "main", HISTORICAL_ARTIFACT_REPO_PATH, HISTORICAL_ARTIFACT_BLOB_SHA, HISTORICAL_ARTIFACT_CACHE_PATH
        )

    canonical_points, canonical_parse = parse_canonical_points(canonical_path)
    historical_audit = parse_historical_artifact(historical_path)

    canonical_gate = bool(canonical_materialization.get("verified") and canonical_parse.get("all_points_valid"))
    historical_gate = bool(
        historical_materialization.get("verified")
        and historical_audit.get("full_parse_complete")
        and historical_audit.get("checkpoint_row_count_match")
    )
    if canonical_gate and historical_gate:
        state = "CANONICAL_POINTS_EXTRACTED_HISTORICAL_198ROW_AUDIT_COMPLETE_BINDING_PENDING"
    elif canonical_gate:
        state = "CANONICAL_POINTS_EXTRACTED_HISTORICAL_AUDIT_BLOCKED"
    elif historical_gate:
        state = "HISTORICAL_198ROW_AUDIT_COMPLETE_CANONICAL_POINT_EXTRACTION_BLOCKED"
    else:
        state = "FAIL_CLOSED_EXACT_BLOB_OR_PARSE_GATE_BLOCKED"

    payload = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "task_version": TASK_VERSION,
        "generated_at": utc_now(),
        "state": state,
        "target_ids": TARGET_IDS,
        "canonical_source_materialization": canonical_materialization,
        "canonical_parse": canonical_parse,
        "canonical_points": canonical_points,
        "historical_artifact_materialization": historical_materialization,
        "historical_audit": historical_audit,
        "canonical_gate_passed": canonical_gate,
        "historical_audit_gate_passed": historical_gate,
        "exact_geometry_rows": len(canonical_points) if canonical_gate else 0,
        "verified_slot_rows": 0,
        "property_type_binding_claimed": False,
        "security_scores_copied": False,
        "historical_artifact_restored_to_canonical_path": False,
        "needs_manual_review": True,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    atomic_write_json(RUNNER_OUTPUT, payload)
    atomic_write_json(WEBSITE_OUTPUT, payload)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"STATE={state}")
    print(f"CANONICAL_GATE_PASSED={str(canonical_gate).lower()}")
    print(f"HISTORICAL_AUDIT_GATE_PASSED={str(historical_gate).lower()}")
    print(f"EXACT_GEOMETRY_ROWS={payload['exact_geometry_rows']}")
    print("VERIFIED_SLOT_ROWS=0")
    print(f"OUTPUT={RUNNER_OUTPUT}")
    print(f"WEBSITE_OUTPUT={WEBSITE_OUTPUT}")
    print("FINAL_READY=false")
    return 0 if canonical_gate and historical_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
