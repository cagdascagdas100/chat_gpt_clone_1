#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import http.cookiejar
import json
import pathlib
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any

INPUT = pathlib.Path(
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json"
)
MANIFEST = pathlib.Path(
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/"
    "hmrc_council_tax_band_exact_address_source_manifest_20260804.json"
)
OUTPUTS = [
    pathlib.Path(
        "docs/chatgpt_status/_shared/slots_21/parcel_label_3/"
        "hmrc_council_tax_band_exact_address_result_latest.json"
    ),
    pathlib.Path(
        "england_map_web/data/aays_21_slots/parcel_label_3/"
        "hmrc_council_tax_band_exact_address_latest.json"
    ),
]
SEARCH_URL = "https://www.tax.service.gov.uk/check-council-tax-band/search"
ALLOWED_HOST = "www.tax.service.gov.uk"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_GET_REQUESTS = 3
MAX_POST_REQUESTS = 3
BAND_RE = re.compile(r"(?:COUNCIL\s*TAX\s*)?BAND\s*([A-H])\b", re.I)
SINGLE_BAND_RE = re.compile(r"^[A-H]$", re.I)


def now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() != ALLOWED_HOST
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise RuntimeError(f"UNSAFE_OR_UNTRUSTED_URL:{url}")
    return url


def normalize_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", html.unescape(value).upper())


class SearchPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.csrf_token: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "input":
            return
        values = {key.casefold(): value for key, value in attrs}
        if (values.get("name") or "").casefold() == "csrftoken":
            token = values.get("value")
            if token:
                self.csrf_token = token


class ResultRowsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_row = False
        self._cell_depth = 0
        self._cell_parts: list[str] = []
        self._row_cells: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        low = tag.casefold()
        if low == "tr":
            self._in_row = True
            self._row_cells = []
        elif self._in_row and low in {"td", "th"}:
            self._cell_depth += 1
            if self._cell_depth == 1:
                self._cell_parts = []
        elif self._cell_depth and low == "br":
            self._cell_parts.append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell_depth:
            self._cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        low = tag.casefold()
        if self._in_row and low in {"td", "th"} and self._cell_depth:
            self._cell_depth -= 1
            if self._cell_depth == 0:
                text = " ".join(" ".join(self._cell_parts).split())
                self._row_cells.append(text)
                self._cell_parts = []
        elif low == "tr" and self._in_row:
            if self._row_cells:
                self.rows.append(self._row_cells)
            self._in_row = False
            self._cell_depth = 0
            self._cell_parts = []
            self._row_cells = []


def load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("search_url") != SEARCH_URL:
        raise RuntimeError("WRONG_MANIFEST_SEARCH_URL")
    if len(payload.get("target_uprns", [])) != 3:
        raise RuntimeError("SOURCE_MANIFEST_TARGET_COUNT")
    sources = payload.get("sources", [])
    if len(sources) < 4:
        raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
    for source in sources:
        excerpt = source.get("retained_excerpt", "")
        if (
            not excerpt
            or sha256_bytes(excerpt.encode("utf-8"))
            != source.get("retained_excerpt_sha256")
        ):
            raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
    return payload


def load_rows() -> list[dict[str, Any]]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    manifest = load_manifest()
    target_uprns = set(manifest["target_uprns"])
    if len(records) != 3:
        raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
    output: list[dict[str, Any]] = []
    for record in records:
        required = (
            "parcel_id",
            "UPRN",
            "FULLADDRESS",
            "POSTCODE",
            "longitude",
            "latitude",
        )
        if not record.get("exact_uprn_bound") or any(
            field not in record for field in required
        ):
            raise RuntimeError("INVALID_INPUT_ROW")
        row = {field: record[field] for field in required}
        row["UPRN"] = str(row["UPRN"])
        row["exact_uprn_bound"] = True
        row["POSTCODE"] = " ".join(str(row["POSTCODE"]).upper().split())
        row["normalized_full_address"] = normalize_text(str(row["FULLADDRESS"]))
        if row["UPRN"] not in target_uprns:
            raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
        output.append(row)
    if len({row["UPRN"] for row in output}) != 3:
        raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
    if len({row["POSTCODE"] for row in output}) != 3:
        raise RuntimeError("EXPECTED_3_DISTINCT_POSTCODES")
    return output


def read_response(response: Any) -> bytes:
    body = bytearray()
    while True:
        remaining = MAX_RESPONSE_BYTES - len(body) + 1
        chunk = response.read(min(1024 * 1024, remaining))
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_RESPONSE_BYTES:
            raise RuntimeError(
                f"RESPONSE_TOO_LARGE:{len(body)}:{MAX_RESPONSE_BYTES}"
            )
    return bytes(body)


