#!/usr/bin/env python3
"""Fail-closed HMLR INSPIRE ZIP resolver for height_difference_1.

The helper resolves the current Barking and Dagenham authority ZIP from the
official HMLR page, follows only the documented HMLR/S3 delivery path, safely
extracts exactly one GML member, validates native BNG polygon structure, and
writes independent byte/hash receipts. It never creates a parcel or elevation
business result.
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
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPCookieProcessor, Request, build_opener
import zipfile

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.4-exact-s3-path-native-bng-fail-closed"

HMLR_AUTHORITY = "London Borough of Barking and Dagenham"
HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
HMLR_ZIP_URL = (
    "https://use-land-property-data.service.gov.uk/datasets/inspire/download/"
    "London_Borough_of_Barking_and_Dagenham.zip"
)
HMLR_HOST = "use-land-property-data.service.gov.uk"
HMLR_ZIP_PATH = "/datasets/inspire/download/London_Borough_of_Barking_and_Dagenham.zip"
S3_HOST = "datapub-prd-s3-bucket.s3.amazonaws.com"
S3_ZIP_PATH = "/inspire/London_Borough_of_Barking_and_Dagenham.zip"
ALLOWED_ZIP_FINALS = {(HMLR_HOST, HMLR_ZIP_PATH), (S3_HOST, S3_ZIP_PATH)}

USER_AGENT = "AAYS-height-difference-hmlr-zip/1.4"
MAX_PAGE_BYTES = 20_000_000
MAX_ZIP_BYTES = 1_000_000_000
MAX_GML_BYTES = 1_000_000_000
MAX_MEMBERS = 100
MAX_COMPRESSION_RATIO = 250.0
ALLOWED_GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}


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


def sha256_values(values: Iterable[str]) -> str:
    payload = "\n".join(sorted(values)).encode("utf-8")
    return sha256_bytes(payload)


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_bytes(
        path,
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def require_https_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise EvidenceError(f"HTTPS_URL_REQUIRED:{url}")
    return parsed.netloc.lower(), parsed.path


def validate_page_final_url(url: str) -> dict[str, Any]:
    host, path = require_https_url(url)
    expected_path = urlparse(HMLR_DOWNLOAD_PAGE).path
    if host != HMLR_HOST or path != expected_path:
        raise EvidenceError(f"HMLR_PAGE_FINAL_URL_INVALID:{host}:{path}")
    return {"final_host": host, "final_path": path, "final_url_allowlisted": True}


def validate_zip_final_url(url: str) -> dict[str, Any]:
    host, path = require_https_url(url)
    if (host, path) not in ALLOWED_ZIP_FINALS:
        raise EvidenceError(f"HMLR_ZIP_FINAL_URL_INVALID:{host}:{path}")
    return {
        "final_host": host,
        "final_path": path,
        "final_host_allowlisted": True,
        "final_path_allowlisted": True,
    }


def build_http_opener():
    return build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch_bytes(
    opener: Any,
    url: str,
    *,
    timeout: int,
    retries: int,
    max_bytes: int,
) -> tuple[bytes, dict[str, str], str]:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with contextlib.closing(opener.open(request, timeout=timeout)) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise EvidenceError(f"HTTP_{status}:{url}")
                headers = {k.lower(): v for k, v in response.headers.items()}
                declared = headers.get("content-length")
                if declared:
                    try:
                        declared_size = int(declared)
                    except ValueError as exc:
                        raise EvidenceError(f"CONTENT_LENGTH_INVALID:{declared}") from exc
                    if declared_size < 0 or declared_size > max_bytes:
                        raise EvidenceError(
                            f"DECLARED_RESPONSE_SIZE_INVALID:{declared_size}>{max_bytes}"
                        )
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
                final_url = response.geturl()
            if not data:
                raise EvidenceError(f"EMPTY_RESPONSE:{url}")
            return data, headers, final_url
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
    candidates: list[str] = []
    for href in rows[0]["links"]:
        full = urljoin(HMLR_DOWNLOAD_PAGE, href)
        host, path = require_https_url(full)
        if host == HMLR_HOST and path.endswith(".zip"):
            candidates.append(full)
    if len(candidates) != 1:
        raise EvidenceError(f"HMLR_AUTHORITY_ZIP_LINK_NOT_UNIQUE:found={len(candidates)}")
    if candidates[0] != HMLR_ZIP_URL:
        raise EvidenceError(f"HMLR_AUTHORITY_ZIP_ROUTE_CHANGED:{candidates[0]}")
    return candidates[0]


def is_symlink(member: zipfile.ZipInfo) -> bool:
    mode = (member.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def validate_member_path(name: str) -> None:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts:
        raise EvidenceError(f"HMLR_ZIP_UNSAFE_MEMBER_PATH:{name}")


def validate_gml_prefix(data: bytes) -> None:
    if len(data) < 32:
        raise EvidenceError("HMLR_GML_TOO_SMALL")
    prefix = data[:4096].lstrip().lower()
    if prefix.startswith(b"<html") or b"<!doctype html" in prefix:
        raise EvidenceError("HMLR_GML_IS_HTML")
    if not (prefix.startswith(b"<?xml") or prefix.startswith(b"<")):
        raise EvidenceError("HMLR_GML_NOT_XML")


def extract_single_gml(zip_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    valid_magic = {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}
    if len(zip_bytes) < 4 or zip_bytes[:4] not in valid_magic:
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
                raise EvidenceError(
                    f"HMLR_ZIP_UNCOMPRESSED_TOO_LARGE:{total_uncompressed}"
                )
            if member.compress_size == 0 and member.file_size > 0:
                raise EvidenceError(
                    f"HMLR_ZIP_INVALID_COMPRESSION_SIZE:{member.filename}"
                )
            if member.compress_size > 0:
                ratio = member.file_size / member.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise EvidenceError(
                        f"HMLR_ZIP_COMPRESSION_RATIO_TOO_HIGH:"
                        f"{member.filename}:{ratio:.2f}"
                    )
            if member.filename.lower().endswith(".gml") and not member.is_dir():
                gml_members.append(member)
        if len(gml_members) != 1:
            raise EvidenceError(
                f"HMLR_ZIP_GML_MEMBER_NOT_UNIQUE:found={len(gml_members)}"
            )
        member = gml_members[0]
        gml_bytes = archive.read(member)
    if len(gml_bytes) > MAX_GML_BYTES:
        raise EvidenceError(f"HMLR_GML_TOO_LARGE:{len(gml_bytes)}")
    validate_gml_prefix(gml_bytes)
    return gml_bytes, {
        "member_name": member.filename,
        "member_compressed_bytes": int(member.compress_size),
        "member_uncompressed_bytes": int(member.file_size),
        "archive_member_count": len(members),
        "archive_total_uncompressed_bytes": total_uncompressed,
    }


def choose_identifier_column(columns: Iterable[str]) -> str:
    original = [str(column) for column in columns]
    lowered = {column.lower(): column for column in original}
    for key in (
        "inspireid",
        "inspire_id",
        "landregistry-inspire-id",
        "gml_id",
        "gml:id",
        "id",
    ):
        if key in lowered:
            return lowered[key]
    for column in original:
        compact = column.lower().replace("_", "").replace("-", "").replace(":", "")
        if "inspire" in compact and "id" in compact:
            return column
    raise EvidenceError("HMLR_INSPIRE_IDENTIFIER_COLUMN_NOT_RESOLVED")


def validate_gml_structure(gml_path: Path) -> dict[str, Any]:
    try:
        import geopandas as gpd  # type: ignore
    except Exception as exc:
        raise EvidenceError(f"GEOPANDAS_REQUIRED_FOR_GML_PREFLIGHT:{exc}") from exc

    gdf = gpd.read_file(gml_path)
    if gdf.empty:
        raise EvidenceError("HMLR_GML_HAS_ZERO_FEATURES")
    if gdf.crs is None or gdf.crs.to_epsg() != 27700:
        observed = str(gdf.crs) if gdf.crs is not None else None
        raise EvidenceError(f"HMLR_GML_NATIVE_CRS_NOT_EPSG27700:{observed}")

    geometry = gdf.geometry
    if geometry.isna().any() or geometry.is_empty.any():
        raise EvidenceError("HMLR_GML_EMPTY_OR_NULL_GEOMETRY")
    geometry_types = set(geometry.geom_type.astype(str))
    if not geometry_types.issubset(ALLOWED_GEOMETRY_TYPES):
        raise EvidenceError(
            "HMLR_GML_GEOMETRY_TYPE_INVALID:" + ",".join(sorted(geometry_types))
        )
    if not geometry.is_valid.all():
        raise EvidenceError("HMLR_GML_INVALID_GEOMETRY")
    areas = geometry.area
    if (areas <= 0).any():
        raise EvidenceError("HMLR_GML_NON_POSITIVE_POLYGON_AREA")

    minx, miny, maxx, maxy = [float(value) for value in gdf.total_bounds]
    if not (
        0 <= minx < maxx <= 700_000
        and 0 <= miny < maxy <= 1_300_000
    ):
        raise EvidenceError(
            f"HMLR_GML_BNG_BOUNDS_IMPLAUSIBLE:{minx},{miny},{maxx},{maxy}"
        )

    identifier_column = choose_identifier_column(gdf.columns)
    identifiers = [str(value).strip() for value in gdf[identifier_column].tolist()]
    if any(not value or value.lower() in {"none", "nan"} for value in identifiers):
        raise EvidenceError("HMLR_GML_IDENTIFIER_EMPTY")
    if len(set(identifiers)) != len(identifiers):
        raise EvidenceError("HMLR_GML_IDENTIFIER_NOT_UNIQUE")

    return {
        "feature_count": int(len(gdf)),
        "native_crs_epsg": 27700,
        "geometry_types": sorted(geometry_types),
        "valid_geometry_count": int(geometry.is_valid.sum()),
        "positive_area_count": int((areas > 0).sum()),
        "total_bounds_bng": [round(value, 3) for value in (minx, miny, maxx, maxy)],
        "identifier_column": identifier_column,
        "unique_identifier_count": len(identifiers),
        "identifier_set_sha256": sha256_values(identifiers),
    }


def expect_error(callable_obj: Any, expected: str) -> int:
    try:
        callable_obj()
    except Exception as exc:
        if expected not in str(exc):
            raise EvidenceError(
                f"SELF_TEST_WRONG_ERROR:expected={expected}:observed={exc}"
            ) from exc
        return 1
    raise EvidenceError(f"SELF_TEST_EXPECTED_ERROR_NOT_RAISED:{expected}")


def run_self_test() -> dict[str, Any]:
    checks = 0
    sample_page = (
        '<table><tr><td>London Borough of Barking and Dagenham</td>'
        '<td><a href="/datasets/inspire/download/'
        'London_Borough_of_Barking_and_Dagenham.zip">Download .gml</a>'
        "</td></tr></table>"
    ).encode()
    if discover_authority_zip(sample_page) != HMLR_ZIP_URL:
        raise EvidenceError("SELF_TEST_DISCOVERY_FAILED")
    checks += 1

    validate_page_final_url(HMLR_DOWNLOAD_PAGE)
    checks += 1
    validate_zip_final_url(HMLR_ZIP_URL)
    checks += 1
    validate_zip_final_url(
        "https://datapub-prd-s3-bucket.s3.amazonaws.com/"
        "inspire/London_Borough_of_Barking_and_Dagenham.zip"
    )
    checks += 1

    checks += expect_error(
        lambda: validate_zip_final_url(
            "https://datapub-prd-s3-bucket.s3.amazonaws.com/"
            "inspire/Other_Authority.zip"
        ),
        "HMLR_ZIP_FINAL_URL_INVALID",
    )
    checks += expect_error(
        lambda: validate_zip_final_url(
            "http://datapub-prd-s3-bucket.s3.amazonaws.com/"
            "inspire/London_Borough_of_Barking_and_Dagenham.zip"
        ),
        "HTTPS_URL_REQUIRED",
    )
    checks += expect_error(
        lambda: validate_zip_final_url(
            "https://untrusted.example/inspire/"
            "London_Borough_of_Barking_and_Dagenham.zip"
        ),
        "HMLR_ZIP_FINAL_URL_INVALID",
    )

    payload = b'<?xml version="1.0"?><gml><feature>test</feature></gml>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Land_Registry_Cadastral_Parcels.gml", payload)
    extracted, receipt = extract_single_gml(buffer.getvalue())
    if extracted != payload or receipt["archive_member_count"] != 1:
        raise EvidenceError("SELF_TEST_EXTRACTION_FAILED")
    checks += 1

    unsafe = io.BytesIO()
    with zipfile.ZipFile(unsafe, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../escape.gml", payload)
    checks += expect_error(
        lambda: extract_single_gml(unsafe.getvalue()),
        "HMLR_ZIP_UNSAFE_MEMBER_PATH",
    )

    duplicate = io.BytesIO()
    with zipfile.ZipFile(duplicate, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("a.gml", payload)
        archive.writestr("b.gml", payload)
    checks += expect_error(
        lambda: extract_single_gml(duplicate.getvalue()),
        "HMLR_ZIP_GML_MEMBER_NOT_UNIQUE",
    )

    if checks != 10:
        raise EvidenceError(f"SELF_TEST_CHECK_COUNT_INVALID:{checks}")
    return {
        "state": "PASS",
        "checks": checks,
        "script_version": SCRIPT_VERSION,
        "scope": [
            "authority-row discovery",
            "page final URL",
            "HMLR ZIP final URL",
            "S3 ZIP final URL",
            "wrong S3 object rejection",
            "HTTP rejection",
            "unknown host rejection",
            "single-GML extraction",
            "traversal rejection",
            "multiple-GML rejection",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-output", type=Path)
    parser.add_argument("--gml-output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if args.page_output is None or args.gml_output is None or args.receipt_output is None:
        raise SystemExit("--page-output, --gml-output and --receipt-output are required")

    result: dict[str, Any] = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "started_at": utc_now(),
        "state": "STARTED_FAIL_CLOSED",
        "authority": HMLR_AUTHORITY,
        "download_page_url": HMLR_DOWNLOAD_PAGE,
        "origin_zip_url": HMLR_ZIP_URL,
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
        page_bytes, page_headers, page_final_url = fetch_bytes(
            opener,
            HMLR_DOWNLOAD_PAGE,
            timeout=180,
            retries=3,
            max_bytes=MAX_PAGE_BYTES,
        )
        page_delivery = validate_page_final_url(page_final_url)
        discovered_url = discover_authority_zip(page_bytes)

        zip_bytes, zip_headers, zip_final_url = fetch_bytes(
            opener,
            discovered_url,
            timeout=300,
            retries=3,
            max_bytes=MAX_ZIP_BYTES,
        )
        zip_delivery = validate_zip_final_url(zip_final_url)
        gml_bytes, archive_receipt = extract_single_gml(zip_bytes)

        atomic_bytes(args.page_output, page_bytes)
        atomic_bytes(args.gml_output, gml_bytes)
        structure = validate_gml_structure(args.gml_output)

        result["artifacts"] = {
            "download_page": {
                "output_path": str(args.page_output),
                "sha256": sha256_bytes(page_bytes),
                "bytes": len(page_bytes),
                "content_type": page_headers.get("content-type"),
                **page_delivery,
            },
            "hmlr_zip": {
                "origin_url": discovered_url,
                "sha256": sha256_bytes(zip_bytes),
                "bytes": len(zip_bytes),
                "content_type": zip_headers.get("content-type"),
                **zip_delivery,
            },
            "hmlr_gml": {
                "output_path": str(args.gml_output),
                "sha256": sha256_bytes(gml_bytes),
                "bytes": len(gml_bytes),
                **archive_receipt,
                "structure": structure,
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
