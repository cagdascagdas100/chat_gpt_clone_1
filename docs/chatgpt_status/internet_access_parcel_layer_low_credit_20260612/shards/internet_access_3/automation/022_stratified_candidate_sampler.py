#!/usr/bin/env python3
"""Build a deterministic stratified candidate manifest for internet_access_3.

The manifest balances existing postcode-proxy rows by authority, postcode area,
quality band and unable-30 bucket. It is candidate preparation only; no official
source has been revalidated and no confidence is raised.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROWS_EXPECTED = 30761
DEFAULT_SAMPLE_SIZE = 384


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/017_stratified_candidate_sampler_latest.json")
    p.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def postcode(value: Any) -> str | None:
    clean = re.sub(r"\s+", "", str(value or "")).upper()
    return clean if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}", clean) else None


def postcode_area(value: Any) -> str | None:
    clean = postcode(value)
    if not clean:
        return None
    match = re.match(r"[A-Z]{1,2}", clean)
    return match.group(0) if match else None


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def unable_bucket(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return "missing"
    if number == 0:
        return "0"
    if number <= 10:
        return "0_to_10"
    if number <= 50:
        return "10_to_50"
    if number < 100:
        return "50_to_100"
    return "100"


def quality_band(value: Any) -> str:
    clean = re.sub(r"\s+", "_", str(value or "unknown").strip().lower())
    return clean or "unknown"


def eligible(row: dict[str, Any]) -> bool:
    return bool(
        postcode(row.get("postcode"))
        and row.get("hmlr_inspire_id")
        and row.get("canonical_program_parcel_id")
        and str(row.get("london_authority") or "").strip()
        and row.get("internet_status") in {"verified_existing_postcode_proxy", "official_2026_postcode_proxy_sample"}
    )


def stratum(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("london_authority") or "").strip(),
        postcode_area(row.get("postcode")) or "unknown",
        quality_band(row.get("internet_quality_band")),
        unable_bucket(row.get("unable_30mbps_pct")),
    )


def round_robin(rows: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if eligible(row):
            groups[stratum(row)].append(row)
    for values in groups.values():
        values.sort(key=lambda item: int(item["row_no"]))
    keys = sorted(groups, key=lambda key: (len(groups[key]), key))
    selected: list[dict[str, Any]] = []
    cursor = 0
    while keys and len(selected) < size:
        next_keys: list[tuple[str, str, str, str]] = []
        for key in keys:
            values = groups[key]
            if cursor < len(values):
                selected.append(values[cursor])
                if len(selected) >= size:
                    break
            if cursor + 1 < len(values):
                next_keys.append(key)
        cursor += 1
        keys = next_keys
    selected.sort(key=lambda item: int(item["row_no"]))
    return selected


def distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    authorities = sorted({str(row.get("london_authority") or "").strip() for row in rows})
    areas = sorted({postcode_area(row.get("postcode")) or "unknown" for row in rows})
    bands = sorted({quality_band(row.get("internet_quality_band")) for row in rows})
    buckets = sorted({unable_bucket(row.get("unable_30mbps_pct")) for row in rows})
    return {
        "authorities": authorities,
        "postcode_areas": areas,
        "quality_bands": bands,
        "unable30_buckets": buckets,
        "authority_count": len(authorities),
        "postcode_area_count": len(areas),
        "quality_band_count": len(bands),
        "unable30_bucket_count": len(buckets),
    }


def update_feed(output_root: Path, summary: dict[str, Any]) -> None:
    path = output_root / "operation_feed_revision8_runtime_latest.json"
    feed = load_json(path) if path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    dist = summary["distribution"]
    operations.append({
        "sequence": sequence,
        "status": "PASS" if summary["validation"]["passed"] else "BLOCKED",
        "operation": "STRATIFIED_CANDIDATE_MANIFEST",
        "detail": f"selected={summary['result']['sample_rows_selected']}; authorities={dist['authority_count']}; postcode_areas={dist['postcode_area_count']}; quality_bands={dist['quality_band_count']}; unable30_buckets={dist['unable30_bucket_count']}; prepared_not_revalidated",
    })
    feed.update({"updated_at": summary["updated_at"], "display_mode": "line_by_line", "final_ready": False, "operations": operations, "safety": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False}})
    atomic_json(path, feed)


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    rows = load_json(repo / args.rows)
    if not isinstance(rows, list) or len(rows) != ROWS_EXPECTED:
        raise ValueError("migrated internet_access_3 rows missing or wrong count")
    selected = round_robin(rows, args.sample_size)
    dist = distribution(selected)
    manifest = [
        {
            "sample_index": index,
            "row_no": int(row["row_no"]),
            "parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": row.get("hmlr_inspire_id"),
            "postcode": postcode(row.get("postcode")),
            "postcode_area": postcode_area(row.get("postcode")),
            "london_authority": row.get("london_authority"),
            "internet_quality_band": row.get("internet_quality_band"),
            "unable_30mbps_pct": as_float(row.get("unable_30mbps_pct")),
            "unable30_bucket": unable_bucket(row.get("unable_30mbps_pct")),
            "selection_stratum": list(stratum(row)),
            "status": "PREPARED_NOT_REVALIDATED",
            "official_source_revalidated": False,
            "parcel_relation_promoted": False,
            "confidence_raised": False,
        }
        for index, row in enumerate(selected, 1)
    ]
    blockers: list[str] = []
    if len(selected) != args.sample_size:
        blockers.append(f"SAMPLE_SIZE_MISMATCH:{len(selected)}")
    minimums = {"authority_count": 8, "postcode_area_count": 8, "quality_band_count": 3, "unable30_bucket_count": 3}
    for field, minimum in minimums.items():
        if int(dist[field]) < minimum:
            blockers.append(f"STRATIFICATION_{field.upper()}_BELOW_MINIMUM:{dist[field]}<{minimum}")
    duplicate_rows = len({item["row_no"] for item in manifest}) != len(manifest)
    if duplicate_rows:
        blockers.append("DUPLICATE_SAMPLE_ROWS")
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "task_id": "aays1-internet-access-3-stratified-candidate-sampler-20260722",
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if not blockers else "blocked",
        "updated_at": now,
        "result": {
            "sample_rows_requested": args.sample_size,
            "sample_rows_selected": len(selected),
            "eligible_proxy_rows_seen": sum(1 for row in rows if eligible(row)),
            "official_source_rows_revalidated": 0,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
            "actual_business_data_rows_written": 0,
        },
        "distribution": dist,
        "validation": {"passed": not blockers, "blockers": blockers, "duplicate_sample_rows": duplicate_rows, "minimums": minimums},
        "output_semantics": "STRATIFIED_EXISTING_PROXY_CANDIDATE_MANIFEST_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "RUN_EXACT_OFcom_ONSPD_AND_HMLR_VALIDATION_ON_STRATIFIED_MANIFEST",
    }
    output_root = repo / args.output_root
    atomic_json(output_root / "stratified_candidate_manifest_latest.json", manifest)
    atomic_json(output_root / "stratified_candidate_summary_latest.json", summary)
    atomic_json(repo / args.runner_output, summary)
    update_feed(output_root, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
