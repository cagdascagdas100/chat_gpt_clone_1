from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
CORE_PATH = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave134_official_binary_shapefile_dbf_crs_geometry_reconciliation_20260731.py"
spec = importlib.util.spec_from_file_location("wave134_core", CORE_PATH)
core = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(core)

PORTAL = "https://www.arcgis.com/sharing/rest"
KNOWN_BOUNDARY_SERVICE_ITEMS = [
    "357ee15b1080431491bf965394090c72",  # 2011 BFC
    "a81d7fb9efe94d369d153499f95835d5",  # 2011 BGC
    "2bbaef5230694f3abae4f9145a3a9800",  # 2021 BFC
    "68515293204e43ca8ab56fa13ae8a547",  # 2021 BGC
]
SEARCH_QUERIES = [
    'owner:ONSGeography_data "Lower Layer Super Output Areas December 2011 Boundaries" type:Shapefile',
    'owner:ONSGeography_data "Lower Layer Super Output Areas December 2021 Boundaries" type:Shapefile',
    'owner:ONSGeography_data "LSOA 2011 Boundaries" type:Shapefile',
    'owner:ONSGeography_data "LSOA 2021 Boundaries" type:Shapefile',
    'owner:ONSGeography_data "Lower Layer Super Output Areas" "File Geodatabase"',
]
ALLOWED_TYPES = {"shapefile", "file geodatabase", "csv", "geojson"}


def official(meta: dict[str, Any]) -> bool:
    owner = str(meta.get("owner") or "").lower()
    return owner.startswith("onsgeography")


def relevant(meta: dict[str, Any]) -> bool:
    text = " ".join(str(meta.get(key) or "") for key in ("title", "tags", "snippet", "description", "typeKeywords")).lower()
    return ("lower layer super output" in text or "lsoa" in text) and ("boundar" in text or "shapefile" in text)


def fetch_meta(item_id: str) -> dict[str, Any] | None:
    result = core.w.safe_json("wave134_repair_item_metadata", f"{PORTAL}/content/items/{item_id}", {"f": "json"})
    if not result["ok"] or result["data"].get("error"):
        return None
    return result["data"]


def add_candidate(store: dict[str, dict[str, Any]], meta: dict[str, Any], relation: str) -> None:
    item_id = str(meta.get("id") or "")
    item_type = str(meta.get("type") or "")
    if not item_id or not official(meta) or not relevant(meta) or item_type.lower() not in ALLOWED_TYPES:
        return
    url = f"{PORTAL}/content/items/{item_id}/data"
    store[url] = {
        "item_id": item_id,
        "title": meta.get("title"),
        "item_type": item_type,
        "kind": "official_item_data_binary",
        "url": url,
        "previous_sha256": None,
        "previous_content_type": None,
        "previous_bytes_read": None,
        "previous_members": [],
        "binary_members_previously_seen": False,
        "discovery_relation": relation,
        "owner": meta.get("owner"),
        "created": meta.get("created"),
        "modified": meta.get("modified"),
        "size": meta.get("size"),
    }


def discover(previous: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}

    # Reuse any directly downloadable official file items already catalogued by Wave133.
    for meta in previous.get("official_item_details", []):
        add_candidate(candidates, meta, "wave133_catalog")

    # Resolve official Service2Data links in both directions from the four known ONS boundary services.
    discovered_ids: set[str] = set(KNOWN_BOUNDARY_SERVICE_ITEMS)
    for service_id in KNOWN_BOUNDARY_SERVICE_ITEMS:
        service_meta = fetch_meta(service_id)
        if service_meta:
            core.add("wave134_repair_seed_service", service_id, True, {
                "title": service_meta.get("title"), "type": service_meta.get("type"), "owner": service_meta.get("owner")
            })
        for direction in ("forward", "reverse"):
            rel = core.w.safe_json(
                "wave134_repair_related_items",
                f"{PORTAL}/content/items/{service_id}/relatedItems",
                {"f": "json", "relationshipType": "Service2Data", "direction": direction},
            )
            rows = rel["data"].get("relatedItems", []) if rel["ok"] else []
            core.add("wave134_repair_relation_summary", service_id, rel["ok"], {
                "direction": direction, "related_count": len(rows), "related_ids": [row.get("id") for row in rows]
            }, rel.get("error"))
            for row in rows:
                item_id = str(row.get("id") or "")
                if item_id:
                    discovered_ids.add(item_id)
                add_candidate(candidates, row, f"Service2Data:{service_id}:{direction}")

    # Metadata readback catches relatedItems responses that omit type/owner fields.
    for item_id in sorted(discovered_ids):
        meta = fetch_meta(item_id)
        if meta:
            add_candidate(candidates, meta, "metadata_readback")

    # Independent official ArcGIS catalogue search for binary boundary packages.
    for query in SEARCH_QUERIES:
        result = core.w.safe_json("wave134_repair_catalog_search", f"{PORTAL}/search", {"f": "json", "num": 100, "q": query})
        rows = result["data"].get("results", []) if result["ok"] else []
        core.add("wave134_repair_catalog_summary", query, result["ok"], {
            "returned": len(rows), "official_relevant": sum(official(row) and relevant(row) for row in rows)
        }, result.get("error"))
        for row in rows:
            add_candidate(candidates, row, f"catalog:{query}")

    ranked = sorted(
        candidates.values(),
        key=lambda row: (
            0 if "2011" in str(row.get("title") or "") else 1,
            0 if "2021" in str(row.get("title") or "") else 1,
            0 if "generalised" in str(row.get("title") or "").lower() else 1,
            0 if "full clipped" in str(row.get("title") or "").lower() else 1,
            int(row.get("size") or 0),
            str(row.get("item_id") or ""),
        ),
    )[: core.MAX_PACKAGES]
    core.add("wave134_repair_candidate_gate", "official_binary_package_candidates", bool(ranked), {
        "candidate_count": len(ranked),
        "candidate_ids": [row.get("item_id") for row in ranked],
        "candidate_titles": [row.get("title") for row in ranked],
    }, None if ranked else "NO_OFFICIAL_BINARY_PACKAGE_CANDIDATES")
    if not ranked:
        raise RuntimeError("Wave134 repair found no official ONS binary package candidates")
    return ranked


core.package_candidates = discover

if __name__ == "__main__":
    core.main()
