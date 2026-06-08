from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/topography", tags=["topography"])
legacy_router = APIRouter(tags=["topography"])


LOOKUP_CANDIDATES = [
    os.environ.get("AAYS_TOPOGRAPHY_LOOKUP_V2_PATH"),
    "data/topography/parcel_elevation_lookup_v2.json",
    "terrayield_land_intelligence/data/topography/parcel_elevation_lookup_v2.json",
    "terrayield_land_intelligence/docs/chatgpt_handoff/parcel_elevation_difference_low_credit_20260602/parcel_elevation_lookup_v2.json",
]


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
        if parsed != parsed:
            return None
        return parsed
    except Exception:
        return None


def _load_lookup_index() -> dict[str, Any]:
    for candidate in LOOKUP_CANDIDATES:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            if isinstance(payload.get("parcels"), dict):
                return payload["parcels"]
            return payload
    return {}


def _normalize_topography_payload(parcel_id: str, raw: Any) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    center = _safe_float(
        source.get("center_elevation_m")
        or source.get("elevation_m")
        or source.get("elevation")
        or source.get("height_m")
    )
    region_average = _safe_float(
        source.get("region_average_elevation_m")
        or source.get("average_elevation_m")
        or source.get("area_average_elevation_m")
    )
    difference = _safe_float(
        source.get("elevation_difference_from_region_average_m")
        or source.get("difference_from_region_average_m")
        or source.get("region_elevation_delta_m")
    )
    if difference is None and center is not None and region_average is not None:
        difference = center - region_average
    sample_count = source.get("region_sample_count")
    try:
        sample_count = int(sample_count) if sample_count is not None and sample_count != "" else None
    except Exception:
        sample_count = None
    return {
        "parcel_id": str(parcel_id),
        "center_elevation_m": center,
        "region_average_elevation_m": region_average,
        "elevation_difference_from_region_average_m": difference,
        "region_sample_count": sample_count,
        "datum": source.get("datum") or source.get("vertical_datum"),
        "source_dataset": source.get("source_dataset") or source.get("source"),
        "status": "ok" if center is not None else "no_data",
    }


def lookup_topography_payload(parcel_id: str) -> dict[str, Any]:
    lookup = _load_lookup_index()
    raw = lookup.get(str(parcel_id)) or lookup.get(int(parcel_id)) if str(parcel_id).isdigit() else lookup.get(str(parcel_id))
    return _normalize_topography_payload(parcel_id, raw)


@router.get("/lookup")
def topography_lookup_v2(parcel_id: str = Query(..., min_length=1)) -> dict[str, Any]:
    return lookup_topography_payload(parcel_id)


@legacy_router.get("/lookup")
def legacy_lookup_v2(parcel_id: str = Query(..., min_length=1)) -> dict[str, Any]:
    return lookup_topography_payload(parcel_id)
