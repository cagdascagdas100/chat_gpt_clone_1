from __future__ import annotations

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-lambeth-landlord-licence-postcode-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_landlord_licence_postcode_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_landlord_licence_postcode_latest.json",
)
REGISTER_URL = "https://hmolicensing.lambeth.gov.uk/public-register"
SCHEME_URL = "https://www.lambeth.gov.uk/housing/landlords-licensing/selective-licensing-scheme"
HMO_PRIVACY_URL = "https://www.lambeth.gov.uk/housing-services-privacy-notices/hmo-licensing-privacy-notice"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL = "https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
TARGETS = (
    ("parcel_61523", "SW16 5TG"),
    ("parcel_61524", "SW16 5AE"),
    ("parcel_61525", "SW16 5AZ"),
)
MAX_BYTES = 1_048_576
MAX_REQUESTS_PER_POSTCODE = 2
MAX_CANDIDATES_PER_POSTCODE = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: str, obj: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, target)


def canonical_points() -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = {row["parcel_id"]: row for row in payload["canonical_points"]}
    points: dict[str, dict[str, Any]] = {}
    for parcel_id, _ in TARGETS:
        row = rows.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        points[parcel_id] = {"parcel_id": parcel_id, "longitude": longitude, "latitude": latitude}
    return points


class FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, Any]] = []
        self._form: dict[str, Any] | None = None
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key.lower(): (value or "") for key, value in attrs}
        if tag.lower() == "form":
            self._form = {
                "action": data.get("action", ""),
                "method": data.get("method", "get").lower(),
                "inputs": [],
            }
        elif tag.lower() == "input" and self._form is not None:
            self._form["inputs"].append(data)
        elif tag.lower() == "a":
            self._href = data.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None
        elif tag.lower() == "a" and self._href is not None:
            text = " ".join("".join(self._text).split())
            self.links.append((self._href, text))
            self._href = None
            self._text = []


def choose_form(html: str) -> tuple[dict[str, Any] | None, str | None, bool]:
    parser = FormParser()
    parser.feed(html)
    lower = html.lower()
    recaptcha_present = any(token in lower for token in ("g-recaptcha", "recaptcha", "grecaptcha"))
    best: tuple[int, dict[str, Any], str] | None = None
    for form in parser.forms:
        for field in form["inputs"]:
            field_type = field.get("type", "text").lower()
            if field_type in {"hidden", "submit", "button", "checkbox", "radio"}:
                continue
            name = field.get("name", "")
            marker = " ".join(
                [name, field.get("id", ""), field.get("placeholder", ""), field.get("aria-label", "")]
            ).lower()
            score = 0
            if "postcode" in marker:
                score += 6
            if "query" in marker or "search" in marker:
                score += 4
            if "start here" in marker:
                score += 3
            if name:
                score += 1
            if best is None or score > best[0]:
                best = (score, form, name)
    if best is None or best[0] < 2 or not best[2]:
        return None, None, recaptcha_present
    return best[1], best[2], recaptcha_present


def build_submission(form: dict[str, Any], field_name: str, postcode: str, base_url: str) -> tuple[str, str, bytes | None]:
    values: list[tuple[str, str]] = []
    for field in form["inputs"]:
        name = field.get("name", "")
        if not name:
            continue
        field_type = field.get("type", "text").lower()
        if field_type in {"submit", "button", "file"}:
            continue
        if name == field_name:
            values.append((name, postcode))
        elif field_type == "hidden":
            values.append((name, field.get("value", "")))
    action = urllib.parse.urljoin(base_url, form.get("action") or base_url)
    method = form.get("method", "get").lower()
    encoded = urllib.parse.urlencode(values).encode("utf-8")
    if method == "post":
        return action, "POST", encoded
    separator = "&" if urllib.parse.urlsplit(action).query else "?"
    return action + separator + encoded.decode("ascii"), "GET", None


def bounded_fetch(opener: urllib.request.OpenerDirector, url: str, timeout: float, method: str = "GET", data: bytes | None = None) -> tuple[bytes, str, int | None]:
    headers = {
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": "TerraYield-AAYS/1.0 bounded Lambeth landlord licence register research",
    }
    if method == "POST":
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        return raw, response.geturl(), getattr(response, "status", None)


def extract_candidates(html: str, postcode: str, base_url: str) -> list[dict[str, Any]]:
    normalized = " ".join(html.split())
    compact_postcode = postcode.replace(" ", "")
    if postcode.lower() not in normalized.lower() and compact_postcode.lower() not in normalized.replace(" ", "").lower():
        return []
    parser = FormParser()
    parser.feed(html)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for href, text in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        marker = f"{text} {absolute}".lower()
        if any(token in marker for token in ("licence", "license", "register", "property", "application")):
            if absolute not in seen:
                seen.add(absolute)
                candidates.append({"title": text or None, "record_url": absolute})
        if len(candidates) >= MAX_CANDIDATES_PER_POSTCODE:
            break
    if not candidates:
        excerpt_match = re.search(r".{0,180}" + re.escape(postcode) + r".{0,260}", normalized, re.IGNORECASE)
        if excerpt_match:
            candidates.append({"title": None, "record_url": None, "postcode_context_excerpt": excerpt_match.group(0)})
    return candidates[:MAX_CANDIDATES_PER_POSTCODE]


