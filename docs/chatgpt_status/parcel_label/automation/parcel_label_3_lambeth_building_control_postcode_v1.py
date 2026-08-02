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

TASK_ID = "parcel-label-3-lambeth-building-control-postcode-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_building_control_postcode_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_building_control_postcode_latest.json",
)
LANDING_URL = "https://www.lambeth.gov.uk/planning-and-building-control/building-control-and-regulations/search-building-regulation"
BUILDING_REGULATIONS_URL = "https://www.lambeth.gov.uk/planning-building-control/building-control-regulations/building-regulations"
CONTACT_URL = "https://www.lambeth.gov.uk/about-council/contact-us/contact-details/building-control"
POSTCODES = (
    ("parcel_61523", "SW16 5TG"),
    ("parcel_61524", "SW16 5AE"),
    ("parcel_61525", "SW16 5AZ"),
)
MAX_BYTES = 1_048_576
MAX_CANDIDATES = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, obj: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)


def canonical_points() -> list[dict]:
    raw = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    by_id = {row["parcel_id"]: row for row in raw["canonical_points"]}
    out = []
    for parcel_id, _postcode in POSTCODES:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon, lat = float(row["longitude"]), float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        out.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return out


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            values = dict(attrs)
            self._href = values.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append({"href": self._href, "text": " ".join(self._text).strip()})
            self._href = None
            self._text = []


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict] = []
        self._form: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        tag = tag.lower()
        if tag == "form":
            self._form = {
                "action": values.get("action") or "",
                "method": (values.get("method") or "get").lower(),
                "inputs": [],
            }
        elif self._form is not None and tag in {"input", "button", "select", "textarea"}:
            self._form["inputs"].append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None


def bounded_fetch(url: str, timeout: float, data: bytes | None = None) -> tuple[bytes, int | None, str]:
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
            "User-Agent": "TerraYield-AAYS/1.0 bounded Lambeth Building Control research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        return raw, getattr(response, "status", None), response.geturl()


def text_of(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")


def discover_database_url(raw: bytes, base_url: str) -> str:
    parser = LinkParser()
    parser.feed(text_of(raw))
    ranked: list[tuple[int, str]] = []
    for link in parser.links:
        href = str(link.get("href") or "").strip()
        label = re.sub(r"\s+", " ", str(link.get("text") or "")).strip().lower()
        if not href:
            continue
        combined = f"{label} {href.lower()}"
        score = 0
        if "building regulation" in combined or "building control" in combined:
            score += 4
        if "database" in combined or "publicaccess" in combined or "online-applications" in combined:
            score += 4
        if "application" in combined or "search" in combined:
            score += 2
        if score:
            ranked.append((score, urllib.parse.urljoin(base_url, href)))
    if not ranked:
        raise ValueError("official building regulation database link not discovered")
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def choose_form(raw: bytes, page_url: str) -> tuple[str, str, dict[str, str], str]:
    parser = FormParser()
    parser.feed(text_of(raw))
    candidates: list[tuple[int, dict, str]] = []
    for form in parser.forms:
        search_name = ""
        score = 0
        for attrs in form["inputs"]:
            name = str(attrs.get("name") or "")
            identity = " ".join(
                str(attrs.get(key) or "") for key in ("name", "id", "placeholder", "aria-label", "title", "value")
            ).lower()
            input_type = str(attrs.get("type") or "text").lower()
            if input_type in {"hidden", "submit", "button", "image", "checkbox", "radio", "file"}:
                continue
            local_score = 0
            if "postcode" in identity:
                local_score += 10
            if "keyword" in identity or "search" in identity:
                local_score += 7
            if "address" in identity or "property" in identity:
                local_score += 5
            if local_score > score and name:
                score = local_score
                search_name = name
        if search_name:
            candidates.append((score, form, search_name))
    if not candidates:
        raise ValueError("search form field not discovered")
    candidates.sort(key=lambda item: -item[0])
    _score, form, search_name = candidates[0]
    defaults: dict[str, str] = {}
    for attrs in form["inputs"]:
        name = str(attrs.get("name") or "")
        if not name or name == search_name:
            continue
        input_type = str(attrs.get("type") or "text").lower()
        if input_type == "hidden" or (input_type in {"submit", "button"} and attrs.get("value")):
            defaults[name] = str(attrs.get("value") or "")
    action = urllib.parse.urljoin(page_url, str(form.get("action") or ""))
    return action, str(form.get("method") or "get").lower(), defaults, search_name


def submit_search(
    action: str, method: str, defaults: dict[str, str], search_name: str, postcode: str, timeout: float
) -> tuple[bytes, int | None, str]:
    fields = dict(defaults)
    fields[search_name] = postcode
    encoded = urllib.parse.urlencode(fields).encode("utf-8")
    if method == "post":
        return bounded_fetch(action, timeout, encoded)
    separator = "&" if urllib.parse.urlsplit(action).query else "?"
    return bounded_fetch(action + separator + encoded.decode("ascii"), timeout)


def extract_candidates(raw: bytes, base_url: str, postcode: str) -> list[dict]:
    parser = LinkParser()
    parser.feed(text_of(raw))
    candidates = []
    seen = set()
    for link in parser.links:
        href = str(link.get("href") or "").strip()
        label = html.unescape(re.sub(r"\s+", " ", str(link.get("text") or ""))).strip()
        if not href or not label:
            continue
        combined = f"{href} {label}".lower()
        if not any(token in combined for token in ("application", "case", "record", "property", "building")):
            continue
        url = urllib.parse.urljoin(base_url, href)
        key = (url, label)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            {
                "source_url": url,
                "visible_text": label[:500],
                "searched_postcode": postcode,
                "candidate_only": True,
                "exact_parcel_binding_claimed": False,
                "property_type_binding_claimed": False,
            }
        )
        if len(candidates) >= MAX_CANDIDATES:
            break
    return candidates


