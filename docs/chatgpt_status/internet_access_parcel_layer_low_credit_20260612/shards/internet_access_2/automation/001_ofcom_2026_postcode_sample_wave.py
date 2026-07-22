# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
PARTITION_START = 30762
PARTITION_END = 61522
SAMPLE_SIZE = 12
SOURCE_SNAPSHOT = "2026-01"
SOURCE_RELEASE = "Connected Nations Spring 2026 v2 (2026-07-07 correction)"
ZIP_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
)
ABOUT_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf?v=422757"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def append_progress(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"at": utc_now(), "step": step, "operation": operation, "state": state, **extra}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def norm_postcode(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def postcode_area(postcode: str) -> str:
    match = re.match(r"^[A-Z]+", postcode)
    return match.group(0) if match else ""


def norm_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def parse_percent(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.casefold() in {"na", "n/a", "null", "none", "-"}:
        return None
    try:
        return round(float(text), 4)
    except ValueError:
        return None


def parse_legacy_value(text: Any) -> dict[str, Any]:
    raw = str(text or "")
    patterns = {
        "postcode": r"postcode=([^;]+)",
        "gigabit_available_pct": r"gigabit=([0-9.]+)%",
        "ultrafast_100mbps_available_pct": r"ufbb100=([0-9.]+)%",
        "superfast_30mbps_available_pct": r"sfbb=([0-9.]+)%",
        "unable_30mbps_pct": r"unable30=([0-9.]+)%",
    }
    result: dict[str, Any] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if not match:
            result[key] = None
        elif key == "postcode":
            result[key] = norm_postcode(match.group(1))
        else:
            result[key] = parse_percent(match.group(1))
    return result


def pick(row: dict[str, str], aliases: Iterable[str]) -> str | None:
    normalized = {norm_header(k): v for k, v in row.items() if k is not None}
    for alias in aliases:
        key = norm_header(alias)
        if key in normalized:
            return normalized[key]
    return None


def deterministic_sample(features: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    if len(features) <= size:
        return features
    indexes = [round(i * (len(features) - 1) / (size - 1)) for i in range(size)]
    sample: list[dict[str, Any]] = []
    seen_rows: set[int] = set()
    for index in indexes:
        feature = features[index]
        row_no = int(feature.get("properties", {}).get("row_no") or 0)
        if row_no and row_no not in seen_rows:
            sample.append(feature)
            seen_rows.add(row_no)
    if len(sample) < size:
        for feature in features:
            row_no = int(feature.get("properties", {}).get("row_no") or 0)
            if row_no and row_no not in seen_rows:
                sample.append(feature)
                seen_rows.add(row_no)
                if len(sample) == size:
                    break
    return sample


def find_area_member(names: list[str], area: str) -> str | None:
    area_upper = area.upper()
    r2 = re.compile(rf"202601_fixed_postcode_coverage_r2_{re.escape(area_upper)}\.csv$", re.I)
    for name in names:
        if r2.search(name.replace("\\", "/")):
            return name
    fallback = re.compile(rf"fixed_postcode_coverage_r[12]_{re.escape(area_upper)}\.csv$", re.I)
    for name in names:
        if fallback.search(name.replace("\\", "/")):
            return name
    return None


def load_area_rows(archive: zipfile.ZipFile, member: str, targets: set[str]) -> dict[str, dict[str, str]]:
    found: dict[str, dict[str, str]] = {}
    with archive.open(member, "r") as raw:
        import io
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text)
        for row in reader:
            postcode = norm_postcode(pick(row, ["postcode", "postcode_space"]))
            if postcode in targets:
                found[postcode] = row
                if len(found) == len(targets):
                    break
    return found


def official_metrics(row: dict[str, str]) -> dict[str, float | None]:
    return {
        "superfast_30mbps_available_pct": parse_percent(pick(row, [
            "SFBB availability (% premises)", "SFBB availability", "sfbb"
        ])),
        "ultrafast_100mbps_available_pct": parse_percent(pick(row, [
            "UFBB (100Mbit/s) availability (% premises)",
            "UFBB100 availability (% premises)", "UFBB 100 availability"
        ])),
        "ultrafast_300mbps_available_pct": parse_percent(pick(row, [
            "UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"
        ])),
        "gigabit_available_pct": parse_percent(pick(row, [
            "Gigabit availability (% premises)", "Gigabit availability"
        ])),
        "unable_30mbps_pct": parse_percent(pick(row, [
            "% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"
        ])),
        "decent_broadband_unavailable_fixed_pct": parse_percent(pick(row, [
            "% of premises unable to receive decent broadband from fixed networks",
            "decent broadband unavailable fixed"
        ])),
        "decent_broadband_unavailable_fixed_or_fwa_pct": parse_percent(pick(row, [
            "% of premises unable to receive decent broadband from fixed or FWA networks",
            "decent broadband unavailable fixed or fwa"
        ])),
    }


def metric_delta(old: dict[str, Any], new: dict[str, Any]) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for key in (
        "gigabit_available_pct",
        "ultrafast_100mbps_available_pct",
        "superfast_30mbps_available_pct",
        "unable_30mbps_pct",
    ):
        left = old.get(key)
        right = new.get(key)
        result[key] = None if left is None or right is None else round(float(right) - float(left), 4)
    return result


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    root = repo_root()
    shard_root = root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards" / SLOT_ID
    progress_path = shard_root / "progress/001_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")

    source_registry_path = shard_root / "source_snapshots/001_ofcom_2026_source_registry.json"
    candidates_path = shard_root / "data/001_existing_shard2_sample_candidates.jsonl"
    validation_path = shard_root / "validation/001_ofcom_2026_sample_validation.json"
    report_path = shard_root / "reports/001_ofcom_2026_postcode_sample_wave.md"
    status_path = shard_root / "status/001_status.json"

    append_progress(progress_path, 1, "slot_and_partition_guard", "PASS", slot_id=SLOT_ID,
                    partition=[PARTITION_START, PARTITION_END])

    matrix_path = root / "england_map_web/data/program_layer_matrix/internet.geojson"
    with matrix_path.open("r", encoding="utf-8-sig") as handle:
        matrix = json.load(handle)
    all_features = matrix.get("features") or []
    shard_features = sorted(
        [feature for feature in all_features
         if PARTITION_START <= int(feature.get("properties", {}).get("row_no") or 0) <= PARTITION_END],
        key=lambda feature: int(feature.get("properties", {}).get("row_no") or 0),
    )
    append_progress(progress_path, 2, "existing_33785_matrix_shard_filter", "PASS",
                    canonical_existing_features=len(all_features), shard2_existing_features=len(shard_features))

    sample = deterministic_sample(shard_features, SAMPLE_SIZE)
    prepared: list[dict[str, Any]] = []
    for feature in sample:
        props = feature.get("properties") or {}
        legacy = parse_legacy_value(props.get("internet_level_value"))
        prepared.append({"row_no": int(props.get("row_no") or 0), "parcel_id": props.get("parcel_id"),
                         "hmlr_inspire_id": props.get("hmlr_inspire_id"),
                         "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
                         "postcode": legacy.get("postcode"), "legacy_metrics": legacy})
    append_progress(progress_path, 3, "deterministic_shard2_sample_selection", "PASS",
                    requested=SAMPLE_SIZE, selected=len(prepared))

    source_registry: dict[str, Any] = {
        "slot_id": SLOT_ID, "source_name": "Ofcom Connected Nations Spring 2026 fixed broadband coverage",
        "source_release": SOURCE_RELEASE, "source_snapshot_date": SOURCE_SNAPSHOT,
        "source_level": "POSTCODE", "license": "Open Government Licence",
        "zip_url": ZIP_URL, "about_data_url": ABOUT_URL,
        "expected_all_premises_postcode_rows": 1741096, "expected_postcode_file_count": 121,
        "expected_filename_pattern": "202601_fixed_postcode_coverage_r2_XX.csv",
        "downloaded": False, "zip_sha256": None, "zip_members": 0,
        "verified_at": utc_now(), "final_ready": False,
    }

    candidates: list[dict[str, Any]] = []
    blocker: str | None = None
    with tempfile.TemporaryDirectory(prefix="aays_ofcom_2026_") as temp_dir:
        zip_path = Path(temp_dir) / "ofcom_connected_nations_spring_2026.zip"
        try:
            request = urllib.request.Request(ZIP_URL, headers={"User-Agent": "AAYS-TerraYield/1.0 source-validation"})
            with urllib.request.urlopen(request, timeout=180) as response, zip_path.open("wb") as output:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block)
            source_registry["downloaded"] = True
            source_registry["zip_sha256"] = sha256_file(zip_path)
            source_registry["zip_size_bytes"] = zip_path.stat().st_size
            append_progress(progress_path, 4, "official_ofcom_zip_download", "PASS",
                            bytes=zip_path.stat().st_size, sha256=source_registry["zip_sha256"])

            with zipfile.ZipFile(zip_path, "r") as archive:
                names = archive.namelist()
                source_registry["zip_members"] = len(names)
                target_by_area: dict[str, set[str]] = {}
                for row in prepared:
                    postcode = norm_postcode(row.get("postcode"))
                    area = postcode_area(postcode)
                    if postcode and area:
                        target_by_area.setdefault(area, set()).add(postcode)
                official_by_postcode: dict[str, dict[str, str]] = {}
                used_members: list[str] = []
                missing_areas: list[str] = []
                for area, targets in sorted(target_by_area.items()):
                    member = find_area_member(names, area)
                    if not member:
                        missing_areas.append(area)
                        continue
                    used_members.append(member)
                    official_by_postcode.update(load_area_rows(archive, member, targets))
                source_registry["used_postcode_files"] = used_members
                source_registry["missing_postcode_areas"] = missing_areas
                append_progress(progress_path, 5, "r2_postcode_file_and_schema_resolution",
                                "PASS" if not missing_areas else "PARTIAL",
                                postcode_areas=len(target_by_area), files_used=len(used_members),
                                missing_areas=missing_areas)

                for row in prepared:
                    postcode = norm_postcode(row.get("postcode"))
                    official_row = official_by_postcode.get(postcode)
                    if official_row is None:
                        candidates.append({**row, "source_snapshot_date": SOURCE_SNAPSHOT,
                            "source_release": SOURCE_RELEASE, "source_level": "NO_DATA",
                            "match_method": "EXACT_POSTCODE_NOT_FOUND_IN_OFFICIAL_R2",
                            "match_confidence": 0.0, "internet_accuracy": "0/4",
                            "official_metrics": None, "metric_delta_vs_legacy": None,
                            "candidate_status": "NO_DATA_NOT_INFERRED",
                            "published_as_parcel_measurement": False})
                        continue
                    official = official_metrics(official_row)
                    core_complete = all(official.get(key) is not None for key in (
                        "gigabit_available_pct", "ultrafast_100mbps_available_pct",
                        "superfast_30mbps_available_pct", "unable_30mbps_pct"))
                    candidates.append({**row, "source_snapshot_date": SOURCE_SNAPSHOT,
                        "source_release": SOURCE_RELEASE, "source_level": "POSTCODE_PROXY",
                        "match_method": "EXACT_NORMALIZED_POSTCODE_TO_OFCom_R2",
                        "match_confidence": 0.75 if core_complete else 0.5,
                        "internet_accuracy": "3/4" if core_complete else "2/4",
                        "official_metrics": official,
                        "metric_delta_vs_legacy": metric_delta(row["legacy_metrics"], official),
                        "candidate_status": "VERIFIED_POSTCODE_PROXY_CANDIDATE" if core_complete else "PARTIAL_SOURCE_FIELDS",
                        "published_as_parcel_measurement": False})
                append_progress(progress_path, 6, "exact_postcode_sample_validation", "PASS",
                                candidates=len(candidates),
                                exact_matches=sum(1 for r in candidates if r["source_level"] == "POSTCODE_PROXY"),
                                no_data=sum(1 for r in candidates if r["source_level"] == "NO_DATA"))
        except Exception as exc:
            blocker = f"OFCom_2026_ZIP_OR_SCHEMA_VALIDATION_BLOCKED: {type(exc).__name__}: {exc}"
            source_registry["download_error"] = blocker
            append_progress(progress_path, 4, "official_ofcom_zip_download_or_parse", "BLOCKED", blocker=blocker)
            for row in prepared:
                candidates.append({**row, "source_snapshot_date": SOURCE_SNAPSHOT,
                    "source_release": SOURCE_RELEASE,
                    "source_level": "CANDIDATE_PENDING_OFFICIAL_R2_READBACK",
                    "match_method": "LEGACY_EXACT_POSTCODE_ONLY_NOT_UPGRADED",
                    "match_confidence": 0.0, "internet_accuracy": "2/4",
                    "official_metrics": None, "metric_delta_vs_legacy": None,
                    "candidate_status": "BLOCKED_NO_OFFICIAL_R2_ROW_EVIDENCE",
                    "published_as_parcel_measurement": False})

    write_json(source_registry_path, source_registry)
    write_jsonl(candidates_path, candidates)
    exact = sum(1 for row in candidates if row.get("candidate_status") == "VERIFIED_POSTCODE_PROXY_CANDIDATE")
    no_data = sum(1 for row in candidates if row.get("candidate_status") == "NO_DATA_NOT_INFERRED")
    partial = len(candidates) - exact - no_data
    validation = {"slot_id": SLOT_ID,
        "partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "existing_canonical_feature_count": len(all_features), "existing_shard2_feature_count": len(shard_features),
        "sample_requested": SAMPLE_SIZE, "sample_written": len(candidates),
        "verified_postcode_proxy_candidates": exact, "no_data_not_inferred": no_data,
        "partial_or_blocked": partial, "maximum_accuracy_for_postcode_proxy": "3/4",
        "parcel_measured_values_written": 0, "fake_data": False, "db_write": False,
        "migration": False, "production_deploy": False, "final_ready": False,
        "blocker": blocker, "validated_at": utc_now()}
    write_json(validation_path, validation)

    status = {"slot_id": SLOT_ID, "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "BLOCKED_WITH_EVIDENCE" if blocker else "SAMPLE_WAVE_VERIFIED",
        "completed_operations": 7 if not blocker else 4, "total_operations_in_wave": 8,
        "verified_candidates": exact, "sample_rows": len(candidates),
        "existing_shard2_rows": len(shard_features), "source_snapshot_date": SOURCE_SNAPSHOT,
        "source_release": SOURCE_RELEASE,
        "next_step": "EXPAND_EXACT_POSTCODE_REVALIDATION_ACROSS_ALL_EXISTING_SHARD2_ROWS_THEN_NO_DATA_GAP_WAVE",
        "blocker": blocker, "final_ready": False, "fake_data": False, "db_write": False,
        "migration": False, "production_deploy": False, "updated_at": utc_now()}
    write_json(status_path, status)

    report = f"""# internet_access_2 — Ofcom 2026 postcode sample wave 001

- Slot range: {PARTITION_START}-{PARTITION_END}
- Existing canonical internet features: {len(all_features)}
- Existing features inside shard 2: {len(shard_features)}
- Sample rows written: {len(candidates)}
- Verified exact-postcode r2 candidates: {exact}
- Explicit NO_DATA rows: {no_data}
- Partial or blocked rows: {partial}
- Source: {SOURCE_RELEASE}; snapshot {SOURCE_SNAPSHOT}
- Maximum accuracy: 3/4 because this is postcode coverage proxy, not parcel-measured speed
- Parcel-measured values written: 0
- Blocker: {blocker or 'none for this sample wave'}
- Next: expand exact-postcode r2 validation across every existing shard-2 feature, then evaluate missing rows under NO_DATA_NOT_INFERRED
- final_ready: false
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    append_progress(progress_path, 7, "evidence_artifacts_written_for_web_and_remote_readback", "PASS",
                    files=[str(p.relative_to(root)).replace("\\", "/") for p in (
                        source_registry_path, candidates_path, validation_path, report_path, status_path, progress_path)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
