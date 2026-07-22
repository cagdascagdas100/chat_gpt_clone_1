#!/usr/bin/env python3
"""Read-only TGL419520 extractor for the current Barking and Dagenham HMLR INSPIRE GML.

The script resolves the official local-authority GML link, records download metadata,
finds feature windows containing the exact title number and extracts CRS/coordinate
metadata. A title polygon candidate is never promoted to a parcel intersection here.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_1"
TARGET_TITLE = "TGL419520"
AUTHORITY = "London Borough of Barking and Dagenham"
INDEX_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
USER_AGENT = "AAYS-gas_emissions_1-hmlr-title-audit/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: int = 180) -> tuple[bytes | None, str | None]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        if not data:
            return None, "ZERO_BYTE_DOWNLOAD"
        return data, None
    except Exception as exc:  # network/runtime evidence is persisted rather than hidden
        return None, f"{type(exc).__name__}: {exc}"


def resolve_authority_gml(index_html: str) -> tuple[str | None, str | None]:
    escaped = re.escape(AUTHORITY)
    patterns = (
        rf"<tr[^>]*>.*?{escaped}.*?<a[^>]+href=[\"']([^\"']+)[\"']",
        rf"{escaped}.{{0,1600}}?<a[^>]+href=[\"']([^\"']+\.gml[^\"']*)[\"']",
    )
    for pattern in patterns:
        match = re.search(pattern, index_html, flags=re.I | re.S)
        if match:
            return urllib.parse.urljoin(INDEX_URL, match.group(1)), None
    return None, "BARKING_DAGENHAM_GML_LINK_NOT_RESOLVED"


def feature_window(text: str, position: int) -> str:
    lowered = text.casefold()
    start_markers = ("<gml:featuremember", "<wfs:member", "<member")
    end_markers = ("</gml:featuremember>", "</wfs:member>", "</member>")
    starts = [lowered.rfind(marker, 0, position) for marker in start_markers]
    start = max(starts)
    if start < 0:
        start = max(0, position - 30000)
    ends = []
    for marker in end_markers:
        found = lowered.find(marker, position)
        if found >= 0:
            ends.append(found + len(marker))
    end = min(ends) if ends else min(len(text), position + 30000)
    if end <= start:
        end = min(len(text), position + 30000)
    return text[start:end]


def numeric_pairs(raw_values: list[str]) -> list[list[float]]:
    values: list[float] = []
    for raw in raw_values:
        for token in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", raw):
            try:
                values.append(float(token))
            except ValueError:
                continue
    return [[values[i], values[i + 1]] for i in range(0, len(values) - 1, 2)]


def extract_candidates(gml_text: str) -> tuple[int, list[dict[str, Any]]]:
    lowered = gml_text.casefold()
    target = TARGET_TITLE.casefold()
    positions: list[int] = []
    cursor = 0
    while True:
        position = lowered.find(target, cursor)
        if position < 0:
            break
        positions.append(position)
        cursor = position + len(target)

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position in positions:
        window = feature_window(gml_text, position)
        fingerprint = sha256_bytes(window.encode("utf-8", errors="replace"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        srs_names = sorted(set(re.findall(r"srsName=[\"']([^\"']+)[\"']", window, flags=re.I)))
        pos_lists = re.findall(r"<(?:\w+:)?posList\b[^>]*>(.*?)</(?:\w+:)?posList>", window, flags=re.I | re.S)
        positions_raw = re.findall(r"<(?:\w+:)?pos\b[^>]*>(.*?)</(?:\w+:)?pos>", window, flags=re.I | re.S)
        pairs = numeric_pairs(pos_lists + positions_raw)
        bbox = None
        if pairs:
            xs = [pair[0] for pair in pairs]
            ys = [pair[1] for pair in pairs]
            bbox = {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)}
        candidates.append(
            {
                "title_number": TARGET_TITLE,
                "feature_window_sha256": fingerprint,
                "srs_names": srs_names,
                "pos_list_count": len(pos_lists),
                "pos_count": len(positions_raw),
                "coordinate_pair_count": len(pairs),
                "bbox": bbox,
                "coordinate_sample": pairs[:10],
                "geometry_candidate_present": bool(pairs),
                "semantics": "HMLR_TITLE_GEOMETRY_CANDIDATE_NOT_PARCEL_INTERSECTION",
            }
        )
    return len(positions), candidates


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")

    root = Path.cwd()
    report_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_tgl419520_hmlr_geometry_latest.json"
    status_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_tgl419520_hmlr_geometry_latest.json"
    web_path = root / "england_map_web/data/aays_21_slots/gas_emissions_1/tgl419520_hmlr_geometry_latest.json"

    index_data, index_error = fetch_bytes(INDEX_URL, timeout=90)
    gml_url = None
    resolve_error = index_error
    if index_data is not None:
        gml_url, resolve_error = resolve_authority_gml(index_data.decode("utf-8", errors="replace"))

    gml_data = None
    gml_error = resolve_error
    if gml_url:
        gml_data, gml_error = fetch_bytes(gml_url)

    occurrences = 0
    candidates: list[dict[str, Any]] = []
    if gml_data is not None:
        occurrences, candidates = extract_candidates(gml_data.decode("utf-8", errors="replace"))

    geometry_candidates = sum(1 for item in candidates if item["geometry_candidate_present"])
    passed = gml_data is not None and occurrences > 0 and geometry_candidates > 0
    payload: dict[str, Any] = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID", "gas_emissions_1_extract_tgl419520_hmlr_gml_20260722"),
        "generated_at": utc_now(),
        "status": "PASS_HMLR_TITLE_GEOMETRY_CANDIDATE_EXTRACTED" if passed else "BLOCKED_HMLR_TITLE_GEOMETRY_NOT_EXTRACTED",
        "source": {
            "publisher": "HM Land Registry",
            "dataset": "INSPIRE Index Polygons",
            "snapshot_date": "2026-07-05",
            "authority": AUTHORITY,
            "index_url": INDEX_URL,
            "gml_url": gml_url,
            "index_sha256": sha256_bytes(index_data) if index_data else None,
            "gml_sha256": sha256_bytes(gml_data) if gml_data else None,
            "gml_size_bytes": len(gml_data) if gml_data else 0,
        },
        "target_title": TARGET_TITLE,
        "exact_title_occurrences": occurrences,
        "feature_candidate_count": len(candidates),
        "geometry_candidate_count": geometry_candidates,
        "candidates": candidates,
        "blocker": None if passed else (gml_error or "TITLE_OR_GEOMETRY_NOT_FOUND"),
        "verified_title_geometry_candidates": geometry_candidates,
        "verified_parcel_bindings": 0,
        "measured_parcel_emission_rows": 0,
        "quality_gate": "A title geometry candidate requires CRS and coordinate review, then an explicit parcel intersection. This task never emits a parcel emission value.",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    for path in (report_path, status_path, web_path):
        write_json(path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
