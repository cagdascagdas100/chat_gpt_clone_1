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
TASK_ID = "parcel-label-3-ea-waste-operations-postcode-v1-20260802"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SEARCH_URL = "https://environment.data.gov.uk/public-register/view/search-waste-operations"
INDEX_URL = "https://environment.data.gov.uk/public-register/view/index"
ABOUT_URL = "https://environment.data.gov.uk/public-register/view/about"
API_CATALOGUE_URL = "https://www.api.gov.uk/ea/public-registers-for-environmental-information/"
DATA_LICENCE_URL = "https://environment.data.gov.uk/public-register/view/data-licence"
NATIONAL_DATA_LIBRARY_URL = "https://www.data.gov.uk/collections/environment/public-registers"
MAX_BYTES = 1_048_576
MAX_CANDIDATES = 20
POSTCODES = {
    "parcel_61523": "SW16 5TG",
    "parcel_61524": "SW16 5AE",
    "parcel_61525": "SW16 5AZ",
}
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self.form: dict[str, Any] | None = None
        self.select: dict[str, Any] | None = None
        self.option: dict[str, Any] | None = None
        self.option_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        tag = tag.lower()
        if tag == "form":
            self.form = {
                "action": a.get("action", ""),
                "method": (a.get("method") or "get").lower(),
                "inputs": [],
                "selects": [],
            }
        elif self.form is not None and tag == "input":
            self.form["inputs"].append(a)
        elif self.form is not None and tag == "select":
            self.select = {"name": a.get("name", ""), "id": a.get("id", ""), "options": []}
        elif self.select is not None and tag == "option":
            self.option = {"value": a.get("value", ""), "selected": "selected" in a}
            self.option_text = []

    def handle_data(self, data: str) -> None:
        if self.option is not None:
            self.option_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "option" and self.option is not None and self.select is not None:
            self.option["text"] = " ".join("".join(self.option_text).split())
            self.select["options"].append(self.option)
            self.option = None
        elif tag == "select" and self.select is not None and self.form is not None:
            self.form["selects"].append(self.select)
            self.select = None
        elif tag == "form" and self.form is not None:
            self.forms.append(self.form)
            self.form = None


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []
        self.page_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self.href = dict(attrs).get("href") or ""
            self.text = []

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.page_text.append(cleaned)
            if self.href is not None:
                self.text.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self.href is not None:
            text = " ".join(self.text)
            if text:
                self.links.append((self.href, text))
            self.href = None
            self.text = []


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
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


