#!/usr/bin/env python3
"""Download current HMLR INSPIRE files for validated starter candidates.

Only a unique normalized local-authority match is accepted. Entry links are
restricted to the official HMLR host; the known HMLR signed S3 distribution
redirect is also accepted. Downloads are hashed and inspected; ambiguous links,
HTML error pages and unsafe archives fail closed. Network downloads and extracted
vectors are materialized atomically. No parcel measurement is produced here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests

DEFAULT_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
HMLR_SIGNED_DOWNLOAD_HOST = "datapub-prd-s3-bucket.s3.amazonaws.com"
TRUSTED_DOWNLOAD_HOSTS = {OFFICIAL_HOST, HMLR_SIGNED_DOWNLOAD_HOST}
MAX_DOWNLOAD_BYTES = 1_500_000_000
MAX_EXTRACTED_BYTES = 2_000_000_000


class AnchorParser(HTMLParser):
    """Capture links with conservative table/list-row context."""

    BLOCK_TAGS = {"tr", "li"}

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, str]] = []
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self._block_tag: str | None = None
        self._block_text: list[str] = []
        self._block_links: list[tuple[str, str]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        lower = tag.lower()
        if lower in self.BLOCK_TAGS and self._block_tag is None:
            self._block_tag = lower
            self._block_text = []
            self._block_links = []
        if lower == "a":
            self._href = dict(attrs).get("href")
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._block_tag is not None:
            self._block_text.append(data)
        if self._href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "a" and self._href is not None:
            anchor = " ".join(self._anchor_text).strip()
            if self._block_tag is not None:
                self._block_links.append((anchor, self._href))
            else:
                self.links.append((anchor, self._href, anchor))
            self._href = None
            self._anchor_text = []
        if self._block_tag == lower:
            context = " ".join(self._block_text).strip()
            for anchor, href in self._block_links:
                self.links.append((context, href, anchor))
            self._block_tag = None
            self._block_text = []
            self._block_links = []


def _normal_authority(value: Any) -> str:
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").casefold(),
    ).strip()
    return " ".join(text.split())


def _authority_key(value: Any) -> str:
    text = _normal_authority(value)
    prefixes = (
        "the ",
        "city of ",
        "london borough of ",
        "royal borough of ",
        "metropolitan borough of ",
    )
    changed = True
    while changed:
        changed = False
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                changed = True
                break
    suffixes = (
        " metropolitan borough council",
        " london borough council",
        " borough council",
        " district council",
        " city council",
        " county council",
        " council",
    )
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                changed = True
                break
    return text


def _context_authority_key(context: str, anchor_text: str) -> str:
    context_norm = _normal_authority(context)
    anchor_norm = _normal_authority(anchor_text)
    if anchor_norm and context_norm.endswith(anchor_norm):
        context_norm = context_norm[: -len(anchor_norm)].strip()
    return _authority_key(context_norm)


def _official_entry(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == OFFICIAL_HOST
    )


def _trusted_download(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in TRUSTED_DOWNLOAD_HOSTS
    )


def _slug(value: str) -> str:
    return (
        re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
        or "authority"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    values = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("starter manifest has no candidates")
    result = []
    for index, value in enumerate(values, 1):
        row = dict(value)
        authority = str(row.get("local_authority_name", "")).strip()
        if not authority:
            raise ValueError(
                f"candidate {index} lacks local_authority_name"
            )
        if "row_no" not in row or "parcel_id" not in row:
            raise ValueError(
                f"candidate {index} lacks row_no or parcel_id"
            )
        result.append(row)
    return result


def _stream_download(
    session: requests.Session,
    url: str,
    output: Path,
    timeout: int,
) -> dict[str, Any]:
    """Download to a temporary file and atomically replace the final path."""
    if not _official_entry(url):
        raise ValueError(
            "HMLR download URL is not the pinned official entry host"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output.name}_",
        suffix=".download.tmp",
        dir=output.parent,
    )
    os.close(fd)
    temp = Path(temp_name)
    total = 0
    resolved_url = ""
    content_type = ""
    try:
        with session.get(
            url,
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        ) as response:
            response.raise_for_status()
            if not _trusted_download(response.url):
                raise ValueError(
                    "HMLR download redirected to untrusted host: "
                    f"{response.url}"
                )
            resolved_url = response.url
            content_type = response.headers.get("content-type", "")
            with temp.open("wb") as handle:
                for chunk in response.iter_content(1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError(
                            "HMLR download exceeds safety size limit"
                        )
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if total == 0:
            raise ValueError("HMLR download is empty")
        temp.replace(output)
        return {
            "resolved_url": resolved_url,
            "resolved_host": urlparse(resolved_url).hostname,
            "content_type": content_type,
            "size_bytes": total,
            "trusted_redirect": True,
            "atomic_materialization": True,
        }
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _safe_extract_gml(
    archive: Path,
    output_dir: Path,
) -> list[Path]:
    """Extract accepted vector members with per-file atomic replacement."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    total = 0
    seen_targets: set[str] = set()
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            suffix = Path(info.filename).suffix.lower()
            if info.is_dir() or suffix not in {".gml", ".xml"}:
                continue
            if info.file_size < 0:
                raise ValueError(
                    f"HMLR archive member has invalid size: {info.filename}"
                )
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError(
                    "HMLR archive exceeds extracted-size safety limit"
                )
            name = Path(info.filename).name
            folded = name.casefold()
            if folded in seen_targets:
                raise ValueError(
                    "HMLR archive contains duplicate flattened vector name: "
                    f"{name}"
                )
            seen_targets.add(folded)
            target = output_dir / name
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}_",
                suffix=".extract.tmp",
                dir=output_dir,
            )
            os.close(fd)
            temp = Path(temp_name)
            try:
                written = 0
                with (
                    zf.open(info) as source,
                    temp.open("wb") as destination,
                ):
                    while chunk := source.read(1024 * 1024):
                        written += len(chunk)
                        if written > info.file_size:
                            raise ValueError(
                                "HMLR member expanded beyond declared size: "
                                f"{info.filename}"
                            )
                        destination.write(chunk)
                    destination.flush()
                    os.fsync(destination.fileno())
                if written != info.file_size:
                    raise ValueError(
                        "HMLR member size mismatch after extraction: "
                        f"{info.filename} expected={info.file_size} "
                        f"actual={written}"
                    )
                temp.replace(target)
            except Exception:
                temp.unlink(missing_ok=True)
                raise
            extracted.append(target)
    if not extracted:
        raise ValueError(
            "HMLR archive contains no GML/XML file"
        )
    return extracted


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--starter-manifest",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--download-page",
        default=DEFAULT_PAGE,
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--user-agent",
        default="TerraYield-AAYS/height_difference_3",
    )
    args = parser.parse_args(argv)

    if not _official_entry(args.download_page):
        raise ValueError(
            "HMLR download page is not the pinned official host"
        )

    candidates = _load_candidates(args.starter_manifest)
    authorities = sorted(
        {
            str(row["local_authority_name"]).strip()
            for row in candidates
        }
    )
    session = requests.Session()
    session.headers.update(
        {"User-Agent": args.user_agent}
    )
    page_response = session.get(
        args.download_page,
        timeout=args.timeout,
        allow_redirects=True,
    )
    page_response.raise_for_status()
    if not _official_entry(page_response.url):
        raise ValueError(
            "HMLR download page redirected off official host: "
            f"{page_response.url}"
        )
    page_body = page_response.content
    parser_html = AnchorParser()
    parser_html.feed(
        page_body.decode("utf-8", errors="replace")
    )

    records = []
    vector_paths: list[str] = []
    blocked = []
    for authority in authorities:
        target_key = _authority_key(authority)
        if not target_key:
            raise ValueError(
                f"authority normalizes to empty key: {authority!r}"
            )
        matches = []
        for context, href, anchor_text in parser_html.links:
            if not href:
                continue
            resolved = urljoin(page_response.url, href)
            if not _official_entry(resolved):
                continue
            context_key = _context_authority_key(
                context,
                anchor_text,
            )
            href_key = _authority_key(
                Path(urlparse(resolved).path).stem
            )
            if target_key in {context_key, href_key}:
                matches.append(
                    {
                        "context": context,
                        "anchor_text": anchor_text,
                        "url": resolved,
                        "target_authority_key": target_key,
                        "context_authority_key": context_key,
                        "href_authority_key": href_key,
                        "match_method": (
                            "EXACT_NORMALIZED_AUTHORITY_CONTEXT_OR_HREF"
                        ),
                    }
                )
        unique = {
            item["url"]: item
            for item in matches
        }
        matches = list(unique.values())
        if len(matches) != 1:
            blocked.append(
                {
                    "authority": authority,
                    "status": "NO_UNIQUE_EXACT_DOWNLOAD_LINK",
                    "target_authority_key": target_key,
                    "matches": matches,
                }
            )
            continue

        match = matches[0]
        authority_dir = (
            args.output_dir
            / "hmlr"
            / _slug(authority)
        )
        raw_path = authority_dir / "source_download"
        meta = _stream_download(
            session,
            match["url"],
            raw_path,
            args.timeout,
        )
        with raw_path.open("rb") as handle:
            head = handle.read(512).lstrip().lower()
        if (
            head.startswith(b"<html")
            or b"<!doctype html" in head
        ):
            raw_path.unlink(missing_ok=True)
            raise ValueError(
                f"HMLR source for {authority} returned HTML "
                "instead of GML/archive"
            )

        if zipfile.is_zipfile(raw_path):
            vectors = _safe_extract_gml(
                raw_path,
                authority_dir / "extracted",
            )
            container_type = "zip"
        else:
            suffix = Path(
                urlparse(match["url"]).path
            ).suffix.lower()
            final_path = authority_dir / (
                "source.gml"
                if suffix not in {".gml", ".xml"}
                else f"source{suffix}"
            )
            raw_path.replace(final_path)
            vectors = [final_path]
            container_type = "direct"

        vector_info = []
        for vector in vectors:
            info = {
                "path": str(vector),
                "size_bytes": vector.stat().st_size,
                "sha256": _sha256(vector),
                "atomic_materialization": True,
            }
            vector_info.append(info)
            vector_paths.append(str(vector))
        records.append(
            {
                "authority": authority,
                "normalized_authority_key": target_key,
                "authority_match_method": match[
                    "match_method"
                ],
                "download_link": match,
                "resolved_url": meta["resolved_url"],
                "resolved_host": meta["resolved_host"],
                "trusted_redirect": meta[
                    "trusted_redirect"
                ],
                "content_type": meta["content_type"],
                "container_type": container_type,
                "vectors": vector_info,
            }
        )

    status = (
        "READY"
        if len(records) == len(authorities) and not blocked
        else "BLOCKED_HMLR_SOURCE_PREPARATION"
    )
    payload = {
        "schema_version": 4,
        "slot_id": "height_difference_3",
        "status": status,
        "download_page": args.download_page,
        "download_page_resolved_url": page_response.url,
        "download_page_sha256": hashlib.sha256(
            page_body
        ).hexdigest(),
        "official_entry_host": OFFICIAL_HOST,
        "trusted_download_hosts": sorted(
            TRUSTED_DOWNLOAD_HOSTS
        ),
        "candidate_count": len(candidates),
        "authority_count": len(authorities),
        "prepared_authority_count": len(records),
        "records": records,
        "blocked": blocked,
        "vector_paths": vector_paths,
        "authority_match_policy": (
            "EXACT_NORMALIZED_AUTHORITY_CONTEXT_OR_HREF_ONLY"
        ),
        "nearest_or_fuzzy_authority_match_used": False,
        "atomic_download_materialization": True,
        "atomic_vector_materialization": True,
        "duplicate_flattened_vector_names_forbidden": True,
        "partial_canonical_source_files_forbidden": True,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output = (
        args.output_dir
        / "hmlr_source_manifest.json"
    )
    _write(output, payload)
    print(
        json.dumps(
            {
                "ok": status == "READY",
                "status": status,
                "manifest": str(output),
                "atomic_source_materialization": True,
            }
        )
    )
    return 0 if status == "READY" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        f"{type(exc).__name__}: {exc}"
                    ),
                }
            ),
            file=sys.stderr,
        )
        raise
