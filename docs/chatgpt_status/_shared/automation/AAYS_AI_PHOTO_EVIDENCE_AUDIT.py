from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image


FEATURE_PATTERN = re.compile(rb'"type"\s*:\s*"Feature"')
NULL_GEOMETRY_PATTERN = re.compile(rb'"geometry"\s*:\s*null')


def count_patterns(path: Path) -> tuple[int, int]:
    feature_count = 0
    null_geometry_count = 0
    tail = b""
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            payload = tail + chunk
            boundary = len(tail)
            feature_count += sum(
                match.end() > boundary for match in FEATURE_PATTERN.finditer(payload)
            )
            null_geometry_count += sum(
                match.end() > boundary
                for match in NULL_GEOMETRY_PATTERN.finditer(payload)
            )
            tail = payload[-128:]
    return feature_count, null_geometry_count


def resolve_web_path(web_root: Path, raw_path: str) -> Path:
    normalized = raw_path.replace("\\", "/").lstrip("/")
    prefix = "england_map_web/"
    if normalized.casefold().startswith(prefix):
        normalized = normalized[len(prefix) :]
    candidate = (web_root / normalized).resolve()
    try:
        candidate.relative_to(web_root.resolve())
    except ValueError as exc:
        raise ValueError(f"PATH_OUTSIDE_WEB_ROOT:{raw_path}") from exc
    return candidate


def append_paths(target: set[str], value: Any) -> None:
    if isinstance(value, str) and value.strip():
        target.add(value.strip())
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                target.add(item.strip())