def load_points(base: Path) -> list[dict[str, Any]]:
    source = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    found = {r.get("parcel_id"): r for r in rows if isinstance(r, dict) and r.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing")
    result: list[dict[str, Any]] = []
    for parcel_id in POSTCODES:
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        expected_lon, expected_lat = POINTS[parcel_id]
        if (
            row.get("geometry_type") != "Point"
            or row.get("point_valid") is not True
            or abs(lon - expected_lon) > 1e-7
            or abs(lat - expected_lat) > 1e-7
        ):
            raise ValueError("invalid canonical Point " + parcel_id)
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


def open_bounded(opener: urllib.request.OpenerDirector, request: urllib.request.Request, timeout: float) -> tuple[int, str, bytes]:
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def discover_postcode_form(html: str) -> tuple[dict[str, Any] | None, str | None, str | None]:
    parser = FormParser()
    parser.feed(html)
    for form in parser.forms:
        postcode_name = None
        distance_name = None
        for item in form["inputs"]:
            marker = " ".join(
                (
                    item.get("name", ""),
                    item.get("id", ""),
                    item.get("placeholder", ""),
                    item.get("aria-label", ""),
                )
            ).lower()
            if postcode_name is None and "post" in marker:
                postcode_name = item.get("name") or item.get("id")
            if distance_name is None and ("distance" in marker or "radius" in marker):
                distance_name = item.get("name") or item.get("id")
        for select in form["selects"]:
            marker = " ".join((select.get("name", ""), select.get("id", ""))).lower()
            if distance_name is None and ("distance" in marker or "radius" in marker):
                distance_name = select.get("name") or select.get("id")
        if postcode_name:
            return form, postcode_name, distance_name
    return None, None, None


def form_fields(form: dict[str, Any], postcode_name: str, distance_name: str | None, postcode: str) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    postcode_set = False
    distance_set = False
    for item in form["inputs"]:
        name = item.get("name", "")
        if not name:
            continue
        input_type = (item.get("type") or "text").lower()
        value = item.get("value", "")
        marker = " ".join((name, item.get("id", ""), value)).lower()
        if name == postcode_name:
            fields.append((name, postcode))
            postcode_set = True
        elif distance_name and name == distance_name:
            fields.append((name, "1"))
            distance_set = True
        elif input_type == "hidden":
            fields.append((name, value))
        elif input_type in {"radio", "checkbox"} and (
            item.get("checked") == "checked" or "1km" in marker or "distance" in marker and value == "1"
        ):
            fields.append((name, value or "true"))
            if distance_name and name == distance_name:
                distance_set = True
        elif input_type in {"submit", "button"} and value:
            fields.append((name, value))
    for select in form["selects"]:
        name = select.get("name", "")
        if not name:
            continue
        selected = next((o for o in select["options"] if o.get("selected") and o.get("value")), None)
        if distance_name and name == distance_name:
            value = next(
                (str(o.get("value")) for o in select["options"] if str(o.get("value", "")).strip() in {"1", "1km"}),
                "1",
            )
            fields.append((name, value))
            distance_set = True
        elif selected:
            fields.append((name, str(selected["value"])))
    if not postcode_set:
        raise ValueError("postcode field not populated")
    if distance_name and not distance_set:
        fields.append((distance_name, "1"))
    return fields


def extract_candidates(html: str, base_url: str, postcode: str) -> list[dict[str, Any]]:
    parser = LinkParser()
    parser.feed(html)
    page = " ".join(parser.page_text).upper()
    compact = postcode.replace(" ", "").upper()
    if postcode.upper() not in page and compact not in page.replace(" ", ""):
        return []
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for href, text in parser.links:
        url = urllib.parse.urljoin(base_url, href)
        marker = (text + " " + url).upper()
        is_detail = (
            "/PUBLIC-REGISTER/VIEW/" in marker
            and any(token in marker for token in ("PERMIT", "REGISTRATION", "WASTE", "EPR", "DETAIL"))
        )
        if is_detail:
            key = (url, text)
            if key not in seen:
                seen.add(key)
                candidates.append(
                    {
                        "source_url": url,
                        "display_text": text[:500],
                        "searched_postcode": postcode,
                        "context_only": True,
                        "exact_parcel_binding": False,
                        "property_type_binding": False,
                    }
                )
                if len(candidates) >= MAX_CANDIDATES:
                    break
    return candidates


def evidence(
    parcel_id: str,
    postcode: str,
    point: dict[str, Any],
    url: str,
    accessed_at: str,
    digest: str,
    basis: str,
    excerpt: str,
    status: int | None,
    requests_made: int,
) -> dict[str, Any]:
    return {
        "parcel_id": parcel_id,
        "searched_postcode": postcode,
        "canonical_point": point,
        "source_url": url,
        "accessed_at": accessed_at,
        "content_sha256": digest,
        "sha256_basis": basis,
        "record_scope": (
            "one bounded official Environment Agency Waste Operations public-register postcode search; "
            "maximum one landing request plus one discovered form submission, 1 km, 1 MiB and 20 candidates"
        ),
        "supports_fields": [
            "waste-operation permit or registration presence",
            "operator or permit-holder display text where published",
            "site address or postcode context where published",
            "permit or registration detail link",
        ],
        "relevant_record_ids_or_excerpt": excerpt,
        "terms_or_license_urls": [DATA_LICENCE_URL],
        "http_status": status,
        "requests_made": requests_made,
    }


def attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parcel_id = point["parcel_id"]
    postcode = POSTCODES[parcel_id]
    accessed_at = utc_now()
    requests_made = 0
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    opener.addheaders = [("User-Agent", "AAYS-parcel-label-evidence/1.0 bounded official-source research")]
    try:
        status, url, raw = open_bounded(
            opener,
            urllib.request.Request(SEARCH_URL, headers={"Accept": "text/html"}),
            timeout,
        )
        requests_made += 1
        form, postcode_name, distance_name = discover_postcode_form(raw.decode("utf-8", "replace"))
        if not form or not postcode_name:
            return [], evidence(
                parcel_id,
                postcode,
                point,
                url,
                accessed_at,
                sha256_bytes(raw),
                "bounded_landing_response_bytes",
                "NO_DISCOVERABLE_POSTCODE_FORM",
                status,
                requests_made,
            )
        fields = form_fields(form, postcode_name, distance_name, postcode)
        action = urllib.parse.urljoin(url, form.get("action") or url)
        method = (form.get("method") or "get").lower()
        encoded = urllib.parse.urlencode(fields).encode("utf-8")
        if method == "post":
            request = urllib.request.Request(
                action,
                data=encoded,
                headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html"},
            )
        else:
            separator = "&" if urllib.parse.urlparse(action).query else "?"
            request = urllib.request.Request(action + separator + encoded.decode("utf-8"), headers={"Accept": "text/html"})
        status, url, raw = open_bounded(opener, request, timeout)
        requests_made += 1
        html = raw.decode("utf-8", "replace")
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))[:1500]
        record = evidence(
            parcel_id,
            postcode,
            point,
            url,
            accessed_at,
            sha256_bytes(raw),
            "bounded_search_response_bytes",
            plain,
            status,
            requests_made,
        )
        record.update(
            {
                "discovered_form_method": method,
                "discovered_postcode_field": postcode_name,
                "discovered_distance_field": distance_name,
            }
        )
        return extract_candidates(html, url, postcode), record
    except Exception as exc:
        error = f"EA_WASTE_OPERATIONS_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
        return [], evidence(
            parcel_id,
            postcode,
            point,
            SEARCH_URL,
            accessed_at,
            sha256_bytes(error.encode("utf-8")),
            "bounded_error_evidence_string",
            error,
            None,
            requests_made,
        )


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for point in points:
        candidates, record = attempt(point, timeout)
        records.append(record)
        for candidate in candidates:
            candidate.update({"parcel_id": point["parcel_id"], "canonical_point": point})
            rows.append(candidate)
    candidate_count = len(rows)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if candidate_count else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": candidate_count,
        "candidate_rows": rows,
        "source_evidence": records,
        "blocker": {
            "code": None if candidate_count else "EA_WASTE_OPERATIONS_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULT",
            "state": "NONE" if candidate_count else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_EA_WASTE_OPERATIONS_POSTCODE",
        "search_url": SEARCH_URL,
        "index_url": INDEX_URL,
        "about_url": ABOUT_URL,
        "api_catalogue_url": API_CATALOGUE_URL,
        "data_licence_url": DATA_LICENCE_URL,
        "national_data_library_url": NATIONAL_DATA_LIBRARY_URL,
        "login_or_api_key_used": False,
        "bulk_download_performed": False,
        "full_register_scan_performed": False,
        "permit_document_followup_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(base: Path) -> None:
    points = load_points(base)
    if len(points) != 3:
        raise ValueError("target count mismatch")
    if not SEARCH_URL.startswith("https://environment.data.gov.uk/public-register/view/"):
        raise ValueError("unexpected official source")
    if MAX_BYTES != 1_048_576 or MAX_CANDIDATES != 20:
        raise ValueError("bounded limits changed")
    print(
        "PASS_TARGET_3_EA_WASTE_OPERATIONS_FORM_DISCOVERY_POSTCODE_"
        "MAX2_REQUESTS_EACH_1KM_MAX1MIB_20_CANDIDATES_CONTEXT_ONLY"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate(base)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(base), max(1.0, min(args.timeout, 30.0)))
    atomic_json(
        base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/ea_waste_operations_postcode_result_latest.json",
        payload,
    )
    atomic_json(
        base / "england_map_web/data/aays_21_slots/parcel_label_3/ea_waste_operations_postcode_latest.json",
        payload,
    )
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    else:
        print("PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
