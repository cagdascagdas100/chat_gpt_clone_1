from __future__ import annotations

import hashlib
import os
import subprocess

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
    recovered_main = namespace.get("main")
    if not callable(recovered_main):
        raise RuntimeError("WAVE143_MAIN_NOT_CALLABLE")
    recovered_main()


if __name__ == "__main__":
    if not os.environ.get("AAYS_SOURCE_HEAD"):
        raise RuntimeError("AAYS_SOURCE_HEAD_REQUIRED")
    main()