def audit(web_root: Path) -> dict[str, Any]:
    data_root = web_root / "data" / "geometry_review_3of4"
    results_path = data_root / "photo_ai_boundary_review_results.json"
    geometry_path = data_root / "all_1264_real_geometry_3of4.geojson"
    payload = json.loads(results_path.read_text(encoding="utf-8-sig"))
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("RESULTS_LIST_REQUIRED")

    photo_refs: set[str] = set()
    polygon_refs: set[str] = set()
    manifest_refs: set[str] = set()
    source_verified_rows = 0
    rows_with_photo = 0
    rows_with_polygon = 0
    rows_with_manifest = 0
    visual_match_score_rows = 0
    invalid_compared_without_score: list[int] = []
    invalid_confidence_without_score: list[int] = []
    row_ids: list[int] = []

    for result in results:
        if not isinstance(result, dict):
            continue
        row_id = int(result.get("row_id") or 0)
        row_ids.append(row_id)
        if "verified" in str(result.get("source_verification_status") or "").casefold():
            source_verified_rows += 1

        row_photo_refs: set[str] = set()
        append_paths(row_photo_refs, result.get("downloaded_photo_paths"))
        append_paths(row_photo_refs, result.get("downloaded_photo_path"))
        if row_photo_refs:
            rows_with_photo += 1
            photo_refs.update(row_photo_refs)

        polygon = result.get("polygon_render_path")
        if isinstance(polygon, str) and polygon.strip():
            rows_with_polygon += 1
            polygon_refs.add(polygon.strip())

        manifest = result.get("vision_output_path")
        if isinstance(manifest, str) and manifest.strip():
            rows_with_manifest += 1
            manifest_refs.add(manifest.strip())

        score = result.get("visual_match_score")
        has_score = score not in (None, "")
        if has_score:
            visual_match_score_rows += 1
        status_text = " ".join(
            str(result.get(name) or "")
            for name in ("run_status", "vision_status", "photo_boundary_visible")
        ).casefold()
        confidence_text = str(result.get("confidence_after") or "").casefold()
        if "vision_compared" in status_text and not has_score:
            invalid_compared_without_score.append(row_id)
        if not has_score and ("3.5" in confidence_text or "4/4" in confidence_text):
            invalid_confidence_without_score.append(row_id)

    missing_photos: list[str] = []
    corrupt_photos: list[dict[str, str]] = []
    empty_photos: list[str] = []
    decoded_photos = 0
    photo_http_samples: list[str] = []
    for raw_path in sorted(photo_refs):
        try:
            path = resolve_web_path(web_root, raw_path)
        except ValueError as exc:
            corrupt_photos.append({"path": raw_path, "error": str(exc)})
            continue
        if not path.is_file():
            missing_photos.append(raw_path)
            continue
        if path.stat().st_size <= 0:
            empty_photos.append(raw_path)
            continue
        try:
            with Image.open(path) as image:
                image.verify()
            decoded_photos += 1
            if len(photo_http_samples) < 6:
                photo_http_samples.append(raw_path.replace("\\", "/"))
        except Exception as exc:
            corrupt_photos.append({"path": raw_path, "error": str(exc)})

    missing_polygons: list[str] = []
    empty_polygons: list[str] = []
    for raw_path in sorted(polygon_refs):
        path = resolve_web_path(web_root, raw_path)
        if not path.is_file():
            missing_polygons.append(raw_path)
        elif path.stat().st_size <= 0:
            empty_polygons.append(raw_path)

    missing_manifests: list[str] = []
    invalid_manifests: list[dict[str, str]] = []
    manifest_row_mismatches: list[dict[str, Any]] = []
    manifest_compared_without_score: list[int] = []
    parsed_manifests = 0
    for raw_path in sorted(manifest_refs):
        path = resolve_web_path(web_root, raw_path)
        if not path.is_file():
            missing_manifests.append(raw_path)
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8-sig"))
            parsed_manifests += 1
        except Exception as exc:
            invalid_manifests.append({"path": raw_path, "error": str(exc)})
            continue
        manifest_row = int(manifest.get("row_id") or 0)
        match = re.search(r"(?:^|/)row_(\d+)(?:/|$)", raw_path.replace("\\", "/"))
        path_row = int(match.group(1)) if match else 0
        if path_row and manifest_row != path_row:
            manifest_row_mismatches.append(
                {"path": raw_path, "path_row": path_row, "manifest_row": manifest_row}
            )
        manifest_score = manifest.get("visual_match_score")
        if (
            "vision_compared" in str(manifest.get("vision_status") or "").casefold()
            and manifest_score in (None, "")
        ):
            manifest_compared_without_score.append(manifest_row)

    geometry_features, null_geometries = count_patterns(geometry_path)
    rows_total_declared = int(payload.get("rows_total") or 0)
    rows_reviewed_declared = int(payload.get("rows_reviewed") or 0)
    coverage_complete = len(results) == rows_total_declared
    integrity_failures = {
        "duplicate_or_invalid_row_ids": len(row_ids) != len(set(row_ids)) or any(value <= 0 for value in row_ids),
        "reviewed_result_count_mismatch": len(results) != rows_reviewed_declared,
        "geometry_count_mismatch": geometry_features != rows_total_declared,
        "null_geometries_present": null_geometries > 0,
        "missing_photos": bool(missing_photos),
        "empty_photos": bool(empty_photos),
        "corrupt_photos": bool(corrupt_photos),
        "missing_polygons": bool(missing_polygons),
        "empty_polygons": bool(empty_polygons),
        "missing_manifests": bool(missing_manifests),
        "invalid_manifests": bool(invalid_manifests),
        "manifest_row_mismatches": bool(manifest_row_mismatches),
        "invalid_compared_without_score": bool(invalid_compared_without_score),
        "invalid_confidence_without_score": bool(invalid_confidence_without_score),
        "manifest_compared_without_score": bool(manifest_compared_without_score),
    }
    blockers = [name.upper() for name, failed in integrity_failures.items() if failed]
    if not coverage_complete:
        blockers.append(f"AI_EVIDENCE_RESULT_COVERAGE_{len(results)}_OF_{rows_total_declared}")
    if visual_match_score_rows == 0:
        blockers.append("AI_VISUAL_COMPARISON_ROWS_ZERO")

    integrity_pass = not any(integrity_failures.values())
    return {
        "status": (
            "EVIDENCE_INTEGRITY_PASS_COVERAGE_AND_VISION_PENDING"
            if integrity_pass and (not coverage_complete or visual_match_score_rows == 0)
            else "PASS" if integrity_pass else "BLOCKED"
        ),
        "rows_total_declared": rows_total_declared,
        "rows_reviewed_declared": rows_reviewed_declared,
        "result_rows": len(results),
        "rows_without_results": max(0, rows_total_declared - len(results)),
        "coverage_complete": coverage_complete,
        "unique_row_ids": len(set(row_ids)),
        "geometry_features": geometry_features,
        "null_geometries": null_geometries,
        "source_verified_rows": source_verified_rows,
        "rows_with_photo_references": rows_with_photo,
        "unique_photo_files_referenced": len(photo_refs),
        "photo_files_decoded": decoded_photos,
        "missing_photo_files": missing_photos,
        "empty_photo_files": empty_photos,
        "corrupt_photo_files": corrupt_photos,
        "rows_with_polygon_references": rows_with_polygon,
        "unique_polygon_files_referenced": len(polygon_refs),
        "missing_polygon_files": missing_polygons,
        "empty_polygon_files": empty_polygons,
        "rows_with_manifest_references": rows_with_manifest,
        "unique_manifest_files_referenced": len(manifest_refs),
        "parsed_manifest_files": parsed_manifests,
        "missing_manifest_files": missing_manifests,
        "invalid_manifest_files": invalid_manifests,
        "manifest_row_mismatches": manifest_row_mismatches,
        "visual_match_score_rows": visual_match_score_rows,
        "invalid_vision_compared_without_score": invalid_compared_without_score,
        "invalid_confidence_without_score": invalid_confidence_without_score,
        "manifest_compared_without_score": manifest_compared_without_score,
        "photo_http_samples": photo_http_samples,
        "integrity_checks": {name: not failed for name, failed in integrity_failures.items()},
        "evidence_integrity_pass": integrity_pass,
        "actual_ai_model_inference_tested": False,
        "ai_visual_comparison_executed": visual_match_score_rows > 0,
        "blockers": blockers,
        "business_files_written": 0,
        "fake_data": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.web_root.resolve())
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["evidence_integrity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
