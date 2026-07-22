#!/usr/bin/env python3
"""Revalidate a deterministic internet_access_3 sample against corrected Ofcom Spring 2026 postcode data.

The script is intentionally conservative:
- it only operates on rows 61523-92283 already produced by the migration worker;
- it fixes the legacy `unable30` semantic label without inventing a value;
- it downloads only the official Ofcom archive recorded in the source registry;
- it accepts only exact postcode records from corrected r2 all-premises postcode members;
- it refreshes official coverage factors but does not create a parcel score or claim measured speed;
- parcel-to-postcode confidence remains capped because the relation is still a postcode proxy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
TASK_ID = "aays1-internet-access-3-ofcom-2026-sample-revalidation-20260722"
SHARD_START = 61523
SHARD_END = 92283
DEFAULT_SAMPLE_SIZE = 12
MINIMUM_OFFICIAL_MATCHES = 3

DEFAULT_ROWS = "england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json"
DEFAULT_GEOJSON = "england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.geojson"
DEFAULT_REGISTRY = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/source_snapshots/001_ofcom_spring_2026_registry_latest.json"
)
DEFAULT_OUTPUT = "england_map_web/data/aays_21_slots/internet_access_3"
DEFAULT_RUNNER_OUTPUT = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/runner_outputs/002_ofcom_2026_sample_revalidation_latest.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--rows", default=DEFAULT_ROWS)
    parser.add_argument("--geojson", default=DEFAULT_GEOJSON)
    parser.add_argument("--source-registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT)
    parser.add_argument("--runner-output", default=DEFAULT_RUNNER_OUTPUT)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--cache-dir", default=".cache/internet_access_3")
    parser.add_argument("--download-retries", type=int, default=3)
    parser.add_argument("--download-timeout", type=int, default=180)
    return parser.parse_args()


def find_repo_root(explicit: Path | None) -> Path:
    if explicit:
        root = explicit.expanduser().resolve()
        if not (root / "england_map_web").exists():
            raise FileNotFoundError(f"invalid repo root: {root}")
        return root
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found; pass --repo-root")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_postcode(value: Any) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", "", str(value)).upper()
    if not re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}", normalized):
        return None
    return normalized


def postcode_area(postcode: str) -> str:
    match = re.match(r"^([A-Z]{1,2})", postcode)
    if not match:
        raise ValueError(f"postcode area not found: {postcode}")
    return match.group(1)


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower().replace("≥", "gte").replace(">=", "gte"))


def choose_header(headers: list[str], required: tuple[str, ...], excluded: tuple[str, ...] = ()) -> str | None:
    for header in headers:
        normalized = normalized_header(header)
        if all(token in normalized for token in required) and not any(token in normalized for token in excluded):
            return header
    return None


def parse_percent(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in {"na", "n/a", "null", "none", "-"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number < 0 or number > 100:
        return None
    return number


def download_archive(url: str, target: Path, retries: int, timeout: int) -> tuple[Path, bool]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1024 * 1024:
        return target, True
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        part = target.with_suffix(target.suffix + ".part")
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "TerraYield-AAYS-internet-access-3/1.0",
                    "Accept": "application/zip,application/octet-stream,*/*",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response, part.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            if part.stat().st_size <= 1024 * 1024:
                raise ValueError(f"download unexpectedly small: {part.stat().st_size}")
            os.replace(part, target)
            return target, False
        except Exception as exc:
            last_error = exc
            try:
                part.unlink()
            except FileNotFoundError:
                pass
            if attempt < retries:
                time.sleep(min(10, attempt * 2))
    raise RuntimeError(f"official archive download failed after {retries} attempts: {last_error}")


def corrected_members(archive: zipfile.ZipFile) -> dict[str, str]:
    result: dict[str, str] = {}
    bad_r1_members: list[str] = []
    for name in archive.namelist():
        normalized = name.replace("\\", "/")
        lower = normalized.lower()
        if "/postcode_files/" not in "/" + lower:
            continue
        filename = Path(normalized).name
        if re.fullmatch(r"202601_fixed_postcode_coverage_r1_[a-z]{1,2}\.csv", filename, re.I):
            bad_r1_members.append(normalized)
        match = re.fullmatch(r"202601_fixed_postcode_coverage_r2_([a-z]{1,2})\.csv", filename, re.I)
        if match:
            result[match.group(1).upper()] = normalized
    if bad_r1_members:
        raise ValueError(f"uncorrected r1 all-premises postcode members present: {len(bad_r1_members)}")
    if len(result) != 121:
        raise ValueError(f"corrected r2 postcode member count mismatch: {len(result)} != 121")
    for required_area in ("CW", "MK"):
        if required_area not in result:
            raise ValueError(f"corrected required postcode area missing: {required_area}")
    return result


def deterministic_sample(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    eligible = [
        row
        for row in rows
        if SHARD_START <= int(row.get("row_no", -1)) <= SHARD_END
        and row.get("internet_status") in {
            "verified_existing_postcode_proxy",
            "official_2026_postcode_proxy_sample",
        }
        and normalize_postcode(row.get("postcode"))
    ]
    eligible.sort(key=lambda row: int(row["row_no"]))
    if not eligible or size <= 0:
        return []
    if len(eligible) <= size:
        return eligible
    if size == 1:
        return [eligible[len(eligible) // 2]]
    indexes = [round(i * (len(eligible) - 1) / (size - 1)) for i in range(size)]
    seen: set[int] = set()
    selected: list[dict[str, Any]] = []
    for index in indexes:
        row_no = int(eligible[index]["row_no"])
        if row_no not in seen:
            seen.add(row_no)
            selected.append(eligible[index])
    return selected


def field_map(headers: list[str]) -> dict[str, str | None]:
    return {
        "postcode": choose_header(headers, ("postcode",), ("area", "space")),
        "postcode_space": choose_header(headers, ("postcodespace",)),
        "sfbb": choose_header(headers, ("sfbbavailability", "premises")),
        "ufbb100": choose_header(headers, ("ufbb100mbitsavailability", "premises")),
        "ufbb300": choose_header(headers, ("ufbbavailability", "premises"), ("100mbits",)),
        "gigabit": choose_header(headers, ("gigabitavailability", "premises")),
        "unable30": choose_header(headers, ("premisesunabletoreceive30mbits",)),
        "decent_unavailable": choose_header(headers, ("unabletoreceivedecentbroadbandfromfixedorfwa",)),
    }


def load_official_records(
    archive: zipfile.ZipFile,
    members: dict[str, str],
    target_postcodes: set[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    targets_by_area: dict[str, set[str]] = {}
    for postcode in target_postcodes:
        targets_by_area.setdefault(postcode_area(postcode), set()).add(postcode)

    official: dict[str, dict[str, Any]] = {}
    area_audits: list[dict[str, Any]] = []
    for area, area_targets in sorted(targets_by_area.items()):
        member = members.get(area)
        if not member:
            area_audits.append({"area": area, "status": "MEMBER_MISSING", "targets": sorted(area_targets)})
            continue
        with archive.open(member, "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            headers = list(reader.fieldnames or [])
            mapping = field_map(headers)
            postcode_field = mapping["postcode"] or mapping["postcode_space"]
            required_fields = ["sfbb", "ufbb100", "gigabit", "unable30"]
            missing = [name for name in required_fields if not mapping.get(name)]
            if not postcode_field or missing:
                area_audits.append(
                    {
                        "area": area,
                        "status": "SCHEMA_BLOCKED",
                        "member": member,
                        "missing_fields": (["postcode"] if not postcode_field else []) + missing,
                        "headers": headers,
                    }
                )
                continue
            found = 0
            for raw in reader:
                postcode = normalize_postcode(raw.get(postcode_field))
                if postcode not in area_targets:
                    continue
                official[postcode] = {
                    "postcode": postcode,
                    "source_member": member,
                    "superfast_30mbps_available_pct": parse_percent(raw.get(mapping["sfbb"])),
                    "ultrafast_or_100mbps_available_pct": parse_percent(raw.get(mapping["ufbb100"])),
                    "ultrafast_300mbps_available_pct": parse_percent(raw.get(mapping["ufbb300"])) if mapping.get("ufbb300") else None,
                    "gigabit_available_pct": parse_percent(raw.get(mapping["gigabit"])),
                    "unable_30mbps_pct": parse_percent(raw.get(mapping["unable30"])),
                    "decent_broadband_unavailable_pct": (
                        parse_percent(raw.get(mapping["decent_unavailable"]))
                        if mapping.get("decent_unavailable")
                        else None
                    ),
                }
                found += 1
            area_audits.append(
                {
                    "area": area,
                    "status": "READ",
                    "member": member,
                    "target_count": len(area_targets),
                    "found_count": found,
                    "field_map": mapping,
                }
            )
    return official, {"areas": area_audits}


def difference(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    try:
        return round(float(right) - float(left), 4)
    except (TypeError, ValueError):
        return None


def correct_legacy_semantics(row: dict[str, Any]) -> bool:
    changed = False
    if "unable_30mbps_pct" not in row:
        row["unable_30mbps_pct"] = row.get("decent_broadband_unavailable_pct")
        row["decent_broadband_unavailable_pct"] = None
        changed = True
    blockers = list(row.get("blockers") or [])
    marker = "LEGACY_UNABLE30_SEMANTIC_CORRECTED_TO_UNABLE_30MBPS"
    if marker not in blockers and row.get("legacy_internet_level_value"):
        blockers.append(marker)
        row["blockers"] = blockers
        changed = True
    return changed


def update_web_feed(output_root: Path, candidates: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    feed_path = output_root / "operation_feed_latest.json"
    if feed_path.exists():
        feed = load_json(feed_path)
    else:
        feed = {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    next_sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    operations.append(
        {
            "sequence": next_sequence,
            "status": "PASS" if summary["source_validation"]["archive_schema_passed"] else "BLOCKED",
            "operation": "OFcom_2026_ARCHIVE_SCHEMA_READBACK",
            "detail": (
                f"Corrected r2 postcode members={summary['source_validation']['corrected_member_count']}; "
                f"archive_sha256={summary['source_validation']['archive_sha256']}"
            ),
        }
    )
    next_sequence += 1
    for candidate in candidates:
        operations.append(
            {
                "sequence": next_sequence,
                "status": "PASS" if candidate["official_postcode_found"] else "NO_DATA",
                "operation": "SAMPLE_ROW_REVALIDATION",
                "row_no": candidate["row_no"],
                "parcel_id": candidate["canonical_program_parcel_id"],
                "postcode": candidate["postcode"],
                "detail": candidate["candidate_status"],
            }
        )
        next_sequence += 1
    feed.update(
        {
            "updated_at": summary["updated_at"],
            "display_mode": "line_by_line",
            "final_ready": False,
            "operations": operations,
            "safety": {
                "fake_data": False,
                "db_write": False,
                "migration": False,
                "production_deploy": False,
            },
        }
    )
    atomic_write_json(feed_path, feed)

    progress_path = output_root / "progress_latest.json"
    progress = load_json(progress_path) if progress_path.exists() else {"schema_version": 1, "slot_id": SLOT_ID}
    completed = int(progress.get("completed_operations", 0)) + 2 + len(candidates)
    total = max(int(progress.get("total_operations", 50)), completed)
    revalidated = sum(1 for item in candidates if item["official_postcode_found"])
    old_percent = int(progress.get("overall_progress_percent", 0))
    new_percent = min(99, max(old_percent, round(completed * 100 / total)))
    progress.update(
        {
            "updated_at": summary["updated_at"],
            "overall_progress_percent": new_percent,
            "progress_delta_percent": new_percent - old_percent,
            "completed_operations": completed,
            "total_operations": total,
            "candidate_rows_prepared": len(candidates),
            "candidate_rows_revalidated": revalidated,
            "source_registry_entries": 1,
            "sources_promoted": 1,
            "source_accuracy_score": 95,
            "parcel_match_accuracy_score": 50,
            "overall_confidence_score": 50,
            "actual_business_data_rows_written": summary["result"]["sample_rows_refreshed"],
            "runner_pickup_observed": True,
            "runner_execution_claimed": True,
            "current_blocker": (
                "PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY"
                if revalidated >= MINIMUM_OFFICIAL_MATCHES
                else "INSUFFICIENT_OFFICIAL_POSTCODE_SAMPLE_MATCHES"
            ),
            "next_step": "VALIDATE_MORE_POSTCODE_RELATIONS_OR_RETAIN_NO_DATA",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    )
    atomic_write_json(progress_path, progress)


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(args.repo_root)
    rows_path = repo_root / args.rows
    geojson_path = repo_root / args.geojson
    registry_path = repo_root / args.source_registry
    output_root = repo_root / args.output_root
    runner_output = repo_root / args.runner_output
    cache_dir = repo_root / args.cache_dir

    rows = load_json(rows_path)
    geojson = load_json(geojson_path)
    registry = load_json(registry_path)
    if not isinstance(rows, list) or len(rows) != 30761:
        raise ValueError(f"migrated shard row count mismatch: {len(rows) if isinstance(rows, list) else 'not-list'}")
    if geojson.get("type") != "FeatureCollection" or len(geojson.get("features") or []) != 30761:
        raise ValueError("migrated shard GeoJSON count mismatch")

    semantic_fix_count = sum(1 for row in rows if correct_legacy_semantics(row))
    sample = deterministic_sample(rows, args.sample_size)
    if not sample:
        raise ValueError("no eligible migrated postcode proxy rows in internet_access_3")

    archive_path, cache_hit = download_archive(
        registry["download_url"],
        cache_dir / "202601_fixed_broadband_coverage_and_full_fibre_take-up.zip",
        args.download_retries,
        args.download_timeout,
    )
    archive_sha = sha256_file(archive_path)
    with zipfile.ZipFile(archive_path, "r") as archive:
        members = corrected_members(archive)
        target_postcodes = {normalize_postcode(row.get("postcode")) for row in sample}
        target_postcodes.discard(None)
        official, archive_audit = load_official_records(archive, members, set(target_postcodes))

    candidates: list[dict[str, Any]] = []
    row_lookup = {int(row["row_no"]): row for row in rows}
    for selected in sample:
        row_no = int(selected["row_no"])
        row = row_lookup[row_no]
        postcode = normalize_postcode(row.get("postcode"))
        record = official.get(postcode or "")
        candidate = {
            "row_no": row_no,
            "canonical_program_parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": row.get("hmlr_inspire_id"),
            "postcode": postcode,
            "official_postcode_found": record is not None,
            "source_accuracy_score": 95 if record else 0,
            "parcel_match_accuracy_score": 50,
            "overall_confidence_score": 50 if record else 0,
            "legacy_values": {
                "gigabit_available_pct": row.get("gigabit_available_pct"),
                "ultrafast_or_100mbps_available_pct": row.get("ultrafast_or_100mbps_available_pct"),
                "superfast_30mbps_available_pct": row.get("superfast_30mbps_available_pct"),
                "unable_30mbps_pct": row.get("unable_30mbps_pct"),
            },
            "official_2026_values": record,
            "delta": {},
            "candidate_status": "OFFICIAL_POSTCODE_NOT_FOUND_RETAIN_EXISTING_PROXY" if not record else "OFFICIAL_2026_POSTCODE_REFRESHED_PARCEL_PROXY_NOT_PROMOTED",
        }
        if record:
            candidate["delta"] = {
                "gigabit_available_pct": difference(row.get("gigabit_available_pct"), record.get("gigabit_available_pct")),
                "ultrafast_or_100mbps_available_pct": difference(row.get("ultrafast_or_100mbps_available_pct"), record.get("ultrafast_or_100mbps_available_pct")),
                "superfast_30mbps_available_pct": difference(row.get("superfast_30mbps_available_pct"), record.get("superfast_30mbps_available_pct")),
                "unable_30mbps_pct": difference(row.get("unable_30mbps_pct"), record.get("unable_30mbps_pct")),
            }
            legacy_band = row.get("internet_quality_band")
            if legacy_band is not None:
                row["legacy_internet_quality_band"] = legacy_band
            row.update(
                {
                    "internet_status": "official_2026_postcode_proxy_sample",
                    "source_snapshot_date": registry["source_snapshot_date"],
                    "source_url": registry["source_page"],
                    "source_archive_sha256": archive_sha,
                    "source_member": record["source_member"],
                    "source_level": "POSTCODE_PROXY",
                    "gigabit_available_pct": record["gigabit_available_pct"],
                    "ultrafast_or_100mbps_available_pct": record["ultrafast_or_100mbps_available_pct"],
                    "ultrafast_300mbps_available_pct": record["ultrafast_300mbps_available_pct"],
                    "superfast_30mbps_available_pct": record["superfast_30mbps_available_pct"],
                    "unable_30mbps_pct": record["unable_30mbps_pct"],
                    "decent_broadband_unavailable_pct": record["decent_broadband_unavailable_pct"],
                    "internet_availability_quality_percent": None,
                    "internet_quality_band": None,
                    "internet_match_method": "EXISTING_PARCEL_POSTCODE_PROXY_PLUS_OFcom_2026_EXACT_POSTCODE",
                    "internet_match_confidence": 50,
                    "internet_accuracy": "2/4",
                    "source_accuracy_score": 95,
                    "parcel_match_accuracy_score": 50,
                    "overall_confidence_score": 50,
                    "calculation_version": "score-deferred-ofcom-2026-postcode-factors-v1",
                    "calculation_explanation": "January 2026 Ofcom coverage factors refreshed by exact postcode. No measured speed or parcel-level score was created; parcel-to-postcode relation remains a proxy.",
                    "blockers": [
                        "PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY",
                        "QUALITY_SCORE_DEFERRED_UNTIL_VERIFIED_CALCULATION_VERSION",
                    ],
                }
            )
        candidates.append(candidate)

    props_by_row = {int(row["row_no"]): row for row in rows}
    for feature in geojson["features"]:
        props = feature.get("properties") or {}
        row_no = int(props.get("row_no", -1))
        if row_no in props_by_row:
            feature["properties"] = props_by_row[row_no]

    official_matches = sum(1 for item in candidates if item["official_postcode_found"])
    blockers: list[str] = []
    if official_matches < MINIMUM_OFFICIAL_MATCHES:
        blockers.append(f"OFFICIAL_SAMPLE_MATCHES_BELOW_MINIMUM:{official_matches}<{MINIMUM_OFFICIAL_MATCHES}")

    updated_at = "2026-07-22T03:31:15+03:00"
    summary = {
        "schema_version": 1,
        "task_id": TASK_ID,
        "slot_id": SLOT_ID,
        "updated_at": updated_at,
        "state": "sample_revalidation_passed" if not blockers else "blocked",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "source_validation": {
            "authority": registry["source_authority"],
            "publication": registry["publication"],
            "source_snapshot_date": registry["source_snapshot_date"],
            "correction_version": registry["correction"]["version"],
            "archive_path": str(archive_path.relative_to(repo_root)),
            "archive_sha256": archive_sha,
            "archive_cache_hit": cache_hit,
            "corrected_member_count": 121,
            "archive_schema_passed": True,
            "area_audit": archive_audit,
        },
        "result": {
            "semantic_rows_corrected": semantic_fix_count,
            "sample_rows_requested": args.sample_size,
            "sample_rows_selected": len(candidates),
            "official_postcodes_found": official_matches,
            "sample_rows_refreshed": official_matches,
            "quality_scores_created": 0,
            "new_parcel_postcode_matches_created": 0,
            "measured_speed_claims_created": 0,
            "actual_business_data_rows_written": official_matches,
        },
        "accuracy": {
            "source_accuracy_score": 95,
            "parcel_match_accuracy_score": 50,
            "overall_confidence_score": 50,
            "confidence_ceiling_reason": "parcel-to-postcode relation remains an existing proxy",
        },
        "candidates": candidates,
        "blockers": blockers + ["PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY"],
        "first_unverified_step_after_run": "EXPAND_EXACT_POSTCODE_REVALIDATION_THEN_INDEPENDENTLY_VALIDATE_PARCEL_POSTCODE_RELATIONS",
    }

    atomic_write_json(rows_path, rows)
    atomic_write_json(geojson_path, geojson)
    atomic_write_json(output_root / "ofcom_2026_sample_candidates_latest.json", candidates)
    atomic_write_json(output_root / "ofcom_2026_sample_validation_latest.json", summary)
    atomic_write_json(runner_output, summary)
    update_web_feed(output_root, candidates, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        error = {
            "task_id": TASK_ID,
            "slot_id": SLOT_ID,
            "state": "exception",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        raise