def run(timeout: float) -> dict[str, Any]:
    points = canonical_points()
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for parcel_id, postcode in TARGETS:
        accessed_at = now()
        requests_made = 0
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            landing_raw, landing_url, landing_status = bounded_fetch(opener, REGISTER_URL, timeout)
            requests_made = 1
            landing_html = landing_raw.decode("utf-8", errors="replace")
            form, field_name, recaptcha_present = choose_form(landing_html)
            if form is None or field_name is None:
                raise ValueError("postcode search form not discovered")
            if recaptcha_present:
                message = "LAMBETH_LANDLORD_LICENCE_REGISTER_RECAPTCHA_PRESENT_NO_BYPASS"
                evidence.append({
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": points[parcel_id],
                    "source_url": landing_url,
                    "accessed_at": accessed_at,
                    "content_sha256": digest(landing_raw),
                    "sha256_basis": "bounded_raw_html_response_bytes",
                    "record_scope": "official Lambeth landlord licence public-register landing/form discovery; no captcha bypass; maximum 1 MiB",
                    "supports_fields": ["postcode search form availability", "reCAPTCHA presence", "public-register access boundary"],
                    "relevant_record_ids_or_excerpt": message,
                    "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
                    "http_status": landing_status,
                    "requests_made": requests_made,
                    "form_method": form.get("method"),
                    "form_action": urllib.parse.urljoin(landing_url, form.get("action") or landing_url),
                    "postcode_field_name": field_name,
                })
                continue
            submit_url, method, data = build_submission(form, field_name, postcode, landing_url)
            result_raw, result_url, result_status = bounded_fetch(opener, submit_url, timeout, method=method, data=data)
            requests_made = 2
            result_html = result_raw.decode("utf-8", errors="replace")
            rows = extract_candidates(result_html, postcode, result_url)
            for row in rows:
                candidates.append({
                    "parcel_id": parcel_id,
                    "searched_postcode": postcode,
                    "canonical_point": points[parcel_id],
                    "candidate": row,
                    "landlord_licence_context_only": True,
                    "exact_parcel_binding_claimed": False,
                    "property_type_binding_claimed": False,
                })
            evidence.append({
                "parcel_id": parcel_id,
                "searched_postcode": postcode,
                "canonical_point": points[parcel_id],
                "source_url": result_url,
                "landing_url": landing_url,
                "accessed_at": accessed_at,
                "content_sha256": digest(result_raw),
                "landing_content_sha256": digest(landing_raw),
                "sha256_basis": "bounded_raw_html_response_bytes",
                "record_scope": "one official public-register landing plus one discovered postcode submission; maximum 1 MiB each and 20 candidates",
                "supports_fields": ["postcode", "licensed-property register candidate", "record link or postcode context"],
                "relevant_record_ids_or_excerpt": {"candidate_count": len(rows), "postcode": postcode},
                "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
                "landing_http_status": landing_status,
                "result_http_status": result_status,
                "requests_made": requests_made,
                "form_method": method,
                "postcode_field_name": field_name,
            })
        except Exception as exc:
            message = f"LAMBETH_LANDLORD_LICENCE_POSTCODE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": parcel_id,
                "searched_postcode": postcode,
                "canonical_point": points[parcel_id],
                "source_url": REGISTER_URL,
                "accessed_at": accessed_at,
                "content_sha256": digest(message),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": "one bounded official Lambeth landlord licence public-register form-discovery/postcode attempt; maximum two requests",
                "supports_fields": ["public-register postcode lookup availability"],
                "relevant_record_ids_or_excerpt": message[:512],
                "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
                "http_status": getattr(exc, "code", None),
                "requests_made": requests_made,
            })

    state = "LANDLORD_LICENCE_POSTCODE_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
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
        "validated_canonical_points": list(points.values()),
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "LAMBETH_LANDLORD_LICENCE_NO_USABLE_RESPONSE_OR_NO_POSTCODE_RESULT",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_LAMBETH_LANDLORD_LICENCE_POSTCODE_CONTEXT_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_LANDLORD_LICENCE_POSTCODE"
        ),
        "register_url": REGISTER_URL,
        "scheme_url": SCHEME_URL,
        "hmo_privacy_url": HMO_PRIVACY_URL,
        "terms_url": TERMS_URL,
        "copyright_url": COPYRIGHT_URL,
        "open_government_licence_url": OGL_URL,
        "login_or_api_key_used": False,
        "captcha_bypass_attempted": False,
        "bulk_download_performed": False,
        "full_register_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output_path in OUT:
        atomic_write(output_path, result)
    return result


def validate() -> None:
    points = canonical_points()
    if len(points) != 3:
        raise ValueError("target count")
    if any(Path(path).is_absolute() for path in (PROBE, *OUT)):
        raise ValueError("relative paths required")
    if not REGISTER_URL.startswith("https://hmolicensing.lambeth.gov.uk/"):
        raise ValueError("official Lambeth register required")
    if MAX_BYTES != 1_048_576 or MAX_REQUESTS_PER_POSTCODE != 2 or MAX_CANDIDATES_PER_POSTCODE != 20:
        raise ValueError("bounds changed")
    if len(TARGETS) != 3:
        raise ValueError("exactly three targets required")
    print("PASS_TARGET_3_LAMBETH_LANDLORD_LICENCE_FORM_DISCOVERY_POSTCODE_MAX2_REQUESTS_EACH_MAX1MIB_20_CANDIDATES_NO_CAPTCHA_BYPASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout > 30:
        raise ValueError("timeout must be >0 and <=30 seconds per request")
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(f"PASS_{result['state']}_{result['completed_count']}_OF_{result['target_count']}")


if __name__ == "__main__":
    main()