def fetch_search_result(postcode: str, timeout: int) -> tuple[bytes, dict[str, Any]]:
    safe_url(SEARCH_URL)
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar)
    )
    get_request = urllib.request.Request(
        SEARCH_URL,
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with opener.open(get_request, timeout=timeout) as response:
        get_final_url = response.geturl()
        safe_url(get_final_url)
        get_body = read_response(response)
        get_status = int(getattr(response, "status", 200))
    parser = SearchPageParser()
    parser.feed(get_body.decode("utf-8", errors="replace"))
    if not parser.csrf_token:
        raise RuntimeError("CSRF_TOKEN_NOT_FOUND")
    token_hash = sha256_bytes(parser.csrf_token.encode("utf-8"))
    form_body = urllib.parse.urlencode(
        {
            "csrfToken": parser.csrf_token,
            "postcode": postcode,
            "Search": "",
        }
    ).encode("utf-8")
    post_request = urllib.request.Request(
        SEARCH_URL,
        data=form_body,
        method="POST",
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": SEARCH_URL,
        },
    )
    with opener.open(post_request, timeout=timeout) as response:
        post_final_url = response.geturl()
        safe_url(post_final_url)
        post_body = read_response(response)
        post_status = int(getattr(response, "status", 200))
    evidence = {
        "postcode": postcode,
        "get_request_url": SEARCH_URL,
        "get_final_url": get_final_url,
        "get_http_status": get_status,
        "get_bytes": len(get_body),
        "get_response_sha256": sha256_bytes(get_body),
        "csrf_token_present": True,
        "csrf_token_sha256": token_hash,
        "cookie_count": len(cookie_jar),
        "post_request_url": SEARCH_URL,
        "post_final_url": post_final_url,
        "post_http_status": post_status,
        "post_bytes": len(post_body),
        "post_response_sha256": sha256_bytes(post_body),
        "state": "RESPONSE",
    }
    return post_body, evidence


def extract_band_candidates(body: bytes, row: dict[str, Any]) -> list[dict[str, Any]]:
    parser = ResultRowsParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    target = row["normalized_full_address"]
    candidates: list[dict[str, Any]] = []
    for index, cells in enumerate(parser.rows, 1):
        joined = " | ".join(cells)
        normalized = normalize_text(joined)
        if target not in normalized:
            continue
        bands: set[str] = set()
        for cell in cells:
            clean = " ".join(cell.split())
            if SINGLE_BAND_RE.fullmatch(clean):
                bands.add(clean.upper())
            for match in BAND_RE.finditer(clean):
                bands.add(match.group(1).upper())
        if len(bands) != 1:
            candidates.append(
                {
                    "row_index": index,
                    "official_row_text": joined,
                    "official_row_sha256": sha256_bytes(joined.encode("utf-8")),
                    "band_values": sorted(bands),
                    "state": "INVALID_BAND_CARDINALITY",
                }
            )
            continue
        candidates.append(
            {
                "row_index": index,
                "official_row_text": joined,
                "official_row_sha256": sha256_bytes(joined.encode("utf-8")),
                "official_council_tax_band": next(iter(bands)),
                "state": "VALID_EXACT_ADDRESS_ROW",
            }
        )
    return candidates


def synthetic_result_html(row: dict[str, Any], band: str, duplicate_band: str | None = None) -> bytes:
    rows = [
        f"<tr><td>{html.escape(str(row['FULLADDRESS']))}</td><td>Band {band}</td></tr>"
    ]
    if duplicate_band:
        rows.append(
            f"<tr><td>{html.escape(str(row['FULLADDRESS']))}</td><td>Band {duplicate_band}</td></tr>"
        )
    return (
        "<!doctype html><html><body><table><thead><tr><th>Address</th><th>Council Tax band</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></body></html>"
    ).encode("utf-8")


