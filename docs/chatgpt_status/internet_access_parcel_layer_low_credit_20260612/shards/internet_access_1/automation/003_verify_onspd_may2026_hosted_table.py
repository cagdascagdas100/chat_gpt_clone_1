#!/usr/bin/env python3
"""Fail-closed May 2026 ONSPD hosted-table verifier for internet_access_1.

This tool verifies postcode existence and official postcode metadata only.
It never supplies or upgrades broadband coverage values.
"""
from __future__ import annotations

import argparse
import json
import math
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


def normalise_postcode(value: str) -> str:
    compact = "".join(value.upper().split())
    if len(compact) < 5:
        raise ValueError(f"invalid postcode: {value!r}")
    return f"{compact[:-3]} {compact[-3:]}"


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_m = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_query(postcodes: list[str]) -> str:
    normalised = [normalise_postcode(p) for p in postcodes]
    quoted = ",".join("'" + p.replace("'", "''") + "'" for p in normalised)
    params = {
        "where": f"pcds IN ({quoted})",
        "outFields": ",".join(FIELDS),
        "returnGeometry": "false",
        "f": "json",
    }
    return ENDPOINT + "?" + urllib.parse.urlencode(params)


def parse_features(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "error" in payload:
        raise RuntimeError(f"ArcGIS error: {payload['error']}")
    rows: dict[str, dict[str, Any]] = {}
    for feature in payload.get("features", []):
        attrs = feature.get("attributes") or {}
        if not all(field in attrs for field in FIELDS):
            missing = [field for field in FIELDS if field not in attrs]
            raise RuntimeError(f"missing required fields: {missing}")
        postcode = normalise_postcode(str(attrs["pcds"]))
        rows[postcode] = {
            "postcode": postcode,
            "lat": float(attrs["lat"]),
            "lon": float(attrs["long"]),
            "lad25cd": attrs["lad25cd"],
            "rgn25cd": attrs["rgn25cd"],
            "doterm": attrs["doterm"],
            "official_source": "ONSPD_MAY_2026_HOSTED_TABLE",
            "broadband_value_allowed": False,
        }
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
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output")
    args = parser.parse_args()

    if not args.fixture and not args.postcodes:
        parser.error("--postcodes is required unless --fixture is supplied")

    payload, mode = read_payload(args)
    rows = parse_features(payload)
    result = {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "source_mode": mode,
        "source_endpoint": ENDPOINT,
        "rows": list(rows.values()),
        "verified_row_count": len(rows) if mode == "OFFICIAL_NETWORK" else 0,
        "fixture_row_count": len(rows) if mode == "FIXTURE_ONLY" else 0,
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
    raise SystemExit(main())
