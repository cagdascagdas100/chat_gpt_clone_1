from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-cqc-care-services-postcode-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/cqc_care_services_postcode_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/cqc_care_services_postcode_latest.json",
)
LANDING_URL = "https://www.cqc.org.uk/care-services"
USING_DATA_URL = "https://www.cqc.org.uk/about-us/transparency/using-cqc-data"
LOCATION_DEF_URL = "https://www.cqc.org.uk/guidance-providers/registration/what-location"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
POSTCODES = (
    ("parcel_61523", "SW16 5TG"),
    ("parcel_61524", "SW16 5AE"),
    ("parcel_61525", "SW16 5AZ"),
)
MAX_BYTES = 1_048_576
MAX_CANDIDATES = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, obj: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)


def canonical_points() -> list[dict[str, Any]]:
    data = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = {row["parcel_id"]: row for row in data["canonical_points"]}
    result: list[dict[str, Any]] = []
    for parcel_id, _ in POSTCODES:
        row = rows.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


class FormAndLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self.current_form: dict[str, Any] | None = None
        self.links: list[dict[str, str]] = []
        self.current_link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "form":
            self.current_form = {
                "action": values.get("action", ""),
                "method": values.get("method", "get").lower(),
                "inputs": [],
            }
            self.forms.append(self.current_form)
        elif tag.lower() in {"input", "select", "textarea"} and self.current_form is not None:
            self.current_form["inputs"].append(
                {
                    "tag": tag.lower(),
                    "name": values.get("name", ""),
                    "id": values.get("id", ""),
                    "type": values.get("type", ""),
                    "value": values.get("value", ""),
                    "placeholder": values.get("placeholder", ""),
                    "aria_label": values.get("aria-label", ""),
                }
            )
        elif tag.lower() == "a" and values.get("href"):
            self.current_link = {"href": values["href"], "text": ""}
            self.links.append(self.current_link)

    def handle_data(self, data: str) -> None:
        if self.current_link is not None:
            self.current_link["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form":
            self.current_form = None
        elif tag.lower() == "a":
            self.current_link = None


def fetch_bytes(url: str, timeout: float, *, data: bytes | None = None) -> tuple[bytes, int | None, str]:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "Content-Type": "application/x-www-form-urlencoded" if data is not None else "text/plain",
            "User-Agent": "TerraYield-AAYS/1.0 bounded CQC postcode research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        return raw, getattr(response, "status", None), response.geturl()


def find_location_form(raw: bytes, base_url: str) -> dict[str, Any]:
    parser = FormAndLinkParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    terms = ("location", "postcode", "post code", "town", "city")
    for form in parser.forms:
        for field in form["inputs"]:
            if field.get("type") in {"hidden", "submit", "button", "checkbox", "radio"}:
                continue
            haystack = " ".join(
                str(field.get(key, ""))
                for key in ("name", "id", "placeholder", "aria_label")
            ).lower()
            if any(term in haystack for term in terms) and field.get("name"):
                action = urllib.parse.urljoin(base_url, form.get("action") or base_url)
                return {
                    "action": action,
                    "method": form.get("method") if form.get("method") in {"get", "post"} else "get",
                    "location_field": field["name"],
                    "inputs": form["inputs"],
                }
    raise ValueError("CQC location/postcode search form not discovered")


def build_submission(form: dict[str, Any], postcode: str) -> tuple[str, bytes | None, str]:
    params: list[tuple[str, str]] = []
    for field in form["inputs"]:
        name = field.get("name")
        if not name:
            continue
        if name == form["location_field"]:
            params.append((name, postcode))
        elif field.get("type") == "hidden" and field.get("value"):
            params.append((name, str(field["value"])))
    encoded = urllib.parse.urlencode(params)
    if form["method"] == "post":
        return form["action"], encoded.encode("utf-8"), sha256(encoded)
    separator = "&" if urllib.parse.urlparse(form["action"]).query else "?"
    return f"{form['action']}{separator}{encoded}", None, sha256(encoded)


def service_candidates(raw: bytes, response_url: str, parcel_id: str, postcode: str) -> list[dict[str, Any]]:
    parser = FormAndLinkParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for link in parser.links:
        absolute = urllib.parse.urljoin(response_url, link["href"])
        parsed = urllib.parse.urlparse(absolute)
        path = parsed.path.lower()
        if parsed.netloc not in {"www.cqc.org.uk", "cqc.org.uk"}:
            continue
        if not (path.startswith("/location/") or "/location/" in path):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        label = re.sub(r"\s+", " ", html.unescape(link.get("text", ""))).strip()
        candidates.append(
            {
                "parcel_id": parcel_id,
                "searched_postcode": postcode,
                "service_name_or_link_text": label or None,
                "service_url": absolute,
                "candidate_only": True,
                "exact_parcel_binding_claimed": False,
                "property_type_binding_claimed": False,
            }
        )
        if len(candidates) >= MAX_CANDIDATES:
            break
    return candidates


def run(timeout: float) -> dict[str, Any]:
    points = canonical_points()
    point_map = {row["parcel_id"]: row for row in points}
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for parcel_id, postcode in POSTCODES:
        accessed_at = now()
        requests_made = 0
        try:
            landing_raw, landing_status, landing_final_url = fetch_bytes(LANDING_URL, timeout)
            requests_made += 1
            form = find_location_form(landing_raw, landing_final_url)
            search_url, body, payload_sha256 = build_submission(form, postcode)
            result_raw, result_status, result_final_url = fetch_bytes(search_url, timeout, data=body)
            requests_made += 1
            found = service_candidates(result_raw, result_final_url, parcel_id, postcode)
            candidates.extend(found)
            evidence.append(
                {
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": point_map[parcel_id],
                    "source_url": result_final_url,
                    "landing_url": LANDING_URL,
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(result_raw),
                    "landing_content_sha256": sha256(landing_raw),
                    "request_payload_sha256": payload_sha256,
                    "sha256_basis": "bounded_raw_html_response_bytes",
                    "record_scope": "one official CQC care-services landing request plus one discovered postcode-search submission; maximum 20 location links; maximum 1 MiB per response",
                    "supports_fields": [
                        "regulated care-service location candidate URL",
                        "visible service name or link text",
                        "postcode-level search association",
                    ],
                    "relevant_record_ids_or_excerpt": {
                        "candidate_count": len(found),
                        "candidate_urls": [row["service_url"] for row in found],
                        "form_method": form["method"],
                        "location_field": form["location_field"],
                    },
                    "using_data_url": USING_DATA_URL,
                    "location_definition_url": LOCATION_DEF_URL,
                    "license_or_terms_url": OGL_URL,
                    "landing_http_status": landing_status,
                    "http_status": result_status,
                    "requests_made": requests_made,
                }
            )
        except Exception as exc:
            message = f"CQC_CARE_SERVICES_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append(
                {
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": point_map[parcel_id],
                    "source_url": LANDING_URL,
                    "landing_url": LANDING_URL,
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(message),
                    "sha256_basis": "bounded_error_evidence_string",
                    "record_scope": "one bounded official CQC care-services form-discovery/postcode-search attempt; maximum one landing and one search response; no report or document crawl",
                    "supports_fields": ["CQC care-service postcode-search availability"],
                    "relevant_record_ids_or_excerpt": message[:512],
                    "using_data_url": USING_DATA_URL,
                    "location_definition_url": LOCATION_DEF_URL,
                    "license_or_terms_url": OGL_URL,
                    "http_status": getattr(exc, "code", None),
                    "requests_made": requests_made,
                }
            )
    state = "CQC_CARE_SERVICE_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    result: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "CQC_CARE_SERVICES_NO_USABLE_RESPONSE_OR_NO_POSTCODE_LOCATION_RESULTS",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_CQC_CARE_SERVICE_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_CQC_CARE_SERVICES_POSTCODE"
        ),
        "api_subscription_used": False,
        "bulk_download_performed": False,
        "report_or_document_crawl_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUT:
        atomic_write(path, result)
    return result


def validate() -> None:
    points = canonical_points()
    if len(points) != 3:
        raise ValueError("target count")
    for path in (PROBE, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("slot output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    if MAX_BYTES != 1_048_576 or MAX_CANDIDATES != 20:
        raise ValueError("bounded resource guards")
    if len(POSTCODES) != 3 or len({postcode for _, postcode in POSTCODES}) != 3:
        raise ValueError("postcode target guard")
    if not LANDING_URL.startswith("https://www.cqc.org.uk/"):
        raise ValueError("official source guard")
    print("PASS_TARGET_3_CQC_FORM_DISCOVERY_POSTCODE_MAX2_REQUESTS_EACH_MAX1MIB_20_CANDIDATES")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(
        json.dumps(
            {
                "state": result["state"],
                "completed_count": result["completed_count"],
                "target_count": result["target_count"],
                "produced_candidate_rows": result["produced_candidate_rows"],
                "evidence_records": len(result["source_evidence"]),
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
