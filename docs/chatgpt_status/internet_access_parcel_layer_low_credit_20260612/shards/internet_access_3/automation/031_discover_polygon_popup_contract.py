#!/usr/bin/env python3
"""Discover an exact main-map polygon popup contract without guessing paths.

The scanner reads only tracked text assets under england_map_web, groups each HTML
entry with its local script dependencies, and requires internet, popup, identity and
map-engine evidence. Ambiguous or missing candidates remain WAITING.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SLOT_ID = "internet_access_3"
TEXT_EXTENSIONS = {".html", ".htm", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".vue"}
SCRIPT_RE = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.I)
TOKEN_WEIGHTS = {
    "bindPopup": 10,
    "openPopup": 5,
    "leaflet-popup-content": 4,
    "L.geoJSON": 7,
    "L.map(": 5,
    "queryRenderedFeatures": 10,
    "querySourceFeatures": 8,
    "maplibregl-popup-content": 4,
    "new maplibregl.Map": 6,
    "Internet Availability": 8,
    "internet_availability": 8,
    "internet.geojson": 10,
    "program_layer_matrix/internet": 10,
    "parcel_id": 4,
    "row_no": 4,
    "hmlr_inspire_id": 2,
}


def _safe_relative(base: PurePosixPath, src: str) -> str | None:
    if not src or "://" in src or src.startswith(("//", "data:", "blob:")):
        return None
    clean = src.split("?", 1)[0].split("#", 1)[0]
    candidate = base.joinpath(clean)
    parts: list[str] = []
    for part in candidate.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    path = PurePosixPath(*parts).as_posix()
    return path if path.startswith("england_map_web/") else None


def _engine(tokens: set[str]) -> str | None:
    leaflet = bool(tokens & {"bindPopup", "openPopup", "leaflet-popup-content", "L.geoJSON", "L.map("})
    maplibre = bool(tokens & {"queryRenderedFeatures", "querySourceFeatures", "maplibregl-popup-content", "new maplibregl.Map"})
    if leaflet and maplibre:
        return "leaflet_or_maplibre"
    if leaflet:
        return "leaflet"
    if maplibre:
        return "maplibre"
    return None


def discover_from_files(files: dict[str, str]) -> dict[str, Any]:
    normalized = {PurePosixPath(path).as_posix(): text for path, text in files.items()}
    candidates: list[dict[str, Any]] = []
    for html_path, html in normalized.items():
        if PurePosixPath(html_path).suffix.lower() not in {".html", ".htm"}:
            continue
        included = [html_path]
        bundle = [html]
        base = PurePosixPath(html_path).parent
        for src in SCRIPT_RE.findall(html):
            resolved = _safe_relative(base, src)
            if resolved and resolved in normalized:
                included.append(resolved)
                bundle.append(normalized[resolved])
        joined = "\n".join(bundle)
        tokens = {token for token in TOKEN_WEIGHTS if token in joined}
        engine = _engine(tokens)
        popup = bool(tokens & {"bindPopup", "openPopup", "leaflet-popup-content", "queryRenderedFeatures", "maplibregl-popup-content"})
        internet = bool(tokens & {"Internet Availability", "internet_availability", "internet.geojson", "program_layer_matrix/internet"})
        identity = bool(tokens & {"parcel_id", "row_no", "hmlr_inspire_id"})
        score = sum(TOKEN_WEIGHTS[token] for token in tokens)
        candidates.append({
            "html_path": html_path,
            "included_paths": included,
            "engine": engine,
            "popup_evidence": popup,
            "internet_evidence": internet,
            "identity_evidence": identity,
            "score": score,
            "matched_tokens": sorted(tokens),
            "bundle_sha256": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        })
    candidates.sort(key=lambda item: (-item["score"], item["html_path"]))
    qualified = [item for item in candidates if item["engine"] and item["popup_evidence"] and item["internet_evidence"] and item["identity_evidence"]]
    selected = None
    state = "WAITING_UNIQUE_MAIN_MAP_POPUP_CONTRACT"
    reason = "no qualified tracked HTML bundle"
    if qualified:
        top_score = qualified[0]["score"]
        top = [item for item in qualified if item["score"] == top_score]
        if len(top) == 1:
            selected = top[0]
            state = "PASS_UNIQUE_MAIN_MAP_POPUP_CONTRACT_DISCOVERED"
            reason = "one highest-scoring exact tracked HTML bundle"
        else:
            reason = f"ambiguous highest score across {len(top)} bundles"
    return {"state": state, "reason": reason, "selected": selected, "candidates": candidates}


def _atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _tracked_files(repo_root: Path, max_bytes: int) -> dict[str, str]:
    proc = subprocess.run(["git", "ls-files", "-z", "--", "england_map_web"], cwd=repo_root, capture_output=True, check=True)
    result: dict[str, str] = {}
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="strict")
        if PurePosixPath(rel).suffix.lower() not in TEXT_EXTENSIONS:
            continue
        path = repo_root / rel
        if not path.is_file() or path.stat().st_size > max_bytes:
            continue
        try:
            result[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    discovery = discover_from_files(_tracked_files(root, args.max_bytes))
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        **discovery,
        "nearest_feature_fallback_allowed": False,
        "manual_coordinate_fallback_allowed": False,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    _atomic(args.output, payload)
    print(json.dumps({"state": payload["state"], "candidate_count": len(payload["candidates"]), "selected": (payload["selected"] or {}).get("html_path")}, sort_keys=True))
    return 0 if payload["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
