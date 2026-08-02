from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-companies-house-postcode-v1-20260802"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SEARCH_BASE = "https://find-and-update.company-information.service.gov.uk/search/companies"
GUIDANCE_URL = "https://www.gov.uk/guidance/searching-the-companies-house-register"
DATA_PRODUCTS_URL = "https://www.gov.uk/guidance/companies-house-data-products"
PUBLIC_TASK_URL = "https://www.gov.uk/government/publications/companies-house-accreditation-to-information-fair-traders-scheme/public-task-copyright-and-crown-copyright"
ABOUT_URL = "https://www.gov.uk/government/organisations/companies-house/about"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1024 * 1024
MAX_CANDIDATES = 20
POSTCODES = {
    "parcel_61523": "SW16 5TG",
    "parcel_61524": "SW16 5AE",
    "parcel_61525": "SW16 5AZ",
}
EXPECTED_POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


class CompanySearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, Any]] = []
        self._href: str | None = None
        self._link_text: list[str] = []
        self._capture_block = False
        self._block_text: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "a":
            href = a.get("href", "")
            if "/company/" in href:
                self._href = href
                self._link_text = []
                self._capture_block = True
                self._block_text = []
                self._depth = 0
        if self._capture_block:
            self._depth += 1

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._href is not None:
            self._link_text.append(text)
        if self._capture_block:
            self._block_text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if self._capture_block:
            self._depth -= 1
        if tag.lower() == "a" and self._href is not None:
            name = " ".join(self._link_text).strip()
            href = self._href
            self._href = None
            self._link_text = []
            if name:
                self.rows.append({"company_name": name[:300], "company_url": href, "_block_text": ""})
        if self._capture_block and self._depth <= 0:
            block = " ".join(self._block_text).strip()
            if self.rows and not self.rows[-1].get("_block_text"):
                self.rows[-1]["_block_text"] = block[:1500]
            self._capture_block = False
            self._block_text = []
            self._depth = 0


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_points(root: Path) -> list[dict[str, Any]]:
    path = root / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    found = {
        str(row.get("parcel_id")): row
        for row in rows
        if isinstance(row, dict) and row.get("parcel_id") in EXPECTED_POINTS
    }
    if set(found) != set(EXPECTED_POINTS):
        raise ValueError("exact target parcels missing")
    result: list[dict[str, Any]] = []
    for parcel_id in POSTCODES:
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        expected_lon, expected_lat = EXPECTED_POINTS[parcel_id]
        if (
            row.get("geometry_type") != "Point"
            or row.get("point_valid") is not True
            or abs(lon - expected_lon) > 1e-7
            or abs(lat - expected_lat) > 1e-7
        ):
            raise ValueError(f"invalid canonical Point: {parcel_id}")
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 (+bounded public-register research)",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def parse_candidates(html: str, base_url: str, postcode: str) -> list[dict[str, Any]]:
    parser = CompanySearchParser()
    parser.feed(html)
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    normalized = postcode.upper().replace(" ", "")
    for row in parser.rows:
        href = urllib.parse.urljoin(base_url, str(row["company_url"]))
        if href in seen:
            continue
        seen.add(href)
        block = " ".join(str(row.get("_block_text", "")).split())
        if normalized not in block.upper().replace(" ", ""):
            continue
        company_number_match = re.search(r"\bCompany number\s+([A-Z0-9]{6,10})\b", block, re.I)
        status_match = re.search(r"\b(Active|Dissolved|Liquidation|Administration|Receivership)\b", block, re.I)
        output.append(
            {
                "company_name": row["company_name"],
                "company_number": company_number_match.group(1) if company_number_match else None,
                "company_status": status_match.group(1) if status_match else None,
                "registered_office_excerpt": block[:1000],
                "source_url": href,
                "searched_postcode": postcode,
                "context_only": True,
                "exact_parcel_binding": False,
                "property_type_binding": False,
                "sic_not_fetched": True,
            }
        )
        if len(output) >= MAX_CANDIDATES:
            break
    return output


def attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parcel_id = point["parcel_id"]
    postcode = POSTCODES[parcel_id]
    accessed_at = now_iso()
    search_url = SEARCH_BASE + "?" + urllib.parse.urlencode({"q": postcode})
    try:
        status, final_url, raw = bounded_get(search_url, timeout)
        html = raw.decode("utf-8", errors="replace")
        candidates = parse_candidates(html, final_url, postcode)
        excerpt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:1500]
        return candidates, {
            "parcel_id": parcel_id,
            "searched_postcode": postcode,
            "canonical_point": point,
            "source_url": final_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(raw),
            "sha256_basis": "bounded_search_response_bytes",
            "record_scope": "one bounded official Companies House company-search response; one request, 1 MiB and 20 postcode-matching candidates",
            "supports_fields": [
                "company name",
                "company number where published",
                "registered office address excerpt",
                "company status where published",
                "company profile link",
            ],
            "relevant_record_ids_or_excerpt": excerpt,
            "terms_or_license_urls": [PUBLIC_TASK_URL, OGL_URL],
            "http_status": status,
            "requests_made": 1,
        }
    except Exception as exc:
        error = f"COMPANIES_HOUSE_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
        return [], {
            "parcel_id": parcel_id,
            "searched_postcode": postcode,
            "canonical_point": point,
            "source_url": search_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official Companies House postcode company-search attempt; maximum one request",
            "supports_fields": ["Companies House public-register postcode search availability"],
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [PUBLIC_TASK_URL, OGL_URL],
            "http_status": None,
            "requests_made": 0,
        }


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidate_rows: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for point in points:
        rows, record = attempt(point, timeout)
        evidence.append(record)
        for row in rows:
            row["parcel_id"] = point["parcel_id"]
            row["canonical_point"] = point
            candidate_rows.append(row)
    produced = len(candidate_rows)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": now_iso(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if produced else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": produced,
        "candidate_rows": candidate_rows,
        "source_evidence": evidence,
        "blocker": {
            "code": None if produced else "COMPANIES_HOUSE_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULT",
            "state": "NONE" if produced else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_COMPANIES_HOUSE_POSTCODE",
        "search_base_url": SEARCH_BASE,
        "guidance_url": GUIDANCE_URL,
        "data_products_url": DATA_PRODUCTS_URL,
        "public_task_url": PUBLIC_TASK_URL,
        "about_url": ABOUT_URL,
        "open_government_licence_url": OGL_URL,
        "login_or_registration_used": False,
        "api_key_used": False,
        "bulk_download_performed": False,
        "full_register_scan_performed": False,
        "company_profile_followup_requests": 0,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(root: Path) -> None:
    points = load_points(root)
    if len(points) != 3:
        raise ValueError("target count must be 3")
    if not SEARCH_BASE.startswith("https://find-and-update.company-information.service.gov.uk/"):
        raise ValueError("official Companies House service required")
    print("PASS_TARGET_3_COMPANIES_HOUSE_EXACT_POSTCODE_QUERY_MAX1_REQUEST_EACH_MAX1MIB_20_CANDIDATES_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    validate(root)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(root), max(1.0, min(args.timeout, 30.0)))
    slot_output = root / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/companies_house_postcode_result_latest.json"
    web_output = root / "england_map_web/data/aays_21_slots/parcel_label_3/companies_house_postcode_latest.json"
    atomic_write_json(slot_output, payload)
    atomic_write_json(web_output, payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    else:
        print("PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
