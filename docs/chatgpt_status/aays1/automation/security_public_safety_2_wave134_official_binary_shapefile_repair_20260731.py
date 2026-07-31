from __future__ import annotations

import collections
import importlib.util
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
    "owner:ONSGeography_data LSOA 2011 boundaries",
    "owner:ONSGeography_data LSOA 2021 boundaries",
    'owner:ONSGeography_data "Lower Layer Super Output Areas" 2011',
    'owner:ONSGeography_data "Lower Layer Super Output Areas" 2021',
    'owner:ONSGeography "Lower Layer Super Output Areas" boundaries',
    'owner:ONSGeography_data "Lower Layer Super Output Areas" Shapefile',
    'owner:ONSGeography_data "Lower Layer Super Output Areas" "File Geodatabase"',
    'owner:ONSGeography_data "LSOA" "Full Clipped"',
    'owner:ONSGeography_data "LSOA" "Generalised Clipped"',
]
FILE_TYPES = {
    "shapefile",
    "file geodatabase",
    "service definition",
    "csv",
    "geojson",
    "microsoft excel",
    "kml",
    "map package",
    "sqlite geodatabase",
}
DENIED_TYPES = {
    "feature service",
    "map service",
    "image service",
    "web map",
    "web mapping application",
    "dashboard",
    "storymap",
    "vector tile service",
}
ITEM_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def official(meta: dict[str, Any]) -> bool:
    owner = str(meta.get("owner") or "").lower()
    url = str(meta.get("url") or "").lower()
    return owner.startswith("onsgeography") or "services1.arcgis.com/esmarspqhymw9bz9" in url


def relevant(meta: dict[str, Any], trusted_relation: bool = False) -> bool:
    if trusted_relation:
        return True
    text = " ".join(str(meta.get(key) or "") for key in ("title", "tags", "snippet", "description", "typeKeywords")).lower()
    return "lower layer super output" in text or "lsoa" in text


def fetch_meta(item_id: str) -> dict[str, Any] | None:
    result = core.w.safe_json("wave134_repair_item_metadata", f"{PORTAL}/content/items/{item_id}", {"f": "json"})
    if not result["ok"] or result["data"].get("error"):
        return None
    return result["data"]


def extract_item_ids(value: Any, key_hint: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.update(extract_item_ids(child, str(key)))
    elif isinstance(value, list):
        for child in value:
            found.update(extract_item_ids(child, key_hint))
    elif isinstance(value, str):
        candidate = value.strip()
        if ITEM_ID_RE.fullmatch(candidate) and any(token in key_hint.lower() for token in ("item", "service", "source", "data", "origin")):
            found.add(candidate.lower())
    return found


def add_candidate(
    store: dict[str, dict[str, Any]],
    meta: dict[str, Any],
    relation: str,
    trusted_relation: bool = False,
) -> None:
    item_id = str(meta.get("id") or "")
    item_type = str(meta.get("type") or "").strip()
    item_type_lower = item_type.lower()
    if not item_id or not ITEM_ID_RE.fullmatch(item_id):
        return
    if not trusted_relation and not official(meta):
        return
    if not relevant(meta, trusted_relation=trusted_relation):
        return
    if item_type_lower in DENIED_TYPES:
        return
    size = int(meta.get("size") or 0)
    file_backed = item_type_lower in FILE_TYPES or size > 0
    if not file_backed:
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
        "trusted_official_relation": trusted_relation,
        "owner": meta.get("owner"),
        "created": meta.get("created"),
        "modified": meta.get("modified"),
        "size": size,
    }


