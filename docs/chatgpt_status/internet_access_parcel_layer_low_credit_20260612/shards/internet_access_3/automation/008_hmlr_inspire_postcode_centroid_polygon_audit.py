#!/usr/bin/env python3
"""Audit postcode-centroid evidence against HMLR INSPIRE polygons for internet_access_3.

Evidence only: an ONSPD postcode centroid inside an indicative HMLR polygon does not
establish an address, UPRN or measured parcel broadband service. No confidence is raised.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SLOT_ID = "internet_access_3"
SAMPLE_SIZE = 192
ROWS_EXPECTED = 30761


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--onspd-registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/003_onspd_may_2026_registry_latest.json")
    p.add_argument("--hmlr-registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/004_hmlr_inspire_july_2026_registry_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/006_hmlr_inspire_polygon_audit_latest.json")
    p.add_argument("--sample-size", type=int, default=SAMPLE_SIZE)
    p.add_argument("--max-authorities", type=int, default=8)
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--timeout", type=int, default=180)
    return p.parse_args()


def repo_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "england_map_web").exists() and (candidate / "docs").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def postcode(value: Any) -> str | None:
    value = re.sub(r"\s+", "", str(value or "")).upper()
    return value if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}", value) else None


def balanced_sample(rows: list[dict[str, Any]], size: int, max_authorities: int) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        authority = str(row.get("london_authority") or "").strip()
        if (
            row.get("hmlr_inspire_id")
            and postcode(row.get("postcode"))
            and authority
            and row.get("internet_status") in {"verified_existing_postcode_proxy", "official_2026_postcode_proxy_sample"}
        ):
            groups[authority].append(row)
    chosen = sorted(groups, key=lambda key: (-len(groups[key]), key))[:max(1, max_authorities)]
    if not chosen:
        return []
    for values in groups.values():
        values.sort(key=lambda row: int(row["row_no"]))
    selected: list[dict[str, Any]] = []
    per_group = max(1, math.ceil(size / len(chosen)))
    for authority in chosen:
        values = groups[authority]
        take = min(per_group, len(values))
        if take == 1:
            indexes = [len(values) // 2]
        else:
            indexes = [round(i * (len(values) - 1) / (take - 1)) for i in range(take)]
        selected.extend(values[index] for index in indexes)
    selected.sort(key=lambda row: int(row["row_no"]))
    if len(selected) > size:
        indexes = [round(i * (len(selected) - 1) / (size - 1)) for i in range(size)] if size > 1 else [0]
        selected = [selected[index] for index in indexes]
    return selected


class LinkParser(HTMLParser):
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


def request_bytes(url: str, timeout: int, data: bytes | None = None) -> bytes:
    request = urllib.request.Request(url, data=data, headers={"User-Agent": "TerraYield-AAYS-internet-access-3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def download_links(page_url: str, timeout: int) -> list[dict[str, str]]:
    parser = LinkParser()
    parser.feed(request_bytes(page_url, timeout).decode("utf-8", errors="replace"))
    result = []
    for item in parser.links:
        href = urllib.parse.urljoin(page_url, item["href"])
        combined = (item["text"] + " " + href).lower()
        if any(token in combined for token in (".zip", ".gml", "download")):
            result.append({"href": href, "text": item["text"]})
    return result


def best_link(authority: str, links: list[dict[str, str]]) -> dict[str, str] | None:
    target = set(norm(authority).split())
    best: tuple[float, dict[str, str]] | None = None
    for item in links:
        terms = set(norm(item["text"] + " " + item["href"]).split())
        if not terms:
            continue
        score = len(target & terms) / max(1, len(target | terms))
        if norm(authority) in norm(item["text"] + " " + item["href"]):
            score += 1.0
        if best is None or score > best[0]:
            best = (score, item)
    return best[1] if best and best[0] >= 0.20 else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hydrate(authority: str, link: dict[str, str], cache: Path, timeout: int) -> dict[str, Any]:
    cache.mkdir(parents=True, exist_ok=True)
    suffix = ".zip" if ".zip" in link["href"].lower() else ".gml"
    target = cache / (re.sub(r"[^a-z0-9]+", "_", authority.lower()).strip("_") + suffix)
    cache_hit = target.exists() and target.stat().st_size > 1024
    if not cache_hit:
        content = request_bytes(link["href"], timeout)
        if len(content) <= 1024:
            raise ValueError(f"HMLR download unexpectedly small for {authority}: {len(content)}")
        target.write_bytes(content)
    gml_files: list[Path] = []
    if zipfile.is_zipfile(target):
        extract_dir = cache / (target.stem + "_extracted")
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target) as archive:
            for member in archive.namelist():
                if member.lower().endswith(".gml"):
                    output = extract_dir / Path(member).name
                    if not output.exists():
                        output.write_bytes(archive.read(member))
                    gml_files.append(output)
    elif target.suffix.lower() == ".gml":
        gml_files.append(target)
    return {
        "authority": authority,
        "url": link["href"],
        "link_text": link["text"],
        "cache_hit": cache_hit,
        "download_sha256": sha256(target),
        "download_size": target.stat().st_size,
        "gml_files": [str(path) for path in gml_files],
    }


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_ring(text: str) -> list[tuple[float, float]]:
    values = [float(value) for value in re.split(r"[\s,]+", text.strip()) if value]
    if len(values) < 6 or len(values) % 2:
        return []
    ring = list(zip(values[0::2], values[1::2]))
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def find_target_rings(gml_files: list[Path], target_ids: set[str]) -> dict[str, list[tuple[float, float]]]:
    found: dict[str, list[tuple[float, float]]] = {}
    for path in gml_files:
        root = ET.parse(path).getroot()
        for element in root.iter():
            if local(element.tag) not in {"cadastralparcel", "featuremember", "member"}:
                continue
            texts = {text.strip() for text in element.itertext() if text and text.strip()}
            matches = target_ids & texts
            if not matches:
                continue
            pos = next((child.text for child in element.iter() if local(child.tag) in {"poslist", "coordinates"} and child.text), None)
            ring = parse_ring(pos or "")
            if ring:
                for inspire_id in matches:
                    found.setdefault(inspire_id, ring)
    return found


def point_in_ring(x: float, y: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def distance_to_ring(x: float, y: float, ring: list[tuple[float, float]]) -> float:
    if point_in_ring(x, y, ring):
        return 0.0
    return min(segment_distance(x, y, *ring[i], *ring[i + 1]) for i in range(len(ring) - 1))


def fetch_onspd(query_url: str, postcodes: list[str], timeout: int) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(postcodes), 75):
        batch = postcodes[offset:offset + 75]
        quoted = ",".join("'" + item.replace("'", "''") + "'" for item in batch)
        data = urllib.parse.urlencode({
            "f": "json",
            "where": f"pcd7 IN ({quoted})",
            "outFields": "pcd7,pcds,east1m,north1m,doterm",
            "returnGeometry": "false",
            "resultRecordCount": "1000",
        }).encode()
        payload = json.loads(request_bytes(query_url, timeout, data=data).decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        for feature in payload.get("features", []):
            attrs = (feature or {}).get("attributes") or {}
            key = postcode(attrs.get("pcd7") or attrs.get("pcds"))
            if key:
                result[key] = attrs
    return result


def update_feed(output_root: Path, candidates: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    feed_path = output_root / "operation_feed_latest.json"
    feed = load_json(feed_path) if feed_path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    operations.append({"sequence": sequence, "status": "PASS" if summary["validation"]["passed"] else "BLOCKED", "operation": "HMLR_INSPIRE_POLYGON_SOURCE_READBACK", "detail": f"authorities={summary['result']['authorities_hydrated']}; polygons={summary['result']['inspire_polygons_found']}; confidence_not_raised"})
    sequence += 1
    for candidate in candidates:
        operations.append({"sequence": sequence, "status": "PASS" if candidate["hmlr_polygon_found"] else "NO_DATA", "operation": "HMLR_POSTCODE_CENTROID_POLYGON_AUDIT", "row_no": candidate["row_no"], "parcel_id": candidate["canonical_program_parcel_id"], "postcode": candidate["postcode"], "detail": f"{candidate['candidate_status']}; inside={candidate['postcode_centroid_inside_indicative_polygon']}; distance_m={candidate['postcode_centroid_to_polygon_distance_m']}; confidence_not_raised"})
        sequence += 1
    feed.update({"updated_at": summary["updated_at"], "display_mode": "line_by_line", "final_ready": False, "operations": operations, "safety": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False}})
    atomic_json(feed_path, feed)


def main() -> int:
    args = parse_args()
    root = repo_root(args.repo_root)
    rows = load_json(root / args.rows)
    onspd_registry = load_json(root / args.onspd_registry)
    hmlr_registry = load_json(root / args.hmlr_registry)
    output_root = root / args.output_root
    if not isinstance(rows, list) or len(rows) != ROWS_EXPECTED:
        raise ValueError("migrated internet_access_3 rows missing or wrong count")
    sample = balanced_sample(rows, args.sample_size, args.max_authorities)
    if not sample:
        raise ValueError("no eligible HMLR/postcode proxy sample rows")
    authorities = sorted({str(row["london_authority"]) for row in sample})
    links = download_links(hmlr_registry["download_page"], args.timeout)
    cache = args.cache_dir or Path(tempfile.gettempdir()) / "aays_internet_access_3_hmlr_202607"
    hydrations: list[dict[str, Any]] = []
    missing_links: list[str] = []
    authority_gml: dict[str, list[Path]] = {}
    for authority in authorities:
        link = best_link(authority, links)
        if not link:
            missing_links.append(authority)
            continue
        hydrated = hydrate(authority, link, cache, args.timeout)
        hydrations.append(hydrated)
        authority_gml[authority] = [Path(value) for value in hydrated["gml_files"]]
    targets_by_authority: dict[str, set[str]] = defaultdict(set)
    for row in sample:
        targets_by_authority[str(row["london_authority"])].add(str(row["hmlr_inspire_id"]))
    rings: dict[str, list[tuple[float, float]]] = {}
    for authority, target_ids in targets_by_authority.items():
        rings.update(find_target_rings(authority_gml.get(authority, []), target_ids))
    official = fetch_onspd(onspd_registry["query_url"], sorted({postcode(row.get("postcode")) for row in sample} - {None}), args.timeout)
    candidates: list[dict[str, Any]] = []
    inside_count = 0
    near_25 = 0
    polygon_found = 0
    for row in sample:
        pc = postcode(row.get("postcode"))
        inspire_id = str(row.get("hmlr_inspire_id"))
        record = official.get(pc or "")
        ring = rings.get(inspire_id)
        east = float(record["east1m"]) if record and record.get("east1m") not in {None, ""} else None
        north = float(record["north1m"]) if record and record.get("north1m") not in {None, ""} else None
        inside = bool(ring and east is not None and north is not None and point_in_ring(east, north, ring))
        distance = round(distance_to_ring(east, north, ring), 2) if ring and east is not None and north is not None else None
        if ring:
            polygon_found += 1
        if inside:
            inside_count += 1
        if distance is not None and distance <= 25:
            near_25 += 1
        status = "HMLR_POLYGON_NOT_FOUND"
        if ring and record:
            status = "POSTCODE_CENTROID_INSIDE_INDICATIVE_HMLR_POLYGON" if inside else "POSTCODE_CENTROID_OUTSIDE_INDICATIVE_HMLR_POLYGON"
        elif ring and not record:
            status = "ONSPD_POSTCODE_NOT_FOUND"
        candidates.append({
            "row_no": int(row["row_no"]),
            "canonical_program_parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": inspire_id,
            "london_authority": row.get("london_authority"),
            "postcode": pc,
            "hmlr_polygon_found": ring is not None,
            "onspd_postcode_found": record is not None,
            "onspd_east1m": east,
            "onspd_north1m": north,
            "postcode_centroid_inside_indicative_polygon": inside,
            "postcode_centroid_to_polygon_distance_m": distance,
            "candidate_status": status,
            "parcel_relation_promoted": False,
            "confidence_raised": False,
            "source_accuracy_scores": {"hmlr_inspire": 96 if ring else 0, "onspd": 96 if record else 0},
            "parcel_relation_accuracy_ceiling": 50,
            "evidence_semantics": "POSTCODE_CENTROID_VS_INDICATIVE_HMLR_POLYGON_ONLY",
            "blockers": ["HMLR_INSPIRE_POLYGON_IS_INDICATIVE_NOT_LEGAL_BOUNDARY", "POSTCODE_CENTROID_IS_NOT_ADDRESS_OR_UPRN_PROOF"],
        })
    passed = not missing_links and polygon_found > 0 and len(official) > 0
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "task_id": "aays1-internet-access-3-hmlr-inspire-postcode-centroid-audit-20260722",
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if passed else "blocked",
        "updated_at": now,
        "source_validation": {"dataset": hmlr_registry["dataset"], "publication_date": hmlr_registry["publication_date"], "download_page": hmlr_registry["download_page"], "hydrations": hydrations, "missing_authority_links": missing_links},
        "result": {"sample_rows_requested": args.sample_size, "sample_rows_selected": len(sample), "authorities_selected": len(authorities), "authorities_hydrated": len(hydrations), "inspire_polygons_found": polygon_found, "onspd_exact_postcodes_found": len(official), "postcode_centroids_inside_indicative_polygon": inside_count, "postcode_centroids_within_25m_of_polygon": near_25, "parcel_relations_promoted": 0, "confidence_uplifts": 0, "quality_scores_created": 0, "actual_business_data_rows_written": 0},
        "validation": {"passed": passed, "blockers": ["PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY", "EXACT_UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED"] + (["HMLR_AUTHORITY_DOWNLOAD_LINKS_MISSING"] if missing_links else [])},
        "output_semantics": "POSTCODE_CENTROID_VS_INDICATIVE_HMLR_POLYGON_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "HYDRATE_OS_OPEN_UPRN_AND_CURRENT_ONSUD_THEN_TEST_EXACT_UPRN_POSTCODE_RELATIONS",
    }
    atomic_json(output_root / "hmlr_inspire_postcode_centroid_candidates_latest.json", candidates)
    atomic_json(output_root / "hmlr_inspire_postcode_centroid_validation_latest.json", summary)
    atomic_json(root / args.runner_output, summary)
    update_feed(output_root, candidates, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
