from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-wikidata-nearby-v1-20260801"
ENDPOINT = "https://query.wikidata.org/sparql"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/wikidata_nearby_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/wikidata_nearby_latest.json",
)
EXPECTED = ("parcel_61523", "parcel_61524", "parcel_61525")
RADIUS_KM = 0.1
LIMIT = 25


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_points(root: Path) -> list[dict]:
    rows = json.loads((root / PROBE).read_text(encoding="utf-8-sig"))["canonical_points"]
    if len(rows) != 3:
        raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    points = []
    for row in rows:
        if row.get("parcel_id") not in EXPECTED or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError("CANONICAL_POINT_INVALID")
        points.append({"parcel_id": row["parcel_id"], "latitude": float(row["latitude"]), "longitude": float(row["longitude"])})
    points.sort(key=lambda row: EXPECTED.index(row["parcel_id"]))
    if tuple(row["parcel_id"] for row in points) != EXPECTED:
        raise ValueError("CANONICAL_POINT_IDS_MISMATCH")
    return points


def query_for(point: dict) -> str:
    return f'''SELECT ?item ?itemLabel ?location ?instanceOf ?instanceOfLabel WHERE {{
  SERVICE wikibase:around {{
    ?item wdt:P625 ?location .
    bd:serviceParam wikibase:center "Point({point["longitude"]} {point["latitude"]})"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "{RADIUS_KM}" .
  }}
  OPTIONAL {{ ?item wdt:P31 ?instanceOf . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {LIMIT}'''


def fetch(query: str, timeout: int) -> tuple[bytes, int]:
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=data,
        method="POST",
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0 (https://github.com/cagdascagdas100/chat_gpt_clone_1)",
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), int(response.status)


def qid(uri: object) -> str | None:
    if not isinstance(uri, str) or "/entity/Q" not in uri:
        return None
    value = uri.rsplit("/", 1)[-1]
    return value if value[1:].isdigit() else None


def candidates(point: dict, payload: dict) -> list[dict]:
    result, seen = [], set()
    for row in payload.get("results", {}).get("bindings", [])[:LIMIT]:
        item_uri = row.get("item", {}).get("value")
        item_qid = qid(item_uri)
        location = row.get("location", {}).get("value")
        instance_uri = row.get("instanceOf", {}).get("value")
        instance_qid = qid(instance_uri)
        key = (item_qid, instance_qid)
        if item_qid is None or not isinstance(location, str) or not location.startswith("Point(") or key in seen:
            continue
        seen.add(key)
        result.append({
            "parcel_id": point["parcel_id"],
            "canonical_point": {"latitude": point["latitude"], "longitude": point["longitude"]},
            "wikidata_item": item_qid,
            "item_uri": item_uri,
            "item_label": row.get("itemLabel", {}).get("value"),
            "location_wkt": location,
            "instance_of": instance_qid,
            "instance_of_uri": instance_uri,
            "instance_of_label": row.get("instanceOfLabel", {}).get("value"),
            "candidate_only": True,
            "exact_uprn_bound": False,
            "property_type_bound": False,
            "parcel_binding_claimed": False,
        })
    return result


def run(root: Path, timeout: int) -> dict:
    evidence, found = [], []
    for index, point in enumerate(load_points(root)):
        query = query_for(point)
        row = {
            "parcel_id": point["parcel_id"],
            "source_url": ENDPOINT,
            "accessed_at": now(),
            "query_sha256": digest(query.encode()),
            "query_scope": {"radius_km": RADIUS_KM, "limit": LIMIT, "fields": ["item", "itemLabel", "location", "instanceOf", "instanceOfLabel"]},
            "http_status": None,
            "content_sha256": None,
            "sha256_basis": "raw_response_bytes",
            "relevant_record_ids_or_excerpt": None,
            "proven_fields": ["Wikidata QID", "coordinate WKT", "instance-of QID", "labels"],
            "documentation_url": "https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/en",
            "license_or_terms_url": "https://www.wikidata.org/wiki/Wikidata:Licensing",
            "user_agent_policy_url": "https://wikitech.wikimedia.org/wiki/Wikidata_Query_Service/Technical_interactions",
        }
        try:
            body, status = fetch(query, timeout)
            row["http_status"] = status
            row["content_sha256"] = digest(body)
            batch = candidates(point, json.loads(body.decode()))
            found.extend(batch)
            row["relevant_record_ids_or_excerpt"] = [item["wikidata_item"] for item in batch]
        except Exception as exc:
            error = f"WIKIDATA_SPARQL_ERROR:{type(exc).__name__}"
            row["content_sha256"] = digest(error.encode())
            row["sha256_basis"] = "bounded_error_evidence_string"
            row["relevant_record_ids_or_excerpt"] = error
        evidence.append(row)
        if index < 2:
            time.sleep(1.2)

    completed = len(evidence)
    progress = round(100 * completed / 3, 4)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "PUBLISHED_CANDIDATE_ONLY" if found else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": progress,
        "percent_increase": progress,
        "produced_candidate_rows": len(found),
        "candidates": found,
        "source_evidence": evidence,
        "blocker": None if found else {"code": "WIKIDATA_SPARQL_NO_USABLE_RESPONSE", "state": "NO_DATA_CONTINUE", "candidate_research_blocked": False, "manual_action_required": False, "retry_unchanged_route": False},
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_WIKIDATA",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate() -> dict:
    assert len(EXPECTED) == 3 and RADIUS_KM == 0.1 and LIMIT == 25
    assert urllib.parse.urlparse(ENDPOINT).hostname == "query.wikidata.org"
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in (PROBE, *OUTPUTS))
    return {"state": "VALIDATED", "target_count": 3, "expected_ids": list(EXPECTED), "resource_class": "network_fetch", "read_path": PROBE, "write_paths": list(OUTPUTS), "radius_km": RADIUS_KM, "limit": LIMIT, "minimum_request_spacing_seconds": 1.2}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate()))
        return 0
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    result = run(root, max(1, min(args.timeout, 60)))
    for output in OUTPUTS:
        write_json(root / output, result)
    print(json.dumps({"state": result["state"], "completed_count": result["completed_count"], "target_count": 3, "produced_candidate_rows": result["produced_candidate_rows"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
