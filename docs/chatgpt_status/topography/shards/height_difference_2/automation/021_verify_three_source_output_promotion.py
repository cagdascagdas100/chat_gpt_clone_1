#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "height_difference_2"
ROWS = {30762, 46142, 61522}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _exact_rows(values: list[dict[str, Any]], label: str) -> dict[int, dict[str, Any]]:
    rows = {int(v["row_no"]): v for v in values}
    if set(rows) != ROWS or len(values) != 3:
        raise ValueError(f"{label} must contain exactly target rows {sorted(ROWS)}")
    return rows


def _safe(payload: dict[str, Any], label: str) -> None:
    if any(bool(payload.get(k)) for k in ("fake_data", "db_write", "migration", "production_deploy", "final_ready")):
        raise ValueError(f"{label} safety flag mismatch")


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate-seeds", type=Path, required=True)
    p.add_argument("--hmlr-matches", type=Path, required=True)
    p.add_argument("--ea-samples", type=Path, required=True)
    p.add_argument("--terrain50-crosschecks", type=Path, required=True)
    p.add_argument("--final-output", type=Path, required=True)
    p.add_argument("--web-acceptance", type=Path, required=True)
    p.add_argument("--expected-web-rows", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    checks: dict[str, Any] = {}
    code = 2
    try:
        candidate = _load(args.candidate_seeds)
        hmlr = _load(args.hmlr_matches)
        ea = _load(args.ea_samples)
        terrain = _load(args.terrain50_crosschecks)
        final = _load(args.final_output)
        web = _load(args.web_acceptance)
        for label, payload in (("candidate", candidate), ("hmlr", hmlr), ("ea", ea), ("terrain", terrain), ("final", final), ("web", web)):
            if payload.get("slot_id") != SLOT_ID:
                raise ValueError(f"{label} slot mismatch")
            _safe(payload, label)

        candidate_rows = _exact_rows(candidate.get("candidates") or candidate.get("candidate_seeds") or [], "candidate")
        if len({str(v.get("hmlr_inspire_id")) for v in candidate_rows.values()}) != 3:
            raise ValueError("candidate HMLR identities are not distinct")
        if any(v.get("hmlr_geometry_accuracy") != "4/4" for v in candidate_rows.values()):
            raise ValueError("candidate HMLR geometry accuracy below 4/4")

        hmlr_rows = _exact_rows(hmlr.get("results", []), "HMLR")
        if hmlr.get("status") != "THREE_HMLR_EXACT_POLYGONS_MATCHED":
            raise ValueError("HMLR status incomplete")
        for row in hmlr_rows.values():
            if row.get("status") != "MATCHED_EXACT_ID_AND_POINT_INSIDE":
                raise ValueError("HMLR exact-id/inside gate failed")
            match = row.get("match") or {}
            if not match.get("candidate_point_inside") or not match.get("geometry_geojson_epsg27700"):
                raise ValueError("HMLR geometry evidence missing")

        ea_rows = _exact_rows(ea.get("samples", []), "EA")
        if ea.get("status") != "THREE_EA_DTM1M_POLYGON_SAMPLES_READY":
            raise ValueError("EA status incomplete")
        for row in ea_rows.values():
            q1, med, q3 = map(float, (row["q1_m_odn"], row["median_m_odn"], row["q3_m_odn"]))
            if not (math.isfinite(q1) and q1 <= med <= q3 and math.isfinite(q3)):
                raise ValueError("EA quantiles invalid")
            if int(row.get("valid_pixel_count", 0)) <= 0:
                raise ValueError("EA polygon has no valid pixels")
            if not row.get("source_sha256") and not row.get("source_files"):
                raise ValueError("EA source hash evidence missing")

        terrain_rows = _exact_rows(terrain.get("crosschecks", []), "Terrain50")
        if terrain.get("status") != "THREE_OS_TERRAIN50_CROSSCHECKS_READY":
            raise ValueError("Terrain50 status incomplete")
        if terrain.get("acceptance_threshold_applied") is not False:
            raise ValueError("Terrain50 automatic threshold must remain disabled")
        for row in terrain_rows.values():
            if int(row.get("terrain50_valid_pixel_count_all_touched", 0)) <= 0:
                raise ValueError("Terrain50 polygon has no valid pixels")
            if not math.isfinite(float(row["absolute_crosscheck_difference_m"])):
                raise ValueError("Terrain50 difference invalid")
            files = row.get("source_files") or []
            if not files or any(not f.get("sha256") for f in files):
                raise ValueError("Terrain50 source hashes missing")

        final_rows = _exact_rows(final.get("measured_rows", []), "final")
        if final.get("status") != "THREE_OFFICIAL_NUMERIC_ROWS_READY_PENDING_REVIEW":
            raise ValueError("final output status incomplete")
        if final.get("automatic_final_promotion") is not False or final.get("human_crosscheck_review_required") is not True:
            raise ValueError("human-review gate mismatch")
        for row_no, row in final_rows.items():
            if float(row["height_difference_from_sea_level_m"]) != float(ea_rows[row_no]["median_m_odn"]):
                raise ValueError("final numeric value is not EA polygon median")
            if row.get("measurement_geometry") != "exact HMLR INSPIRE polygon":
                raise ValueError("final geometry semantics mismatch")

        visible = int(web.get("visible_operation_rows", web.get("operation_row_count", 0)))
        if web.get("status") not in {"PORT_8012_HEIGHT_DIFFERENCE_2_ACCEPTED", "WEB_ACCEPTANCE_READY"}:
            raise ValueError("web acceptance status incomplete")
        if visible < args.expected_web_rows:
            raise ValueError("web operation rows below checkpoint expectation")

        checks = {
            "target_rows": sorted(ROWS),
            "candidate_count": 3,
            "hmlr_exact_polygon_count": 3,
            "ea_polygon_sample_count": 3,
            "terrain50_crosscheck_count": 3,
            "official_numeric_row_count": 3,
            "web_visible_operation_rows": visible,
            "expected_web_operation_rows": args.expected_web_rows,
            "automatic_promotion": False,
            "human_review_required": True,
        }
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "status": "THREE_SOURCE_OUTPUTS_VERIFIED_PENDING_HUMAN_REVIEW",
            "checks": checks,
            "promotion_allowed": False,
            "measurement_accuracy_score_4": "3.4/4_pending_human_crosscheck_review",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "status": "BLOCKED_THREE_SOURCE_OUTPUT_VERIFICATION",
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "promotion_allowed": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
