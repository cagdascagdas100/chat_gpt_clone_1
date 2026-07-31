from __future__ import annotations

import importlib.util
import json
import time
import urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
ARCHIVE_REPAIR_PATH = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave134_official_binary_archive_gdb_repair_20260731.py"
spec = importlib.util.spec_from_file_location("wave134_archive_repair", ARCHIVE_REPAIR_PATH)
archive_repair = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(archive_repair)
core = archive_repair.core
repair = archive_repair.repair

HUB_BASES = [
    "https://hub.arcgis.com/api/v3/datasets/{dataset}/downloads/data",
    "https://opendata.arcgis.com/api/v3/datasets/{dataset}/downloads/data",
    "https://hub.arcgis.com/api/download/v1/items/{item}/shapefile",
]
BOUNDARY_EXPORTS = [
    ("357ee15b1080431491bf965394090c72", "2011", "LSOA11CD", "BFC"),
    ("a81d7fb9efe94d369d153499f95835d5", "2011", "LSOA11CD", "BGC"),
    ("2bbaef5230694f3abae4f9145a3a9800", "2021", "LSOA21CD", "BFC"),
    ("68515293204e43ca8ab56fa13ae8a547", "2021", "LSOA21CD", "BGC"),
]


def filtered_where(field: str) -> str:
    return f"{field} IN ('{core.w.m.EXPECTED_2011}','{core.w.m.EXPECTED_2021}')"


def discover_filtered_exports(previous: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item_id, year, field, precision in BOUNDARY_EXPORTS:
        meta = repair.fetch_meta(item_id) or {}
        title = str(meta.get("title") or f"ONS LSOA {year} {precision}")
        owner = str(meta.get("owner") or "")
        service_url = str(meta.get("url") or "")
        core.add("wave134_hub_export_seed", item_id, bool(meta), {
            "title": title,
            "owner": owner,
            "service_url": service_url,
            "year": year,
            "precision": precision,
            "field": field,
        }, None if meta else "ITEM_METADATA_UNAVAILABLE")
        where = filtered_where(field)
        for endpoint_index, template in enumerate(HUB_BASES, start=1):
            if "api/download/v1" in template:
                params = {
                    "layers": "0",
                    "where": where,
                    "spatialRefId": "27700",
                }
            else:
                params = {
                    "format": "shp",
                    "spatialRefId": "27700",
                    "where": where,
                }
            url = template.format(dataset=f"{item_id}_0", item=item_id) + "?" + urllib.parse.urlencode(params)
            candidates.append({
                "item_id": item_id,
                "title": f"{title} — filtered official Hub Shapefile endpoint {endpoint_index}",
                "item_type": "Shapefile",
                "kind": "official_hub_filtered_shapefile",
                "url": url,
                "previous_sha256": None,
                "previous_content_type": None,
                "previous_bytes_read": None,
                "previous_members": [],
                "binary_members_previously_seen": True,
                "discovery_relation": "official_feature_service_to_hub_filtered_export",
                "trusted_official_relation": True,
                "owner": owner,
                "created": meta.get("created"),
                "modified": meta.get("modified"),
                "size": meta.get("size"),
                "year_context": year,
                "precision": precision,
                "code_field": field,
                "where": where,
                "service_url": service_url,
                "endpoint_index": endpoint_index,
            })
    core.add("wave134_hub_export_candidate_gate", "official_filtered_hub_shapefile_exports", len(candidates) == 12, {
        "candidate_count": len(candidates),
        "item_ids": [row["item_id"] for row in candidates],
        "endpoint_indexes": [row["endpoint_index"] for row in candidates],
        "where_clauses": sorted({row["where"] for row in candidates}),
    }, None if len(candidates) == 12 else "EXPECTED_TWELVE_FILTERED_EXPORTS")
    if len(candidates) != 12:
        raise RuntimeError("Wave134 filtered Hub export candidate construction failed")
    return candidates


_original_fetch = core.w.fetch_bytes


def _extract_urls(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            urls.extend(_extract_urls(child))
    elif isinstance(value, list):
        for child in value:
            urls.extend(_extract_urls(child))
    elif isinstance(value, str) and value.startswith("http"):
        urls.append(value)
    return urls


def fetch_hub_export(url: str) -> dict[str, Any]:
    first = _original_fetch(url)
    if not first.get("ok") or first.get("truncated"):
        return first
    payload = first.get("bytes", b"")
    content_type = str(first.get("content_type") or "").lower()
    if payload[:2] == b"PK":
        return first
    if "json" not in content_type and not payload.lstrip().startswith((b"{", b"[")):
        return first
    try:
        document = json.loads(payload.decode("utf-8", errors="strict"))
    except Exception:
        return first
    urls = []
    for candidate_url in _extract_urls(document):
        if candidate_url == url:
            continue
        lower = candidate_url.lower()
        if any(token in lower for token in (".zip", "download", "result", "status")):
            urls.append(candidate_url)
    core.add("wave134_hub_export_async_response", url, True, {
        "status": first.get("status"),
        "content_type": first.get("content_type"),
        "document_keys": sorted(document.keys()) if isinstance(document, dict) else [],
        "discovered_urls": urls[:20],
        "document_sha256": core.digest(document),
    })
    visited = {url}
    for round_index in range(1, 7):
        if not urls:
            break
        next_urls: list[str] = []
        for candidate_url in urls[:8]:
            if candidate_url in visited:
                continue
            visited.add(candidate_url)
            result = _original_fetch(candidate_url)
            if result.get("ok") and not result.get("truncated") and result.get("bytes", b"")[:2] == b"PK":
                core.add("wave134_hub_export_resolved", candidate_url, True, {
                    "round": round_index,
                    "bytes_read": result.get("bytes_read"),
                    "sha256": result.get("sha256"),
                    "source_url": url,
                })
                return result
            child_payload = result.get("bytes", b"") if result.get("ok") else b""
            try:
                child = json.loads(child_payload.decode("utf-8"))
            except Exception:
                child = None
            if child is not None:
                for child_url in _extract_urls(child):
                    if child_url not in visited:
                        next_urls.append(child_url)
                core.add("wave134_hub_export_poll", candidate_url, result.get("ok", False), {
                    "round": round_index,
                    "status": result.get("status"),
                    "content_type": result.get("content_type"),
                    "new_urls": next_urls[-20:],
                    "document_sha256": core.digest(child),
                }, result.get("error"))
        urls = next_urls
        if urls:
            time.sleep(min(round_index, 3))
    return first


core.package_candidates = discover_filtered_exports
core.w.fetch_bytes = fetch_hub_export

if __name__ == "__main__":
    core.main()