def run(timeout: float) -> dict:
    points = canonical_points()
    point_by_id = {row["parcel_id"]: row for row in points}
    evidence = []
    candidates = []
    for parcel_id, postcode in POSTCODES:
        accessed_at = now()
        try:
            landing_raw, landing_status, landing_final = bounded_fetch(LANDING_URL, timeout)
            database_url = discover_database_url(landing_raw, landing_final)
            database_raw, database_status, database_final = bounded_fetch(database_url, timeout)
            action, method, defaults, search_name = choose_form(database_raw, database_final)
            result_raw, result_status, result_final = submit_search(
                action, method, defaults, search_name, postcode, timeout
            )
            rows = extract_candidates(result_raw, result_final, postcode)
            candidates.extend(
                {
                    **row,
                    "parcel_id": parcel_id,
                    "canonical_point": point_by_id[parcel_id],
                }
                for row in rows
            )
            evidence.append(
                {
                    "parcel_id": parcel_id,
                    "source_url": result_final,
                    "landing_url": landing_final,
                    "database_url": database_final,
                    "accessed_at": accessed_at,
                    "content_sha256": sha(result_raw),
                    "landing_content_sha256": sha(landing_raw),
                    "database_content_sha256": sha(database_raw),
                    "sha256_basis": "bounded_raw_html_response_bytes",
                    "record_scope": "one official Lambeth Building Control property/application search for one postcode; maximum 20 candidate links; maximum 1 MiB per response",
                    "supports_fields": [
                        "building regulation application candidate link",
                        "visible application or property text",
                        "searched postcode",
                    ],
                    "relevant_record_ids_or_excerpt": {
                        "postcode": postcode,
                        "candidate_count": len(rows),
                        "candidate_links": [row["source_url"] for row in rows],
                    },
                    "official_terms_url": LANDING_URL,
                    "building_regulations_url": BUILDING_REGULATIONS_URL,
                    "contact_url": CONTACT_URL,
                    "landing_http_status": landing_status,
                    "database_http_status": database_status,
                    "result_http_status": result_status,
                    "discovered_search_field": search_name,
                    "search_method": method,
                }
            )
        except Exception as exc:
            message = f"LAMBETH_BUILDING_CONTROL_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append(
                {
                    "parcel_id": parcel_id,
                    "source_url": LANDING_URL,
                    "accessed_at": accessed_at,
                    "content_sha256": sha(message),
                    "sha256_basis": "bounded_error_evidence_string",
                    "record_scope": "one official Lambeth Building Control discovery and postcode-search attempt; at most one landing, one database and one search response; no plan or document crawl",
                    "supports_fields": ["Lambeth Building Control database/search availability"],
                    "relevant_record_ids_or_excerpt": message[:512],
                    "official_terms_url": LANDING_URL,
                    "building_regulations_url": BUILDING_REGULATIONS_URL,
                    "contact_url": CONTACT_URL,
                    "searched_postcode": postcode,
                    "http_status": getattr(exc, "code", None),
                }
            )
    state = "LAMBETH_BUILDING_CONTROL_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {
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
            "code": "NONE" if candidates else "LAMBETH_BUILDING_CONTROL_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULTS",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_LAMBETH_BUILDING_CONTROL_CANDIDATES_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_BUILDING_CONTROL_POSTCODE"
        ),
        "document_crawl_performed": False,
        "plans_downloaded": False,
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
    if len(points) != 3 or len(POSTCODES) != 3:
        raise ValueError("target count must be 3")
    for path in (PROBE, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("state output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    if len({postcode for _parcel_id, postcode in POSTCODES}) != 3:
        raise ValueError("three distinct postcodes required")
    if MAX_BYTES != 1_048_576 or MAX_CANDIDATES != 20:
        raise ValueError("bounded response guards")
    print("PASS_TARGET_3_LAMBETH_BUILDING_CONTROL_FORM_DISCOVERY_POSTCODE_MAX1MIB_CANDIDATE_ONLY")


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
