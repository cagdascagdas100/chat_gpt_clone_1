#!/usr/bin/env python3
"""Wave363: bounded GHCR bottle-layer tarball prefix gate; never full layers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://ghcr.io"
REPO = "homebrew/core/overturemaps"
TAGS = ["1.0.1_1", "1.0.1"]
MAX_MANIFEST = 1_000_000
MAX_CHILD = 4
MAX_LAYERS = 6
MAX_PREFIX = 4096
PREFIX_RANGE = f"bytes=0-{MAX_PREFIX - 1}"
AI = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)
AM = ", ".join(
    [
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)
KEEP = {
    "accept-ranges",
    "content-length",
    "content-range",
    "content-type",
    "docker-content-digest",
    "etag",
    "last-modified",
    "location",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: str, obj: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        handle.write(raw)
        temp_name = handle.name
    os.replace(temp_name, target)


def selected_headers(headers) -> dict:
    return {key.lower(): value for key, value in headers.items() if key.lower() in KEEP}


def request(url: str, timeout: int, *, headers: dict | None = None, max_bytes: int = 0) -> dict:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "AAYS-W363", "Accept-Encoding": "identity", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise ValueError("RESPONSE_EXCEEDED_BOUND")
            result = {
                "ok": True,
                "url": url,
                "method": "GET",
                "status": getattr(response, "status", None),
                "bytes": len(body),
                "body_sha256": sha256_bytes(body),
                "headers": selected_headers(response.headers),
                "seconds": round(time.monotonic() - started, 3),
                "body": body,
            }
            if body:
                try:
                    result["json"] = json.loads(body)
                except Exception:
                    pass
            return result
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "url": url,
            "method": "GET",
            "status": exc.code,
            "bytes": 0,
            "error": f"HTTPError:{exc.code}:{exc.reason}",
            "headers": selected_headers(exc.headers),
            "seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "method": "GET",
            "bytes": 0,
            "error": f"{type(exc).__name__}:{exc}",
            "seconds": round(time.monotonic() - started, 3),
        }


def receipt(result: dict) -> dict:
    return {key: value for key, value in result.items() if key not in {"json", "body"}}


def linux_children(document: dict) -> list[dict]:
    selected: list[dict] = []
    for item in document.get("manifests") or []:
        platform = item.get("platform") or {}
        if platform.get("os") == "linux" and platform.get("architecture") in {"amd64", "arm64"} and item.get("digest"):
            selected.append(
                {
                    "mediaType": item.get("mediaType"),
                    "digest": item.get("digest"),
                    "size": item.get("size"),
                    "platform": platform,
                    "annotations": item.get("annotations"),
                }
            )
    return selected[:MAX_CHILD]


def layer_descriptor(item: dict) -> dict:
    return {
        "mediaType": item.get("mediaType"),
        "digest": item.get("digest"),
        "size": item.get("size"),
        "annotations": item.get("annotations"),
    }


def inspect_prefix(body: bytes) -> dict:
    compression = "UNKNOWN"
    if body.startswith(b"\x1f\x8b"):
        compression = "GZIP"
    elif body.startswith(b"\x28\xb5\x2f\xfd"):
        compression = "ZSTD"
    elif len(body) >= 262 and body[257:262] == b"ustar":
        compression = "TAR"
    elif body.startswith(b"PK\x03\x04"):
        compression = "ZIP"
    return {
        "prefix_bytes": len(body),
        "prefix_sha256": sha256_bytes(body),
        "prefix_hex_first_32": body[:32].hex(),
        "compression_magic": compression,
        "tar_ustar_signature_present": len(body) >= 262 and body[257:262] == b"ustar",
    }


def self_test() -> None:
    assert inspect_prefix(b"\x1f\x8babc")["compression_magic"] == "GZIP"
    assert inspect_prefix(b"\x28\xb5\x2f\xfdabc")["compression_magic"] == "ZSTD"
    tar = bytearray(300)
    tar[257:262] = b"ustar"
    assert inspect_prefix(bytes(tar))["compression_magic"] == "TAR"
    assert PREFIX_RANGE == "bytes=0-4095"
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--accessed-at")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return

    canonical = json.load(open(args.canonical, encoding="utf-8"))
    fixture = json.load(open(args.fixture, encoding="utf-8"))
    assessments = []
    for row in canonical["rows"][:3]:
        props = row["properties"]
        assessments.append(
            {
                "parcel_id": props["parcel_id"],
                "hmlr_inspire_id": props["hmlr_inspire_id"],
                "longitude": props["hmlr_lon"],
                "latitude": props["hmlr_lat"],
                "geometry_type": row.get("geometry_type") or (row.get("geometry") or {}).get("type"),
            }
        )

    ping = request(BASE + "/v2/", args.timeout, max_bytes=64_000)
    token_url = BASE + "/token?" + urllib.parse.urlencode(
        {"service": "ghcr.io", "scope": f"repository:{REPO}:pull"}
    )
    token_receipt = request(token_url, args.timeout, max_bytes=256_000)
    token = (token_receipt.get("json") or {}).get("token") or (token_receipt.get("json") or {}).get("access_token")
    auth = {"Authorization": f"Bearer {token}"} if token else {}

    tag_records: list[dict] = []
    child_manifest_count = 0
    layer_descriptor_count = 0
    prefix_receipt_count = 0
    recognized_tar_prefix_count = 0
    total_prefix_bytes = 0
    full_layer_body_downloaded = False

    if token:
        for tag in TAGS:
            index_result = request(
                f"{BASE}/v2/{REPO}/manifests/{tag}",
                args.timeout,
                headers={**auth, "Accept": AI},
                max_bytes=MAX_MANIFEST,
            )
            index_document = index_result.get("json") or {}
            child_descriptors = linux_children(index_document)
            direct_manifest = False
            if not child_descriptors and isinstance(index_document.get("layers"), list):
                child_descriptors = [{"digest": tag, "platform": {}, "direct": True}]
                direct_manifest = True
            tag_record = {
                "tag": tag,
                "index_receipt": receipt(index_result),
                "index_media_type": index_document.get("mediaType"),
                "selected_child_descriptors": child_descriptors,
                "child_records": [],
                "direct_manifest": direct_manifest,
            }
            for descriptor in child_descriptors:
                if descriptor.get("direct"):
                    manifest_result, manifest_document = index_result, index_document
                else:
                    manifest_result = request(
                        f"{BASE}/v2/{REPO}/manifests/{descriptor['digest']}",
                        args.timeout,
                        headers={**auth, "Accept": AM},
                        max_bytes=MAX_MANIFEST,
                    )
                    manifest_document = manifest_result.get("json") or {}
                if manifest_result.get("ok"):
                    child_manifest_count += 1
                child_record = {
                    "platform": descriptor.get("platform"),
                    "child_manifest_receipt": receipt(manifest_result),
                    "layer_records": [],
                }
                for raw_layer in manifest_document.get("layers") or []:
                    if layer_descriptor_count >= MAX_LAYERS:
                        break
                    descriptor_record = layer_descriptor(raw_layer)
                    digest = descriptor_record.get("digest")
                    if not digest:
                        continue
                    layer_descriptor_count += 1
                    blob_url = f"{BASE}/v2/{REPO}/blobs/{digest}"
                    prefix_result = request(
                        blob_url,
                        args.timeout,
                        headers={**auth, "Range": PREFIX_RANGE},
                        max_bytes=MAX_PREFIX,
                    )
                    body = prefix_result.get("body") or b""
                    prefix_inspection = inspect_prefix(body) if body else None
                    if prefix_result.get("ok") and prefix_result.get("status") == 206 and len(body) <= MAX_PREFIX:
                        prefix_receipt_count += 1
                    if prefix_inspection and prefix_inspection["compression_magic"] in {"GZIP", "ZSTD", "TAR"}:
                        recognized_tar_prefix_count += 1
                    total_prefix_bytes += len(body)
                    if prefix_result.get("ok") and prefix_result.get("status") == 200 and len(body) > 0:
                        full_layer_body_downloaded = True
                    child_record["layer_records"].append(
                        {
                            "descriptor": descriptor_record,
                            "prefix_receipt": receipt(prefix_result),
                            "prefix_range_header": PREFIX_RANGE,
                            "prefix_inspection": prefix_inspection,
                        }
                    )
                tag_record["child_records"].append(child_record)
            tag_records.append(tag_record)
    else:
        tag_records = [{"tag": tag, "attempted": False, "reason": "TOKEN_NOT_ACQUIRED", "child_records": []} for tag in TAGS]

    blockers: list[str] = []
    if not ping.get("ok"):
        blockers.append("GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED")
    if not token:
        blockers.append("GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED")
    if child_manifest_count == 0:
        blockers.append("OVERTUREMAPS_CHILD_MANIFEST_NOT_LIVE_ACQUIRED")
    if layer_descriptor_count == 0:
        blockers.append("OCI_LAYER_DESCRIPTOR_NOT_ACQUIRED")
    if prefix_receipt_count == 0:
        blockers.append("OCI_LAYER_TARBALL_PREFIX_NOT_ACQUIRED")
    if recognized_tar_prefix_count == 0:
        blockers.append("OCI_LAYER_TAR_GZIP_ZSTD_PREFIX_NOT_RECOGNIZED")
    blockers.extend(
        [
            "BOTTLE_LAYER_TARBALL_FULL_BODY_NOT_DOWNLOADED_BY_DESIGN",
            "THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED",
            "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
            "THREE_EXACT_UPRNS_NOT_ACQUIRED",
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
        ]
    )

    excerpt = (
        f"ping={bool(ping.get('ok'))};token={bool(token)};child_manifests={child_manifest_count};"
        f"layer_descriptors={layer_descriptor_count};prefix_receipts={prefix_receipt_count};"
        f"recognized_tar_prefixes={recognized_tar_prefix_count};prefix_bytes={total_prefix_bytes};"
        f"full_layer_body={full_layer_body_downloaded}"
    )
    runtime_evidence = {
        "source_url": f"{BASE}/v2/{REPO}/blobs/<digest>",
        "accessed_at": args.accessed_at,
        "content_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "hash_scope": "ghcr_layer_descriptor_and_bounded_4096_byte_tarball_prefix_receipts",
        "record_scope": "GHCR ping, anonymous token, two bottle tags, up to four Linux child manifests and six bytes=0-4095 layer-prefix probes; no complete layer body.",
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "layer_media_type",
            "layer_digest",
            "layer_size",
            "content_range",
            "prefix_sha256",
            "gzip_zstd_tar_magic",
            "bounded_prefix_only",
            "no_full_layer_body",
        ],
        "license_or_terms_url": "https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry",
    }
    output = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 363,
        "accessed_at": args.accessed_at,
        "assessments": assessments,
        "ghcr_ping": receipt(ping),
        "token_receipt": receipt(token_receipt),
        "token_acquired": bool(token),
        "tag_records": tag_records,
        "child_manifest_count": child_manifest_count,
        "layer_descriptor_count": layer_descriptor_count,
        "prefix_receipt_count": prefix_receipt_count,
        "recognized_tar_prefix_count": recognized_tar_prefix_count,
        "total_prefix_bytes_read": total_prefix_bytes,
        "prefix_range_header": PREFIX_RANGE,
        "max_prefix_bytes_per_layer": MAX_PREFIX,
        "bottle_layer_full_body_downloaded": full_layer_body_downloaded,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TARBALL_PREFIX_GATE_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_BOUNDED_TAR_HEADER_STREAM_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }
    atomic_json(args.output, output)


if __name__ == "__main__":
    main()
