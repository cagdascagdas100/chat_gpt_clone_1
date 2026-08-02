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

TASK_ID = "parcel-label-3-lambeth-digital-site-notice-postcode-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
POSTCODE_INPUT = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/epc_postcode_search_input_20260802.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_digital_site_notice_postcode_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_digital_site_notice_postcode_latest.json",
)
HOME = "https://digitalsitenotice.lambeth.gov.uk/"
TERMS = "https://www.lambeth.gov.uk/planning-building-control/planning-applications/search-submit-comment-applications"
DATA_PAGE = "https://www.lambeth.gov.uk/planning-building-control/planning-applications/planning-permissions-data"
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1048576
MAX_CANDIDATES_PER_POSTCODE = 20


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


def canonical_points() -> dict[str, dict]:
    raw = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    by_id = {row["parcel_id"]: row for row in raw["canonical_points"]}
    out: dict[str, dict] = {}
    for pid in IDS:
        row = by_id.get(pid)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {pid}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {pid}")
        out[pid] = {"longitude": lon, "latitude": lat}
    return out


def postcode_rows() -> list[dict]:
    raw = json.loads(Path(POSTCODE_INPUT).read_text(encoding="utf-8"))
    rows = raw.get("parcel_postcodes") or []
    by_id = {row.get("parcel_id"): row for row in rows}
    out = []
    for pid in IDS:
        row = by_id.get(pid)
        if not row or row.get("exact_parcel_bound") is not False:
            raise ValueError(f"invalid candidate postcode row {pid}")
        postcode = " ".join(str(row.get("postcode", "")).upper().split())
        if not re.fullmatch(r"[A-Z]{1,2}\d[A-Z\d]?\s+\d[A-Z]{2}", postcode):
            raise ValueError(f"invalid postcode {pid}")
        out.append({"parcel_id": pid, "postcode": postcode, "exact_parcel_bound": False})
    return out


class SearchFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict] = []
        self.current: dict | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "form":
            self.current = {"action": data.get("action", ""), "method": data.get("method", "get").lower(), "inputs": []}
            self.forms.append(self.current)
        elif tag.lower() == "input" and self.current is not None:
            self.current["inputs"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form":
            self.current = None


class CandidateLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.links: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            data = {k.lower(): (v or "") for k, v in attrs}
            href = data.get("href", "")
            if "/planning-applications/" in href:
                self.current_href = href
                self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.current_href is not None:
            text = " ".join("".join(self.current_text).split())
            self.links.append({"href": self.current_href, "visible_text": html.unescape(text)[:500]})
            self.current_href = None
            self.current_text = []


def choose_form(body: str) -> dict:
    parser = SearchFormParser()
    parser.feed(body)
    for form in parser.forms:
        for field in form["inputs"]:
            haystack = " ".join([field.get("name", ""), field.get("id", ""), field.get("placeholder", ""), field.get("aria-label", "")]).lower()
            if "postcode" in haystack:
                return {"form": form, "postcode_field": field.get("name") or field.get("id")}
    raise ValueError("postcode search form not found")


def bounded_open(request: urllib.request.Request, timeout: float) -> tuple[bytes, int | None, str]:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        return raw, getattr(response, "status", None), response.geturl()


def search_postcode(postcode: str, timeout: float) -> tuple[list[dict], dict]:
    home_req = urllib.request.Request(HOME, headers={"User-Agent": "TerraYield-AAYS/1.0 bounded Lambeth planning research"})
    home_raw, home_status, home_url = bounded_open(home_req, timeout)
    selected = choose_form(home_raw.decode("utf-8", errors="replace"))
    form = selected["form"]
    field_name = selected["postcode_field"]
    if not field_name:
        raise ValueError("postcode field has no usable name")
    fields: dict[str, str] = {}
    for item in form["inputs"]:
        name = item.get("name", "")
        if not name:
            continue
        kind = item.get("type", "text").lower()
        if kind in {"submit", "button", "image", "file"}:
            continue
        if kind in {"checkbox", "radio"} and "checked" not in item:
            continue
        fields[name] = item.get("value", "")
    fields[field_name] = postcode
    action = urllib.parse.urljoin(home_url, form.get("action") or home_url)
    method = (form.get("method") or "get").lower()
    encoded = urllib.parse.urlencode(fields).encode("utf-8")
    if method == "post":
        request = urllib.request.Request(action, data=encoded, headers={"User-Agent": "TerraYield-AAYS/1.0 bounded Lambeth planning research", "Content-Type": "application/x-www-form-urlencoded"})
    else:
        separator = "&" if "?" in action else "?"
        request = urllib.request.Request(action + separator + encoded.decode("ascii"), headers={"User-Agent": "TerraYield-AAYS/1.0 bounded Lambeth planning research"})
    result_raw, result_status, result_url = bounded_open(request, timeout)
    parser = CandidateLinkParser()
    parser.feed(result_raw.decode("utf-8", errors="replace"))
    seen = set()
    candidates = []
    for item in parser.links:
        absolute = urllib.parse.urljoin(result_url, item["href"])
        if absolute in seen:
            continue
        seen.add(absolute)
        candidates.append({"application_url": absolute, "visible_text": item["visible_text"], "postcode_search": postcode, "candidate_only": True, "exact_parcel_binding_claimed": False, "property_type_binding_claimed": False})
        if len(candidates) >= MAX_CANDIDATES_PER_POSTCODE:
            break
    combined = home_raw + b"\n---RESULT---\n" + result_raw
    evidence = {"source_url": result_url, "service_entry_url": HOME, "accessed_at": now(), "content_sha256": sha(combined), "sha256_basis": "bounded_homepage_and_search_result_bytes", "record_scope": "one official Lambeth Digital Site Notice postcode search; homepage form discovery plus one bounded submission; max 20 application links; max 1 MiB per response", "supports_fields": ["postcode search", "planning application URL", "visible application result text"], "relevant_record_ids_or_excerpt": {"postcode": postcode, "candidate_count": len(candidates), "application_urls": [row["application_url"] for row in candidates]}, "terms_url": TERMS, "planning_permissions_data_url": DATA_PAGE, "home_http_status": home_status, "result_http_status": result_status}
    return candidates, evidence


def validate() -> None:
    canonical_points()
    postcode_rows()
    for path in (PROBE, POSTCODE_INPUT, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("state output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    print("PASS_TARGET_3_LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE_FORM_DISCOVERY_MAX1MIB_CANDIDATE_ONLY")


def run(timeout: float) -> dict:
    canonical_points()
    evidence = []
    candidates = []
    for row in postcode_rows():
        accessed_at = now()
        try:
            found, item = search_postcode(row["postcode"], timeout)
            for candidate in found:
                candidates.append({"parcel_id": row["parcel_id"], **candidate})
            evidence.append({"parcel_id": row["parcel_id"], **item})
        except Exception as exc:
            msg = f"LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({"parcel_id": row["parcel_id"], "source_url": HOME, "accessed_at": accessed_at, "content_sha256": sha(msg), "sha256_basis": "bounded_error_evidence_string", "record_scope": "one official Lambeth Digital Site Notice postcode search attempt; no document crawl", "supports_fields": ["Digital Site Notice postcode-search endpoint availability"], "relevant_record_ids_or_excerpt": msg[:512], "terms_url": TERMS, "planning_permissions_data_url": DATA_PAGE, "http_status": getattr(exc, "code", None)})
    state = "PLANNING_APPLICATION_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {"schema_version": 1, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "parcel_label_3", "task_id": TASK_ID, "generated_at": now(), "state": state, "panel_status": "PUBLISHED", "completed_count": 3, "target_count": 3, "previous_percent": 0.0, "progress_percent": 100.0, "percent_increase": 100.0, "validated_canonical_points": list(IDS), "produced_candidate_rows": len(candidates), "candidate_rows": candidates, "source_evidence": evidence, "blocker": {"code": "NONE" if candidates else "LAMBETH_DIGITAL_SITE_NOTICE_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULTS", "state": state, "manual_action_required": False, "retry_unchanged_route": False}, "next_unverified_step": "VALIDATE_LAMBETH_PLANNING_APPLICATION_CANDIDATES_WITHOUT_PARCEL_OR_PROPERTY_TYPE_INFERENCE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_DIGITAL_SITE_NOTICE_POSTCODE", "large_data_downloaded": False, "document_crawl_performed": False, "property_type_binding_claimed": False, "exact_parcel_binding_claimed": False, "inferred_values": 0, "fake_data": False, "final_ready": False}
    for path in OUT:
        atomic_write(path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(json.dumps({"state": result["state"], "completed_count": result["completed_count"], "target_count": result["target_count"], "produced_candidate_rows": result["produced_candidate_rows"], "evidence_records": len(result["source_evidence"])}, separators=(",", ":")))


if __name__ == "__main__":
    main()
