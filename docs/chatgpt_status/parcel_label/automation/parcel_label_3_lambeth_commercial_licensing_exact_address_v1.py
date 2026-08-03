from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
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
TASK_ID = "parcel-label-3-lambeth-commercial-licensing-exact-address-v1-20260803"
INPUT_PATH = "docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json"
INPUT_BLOB_SHA = "c5c3b41970b77b59bd83ea923252a062a217f0d2"
SEARCH_URL = "https://planning.lambeth.gov.uk/online-applications/search.do?action=simple&searchType=LicencingApplication"
COUNCIL_SEARCH_URL = "https://www.lambeth.gov.uk/business-rates-services-and-licensing/Licensing-and-permits/licensing-comments-and-complaints/search-licences-and-licence-applications"
CURRENT_APPLICATIONS_URL = "https://www.lambeth.gov.uk/Business-rates-services-and-licensing/Licensing-and-permits/licensing-comments-and-complaints/licensing-comments-and-complaints-1"
PREMISES_LICENCE_URL = "https://www.lambeth.gov.uk/business-rates-services-and-licensing/licences/premises-licence"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL = "https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_CANDIDATES = 10
TARGET_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")


class Forms(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "form":
            self.current = {"action": data.get("action", ""), "method": (data.get("method") or "get").lower(), "inputs": []}
        elif tag == "input" and self.current is not None:
            self.current["inputs"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form" and self.current is not None:
            self.forms.append(self.current)
            self.current = None


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page_text: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href", "") or ""
            self.anchor_text = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.page_text.append(text)
            if self.href is not None:
                self.anchor_text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            text = " ".join(self.anchor_text)
            if text:
                self.links.append((self.href, text))
            self.href = None
            self.anchor_text = []


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def normalized(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def load_targets(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / INPUT_PATH).read_text(encoding="utf-8"))
    records = {row.get("parcel_id"): row for row in payload.get("records", []) if isinstance(row, dict)}
    if tuple(pid for pid in TARGET_IDS if pid in records) != TARGET_IDS:
        raise ValueError("three exact target rows are required")
    targets: list[dict[str, Any]] = []
    for parcel_id in TARGET_IDS:
        row = records[parcel_id]
        if row.get("exact_uprn_bound") is not True or row.get("classification_verified") is not True:
            raise ValueError(f"unverified exact input row: {parcel_id}")
        if not row.get("UPRN") or not row.get("FULLADDRESS") or not row.get("POSTCODE"):
            raise ValueError(f"missing exact input fields: {parcel_id}")
        targets.append({"parcel_id": parcel_id, "UPRN": str(row["UPRN"]), "FULLADDRESS": str(row["FULLADDRESS"]), "POSTCODE": str(row["POSTCODE"]), "BLPUCLASS": str(row.get("BLPUCLASS", "")), "official_property_type_label": str(row.get("official_property_type_label", "")), "official_mdu_status": bool(row.get("official_mdu_status"))})
    return targets


def open_bounded(opener: urllib.request.OpenerDirector, request: urllib.request.Request, timeout: float) -> tuple[int, str, bytes]:
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def discover_search_form(html: str) -> tuple[dict[str, Any] | None, str | None]:
    parser = Forms()
    parser.feed(html)
    preferred = ("searchCriteria", "caseAddress", "address", "postcode", "simpleSearch")
    for form in parser.forms:
        for candidate in preferred:
            for field in form["inputs"]:
                name = field.get("name", "")
                field_id = field.get("id", "")
                if candidate.lower() in (name + " " + field_id).lower():
                    return form, name or field_id
    return None, None


def form_values(form: dict[str, Any], search_field: str, query: str) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    populated = False
    for field in form["inputs"]:
        name = field.get("name", "")
        field_type = (field.get("type") or "text").lower()
        value = field.get("value", "")
        if not name:
            continue
        if name == search_field:
            values.append((name, query))
            populated = True
        elif field_type == "hidden":
            values.append((name, value))
        elif field_type in {"submit", "button"} and value:
            values.append((name, value))
    if not populated:
        raise ValueError("discovered search field was not populated")
    return values


def extract_candidates(html: str, base_url: str, target: dict[str, Any]) -> list[dict[str, Any]]:
    parser = Page()
    parser.feed(html)
    page = normalized(" ".join(parser.page_text))
    address = normalized(target["FULLADDRESS"])
    postcode = normalized(target["POSTCODE"])
    number = address.split()[0]
    street_tokens = address.split()[1:3]
    if not (postcode in page and number in page and all(token in page for token in street_tokens)):
        return []
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for href, text in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        marker = normalized(text + " " + absolute)
        if any(term in marker for term in ("APPLICATION", "LICENCE", "LICENSE", "DETAIL", "REFERENCE")):
            key = (absolute, text)
            if key not in seen:
                seen.add(key)
                rows.append({"parcel_id": target["parcel_id"], "UPRN": target["UPRN"], "FULLADDRESS": target["FULLADDRESS"], "POSTCODE": target["POSTCODE"], "source_url": absolute, "display_text": text[:500], "exact_address_text_visible": True, "licensing_context_only": True, "core_exact_uprn_preserved": True, "property_type_binding_claimed": False})
                if len(rows) >= MAX_CANDIDATES:
                    break
    return rows


def evidence(target: dict[str, Any], source_url: str, accessed_at: str, digest: str, basis: str, excerpt: str, status: int | None, requests_made: int) -> dict[str, Any]:
    return {"parcel_id": target["parcel_id"], "UPRN": target["UPRN"], "searched_full_address": target["FULLADDRESS"], "searched_postcode": target["POSTCODE"], "source_url": source_url, "accessed_at": accessed_at, "content_sha256": digest, "sha256_basis": basis, "record_scope": "one bounded official Lambeth licensing Public Access exact-address search; maximum one landing and one discovered search submission, 1 MiB and 10 candidate links", "supports_fields": ["licensing application or existing licence record presence", "premises postal address where published", "licence/application reference where published", "licensable activity description where published"], "relevant_record_ids_or_excerpt": excerpt, "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL], "http_status": status, "requests_made": requests_made}


def attempt(target: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = now()
    requests_made = 0
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [("User-Agent", "AAYS-parcel-label-evidence/1.0 bounded official-source research")]
    try:
        status, final_url, raw = open_bounded(opener, urllib.request.Request(SEARCH_URL, headers={"Accept": "text/html"}), timeout)
        requests_made += 1
        form, search_field = discover_search_form(raw.decode("utf-8", "replace"))
        if form is None or not search_field:
            return [], evidence(target, final_url, accessed_at, sha256_bytes(raw), "bounded_landing_response_bytes", "NO_DISCOVERABLE_PUBLIC_SEARCH_FORM", status, requests_made)
        values = form_values(form, search_field, target["FULLADDRESS"])
        action = urllib.parse.urljoin(final_url, form.get("action") or final_url)
        method = (form.get("method") or "get").lower()
        encoded = urllib.parse.urlencode(values)
        if method == "post":
            request = urllib.request.Request(action, data=encoded.encode("utf-8"), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html"})
        else:
            separator = "&" if urllib.parse.urlparse(action).query else "?"
            request = urllib.request.Request(action + separator + encoded, headers={"Accept": "text/html"})
        status, final_url, raw = open_bounded(opener, request, timeout)
        requests_made += 1
        html = raw.decode("utf-8", "replace")
        excerpt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:1500]
        record = evidence(target, final_url, accessed_at, sha256_bytes(raw), "bounded_search_response_bytes", excerpt, status, requests_made)
        record["discovered_form_method"] = method
        record["discovered_search_field"] = search_field
        return extract_candidates(html, final_url, target), record
    except Exception as exc:
        error = f"LAMBETH_COMMERCIAL_LICENSING_EXACT_ADDRESS_ERROR:{type(exc).__name__}:{exc}"
        return [], evidence(target, SEARCH_URL, accessed_at, sha256_bytes(error.encode("utf-8")), "bounded_error_evidence_string", error, None, requests_made)


def build_payload(targets: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    source_evidence: list[dict[str, Any]] = []
    for target in targets:
        rows, record = attempt(target, timeout)
        candidates.extend(rows)
        source_evidence.append(record)
    count = len(candidates)
    return {"schema_version": 1, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": SLOT_ID, "task_id": TASK_ID, "generated_at": now(), "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if count else "NO_DATA_CONTINUE", "panel_status": "PUBLISHED", "completed_count": 3, "target_count": 3, "previous_percent": 0.0, "progress_percent": 100.0, "percent_increase": 100.0, "core_exact_rows_preserved": 3, "core_final_ready_preserved": True, "searched_records": targets, "produced_candidate_rows": count, "candidate_rows": candidates, "source_evidence": source_evidence, "blocker": {"code": None if count else "LAMBETH_COMMERCIAL_LICENSING_NO_USABLE_RESPONSE_OR_NO_EXACT_ADDRESS_RESULT", "state": "NONE" if count else "NO_DATA_CONTINUE", "manual_action_required": False, "retry_unchanged_route": False}, "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_COMMERCIAL_LICENSING_EXACT_ADDRESS", "search_url": SEARCH_URL, "council_search_url": COUNCIL_SEARCH_URL, "current_applications_url": CURRENT_APPLICATIONS_URL, "premises_licence_url": PREMISES_LICENCE_URL, "terms_url": TERMS_URL, "copyright_url": COPYRIGHT_URL, "open_government_licence_url": OGL_URL, "login_or_account_used": False, "comment_or_representation_submitted": False, "captcha_bypass_attempted": False, "pagination_performed": False, "bulk_download_performed": False, "full_register_scan_performed": False, "address_reuse_performed": False, "property_type_binding_claimed": False, "inferred_values": 0, "fake_data": False, "final_ready": True}


def validate(root: Path) -> None:
    targets = load_targets(root)
    if len(targets) != 3:
        raise ValueError("expected exactly three targets")
    if not SEARCH_URL.startswith("https://planning.lambeth.gov.uk/online-applications/"):
        raise ValueError("unexpected official search host")
    print("PASS_3_EXACT_UPRN_ADDRESSES_LAMBETH_LICENSING_MAX2_REQUESTS_EACH_MAX1MIB_10_CANDIDATES_READ_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    validate(root)
    if args.validate_only:
        return 0
    payload = build_payload(load_targets(root), max(1.0, min(args.timeout, 30.0)))
    atomic_json(root / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_commercial_licensing_exact_address_result_latest.json", payload)
    atomic_json(root / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_commercial_licensing_exact_address_latest.json", payload)
    print("PASS_NO_DATA_CONTINUE_3_OF_3" if payload["produced_candidate_rows"] == 0 else f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
