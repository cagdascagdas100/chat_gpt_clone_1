from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

TASK_ID = "parcel-label-3-national-data-library-lbsm2-lambeth-link-v1-20260802"
SOURCE_URL = "https://www.data.gov.uk/dataset/e03aa07a-ee8a-4b1a-a04c-cc6e23133340/london-building-stock-model-2-lbsm-21"
OFFICIAL_DATASET_URL = "https://data.london.gov.uk/dataset/london-building-stock-model-2-lbsm-2-2k55d"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/national_data_library_lbsm2_lambeth_link_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/national_data_library_lbsm2_lambeth_link_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            text = " ".join(" ".join(self._text).split())
            self.links.append({"href": self._href, "text": text})
            self._href = None
            self._text = []


def load_points(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    points = data.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    selected = []
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point: {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def validate_only() -> None:
    if Path(script_rel := __file__).is_absolute():
        pass
    for value in (PROBE, *OUTPUTS):
        if Path(value).is_absolute() or ".." in Path(value).parts:
            raise ValueError(f"path must be tracked relative: {value}")
    if not PROBE.startswith("england_map_web/data/distance_property_types/"):
        raise ValueError("unexpected probe root")
    if not OUTPUTS[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("unexpected shared output root")
    if not OUTPUTS[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("unexpected website output root")
    parsed = urlparse(SOURCE_URL)
    if parsed.scheme != "https" or parsed.netloc != "www.data.gov.uk":
        raise ValueError("unexpected source URL")
    if MAX_BYTES != 2 * 1024 * 1024:
        raise ValueError("unexpected response bound")
    if len(IDS) != 3 or len(set(IDS)) != 3:
        raise ValueError("unexpected canonical target count")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_NATIONAL_DATA_LIBRARY_LBSM2_LAMBETH_LINK_MAX2MIB_NO_CSV_DOWNLOAD")


def run(timeout: int) -> dict[str, Any]:
    points = load_points(Path(PROBE))
    accessed_at = now()
    query_sha = sha256(SOURCE_URL)
    candidates: list[dict[str, str]] = []
    evidence: dict[str, Any]
    try:
        request = urllib.request.Request(
            SOURCE_URL,
            headers={
                "User-Agent": "TerraYield-AAYS/1.0 (+bounded metadata verification)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeded 2 MiB bound")
            html = raw.decode("utf-8", errors="replace")
            parser = LinkCollector()
            parser.feed(html)
            for link in parser.links:
                combined = f"{link['text']} {link['href']}".lower()
                if "lambeth" not in combined:
                    continue
                candidates.append(
                    {
                        "label": link["text"],
                        "url": urljoin(SOURCE_URL, link["href"]),
                    }
                )
            evidence = {
                "source_url": SOURCE_URL,
                "accessed_at": accessed_at,
                "http_status": getattr(response, "status", None),
                "query_sha256": query_sha,
                "content_sha256": sha256(raw),
                "sha256_basis": "bounded_raw_html",
                "record_scope": "one bounded official National Data Library LBSM2 dataset-page request; max 2 MiB; no CSV download",
                "relevant_record_ids_or_excerpt": [c["label"] for c in candidates[:10]],
                "proven_fields": ["request URL", "access time", "HTTP status", "raw HTML SHA-256", "Lambeth-labelled link candidates"],
                "candidate_count": len(candidates),
            }
    except Exception as exc:
        error_text = f"NATIONAL_DATA_LIBRARY_LBSM2_LAMBETH_LINK_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "http_status": None,
            "query_sha256": query_sha,
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official National Data Library LBSM2 dataset-page request; max 2 MiB; no CSV download",
            "relevant_record_ids_or_excerpt": error_text,
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
            "candidate_count": 0,
        }

    state = "SOURCE_METADATA_CANDIDATES" if candidates else "NO_DATA_CONTINUE"
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
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": None if candidates else "NATIONAL_DATA_LIBRARY_LBSM2_LAMBETH_LINK_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VERIFY_BOUNDED_LAMBETH_RESOURCE_LINK_METADATA"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_NATIONAL_DATA_LIBRARY_LBSM2_LAMBETH_LINK"
        ),
        "csv_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(Path(output), payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    run(args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