def discover(previous: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    discovered_ids: set[str] = set(KNOWN_BOUNDARY_SERVICE_ITEMS)
    trusted_ids: set[str] = set()
    observed_types: collections.Counter[str] = collections.Counter()

    # Reuse all official file-backed LSOA items already catalogued by Wave133.
    for meta in previous.get("official_item_details", []):
        observed_types[str(meta.get("type") or "<missing>")] += 1
        item_id = str(meta.get("id") or "")
        if ITEM_ID_RE.fullmatch(item_id):
            discovered_ids.add(item_id.lower())
        add_candidate(candidates, meta, "wave133_catalog")

    # Resolve Service2Data in both directions and inspect service data JSON for source item identifiers.
    for service_id in KNOWN_BOUNDARY_SERVICE_ITEMS:
        service_meta = fetch_meta(service_id)
        if service_meta:
            observed_types[str(service_meta.get("type") or "<missing>")] += 1
            core.add("wave134_repair_seed_service", service_id, True, {
                "title": service_meta.get("title"),
                "type": service_meta.get("type"),
                "owner": service_meta.get("owner"),
                "url": service_meta.get("url"),
            })
        service_data = core.w.safe_json(
            "wave134_repair_seed_item_data",
            f"{PORTAL}/content/items/{service_id}/data",
            {"f": "json"},
        )
        referenced_ids = extract_item_ids(service_data["data"]) if service_data["ok"] else set()
        discovered_ids.update(referenced_ids)
        trusted_ids.update(referenced_ids)
        core.add("wave134_repair_seed_data_references", service_id, service_data["ok"], {
            "referenced_ids": sorted(referenced_ids),
            "reference_count": len(referenced_ids),
        }, service_data.get("error"))

        for relationship in ("Service2Data", "Service2Service", "Map2Service"):
            for direction in ("forward", "reverse"):
                rel = core.w.safe_json(
                    "wave134_repair_related_items",
                    f"{PORTAL}/content/items/{service_id}/relatedItems",
                    {"f": "json", "relationshipType": relationship, "direction": direction},
                )
                rows = rel["data"].get("relatedItems", []) if rel["ok"] else []
                ids = [str(row.get("id") or "") for row in rows if ITEM_ID_RE.fullmatch(str(row.get("id") or ""))]
                discovered_ids.update(item_id.lower() for item_id in ids)
                if relationship == "Service2Data":
                    trusted_ids.update(item_id.lower() for item_id in ids)
                core.add("wave134_repair_relation_summary", service_id, rel["ok"], {
                    "relationship": relationship,
                    "direction": direction,
                    "related_count": len(rows),
                    "related_ids": ids,
                    "related_types": [row.get("type") for row in rows],
                    "related_titles": [row.get("title") for row in rows],
                }, rel.get("error"))
                for row in rows:
                    observed_types[str(row.get("type") or "<missing>")] += 1
                    add_candidate(
                        candidates,
                        row,
                        f"{relationship}:{service_id}:{direction}",
                        trusted_relation=(relationship == "Service2Data"),
                    )

    # Metadata readback fills missing owner/type/title and applies relation trust where appropriate.
    for item_id in sorted(discovered_ids):
        meta = fetch_meta(item_id)
        if not meta:
            continue
        observed_types[str(meta.get("type") or "<missing>")] += 1
        add_candidate(
            candidates,
            meta,
            "metadata_readback",
            trusted_relation=(item_id.lower() in trusted_ids),
        )

    # Independent broad official catalogue search; no fragile type-qualified query syntax.
    for query in SEARCH_QUERIES:
        result = core.w.safe_json(
            "wave134_repair_catalog_search",
            f"{PORTAL}/search",
            {"f": "json", "num": 100, "q": query},
        )
        rows = result["data"].get("results", []) if result["ok"] else []
        for row in rows:
            observed_types[str(row.get("type") or "<missing>")] += 1
            add_candidate(candidates, row, f"catalog:{query}")
        core.add("wave134_repair_catalog_summary", query, result["ok"], {
            "returned": len(rows),
            "official": sum(official(row) for row in rows),
            "official_relevant": sum(official(row) and relevant(row) for row in rows),
            "types": dict(collections.Counter(str(row.get("type") or "<missing>") for row in rows)),
            "candidate_count_after_query": len(candidates),
        }, result.get("error"))

    core.add("wave134_repair_type_diagnostics", "observed_arcgis_item_types", True, {
        "types": dict(observed_types),
        "discovered_ids": len(discovered_ids),
        "trusted_ids": sorted(trusted_ids),
    })

    type_rank = {
        "shapefile": 0,
        "file geodatabase": 1,
        "service definition": 2,
        "geojson": 3,
        "csv": 4,
        "microsoft excel": 5,
        "kml": 6,
        "map package": 7,
    }
    ranked = sorted(
        candidates.values(),
        key=lambda row: (
            type_rank.get(str(row.get("item_type") or "").lower(), 20),
            0 if "2011" in str(row.get("title") or "") else 1,
            0 if "2021" in str(row.get("title") or "") else 1,
            0 if "full clipped" in str(row.get("title") or "").lower() else 1,
            0 if "generalised" in str(row.get("title") or "").lower() else 1,
            int(row.get("size") or 0) if int(row.get("size") or 0) > 0 else 2**63,
            str(row.get("item_id") or ""),
        ),
    )[: core.MAX_PACKAGES]
    core.add("wave134_repair_candidate_gate", "official_binary_package_candidates", bool(ranked), {
        "candidate_count": len(ranked),
        "candidate_ids": [row.get("item_id") for row in ranked],
        "candidate_titles": [row.get("title") for row in ranked],
        "candidate_types": [row.get("item_type") for row in ranked],
        "candidate_sizes": [row.get("size") for row in ranked],
        "candidate_relations": [row.get("discovery_relation") for row in ranked],
    }, None if ranked else "NO_OFFICIAL_BINARY_PACKAGE_CANDIDATES")
    if not ranked:
        raise RuntimeError("Wave134 repair v2 found no official ONS file-backed LSOA candidates")
    return ranked


core.package_candidates = discover

if __name__ == "__main__":
    core.main()
