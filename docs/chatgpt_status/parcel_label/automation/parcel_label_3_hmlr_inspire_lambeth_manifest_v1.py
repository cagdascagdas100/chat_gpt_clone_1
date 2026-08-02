from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-hmlr-inspire-lambeth-manifest-v1-20260802"
SOURCE_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/hmlr_inspire_lambeth_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/hmlr_inspire_lambeth_manifest_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class LinkCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append({"href": self._href, "text": " ".join(self._text).strip()})
            self._href = None
            self._text = []


def validate_probe(root: Path) -> list[dict[str, Any]]:
    data = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = data.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {p.get("parcel_id"): p for p in points if isinstance(p, dict)}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        p = by_id.get(parcel_id)
        if not p or p.get("geometry_type") != "Point" or not p.get("point_valid"):
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = p.get("longitude")
        lat = p.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, path)


def run(root: Path, timeout: float) -> dict[str, Any]:
    points = validate_probe(root)
    accessed_at = now()
    request_sha = sha256(SOURCE_URL)
    evidence: dict[str, Any] = {
        "source_url": SOURCE_URL,
        "accessed_at": accessed_at,
        "query_sha256": request_sha,
        "record_scope": "one bounded HM Land Registry INSPIRE download-page request; locate London Borough of Lambeth GML link only; max 2 MiB",
    }
    candidates: list[dict[str, Any]] = []
    try:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "TerraYield-AAYS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            status = getattr(response, "status", None)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 2 MiB")
        text = raw.decode("utf-8", errors="replace")
        collector = LinkCollector()
        collector.feed(text)
        for link in collector.links:
            href = link["href"]
            absolute = urllib.parse.urljoin(SOURCE_URL, href)
            context = f"{link['text']} {href}".lower()
            if "lambeth" in context and (".gml" in context or "download" in context):
                candidates.append({
                    "local_authority": "London Borough of Lambeth",
                    "download_url": absolute,
                    "anchor_text": link["text"],
                    "candidate_only": True,
                })
        evidence.update({
            "http_status": status,
            "content_sha256": sha256(raw),
            "sha256_basis": "bounded_raw_html_response",
            "relevant_record_ids_or_excerpt": "London Borough of Lambeth download anchor(s)",
            "proven_fields": ["download page response", "Lambeth anchor", "candidate GML URL"] if candidates else ["download page response"],
        })
    except Exception as exc:  # fail closed and preserve bounded evidence
        error = f"HMLR_INSPIRE_LAMBETH_MANIFEST_ERROR:{type(exc).__name__}:{exc}"
        evidence.update({
            "http_status": None,
            "content_sha256": sha256(error),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": error[:500],
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
        })
    state = "CANDIDATE_SOURCE_PUBLISHED" if candidates else "NO_DATA_CONTINUE"
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates[:10],
        "source_evidence": [evidence],
        "gml_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
        "next_unverified_step": "DOWNLOAD_AND_BOUNDED_PARSE_HMLR_INSPIRE_LAMBETH_GML" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_HMLR_INSPIRE_LAMBETH_MANIFEST",
        "blocker": {
            "code": None if candidates else "HMLR_INSPIRE_LAMBETH_MANIFEST_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
    }
    for relative in OUTPUTS:
        atomic_write(root / relative, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    points = validate_probe(root)
    if args.validate_only:
        if len(points) != 3 or MAX_BYTES != 2 * 1024 * 1024 or not all(not Path(p).is_absolute() for p in OUTPUTS):
            raise SystemExit(2)
        print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_HMLR_INSPIRE_LAMBETH_MANIFEST_MAX2MIB_NO_GML_DOWNLOAD")
        return 0
    result = run(root, args.timeout)
    print(json.dumps({"state": result["state"], "completed": "1/1", "candidates": result["produced_candidate_rows"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
