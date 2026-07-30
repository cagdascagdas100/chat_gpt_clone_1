from __future__ import annotations

import json
import math
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_2"
CONTINUATION_KEY = "c07f950559681f35d0a482491539c1f50400878e0a0b33f9ae3e733574346ce6"
API = "https://www.planning.data.gov.uk/entity.json"


@dataclass(frozen=True)
class CanonicalIdentity:
    parcel_id: str
    reference: str
    longitude: float
    latitude: float


def _finite(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("NON_FINITE_COORDINATE")
    return number


def load_identities(path: Path) -> list[CanonicalIdentity]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_identity_rows")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("CANONICAL_IDENTITY_ROWS_MISSING")
    identities: list[CanonicalIdentity] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("CANONICAL_IDENTITY_ROW_INVALID")
        parcel_id = str(row.get("parcel_id") or "").strip()
        reference = str(row.get("hmlr_inspire_id") or "").strip()
        if not parcel_id or not reference.isdigit() or reference in seen:
            raise RuntimeError(f"CANONICAL_IDENTITY_INVALID:{parcel_id}:{reference}")
        seen.add(reference)
        identities.append(
            CanonicalIdentity(
                parcel_id=parcel_id,
                reference=reference,
                longitude=_finite(row.get("hmlr_lon")),
                latitude=_finite(row.get("hmlr_lat")),
            )
        )
    return identities


def build_url(reference: str) -> str:
    if not reference.isdigit():
        raise ValueError("REFERENCE_NOT_NUMERIC")
    query = urllib.parse.urlencode(
        {
            "dataset": "title-boundary",
            "reference": reference,
            "period": "current",
            "limit": "2",
            "field": ["entity", "dataset", "reference", "geometry", "point", "quality", "entry-date"],
        },
        doseq=True,
    )
    return f"{API}?{query}"


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TerraYield-AAYS/1.0 official-government-crosscheck", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = (response.headers.get_content_type() or "").lower()
        body = response.read()
    if "json" not in content_type and not body.lstrip().startswith((b"{", b"[")):
        raise RuntimeError(f"PLANNING_API_NON_JSON:{content_type}")
    value = json.loads(body.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("PLANNING_API_ROOT_NOT_OBJECT")
    return value


def _entities(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("entities", "results", "data"):
        value = payload.get(key)
        if isinstance(value, list):
            if not all(isinstance(item, dict) for item in value):
                raise RuntimeError("PLANNING_API_ENTITY_NOT_OBJECT")
            return value
    if all(key in payload for key in ("dataset", "reference")):
        return [payload]
    raise RuntimeError("PLANNING_API_ENTITIES_MISSING")


def _wkt_pairs(wkt: str) -> list[tuple[float, float]]:
    if not re.match(r"^\s*(?:MULTI)?POLYGON\s*\(", wkt, re.I):
        raise RuntimeError("PLANNING_GEOMETRY_NOT_POLYGON")
    numbers = [float(token) for token in re.findall(r"[-+]?\d+(?:\.\d+)?", wkt)]
    if len(numbers) < 8 or len(numbers) % 2:
        raise RuntimeError("PLANNING_GEOMETRY_TOO_SHORT")
    return list(zip(numbers[0::2], numbers[1::2]))


def validate_entity(identity: CanonicalIdentity, payload: dict[str, Any], tolerance_degrees: float = 0.0002) -> dict[str, Any]:
    candidates = [
        entity
        for entity in _entities(payload)
        if str(entity.get("dataset") or "") == "title-boundary"
        and str(entity.get("reference") or "") == identity.reference
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"PLANNING_EXACT_REFERENCE_MATCH_COUNT:{len(candidates)}")
    entity = candidates[0]
    pairs = _wkt_pairs(str(entity.get("geometry") or ""))
    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    inside = (
        bbox[0] - tolerance_degrees <= identity.longitude <= bbox[2] + tolerance_degrees
        and bbox[1] - tolerance_degrees <= identity.latitude <= bbox[3] + tolerance_degrees
    )
    if not inside:
        raise RuntimeError("PLANNING_CANONICAL_POINT_OUTSIDE_GEOMETRY_BBOX")
    return {
        "parcel_id": identity.parcel_id,
        "reference": identity.reference,
        "entity": entity.get("entity"),
        "quality": entity.get("quality"),
        "entry_date": entity.get("entry-date"),
        "coordinate_pair_count": len(pairs),
        "bbox": bbox,
        "canonical_point_inside_tolerant_bbox": True,
        "crosscheck_only": True,
        "accepted_as_hmlr_gml_substitute": False,
    }


def audit(path: Path) -> dict[str, Any]:
    identities = load_identities(path)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for identity in identities:
        try:
            rows.append(validate_entity(identity, fetch_json(build_url(identity.reference))))
        except Exception as exc:
            errors.append({"parcel_id": identity.parcel_id, "reference": identity.reference, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "continuation_key": CONTINUATION_KEY,
        "source": API,
        "target_count": len(identities),
        "crosschecked_count": len(rows),
        "failed_count": len(errors),
        "rows": rows,
        "errors": errors,
        "acceptance_scope": "independent government title-boundary consistency check only; never substitutes for current Enfield HMLR GML binary and SHA-256",
        "official_gml_acceptance_passed": False,
        "fake_data": False,
        "final_ready": False,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("result_json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.result_json)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
