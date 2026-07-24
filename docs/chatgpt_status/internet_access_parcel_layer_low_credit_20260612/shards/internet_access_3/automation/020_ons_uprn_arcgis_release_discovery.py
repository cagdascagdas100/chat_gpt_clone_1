#!/usr/bin/env python3
"""Discover current official NSUL and ONSUD ArcGIS data items.

This step resolves public release metadata only. It does not download the large data
packages, create parcel relations or raise confidence.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/008_ons_uprn_arcgis_release_discovery_registry_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json")
    p.add_argument("--timeout", type=int, default=90)
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "docs").exists() and (item / "england_map_web").exists():
            return item
    raise FileNotFoundError("repository root not found")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def request_json(url: str, params: dict[str, str], timeout: int, post: bool = False) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(params)
    if post:
        request = urllib.request.Request(url, data=encoded.encode(), headers={"User-Agent": "TerraYield-AAYS-internet-access-3/1.0"})
    else:
        request = urllib.request.Request(url + ("&" if "?" in url else "?") + encoded, headers={"User-Agent": "TerraYield-AAYS-internet-access-3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("ArcGIS response is not an object")
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return payload


def normalized(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def item_score(item: dict[str, Any], product: dict[str, Any]) -> tuple[int, list[str]]:
    title = normalized(item.get("title"))
    owner = normalized(item.get("owner"))
    tags = normalized(" ".join(str(value) for value in (item.get("tags") or [])))
    item_type = normalized(item.get("type"))
    type_keywords = normalized(" ".join(str(value) for value in (item.get("typeKeywords") or [])))
    reasons: list[str] = []
    required = [normalized(token) for token in product["required_title_tokens"]]
    excluded = [normalized(token) for token in product["excluded_title_tokens"]]
    if any(token and token in title for token in excluded):
        return -10000, ["EXCLUDED_TITLE_TOKEN"]
    missing = [token for token in required if token and token not in title]
    if missing:
        return -5000, ["MISSING_REQUIRED_TITLE_TOKENS:" + ",".join(missing)]
    score = 100
    reasons.append("REQUIRED_TITLE_TOKENS_PRESENT")
    canonical = normalized(product["canonical_name"])
    if title.startswith(canonical):
        score += 30
        reasons.append("CANONICAL_TITLE_PREFIX")
    if "ons" in owner or "office for national statistics" in tags or "ons geography" in tags:
        score += 25
        reasons.append("ONS_AUTHORITY_SIGNAL")
    downloadable_tokens = {"csv", "zip", "file", "document", "data package", "code attachment"}
    if any(token in item_type or token in type_keywords for token in downloadable_tokens):
        score += 20
        reasons.append("DOWNLOADABLE_DATA_SIGNAL")
    size = int(item.get("size") or 0)
    minimum = int(product.get("minimum_data_item_size_bytes") or 0)
    if size >= minimum:
        score += 20
        reasons.append("MINIMUM_DATA_SIZE_MET")
    else:
        score -= 40
        reasons.append("BELOW_MINIMUM_DATA_SIZE")
    if "user guide" in tags or "user guide" in type_keywords:
        score -= 200
        reasons.append("USER_GUIDE_TAG_PENALTY")
    if "metadata" in tags or "metadata" in type_keywords:
        score -= 100
        reasons.append("METADATA_TAG_PENALTY")
    return score, reasons


def discover(search_endpoint: str, item_template: str, product: dict[str, Any], timeout: int) -> dict[str, Any]:
    by_id: dict[str, dict[str, Any]] = {}
    queries: list[dict[str, Any]] = []
    for phrase in product["search_phrases"]:
        payload = request_json(search_endpoint, {"f": "json", "num": "100", "sortField": "modified", "sortOrder": "desc", "q": phrase}, timeout, post=True)
        results = [item for item in payload.get("results", []) if isinstance(item, dict)]
        queries.append({"phrase": phrase, "result_count": len(results)})
        for item in results:
            item_id = str(item.get("id") or "")
            if item_id:
                by_id[item_id] = item
    ranked: list[dict[str, Any]] = []
    for item in by_id.values():
        score, reasons = item_score(item, product)
        ranked.append({"item": item, "score": score, "reasons": reasons})
    ranked.sort(key=lambda entry: (-int(entry["score"]), -int((entry["item"] or {}).get("modified") or 0), str((entry["item"] or {}).get("id") or "")))
    eligible = [entry for entry in ranked if int(entry["score"]) >= 100]
    ambiguity = len(eligible) > 1 and int(eligible[0]["score"]) == int(eligible[1]["score"])
    winner = None if not eligible or ambiguity else eligible[0]
    detail = None
    if winner:
        item_id = str(winner["item"]["id"])
        detail = request_json(item_template.format(item_id=item_id), {"f": "json"}, timeout)
    return {
        "product_id": product["product_id"],
        "canonical_name": product["canonical_name"],
        "queries": queries,
        "unique_items_seen": len(by_id),
        "eligible_count": len(eligible),
        "ambiguous_top_score": ambiguity,
        "selected": {
            "id": detail.get("id"),
            "title": detail.get("title"),
            "owner": detail.get("owner"),
            "type": detail.get("type"),
            "size": detail.get("size"),
            "created": detail.get("created"),
            "modified": detail.get("modified"),
            "tags": detail.get("tags"),
            "url": detail.get("url"),
            "score": winner["score"],
            "score_reasons": winner["reasons"],
        } if detail and winner else None,
        "top_candidates": [
            {
                "id": entry["item"].get("id"),
                "title": entry["item"].get("title"),
                "owner": entry["item"].get("owner"),
                "type": entry["item"].get("type"),
                "size": entry["item"].get("size"),
                "score": entry["score"],
                "score_reasons": entry["reasons"],
            }
            for entry in ranked[:10]
        ],
    }


def update_feed(output_root: Path, summary: dict[str, Any]) -> None:
    path = output_root / "operation_feed_revision8_runtime_latest.json"
    existing = load_json(path) if path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(existing.get("operations") or [])
    sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    for result in summary["products"]:
        operations.append({
            "sequence": sequence,
            "status": "PASS" if result["selected"] and not result["ambiguous_top_score"] else "BLOCKED",
            "operation": "ONS_UPRN_ARCGIS_RELEASE_DISCOVERY",
            "product_id": result["product_id"],
            "detail": f"selected={None if not result['selected'] else result['selected']['title']}; eligible={result['eligible_count']}; ambiguous={result['ambiguous_top_score']}; confidence_not_raised",
        })
        sequence += 1
    existing.update({"updated_at": summary["updated_at"], "display_mode": "line_by_line", "final_ready": False, "operations": operations, "safety": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False}})
    atomic_json(path, existing)


def main() -> int:
    args = parse_args()
    repo = root(args.repo_root)
    registry = load_json(repo / args.registry)
    portal = registry["portal"]
    products = [discover(portal["search_endpoint"], portal["item_endpoint_template"], product, args.timeout) for product in registry["release_contract"]["products"]]
    blockers: list[str] = []
    for result in products:
        if not result["selected"]:
            blockers.append(f"{result['product_id'].upper()}_DATA_ITEM_NOT_UNIQUELY_RESOLVED")
        if result["ambiguous_top_score"]:
            blockers.append(f"{result['product_id'].upper()}_TOP_SCORE_AMBIGUOUS")
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "task_id": "aays1-internet-access-3-ons-uprn-release-discovery-20260722",
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if not blockers else "blocked",
        "updated_at": now,
        "release_label": registry["release_contract"]["release_label"],
        "products": products,
        "validation": {"passed": not blockers, "blockers": blockers},
        "download_bytes_hydrated": 0,
        "parcel_relations_promoted": 0,
        "confidence_uplifts": 0,
        "actual_business_data_rows_written": 0,
        "output_semantics": "OFFICIAL_RELEASE_METADATA_DISCOVERY_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "HYDRATE_SELECTED_NSUL_AND_ONSUD_RELEASE_BYTES_THEN_SCHEMA_AND_HASH_AUDIT",
    }
    output_root = repo / args.output_root
    atomic_json(output_root / "ons_uprn_arcgis_release_discovery_latest.json", summary)
    atomic_json(repo / args.runner_output, summary)
    update_feed(output_root, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not blockers else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
