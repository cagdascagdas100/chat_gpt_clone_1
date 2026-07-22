#!/usr/bin/env python3
"""Guard the legacy HMLR audit with exact link and match-ratio gates.

This wrapper does not promote parcel-postcode relations. It prevents stale monthly
cache reuse, audits authority link ambiguity, runs the existing evidence worker,
and rejects weak partial results that the legacy worker would otherwise accept.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
DEFAULT_SAMPLE_SIZE = 256
DEFAULT_MINIMUM_RATIO = 0.85
STOPWORDS = {"city", "council", "borough", "district", "metropolitan", "royal", "unitary", "authority", "county", "of", "the", "london"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    p.add_argument("--max-authorities", type=int, default=10)
    p.add_argument("--minimum-match-ratio", type=float, default=DEFAULT_MINIMUM_RATIO)
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--hmlr-registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/004_hmlr_inspire_july_2026_registry_latest.json")
    p.add_argument("--legacy-output", default="england_map_web/data/aays_21_slots/internet_access_3/hmlr_inspire_postcode_centroid_validation_latest.json")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/008_hmlr_revision6_guarded_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def normalize(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def tokens(value: Any) -> set[str]:
    return {token for token in normalize(value).split() if token and token not in STOPWORDS}


def postcode(value: Any) -> str | None:
    value = re.sub(r"\s+", "", str(value or "")).upper()
    return value if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}", value) else None


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            self.links.append({"href": self.href, "text": " ".join(self.text).strip()})
            self.href = None
            self.text = []


def request(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS-internet-access-3/2.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def link_score(authority: str, item: dict[str, str]) -> float:
    target = tokens(authority)
    text = item["text"] + " " + urllib.parse.unquote(item["href"])
    candidate = tokens(text)
    if not target:
        return 2.0 if normalize(authority) in normalize(text) else 0.0
    overlap = target & candidate
    score = len(overlap) / len(target)
    if target <= candidate:
        score += 1.0
    if normalize(authority) in normalize(text):
        score += 1.0
    if not (".zip" in item["href"].lower() or ".gml" in item["href"].lower()):
        score -= 0.25
    return score


def authority_manifest(authorities: list[str], page_url: str, timeout: int) -> dict[str, Any]:
    parser = Parser()
    parser.feed(request(page_url, timeout).decode("utf-8", errors="replace"))
    links = []
    for item in parser.links:
        href = urllib.parse.urljoin(page_url, item["href"])
        combined = normalize(item["text"] + " " + href)
        if ".zip" in href.lower() or ".gml" in href.lower() or "download" in combined:
            links.append({"href": href, "text": item["text"]})
    chosen: dict[str, Any] = {}
    missing: list[str] = []
    ambiguous: list[dict[str, Any]] = []
    for authority in authorities:
        ranked = sorted(((link_score(authority, item), item) for item in links), key=lambda pair: (-pair[0], pair[1]["href"]))
        viable = [pair for pair in ranked if pair[0] >= 1.0]
        if not viable:
            missing.append(authority)
            continue
        if len(viable) > 1 and abs(viable[0][0] - viable[1][0]) < 0.05 and viable[0][1]["href"] != viable[1][1]["href"]:
            ambiguous.append({"authority": authority, "first": viable[0][1], "second": viable[1][1]})
            continue
        chosen[authority] = {**viable[0][1], "score": round(viable[0][0], 4)}
    return {"chosen": chosen, "missing": missing, "ambiguous": ambiguous, "link_count": len(links)}


def eligible_authorities(rows: list[dict[str, Any]], maximum: int) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        authority = str(row.get("london_authority") or "").strip()
        if authority and row.get("hmlr_inspire_id") and postcode(row.get("postcode")) and row.get("internet_status") in {"verified_existing_postcode_proxy", "official_2026_postcode_proxy_sample"}:
            counts[authority] = counts.get(authority, 0) + 1
    return sorted(counts, key=lambda value: (-counts[value], value))[:max(1, maximum)]


def main() -> int:
    options = parse_args()
    if not 0 < options.minimum_match_ratio <= 1:
        raise ValueError("minimum-match-ratio must be within (0,1]")
    repo = root(options.repo_root)
    rows = load(repo / options.rows)
    registry = load(repo / options.hmlr_registry)
    authorities = eligible_authorities(rows, options.max_authorities)
    manifest = authority_manifest(authorities, registry["download_page"], options.timeout)
    date_key = re.sub(r"[^0-9]+", "", registry["publication_date"])
    manifest_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    cache_dir = Path(tempfile.gettempdir()) / "aays_internet_access_3_hmlr_guarded" / f"{date_key}_{manifest_hash}"
    legacy = Path(__file__).resolve().parent / "008_hmlr_inspire_postcode_centroid_polygon_audit.py"
    command = [
        sys.executable,
        str(legacy),
        "--repo-root", str(repo),
        "--sample-size", str(options.sample_size),
        "--max-authorities", str(options.max_authorities),
        "--cache-dir", str(cache_dir),
        "--timeout", str(options.timeout),
    ]
    blocked_before_run = bool(manifest["missing"] or manifest["ambiguous"])
    completed = None
    if not blocked_before_run:
        completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
    legacy_summary = load(repo / options.legacy_output) if (repo / options.legacy_output).exists() else None
    selected = int(((legacy_summary or {}).get("result") or {}).get("sample_rows_selected") or 0)
    polygons = int(((legacy_summary or {}).get("result") or {}).get("inspire_polygons_found") or 0)
    onspd = int(((legacy_summary or {}).get("result") or {}).get("onspd_exact_postcodes_found") or 0)
    minimum = math.ceil(selected * options.minimum_match_ratio) if selected else options.sample_size
    passed = (
        not blocked_before_run
        and completed is not None
        and completed.returncode == 0
        and selected == options.sample_size
        and polygons >= minimum
        and onspd >= minimum
    )
    blockers = ["PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY", "EXACT_UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED"]
    if manifest["missing"]:
        blockers.append("HMLR_AUTHORITY_DOWNLOAD_LINKS_MISSING")
    if manifest["ambiguous"]:
        blockers.append("HMLR_AUTHORITY_DOWNLOAD_LINKS_AMBIGUOUS")
    if completed is not None and completed.returncode != 0:
        blockers.append("LEGACY_HMLR_WORKER_EXIT_NONZERO")
    if selected != options.sample_size:
        blockers.append("HMLR_SAMPLE_COUNT_MISMATCH")
    if polygons < minimum:
        blockers.append("HMLR_INSPIRE_ID_MATCH_RATIO_BELOW_85_PERCENT_GATE")
    if onspd < minimum:
        blockers.append("ONSPD_EXACT_POSTCODE_MATCH_RATIO_BELOW_85_PERCENT_GATE")
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if passed else "blocked",
        "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "guard": {
            "sample_size_required": options.sample_size,
            "minimum_match_ratio": options.minimum_match_ratio,
            "minimum_matches_required": minimum,
            "authority_manifest": manifest,
            "cache_dir": str(cache_dir),
            "cache_identity_includes_publication_date_and_manifest_hash": True,
        },
        "legacy_execution": {
            "command": command,
            "executed": completed is not None,
            "exit_code": completed.returncode if completed is not None else None,
            "stdout_tail": completed.stdout[-8000:] if completed is not None else "",
            "stderr_tail": completed.stderr[-8000:] if completed is not None else "",
        },
        "result": {
            "sample_rows_selected": selected,
            "inspire_polygons_found": polygons,
            "onspd_exact_postcodes_found": onspd,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
            "actual_business_data_rows_written": 0,
        },
        "validation": {"passed": passed, "blockers": blockers},
        "output_semantics": "POSTCODE_CENTROID_VS_INDICATIVE_HMLR_POLYGON_GUARDED_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write(repo / options.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
