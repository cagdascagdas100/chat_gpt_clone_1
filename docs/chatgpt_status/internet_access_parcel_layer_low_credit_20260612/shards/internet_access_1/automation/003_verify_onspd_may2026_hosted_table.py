#!/usr/bin/env python3
"""Fail-closed May 2026 ONSPD hosted-table verifier for internet_access_1.

This tool verifies postcode existence and official postcode metadata only.
It never supplies or upgrades broadband coverage values.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "ONS_Postcode_Directory_%28May_2026%29_for_the_United_Kingdom_"
    "%28Hosted_Table%29/FeatureServer/0/query"
)
FIELDS = ("pcds", "lat", "long", "lad25cd", "rgn25cd", "doterm")
LONDON_LAD_RE = re.compile(r"^E090000\d{2}$")
POSTCODE_RE = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$")


def normalise_postcode(value: str) -> str:
    compact = "".join(value.upper().split())
    if len(compact) < 5:
        raise ValueError(f"invalid postcode: {value!r}")
    postcode = f"{compact[:-3]} {compact[-3:]}"
    if not POSTCODE_RE.fullmatch(postcode):
        raise ValueError(f"invalid postcode: {value!r}")
    return postcode


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_m = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_query(postcodes: list[str]) -> str:
    normalised = sorted(set(normalise_postcode(p) for p in postcodes))
    quoted = ",".join("'" + p.replace("'", "''") + "'" for p in normalised)
    params = {
        "where": f"pcds IN ({quoted})",
        "outFields": ",".join(FIELDS),
        "returnGeometry": "false",
        "f": "json",
    }
    return ENDPOINT + "?" + urllib.parse.urlencode(params)


def finite_coordinate(value: Any, field: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"malformed coordinate {field}: {value!r}") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise RuntimeError(f"coordinate out of UK range {field}: {number!r}")
    return number


def normalise_doterm(value: Any) -> str | None:
    if value in (None, "", " "):
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d{6}", text):
        raise RuntimeError(f"invalid doterm: {value!r}")
    return text


def load_references(path: str | None) -> dict[str, tuple[float, float]]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("references must be a postcode keyed object")
    output: dict[str, tuple[float, float]] = {}
    for raw_postcode, coordinates in payload.items():
        if not isinstance(coordinates, dict):
            raise RuntimeError(f"reference coordinates must be an object: {raw_postcode!r}")
        postcode = normalise_postcode(str(raw_postcode))
        lon = finite_coordinate(coordinates.get("lon"), "reference_lon", -9.0, 3.0)
        lat = finite_coordinate(coordinates.get("lat"), "reference_lat", 49.0, 61.0)
        output[postcode] = (lon, lat)
    return output


def parse_features(
    payload: dict[str, Any],
    *,
    expected_postcodes: set[str] | None = None,
    references: dict[str, tuple[float, float]] | None = None,
    max_distance_m: float = 300.0,
    require_london_lad: bool = True,
) -> dict[str, dict[str, Any]]:
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error: {payload['error']}")
    features = payload.get("features")
    if not isinstance(features, list):
        raise RuntimeError("ArcGIS features array missing")
    references = references or {}
    rows: dict[str, dict[str, Any]] = {}
    for feature in features:
        if not isinstance(feature, dict):
            raise RuntimeError("feature must be an object")
        attrs = feature.get("attributes") or {}
        if not isinstance(attrs, dict):
            raise RuntimeError("feature attributes must be an object")
        if not all(field in attrs for field in FIELDS):
            missing = [field for field in FIELDS if field not in attrs]
            raise RuntimeError(f"missing required fields: {missing}")
        postcode = normalise_postcode(str(attrs["pcds"]))
        lat = finite_coordinate(attrs["lat"], "lat", 49.0, 61.0)
        lon = finite_coordinate(attrs["long"], "long", -9.0, 3.0)
        lad25cd = str(attrs["lad25cd"] or "").strip().upper()
        rgn25cd = str(attrs["rgn25cd"] or "").strip().upper()
        if not lad25cd:
            raise RuntimeError(f"missing lad25cd: {postcode}")
        if require_london_lad and not LONDON_LAD_RE.fullmatch(lad25cd):
            raise RuntimeError(f"non-London LAD rejected: {postcode} {lad25cd}")
        if rgn25cd != "E12000007":
            raise RuntimeError(f"non-London region rejected: {postcode} {rgn25cd}")
        doterm = normalise_doterm(attrs["doterm"])
        active = doterm is None
        distance_m: float | None = None
        if postcode in references:
            ref_lon, ref_lat = references[postcode]
            distance_m = haversine_m(ref_lon, ref_lat, lon, lat)
            if distance_m > max_distance_m:
                raise RuntimeError(
                    f"official centroid exceeds max distance: {postcode} {distance_m:.1f}m > {max_distance_m:.1f}m"
                )
        row = {
            "postcode": postcode,
            "lat": lat,
            "lon": lon,
            "lad25cd": lad25cd,
            "rgn25cd": rgn25cd,
            "doterm": doterm,
            "active": active,
            "eligible_for_current_join": active,
            "reference_distance_m": round(distance_m, 1) if distance_m is not None else None,
            "official_source": "ONSPD_MAY_2026_HOSTED_TABLE",
            "broadband_value_allowed": False,
        }
        previous = rows.get(postcode)
        if previous is not None:
            coordinate_gap_m = haversine_m(previous["lon"], previous["lat"], lon, lat)
            same_metadata = all(previous[key] == row[key] for key in ("lad25cd", "rgn25cd", "doterm"))
            if coordinate_gap_m > 1.0 or not same_metadata:
                raise RuntimeError(
                    f"conflicting duplicate postcode: {postcode} coordinate_gap_m={coordinate_gap_m:.1f}"
                )
            continue
        rows[postcode] = row
    if expected_postcodes is not None:
        missing = sorted(expected_postcodes - set(rows))
        unexpected = sorted(set(rows) - expected_postcodes)
        if missing:
            raise RuntimeError(f"requested postcodes missing: {missing}")
        if unexpected:
            raise RuntimeError(f"unexpected postcodes returned: {unexpected}")
    return rows


def read_payload(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    if args.fixture:
        return json.loads(Path(args.fixture).read_text(encoding="utf-8")), "FIXTURE_ONLY"
    url = build_query(args.postcodes)
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-internet-access-1/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            return json.loads(response.read().decode("utf-8")), "OFFICIAL_NETWORK"
    except Exception as exc:
        raise RuntimeError(f"official ONSPD request failed closed: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--postcodes", nargs="+", default=[])
    parser.add_argument("--fixture")
    parser.add_argument("--references")
    parser.add_argument("--max-distance-m", type=float, default=300.0)
    parser.add_argument("--allow-non-london", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output")
    args = parser.parse_args()

    if not args.fixture and not args.postcodes:
        parser.error("--postcodes is required unless --fixture is supplied")
    if args.max_distance_m <= 0:
        parser.error("--max-distance-m must be positive")

    payload, mode = read_payload(args)
    references = load_references(args.references)
    expected = {normalise_postcode(value) for value in args.postcodes} if args.postcodes else None
    rows = parse_features(
        payload,
        expected_postcodes=expected,
        references=references,
        max_distance_m=args.max_distance_m,
        require_london_lad=not args.allow_non_london,
    )
    active_rows = sum(1 for row in rows.values() if row["active"])
    terminated_rows = len(rows) - active_rows
    result = {
        "schema_version": 2,
        "slot_id": "internet_access_1",
        "source_mode": mode,
        "source_endpoint": ENDPOINT,
        "rows": list(rows.values()),
        "verified_row_count": len(rows) if mode == "OFFICIAL_NETWORK" else 0,
        "fixture_row_count": len(rows) if mode == "FIXTURE_ONLY" else 0,
        "active_rows": active_rows,
        "terminated_rows": terminated_rows,
        "current_join_eligible_rows": active_rows,
        "internet_accuracy_upgraded_rows": 0,
        "broadband_values_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "fake_business_data": False,
        "final_ready": False,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "slot_id": "internet_access_1",
                    "status": "BLOCKED_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}: {exc}",
                    "official_rows_verified": 0,
                    "broadband_values_written": 0,
                    "db_write": False,
                    "migration": False,
                    "fake_business_data": False,
                    "final_ready": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise
