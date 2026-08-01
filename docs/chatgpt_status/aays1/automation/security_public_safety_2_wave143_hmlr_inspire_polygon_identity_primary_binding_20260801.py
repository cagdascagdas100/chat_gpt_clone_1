from __future__ import annotations

import hashlib
import os
import subprocess
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

SOURCE_BLOB_SHA1 = "80839cc10a367077046d6e67cd614140a9b11aaf"
EXPECTED_PREVIOUS_CONTINUATION = (
    "fe1d2a0b5bcf7a6f8c14e5f5f83f1226d221d19de1ae934e6fae33c6ebc7f7df"
)
CURRENT_ONS_LAD_ITEM_ID = "2baad669eaea4cb99a88cffb0d366a41"
CURRENT_ONS_LAD_LAYER_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
    "Local_Authority_Districts_DEC_2025_Boundaries_UK_BFC/FeatureServer/0"
)
CURRENT_ONS_LAD_QUERIES = [
    f"id:{CURRENT_ONS_LAD_ITEM_ID}",
    'owner:ONSGeography "Local Authority Districts" "December 2025"',
    '"Local Authority Districts (December 2025) Boundaries UK BFC"',
    'owner:ONSGeography LAD_DEC_2025_UK_BFC',
    '"LAD_DEC_2025_UK_BFC" "Feature Service"',
    '"Local Authority Districts" "Boundaries UK BFC" owner:ONSGeography',
]


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def load_immutable_source() -> bytes:
    result = subprocess.run(
        ["git", "cat-file", "-p", SOURCE_BLOB_SHA1],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    source = result.stdout
    actual_blob_sha1 = git_blob_sha1(source)
    if actual_blob_sha1 != SOURCE_BLOB_SHA1:
        raise RuntimeError(
            f"IMMUTABLE_SOURCE_BLOB_MISMATCH:{actual_blob_sha1}:{SOURCE_BLOB_SHA1}"
        )
    return source


def install_current_ons_lad_source(namespace: dict[str, object]) -> None:
    original_search = namespace.get("search")
    original_resolve = namespace.get("resolve")
    if not callable(original_search) or not callable(original_resolve):
        raise RuntimeError("WAVE143_SOURCE_FUNCTIONS_NOT_CALLABLE")

    namespace["QUERIES"] = list(CURRENT_ONS_LAD_QUERIES)

    def recovered_search(query: str) -> dict[str, object]:
        result = original_search(query)
        if query != CURRENT_ONS_LAD_QUERIES[0]:
            return result
        official_item = {
            "id": CURRENT_ONS_LAD_ITEM_ID,
            "owner": "ONSGeography",
            "type": "Feature Service",
            "title": "Local Authority Districts (December 2025) Boundaries UK BFC",
            "url": CURRENT_ONS_LAD_LAYER_URL.rsplit("/", 1)[0],
            "modified": 1777452587000,
        }
        rows = list(result.get("results") or [])
        if not any(str(row.get("id")) == CURRENT_ONS_LAD_ITEM_ID for row in rows):
            rows.append(official_item)
        result["results"] = rows
        result["total"] = max(int(result.get("total") or 0), len(rows))
        return result

    def recovered_resolve(item: dict[str, object]) -> dict[str, object]:
        if str(item.get("id") or "") != CURRENT_ONS_LAD_ITEM_ID:
            return original_resolve(item)
        probe = namespace["jget"]("wave143_ons_layer", CURRENT_ONS_LAD_LAYER_URL)
        return {
            "item_id": CURRENT_ONS_LAD_ITEM_ID,
            "title": "Local Authority Districts (December 2025) Boundaries UK BFC",
            "modified": 1777452587000,
            "layer_url": CURRENT_ONS_LAD_LAYER_URL,
            "layer_ok": bool(probe.get("ok")),
        }

    namespace["search"] = recovered_search
    namespace["resolve"] = recovered_resolve


def install_hmlr_gml_recovery(namespace: dict[str, object]) -> None:
    original_bget = namespace.get("bget")
    original_core = namespace.get("core")
    original_scan_gml = namespace.get("scan_gml")
    if not callable(original_bget) or not callable(original_core) or not callable(original_scan_gml):
        raise RuntimeError("WAVE143_HMLR_FUNCTIONS_NOT_CALLABLE")

    hmlr_url = str(namespace["HMLR"])

    def recovered_links_for(lad: str) -> tuple[dict[str, object], list[dict[str, object]]]:
        page = original_bget("wave143_hmlr_page", hmlr_url, 8 * 1024 * 1024)
        if not page["ok"]:
            return {key: value for key, value in page.items() if key != "data"}, []
        soup = BeautifulSoup(page["data"], "html.parser")
        wanted = set(original_core(lad).split())
        links: dict[str, dict[str, object]] = {}
        page_base = page["url"].split("#", 1)[0]
        for anchor in soup.find_all("a", href=True):
            href = str(anchor.get("href") or "").strip()
            text = " ".join(anchor.get_text(" ", strip=True).split())
            row = anchor.find_parent("tr")
            item = anchor.find_parent("li")
            container = row or item or anchor.parent
            context = " ".join(
                (container.get_text(" ", strip=True) if container else text).split()
            )
            url = urljoin(page["url"], href)
            parsed = urlparse(url)
            context_tokens = set(original_core(context).split())
            label_is_gml = ".gml" in text.lower()
            path_is_gml = ".gml" in parsed.path.lower()
            is_real_download = (
                parsed.scheme == "https"
                and not parsed.fragment
                and url.split("#", 1)[0] != page_base
                and (label_is_gml or path_is_gml)
            )
            if is_real_download and wanted and wanted.issubset(context_tokens):
                links[url] = {
                    "text": text,
                    "context": context[:500],
                    "url": url,
                    "tokens": sorted(wanted & context_tokens),
                }
        return {key: value for key, value in page.items() if key != "data"}, list(links.values())

    def recovered_scan_gml(data: bytes) -> dict[str, object]:
        prefix = data.lstrip()[:256].lower()
        if b"<!doctype html" in prefix or b"<html" in prefix:
            raise RuntimeError("HMLR_EXPECTED_GML_GOT_HTML")
        result = original_scan_gml(data)
        if int(result.get("features_scanned") or 0) < 1:
            raise RuntimeError("HMLR_GML_ZERO_FEATURES")
        if int(result.get("polygons_scanned") or 0) < 1:
            raise RuntimeError("HMLR_GML_ZERO_POLYGONS")
        return result

    namespace["links_for"] = recovered_links_for
    namespace["scan_gml"] = recovered_scan_gml


def main() -> None:
    source = load_immutable_source()
    source_ref = f"git-blob:{SOURCE_BLOB_SHA1}"
    namespace: dict[str, object] = {
        "__name__": "security_public_safety_2_wave143_recovered",
        "__file__": source_ref,
    }
    exec(compile(source, source_ref, "exec"), namespace)
    namespace["PREVIOUS_CONTINUATION"] = EXPECTED_PREVIOUS_CONTINUATION
    install_current_ons_lad_source(namespace)
    install_hmlr_gml_recovery(namespace)
    recovered_main = namespace.get("main")
    if not callable(recovered_main):
        raise RuntimeError("WAVE143_MAIN_NOT_CALLABLE")
    recovered_main()


if __name__ == "__main__":
    if not os.environ.get("AAYS_SOURCE_HEAD"):
        raise RuntimeError("AAYS_SOURCE_HEAD_REQUIRED")
    main()