def run(
    rows: list[dict[str, Any]],
    timeout: int,
    synthetic: bool = False,
    ambiguous: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    evidence: dict[str, Any] = {
        "accessed_at": now(),
        "search_url": SEARCH_URL,
        "get_request_count": 0,
        "post_request_count": 0,
        "requests": [],
    }
    outputs: list[dict[str, Any]] = []
    matched = 0
    synthetic_bands = ["C", "D", "E"]
    for index, row in enumerate(rows):
        try:
            if synthetic:
                body = synthetic_result_html(
                    row,
                    synthetic_bands[index],
                    duplicate_band="F" if ambiguous and index == 1 else None,
                )
                request_evidence = {
                    "postcode": row["POSTCODE"],
                    "get_request_url": SEARCH_URL,
                    "get_http_status": 200,
                    "get_response_sha256": sha256_bytes(b"synthetic-search-page"),
                    "csrf_token_present": True,
                    "csrf_token_sha256": sha256_bytes(b"synthetic-csrf-token"),
                    "cookie_count": 1,
                    "post_request_url": SEARCH_URL,
                    "post_final_url": SEARCH_URL + "?postcode=synthetic",
                    "post_http_status": 200,
                    "post_response_sha256": sha256_bytes(body),
                    "state": "SYNTHETIC_RESPONSE",
                }
            else:
                evidence["get_request_count"] += 1
                evidence["post_request_count"] += 1
                body, request_evidence = fetch_search_result(
                    row["POSTCODE"], timeout
                )
            candidates = extract_band_candidates(body, row)
            valid = [
                candidate
                for candidate in candidates
                if candidate.get("state") == "VALID_EXACT_ADDRESS_ROW"
            ]
            evidence["requests"].append(
                {
                    **request_evidence,
                    "UPRN": row["UPRN"],
                    "exact_address_candidate_count": len(candidates),
                    "valid_exact_address_band_count": len(valid),
                }
            )
            output = {
                **{key: value for key, value in row.items() if key != "normalized_full_address"},
                "source_url": request_evidence.get("post_final_url", SEARCH_URL),
                "candidate_count": len(candidates),
                "valid_candidate_count": len(valid),
                "inferred": False,
            }
            if len(candidates) == 1 and len(valid) == 1:
                output.update(
                    {
                        "state": "MATCHED_UNIQUE_HMRC_COUNCIL_TAX_EXACT_ADDRESS",
                        "official_domestic_valuation_list_presence": True,
                        "official_council_tax_band": valid[0]["official_council_tax_band"],
                        "official_address_row_text": valid[0]["official_row_text"],
                        "official_address_row_sha256": valid[0]["official_row_sha256"],
                    }
                )
                matched += 1
            elif len(candidates) > 1:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "AMBIGUOUS_MULTIPLE_EXACT_ADDRESS_COUNCIL_TAX_ROWS",
                        "candidate_row_sha256": [
                            candidate["official_row_sha256"]
                            for candidate in candidates
                        ],
                    }
                )
            elif len(candidates) == 1 and len(valid) != 1:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "EXACT_ADDRESS_ROW_HAS_INVALID_BAND_CARDINALITY",
                        "candidate_row_sha256": [
                            candidates[0]["official_row_sha256"]
                        ],
                    }
                )
            else:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "NO_EXACT_ADDRESS_COUNCIL_TAX_ROW",
                    }
                )
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            evidence["requests"].append(
                {
                    "UPRN": row["UPRN"],
                    "postcode": row["POSTCODE"],
                    "get_request_url": SEARCH_URL,
                    "post_request_url": SEARCH_URL,
                    "state": "ERROR",
                    "error": error,
                }
            )
            output = {
                **{key: value for key, value in row.items() if key != "normalized_full_address"},
                "source_url": SEARCH_URL,
                "candidate_count": 0,
                "valid_candidate_count": 0,
                "state": "NO_DATA",
                "reason": error,
                "inferred": False,
            }
        outputs.append(output)
    return evidence, outputs, matched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--synthetic-test", action="store_true")
    parser.add_argument("--synthetic-ambiguous-test", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        raise RuntimeError("INVALID_TIMEOUT")
    rows = load_rows()
    if args.validate_only:
        print(
            json.dumps(
                {
                    "valid": True,
                    "input_count": 3,
                    "target_uprns": [row["UPRN"] for row in rows],
                    "target_postcodes": [row["POSTCODE"] for row in rows],
                    "search_url": SEARCH_URL,
                    "resource_class": "network",
                    "get_request_limit": MAX_GET_REQUESTS,
                    "post_request_limit": MAX_POST_REQUESTS,
                    "max_response_bytes": MAX_RESPONSE_BYTES,
                    "write_paths": [str(path) for path in OUTPUTS],
                },
                sort_keys=True,
            )
        )
        return 0

    synthetic = args.synthetic_test or args.synthetic_ambiguous_test
    evidence, records, matched = run(
        rows,
        args.timeout,
        synthetic=synthetic,
        ambiguous=args.synthetic_ambiguous_test,
    )
    if args.synthetic_test:
        bands = [record.get("official_council_tax_band") for record in records]
        if matched != 3 or bands != ["C", "D", "E"]:
            raise RuntimeError(f"SYNTHETIC_UNIQUE_FAILED:{matched}:{bands}")
        print(
            json.dumps(
                {
                    "valid": True,
                    "matched_rows": matched,
                    "bands": bands,
                    "record_states": [record["state"] for record in records],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.synthetic_ambiguous_test:
        states = [record["state"] for record in records]
        if (
            matched != 2
            or states[1] != "NO_DATA"
            or records[1].get("reason")
            != "AMBIGUOUS_MULTIPLE_EXACT_ADDRESS_COUNCIL_TAX_ROWS"
        ):
            raise RuntimeError(
                f"SYNTHETIC_AMBIGUOUS_FAILED:{matched}:{states}"
            )
        print(
            json.dumps(
                {
                    "valid": True,
                    "matched_rows": matched,
                    "ambiguous_state": states[1],
                    "ambiguous_reason": records[1]["reason"],
                },
                sort_keys=True,
            )
        )
        return 0

    state = "PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-hmrc-council-tax-band-exact-address-v1-20260804",
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_unique_exact_address_rows": matched,
        "evidence_records": len(records),
        "source_evidence": evidence,
        "records": records,
        "estimated_bands": False,
        "unknown_fields_promoted_to_label": False,
        "fake_data": False,
        "large_raw_files_committed": False,
        "generated_at": now(),
    }
    text = canonical_json(result) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(
        json.dumps(
            {
                "completed_count": len(records),
                "target_count": 3,
                "matched_unique_exact_address_rows": matched,
                "state": state,
                "output_sha256": sha256_bytes(text.encode("utf-8")),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
