from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

ROOT = Path.cwd()
BASE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave140_official_hmlr_inspire_os_open_uprn_primary_binding_20260801.py"
spec = importlib.util.spec_from_file_location("wave140_base", BASE)
w = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(w)

ATTEMPT_ONE_OUTPUT = w.OUTPUT
EXPECTED_OS_SHA256 = "d3816e7dd53b97a46092da0db919561502da2115ac6d003204d692e2c2e5ba07"
EXPECTED_OS_MIN_BYTES = 500_000_000
EXPECTED_OS_MIN_ROWS = 40_000_000


def discover_hmlr_zip_links():
    try:
        response = w.req(w.HMLR_PAGE, timeout=(20, 120))
        text = response.text
        soup = BeautifulSoup(text, "html.parser")
        selected = {}
        diagnostic_rows = []
        for row in soup.select("tr.govuk-table__row"):
            row_text = " ".join(row.stripped_strings)
            link = row.select_one("a[href]")
            if link is None:
                continue
            href = urljoin(response.url, link.get("href") or "")
            diagnostic_rows.append({
                "row_text": row_text[:300],
                "href": href,
                "data_ga_download": link.get("data-ga-download"),
            })
            for authority in w.AUTHORITIES:
                if authority.lower() not in row_text.lower():
                    continue
                if not href.lower().endswith(".zip"):
                    continue
                selected[authority] = {
                    "authority": authority,
                    "url": href,
                    "download_name": link.get("data-ga-download"),
                    "row_text": row_text[:400],
                }
        manifest = {
            "ok": True,
            "page_url": response.url,
            "page_sha256": w.sha_bytes(text.encode()),
            "selected": sorted(selected),
            "selected_count": len(selected),
            "zip_links": [selected[key] for key in sorted(selected)],
            "table_rows_scanned": len(diagnostic_rows),
            "repair": "ROW_SCOPED_HREF_ZIP_DISCOVERY",
        }
        w.log("hmlr_zip_discovery", response.url, True, manifest)
        return manifest, [selected[key] for key in sorted(selected)]
    except Exception as exc:
        result = {
            "ok": False,
            "page_url": w.HMLR_PAGE,
            "selected": [],
            "selected_count": 0,
            "error": f"{type(exc).__name__}:{exc}",
        }
        w.log("hmlr_zip_discovery", w.HMLR_PAGE, False, result, result["error"])
        return result, []


def parse_hmlr_zip(tmp: Path, link: dict):
    slug = re.sub(r"[^a-z0-9]+", "_", link["authority"].lower()).strip("_")
    archive = tmp / f"hmlr_{slug}.zip"
    download = w.download(link["url"], archive, w.MAX_GML_BYTES, "hmlr_gml_zip")
    download["authority"] = link["authority"]
    download["download_name"] = link.get("download_name")
    if not download.get("ok"):
        return download, None
    try:
        with zipfile.ZipFile(archive) as zf:
            candidates = [
                member for member in zf.infolist()
                if not member.is_dir() and member.filename.lower().endswith(".gml")
            ]
            if not candidates:
                raise RuntimeError("HMLR_GML_MEMBER_NOT_FOUND")
            member = max(candidates, key=lambda item: item.file_size)
            if member.file_size <= 0 or member.file_size > w.MAX_GML_BYTES:
                raise RuntimeError(f"HMLR_GML_MEMBER_SIZE_INVALID:{member.file_size}")
            gml_path = tmp / f"hmlr_{slug}.gml"
            digest = hashlib.sha256()
            total = 0
            with zf.open(member) as source, gml_path.open("wb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > w.MAX_GML_BYTES:
                        raise RuntimeError(f"HMLR_GML_UNCOMPRESSED_LIMIT:{total}")
                    target.write(chunk)
                    digest.update(chunk)
            prefix = gml_path.read_bytes()[:4096].lstrip().lower()
            if b"<html" in prefix or not (b"<?xml" in prefix or b"featurecollection" in prefix or b"gml" in prefix):
                raise RuntimeError("HMLR_MEMBER_NOT_XML_GML")
            download.update({
                "gml_member": member.filename,
                "gml_uncompressed_bytes": total,
                "gml_sha256": digest.hexdigest(),
                "zip_member_count": len(zf.infolist()),
                "validated_gml": True,
            })
        parsed = w.parse_gml(gml_path, link["authority"])
        if parsed.get("members_scanned", 0) <= 0 or parsed.get("poslists_scanned", 0) <= 0:
            raise RuntimeError(
                f"HMLR_GML_EMPTY_PARSE:{parsed.get('members_scanned')}:{parsed.get('poslists_scanned')}"
            )
        w.log(
            "hmlr_zip_gml_validated",
            link["authority"],
            True,
            {
                "archive_sha256": download.get("sha256"),
                "gml_sha256": download.get("gml_sha256"),
                "members": parsed.get("members_scanned"),
                "poslists": parsed.get("poslists_scanned"),
            },
        )
        return download, parsed
    except Exception as exc:
        download.update({
            "ok": False,
            "validated_gml": False,
            "error": f"{type(exc).__name__}:{exc}",
        })
        w.log("hmlr_zip_gml_validated", link["authority"], False, download, download["error"])
        return download, None


def repaired_process_hmlr(tmp: Path):
    manifest, links = discover_hmlr_zip_links()
    downloads = []
    parses = []
    if links:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(links))) as pool:
            for download, parsed in pool.map(lambda item: parse_hmlr_zip(tmp, item), links):
                downloads.append(download)
                if parsed:
                    parses.append(parsed)
    return manifest, downloads, parses


def reuse_verified_os_open_uprn(_tmp: Path):
    prior = json.loads(ATTEMPT_ONE_OUTPUT.read_text())
    manifest = dict(prior["os_open_uprn_manifest"])
    candidates = [
        {
            key: value
            for key, value in row.items()
            if key not in {"lsoa11_codes", "lsoa21_codes", "official_expected_pair", "official_competing_pair"}
        }
        for row in prior["os_open_uprn_candidates"]
    ]
    if manifest.get("sha256") != EXPECTED_OS_SHA256:
        raise RuntimeError("OS_OPEN_UPRN_ATTEMPT_ONE_SHA_MISMATCH")
    if int(manifest.get("bytes", 0)) < EXPECTED_OS_MIN_BYTES:
        raise RuntimeError("OS_OPEN_UPRN_ATTEMPT_ONE_BYTE_GATE_FAILED")
    if int(manifest.get("rows_scanned", 0)) < EXPECTED_OS_MIN_ROWS:
        raise RuntimeError("OS_OPEN_UPRN_ATTEMPT_ONE_ROW_GATE_FAILED")
    manifest.update({
        "reused_verified_attempt_001": True,
        "repair_scope": "HMLR_ONLY",
        "reuse_validation": {
            "expected_sha256": EXPECTED_OS_SHA256,
            "minimum_bytes": EXPECTED_OS_MIN_BYTES,
            "minimum_rows": EXPECTED_OS_MIN_ROWS,
            "candidate_rows": len(candidates),
        },
    })
    w.log(
        "os_open_uprn_verified_reuse",
        manifest.get("final_url") or manifest.get("requested_url"),
        True,
        {
            "sha256": manifest["sha256"],
            "bytes": manifest["bytes"],
            "rows_scanned": manifest["rows_scanned"],
            "candidate_rows": len(candidates),
        },
    )
    return manifest, candidates


w.discover_hmlr = discover_hmlr_zip_links
w.process_hmlr = repaired_process_hmlr
w.process_uprn = reuse_verified_os_open_uprn

if __name__ == "__main__":
    w.main()
