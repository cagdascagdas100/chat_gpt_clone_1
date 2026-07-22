#!/usr/bin/env python3
"""Resolve the current HMLR Barking and Dagenham INSPIRE ZIP and extract one GML.

Fail closed: the official page row, ZIP route, redirect host, archive structure,
GML bytes and hashes must all validate. No parcel geometry or elevation result is
produced by this helper.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import html.parser
import http.cookiejar
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import time
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener
import zipfile

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.2-hmlr-zip-redirect-host-fail-closed"
HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
HMLR_AUTHORITY = "London Borough of Barking and Dagenham"
HMLR_ORIGIN_HOST = "use-land-property-data.service.gov.uk"
HMLR_OBJECT_HOST = "datapub-prd-s3-bucket.s3.amazonaws.com"
HMLR_ZIP_ALLOWED_FINAL_HOSTS = {HMLR_ORIGIN_HOST, HMLR_OBJECT_HOST}
HMLR_ZIP_URL = (
    "https://use-land-property-data.service.gov.uk/datasets/inspire/download/"
    "London_Borough_of_Barking_and_Dagenham.zip"
)
USER_AGENT = "AAYS-height-difference-hmlr-zip/1.2"
MAX_PAGE_BYTES = 20_000_000
MAX_ZIP_BYTES = 1_000_000_000
MAX_GML_BYTES = 1_000_000_000
MAX_MEMBERS = 100
MAX_COMPRESSION_RATIO = 250.0


class EvidenceError(RuntimeError):
    pass


class TableLinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.rows: list[dict[str, Any]] = []
        self._text: list[str] = []
        self._links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self.in_row = True
            self._text, self._links = [], []
        elif self.in_row and tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self._links.append(href)

    def handle_data(self, data: str) -> None:
        if self.in_row and data.strip():
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.in_row:
            self.rows.append({"text": " ".join(self._text), "links": self._links[:]})
            self.in_row = False


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    atomic_bytes(path, encoded)


def build_http_opener():
    jar = http.cookiejar.CookieJar()
    return build_opener(HTTPCookieProcessor(jar))


def validate_final_url(final_url: str, allowed_hosts: set[str], label: str) -> str:
    parsed = urlparse(final_url)
    if parsed.scheme != "https":
        raise EvidenceError(f"{label}_FINAL_URL_NOT_HTTPS:{parsed.scheme}")
    host = (parsed.hostname or "").lower()
    if host not in allowed_hosts:
        raise EvidenceError(f"{label}_FINAL_HOST_NOT_ALLOWED:{host}")
    return host


def fetch_bytes(
    opener: Any,
    url: str,
    *,
    timeout: int,
    retries: int,
    max_bytes: int,
    allowed_final_hosts: set[str],
    label: str,
):
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with contextlib.closing(opener.open(request, timeout=timeout)) as response:
                status_code = getattr(response, "status", 200)
                if status_code != 200:
                    raise EvidenceError(f"HTTP_{status_code}:{url}")
                headers = {k.lower(): v for k, v in response.headers.items()}
                declared = headers.get("content-length")
                if declared and int(declared) > max_bytes:
                    raise EvidenceError(f"DECLARED_RESPONSE_TOO_LARGE:{declared}>{max_bytes}")
                final_url = response.geturl()
                final_host = validate_final_url(final_url, allowed_final_hosts, label)
                chunks: list[bytes] = []
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise EvidenceError(f"RESPONSE_TOO_LARGE:{total}>{max_bytes}")
                    chunks.append(chunk)
                data = b"".join(chunks)
            if not data:
                raise EvidenceError(f"EMPTY_RESPONSE:{url}")
            return data, headers, final_url, final_host
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(attempt * 3)
    raise EvidenceError(f"DOWNLOAD_FAILED:{url}:{last}")


def discover_authority_zip(page_bytes: bytes) -> str:
    parser = TableLinkParser()
    parser.feed(page_bytes.decode("utf-8", errors="replace"))
    rows = [row for row in parser.rows if HMLR_AUTHORITY.lower() in row["text"].lower()]
    if len(rows) != 1:
        raise EvidenceError(f"HMLR_AUTHORITY_ROW_NOT_UNIQUE:found={len(rows)}")
    candidates = []
    for href in rows[0]["links"]:
        full = urljoin(HMLR_DOWNLOAD_PAGE, href)
        parsed = urlparse(full)
        if (
            parsed.scheme == "https"
            and parsed.netloc == HMLR_ORIGIN_HOST
            and parsed.path.endswith(".zip")
        ):
            candidates.append(full)
    if len(candidates) != 1:
        raise EvidenceError(f"HMLR_AUTHORITY_ZIP_LINK_NOT_UNIQUE:found={len(candidates)}")
    if candidates[0] != HMLR_ZIP_URL:
        raise EvidenceError(f"HMLR_AUTHORITY_ZIP_ROUTE_CHANGED:{candidates[0]}")
    return candidates[0]


def validate_gml_bytes(data: bytes) -> None:
    if len(data) < 32:
        raise EvidenceError("HMLR_GML_TOO_SMALL")
    prefix = data[:2048].lstrip().lower()
    if prefix.startswith(b"<html") or b"<!doctype html" in prefix:
        raise EvidenceError("HMLR_GML_IS_HTML")
    if not (prefix.startswith(b"<?xml") or prefix.startswith(b"<")):
        raise EvidenceError("HMLR_GML_NOT_XML")


def is_symlink(member: zipfile.ZipInfo) -> bool:
    mode = (member.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def validate_member_path(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise EvidenceError(f"HMLR_ZIP_UNSAFE_MEMBER_PATH:{name}")


def extract_single_gml(zip_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    if len(zip_bytes) < 4 or zip_bytes[:4] not in {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}:
        raise EvidenceError("HMLR_RESPONSE_NOT_ZIP_MAGIC")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        members = archive.infolist()
        if not members or len(members) > MAX_MEMBERS:
            raise EvidenceError(f"HMLR_ZIP_MEMBER_COUNT_INVALID:{len(members)}")
        total_uncompressed = 0
        gml_members: list[zipfile.ZipInfo] = []
        for member in members:
            validate_member_path(member.filename)
            if member.flag_bits & 0x1:
                raise EvidenceError(f"HMLR_ZIP_ENCRYPTED_MEMBER:{member.filename}")
            if is_symlink(member):
                raise EvidenceError(f"HMLR_ZIP_SYMLINK_MEMBER:{member.filename}")
            total_uncompressed += int(member.file_size)
            if total_uncompressed > MAX_GML_BYTES:
                raise EvidenceError(f"HMLR_ZIP_UNCOMPRESSED_TOO_LARGE:{total_uncompressed}")
            if member.compress_size == 0 and member.file_size > 0:
                raise EvidenceError(f"HMLR_ZIP_INVALID_COMPRESSION_SIZE:{member.filename}")
            if member.compress_size > 0:
                ratio = member.file_size / member.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise EvidenceError(f"HMLR_ZIP_COMPRESSION_RATIO_TOO_HIGH:{member.filename}:{ratio:.2f}")
            if member.filename.lower().endswith(".gml") and not member.is_dir():
                gml_members.append(member)
        if len(gml_members) != 1:
            raise EvidenceError(f"HMLR_ZIP_GML_MEMBER_NOT_UNIQUE:found={len(gml_members)}")
        member = gml_members[0]
        gml_bytes = archive.read(member)
    if len(gml_bytes) > MAX_GML_BYTES:
        raise EvidenceError(f"HMLR_GML_TOO_LARGE:{len(gml_bytes)}")
    validate_gml_bytes(gml_bytes)
    return gml_bytes, {
        "member_name": member.filename,
        "member_compressed_bytes": int(member.compress_size),
        "member_uncompressed_bytes": int(member.file_size),
        "archive_member_count": len(members),
        "archive_total_uncompressed_bytes": total_uncompressed,
    }


def run_self_test() -> dict[str, Any]:
    sample_page = (
        '<table><tr><td>London Borough of Barking and Dagenham</td>'
        '<td><a href="/datasets/inspire/download/'
        'London_Borough_of_Barking_and_Dagenham.zip">Download .gml</a></td></tr></table>'
    ).encode()
    if discover_authority_zip(sample_page) != HMLR_ZIP_URL:
        raise EvidenceError("SELF_TEST_DISCOVERY_FAILED")
    if validate_final_url(HMLR_DOWNLOAD_PAGE, {HMLR_ORIGIN_HOST}, "PAGE") != HMLR_ORIGIN_HOST:
        raise EvidenceError("SELF_TEST_PAGE_HOST_FAILED")
    sample_signed = (
        "https://datapub-prd-s3-bucket.s3.amazonaws.com/inspire/"
        "London_Borough_of_Barking_and_Dagenham.zip?X-Amz-Expires=60"
    )
    if validate_final_url(sample_signed, HMLR_ZIP_ALLOWED_FINAL_HOSTS, "ZIP") != HMLR_OBJECT_HOST:
        raise EvidenceError("SELF_TEST_OBJECT_HOST_FAILED")
    try:
        validate_final_url("https://example.com/redirect.zip", HMLR_ZIP_ALLOWED_FINAL_HOSTS, "ZIP")
    except EvidenceError:
        pass
    else:
        raise EvidenceError("SELF_TEST_UNKNOWN_HOST_NOT_REJECTED")
    payload = b'<?xml version="1.0"?><gml><feature>test</feature></gml>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Land_Registry_Cadastral_Parcels.gml", payload)
    extracted, receipt = extract_single_gml(buffer.getvalue())
    if extracted != payload or receipt["archive_member_count"] != 1:
        raise EvidenceError("SELF_TEST_EXTRACTION_FAILED")
    return {"state": "PASS", "checks": 6, "script_version": SCRIPT_VERSION}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-output", type=Path, required=False)
    parser.add_argument("--gml-output", type=Path, required=False)
    parser.add_argument("--receipt-output", type=Path, required=False)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0

    if args.page_output is None or args.gml_output is None or args.receipt_output is None:
        raise SystemExit("--page-output, --gml-output and --receipt-output are required")

    result: dict[str, Any] = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "started_at": utc_now(),
        "state": "STARTED_FAIL_CLOSED",
        "authority": HMLR_AUTHORITY,
        "download_page_url": HMLR_DOWNLOAD_PAGE,
        "origin_zip_url": HMLR_ZIP_URL,
        "allowed_zip_final_hosts": sorted(HMLR_ZIP_ALLOWED_FINAL_HOSTS),
        "artifacts": {},
        "errors": [],
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    try:
        opener = build_http_opener()
        page_bytes, page_headers, page_final_url, page_final_host = fetch_bytes(
            opener,
            HMLR_DOWNLOAD_PAGE,
            timeout=180,
            retries=3,
            max_bytes=MAX_PAGE_BYTES,
            allowed_final_hosts={HMLR_ORIGIN_HOST},
            label="HMLR_PAGE",
        )
        discovered_url = discover_authority_zip(page_bytes)
        zip_bytes, zip_headers, zip_final_url, zip_final_host = fetch_bytes(
            opener,
            discovered_url,
            timeout=300,
            retries=3,
            max_bytes=MAX_ZIP_BYTES,
            allowed_final_hosts=HMLR_ZIP_ALLOWED_FINAL_HOSTS,
            label="HMLR_ZIP",
        )
        gml_bytes, archive_receipt = extract_single_gml(zip_bytes)
        atomic_bytes(args.page_output, page_bytes)
        atomic_bytes(args.gml_output, gml_bytes)
        result["artifacts"] = {
            "download_page": {
                "output_path": str(args.page_output),
                "sha256": sha256_bytes(page_bytes),
                "bytes": len(page_bytes),
                "content_type": page_headers.get("content-type"),
                "final_host": page_final_host,
            },
            "hmlr_zip": {
                "origin_url": discovered_url,
                "final_host": zip_final_host,
                "final_host_allowlisted": True,
                "sha256": sha256_bytes(zip_bytes),
                "bytes": len(zip_bytes),
                "content_type": zip_headers.get("content-type"),
            },
            "hmlr_gml": {
                "output_path": str(args.gml_output),
                "sha256": sha256_bytes(gml_bytes),
                "bytes": len(gml_bytes),
                **archive_receipt,
            },
        }
        result["state"] = "COMPLETED_ZIP_AND_GML_VERIFIED"
    except Exception as exc:
        result["state"] = "BLOCKED_FAIL_CLOSED"
        result["errors"].append(str(exc))
        with contextlib.suppress(FileNotFoundError):
            args.page_output.unlink()
        with contextlib.suppress(FileNotFoundError):
            args.gml_output.unlink()
    finally:
        result["finished_at"] = utc_now()
        atomic_json(args.receipt_output, result)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"SCRIPT_VERSION={SCRIPT_VERSION}")
    print(f"STATE={result['state']}")
    print(f"PAGE_OUTPUT={args.page_output}")
    print(f"GML_OUTPUT={args.gml_output}")
    print("FINAL_READY=false")
    return 0 if result["state"] == "COMPLETED_ZIP_AND_GML_VERIFIED" else 2


if __name__ == "__main__":
    sys.exit(main())
