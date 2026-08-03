#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SLOT_ID = "future_growth_2"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
OFFICIAL_HOST = "inspire.landregistry.gov.uk"
DEFAULT_URL = "https://inspire.landregistry.gov.uk/inspire/ows?Request=GetCapabilities&Service=WMS"
MAX_BYTES = 2_000_000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST:
        raise ValueError("official HMLR HTTPS WMS endpoint required")
    query = parsed.query.lower()
    if "service=wms" not in query or "request=getcapabilities" not in query:
        raise ValueError("WMS GetCapabilities query required")


def validate_continuation_key(value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("continuation key must be lowercase SHA-256 hex")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_child_text(node: ET.Element, child_name: str) -> str | None:
    for child in list(node):
        if local_name(child.tag) == child_name and child.text:
            text = child.text.strip()
            if text:
                return text
    return None


def parse_capabilities(body: bytes) -> dict:
    root = ET.fromstring(body)
    version = root.attrib.get("version")
    service_title = None
    service_abstract = None
    layers: list[dict] = []

    for node in root.iter():
        name = local_name(node.tag)
        if name == "Service" and service_title is None:
            service_title = first_child_text(node, "Title")
            service_abstract = first_child_text(node, "Abstract")
        elif name == "Layer":
            layer_name = first_child_text(node, "Name")
            layer_title = first_child_text(node, "Title")
            if layer_name or layer_title:
                layers.append(
                    {
                        "name": layer_name,
                        "title": layer_title,
                        "queryable": node.attrib.get("queryable"),
                    }
                )

    deduped: list[dict] = []
    seen: set[tuple[str | None, str | None]] = set()
    for layer in layers:
        key = (layer["name"], layer["title"])
        if key not in seen:
            seen.add(key)
            deduped.append(layer)

    parcel_layers = [
        item
        for item in deduped
        if "parcel" in ((item.get("name") or "") + " " + (item.get("title") or "")).lower()
        or "cadastral" in ((item.get("name") or "") + " " + (item.get("title") or "")).lower()
    ]
    return {
        "wms_version": version,
        "service_title": service_title,
        "service_abstract_excerpt": service_abstract[:500] if service_abstract else None,
        "layer_count": len(deduped),
        "layers": deduped[:500],
        "parcel_layer_count": len(parcel_layers),
        "parcel_layers": parcel_layers[:100],
    }


def fetch_capabilities(url: str, timeout_seconds: int) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-future_growth_2-official-wms-capabilities/1.0",
            "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("WMS capabilities response exceeds bounded byte limit")
        final_url = response.geturl()
        validate_url(final_url)
        parsed = parse_capabilities(body)
        return {
            "accessed_at_utc": utc_now(),
            "request_url": url,
            "final_url": final_url,
            "http_status": int(response.status),
            "content_type": response.headers.get("content-type"),
            "response_byte_count": len(body),
            "response_sha256": sha256_bytes(body),
            **parsed,
        }


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def fixture_xml() -> bytes:
    return b"""<?xml version='1.0' encoding='UTF-8'?>
<WMS_Capabilities version='1.3.0' xmlns='http://www.opengis.net/wms'>
  <Service><Title>Fixture WMS</Title><Abstract>Parser fixture only.</Abstract></Service>
  <Capability><Layer><Title>Fixture root</Title>
    <Layer queryable='1'><Name>fixture:parcel</Name><Title>Fixture cadastral parcel</Title></Layer>
    <Layer queryable='0'><Name>fixture:background</Name><Title>Fixture background</Title></Layer>
  </Layer></Capability>
</WMS_Capabilities>"""


def build_output(url: str, continuation_key: str, capture: dict | None, error: str | None) -> dict:
    if capture is not None:
        state = "PUBLISHED"
        data_status = "OFFICIAL_WMS_CAPABILITIES_PARSED"
        completed = 1
    else:
        state = "NO_DATA_CONTINUE"
        data_status = "SOURCE_READ_FAILED"
        completed = 1
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_continuation_key": continuation_key,
        "state": state,
        "panel_status": "PUBLISHED" if state == "PUBLISHED" else "BİLGİ TOPLANIYOR",
        "generated_at": utc_now(),
        "completed_count": completed,
        "target_count": 1,
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "data_status": data_status,
        "official_wms_url": url,
        "capabilities": capture,
        "error": error,
        "raw_response_body_copied": False,
        "geometry_copied": False,
        "authority_membership_inferred": False,
        "score_written": False,
        "fake_data": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-url", default=DEFAULT_URL)
    parser.add_argument("--output", required=True)
    parser.add_argument("--task-continuation-key", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    validate_url(args.service_url)
    validate_continuation_key(args.task_continuation_key)
    if not 15 <= args.timeout_seconds <= 180:
        raise ValueError("timeout must be between 15 and 180 seconds")

    capture = None
    error = None
    if args.self_test:
        parsed = parse_capabilities(fixture_xml())
        assert parsed["wms_version"] == "1.3.0"
        assert parsed["layer_count"] == 3
        assert parsed["parcel_layer_count"] == 1
        assert parsed["parcel_layers"][0]["name"] == "fixture:parcel"
        capture = {
            "accessed_at_utc": utc_now(),
            "request_url": args.service_url,
            "final_url": args.service_url,
            "http_status": 200,
            "content_type": "text/xml",
            "response_byte_count": len(fixture_xml()),
            "response_sha256": sha256_bytes(fixture_xml()),
            **parsed,
        }
    else:
        try:
            capture = fetch_capabilities(args.service_url, args.timeout_seconds)
        except Exception as exc:  # bounded evidence only
            error = f"{type(exc).__name__}:{str(exc)[:1000]}"

    output = build_output(args.service_url, args.task_continuation_key, capture, error)
    atomic_write(Path(args.output), output)
    print(
        json.dumps(
            {
                "state": output["state"],
                "completed_count": output["completed_count"],
                "target_count": output["target_count"],
                "parcel_layer_count": (capture or {}).get("parcel_layer_count", 0),
                "output": args.output,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
