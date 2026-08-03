#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "future_growth_2"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
OFFICIAL_HOST = "inspire.landregistry.gov.uk"
OFFICIAL_PATH = "/inspire/ows"
MAX_BYTES = 65_536
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_continuation_key(value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError("continuation key must be lowercase SHA-256 hex")


def load_candidate(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 1:
        raise ValueError("exactly one historical candidate required")
    token = candidates[0].get("layer_token")
    if not isinstance(token, str) or not token or ":" not in token:
        raise ValueError("valid namespaced layer token required")
    if candidates[0].get("current_layer_availability_verified") is not False:
        raise ValueError("input must preserve current availability as unverified")
    return token


def build_url(token: str) -> str:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetMap",
        "LAYERS": token,
        "STYLES": "",
        "CRS": "EPSG:27700",
        "BBOX": "530000,180000,530010,180010",
        "WIDTH": "1",
        "HEIGHT": "1",
        "FORMAT": "image/png",
        "TRANSPARENT": "TRUE",
    }
    return "https://inspire.landregistry.gov.uk/inspire/ows?" + urllib.parse.urlencode(params)


def validate_final_url(url: str, expected_token: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST or parsed.path != OFFICIAL_PATH:
        raise ValueError("official HMLR HTTPS WMS endpoint required")
    query = urllib.parse.parse_qs(parsed.query)
    layer_values = query.get("LAYERS") or query.get("layers")
    if layer_values != [expected_token]:
        raise ValueError("exact candidate layer token required")


def classify_response(status: int, content_type: str | None, body: bytes) -> dict:
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    png = body.startswith(PNG_SIGNATURE)
    verified = status == 200 and ctype == "image/png" and png
    return {
        "http_status": status,
        "content_type": content_type,
        "response_byte_count": len(body),
        "response_sha256": sha256_bytes(body),
        "png_signature_verified": png,
        "current_layer_availability_verified": verified,
        "classification": "CURRENT_LAYER_TOKEN_VERIFIED_BY_OFFICIAL_GETMAP" if verified else "CURRENT_LAYER_TOKEN_UNVERIFIED",
    }


def fetch_validation(url: str, token: str, timeout_seconds: int) -> dict:
    validate_final_url(url, token)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-future_growth_2-current-layer-token-validation/1.0",
            "Accept": "image/png,text/xml;q=0.9,*/*;q=0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("response exceeds bounded byte limit")
        final_url = response.geturl()
        validate_final_url(final_url, token)
        return {
            "accessed_at_utc": utc_now(),
            "request_url": url,
            "final_url": final_url,
            **classify_response(int(response.status), response.headers.get("content-type"), body),
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


def build_output(token: str, continuation_key: str, receipt: dict | None, error: str | None) -> dict:
    verified = bool(receipt and receipt.get("current_layer_availability_verified"))
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": SLOT_ID,
        "task_continuation_key": continuation_key,
        "state": "PUBLISHED" if verified else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "generated_at": utc_now(),
        "completed_count": 1,
        "target_count": 1,
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "historical_layer_token": token,
        "current_layer_availability_verified": verified,
        "validation_receipt": receipt,
        "error": error,
        "next_unverified_step": (
            "USE_VERIFIED_CURRENT_LAYER_TOKEN_FOR_BOUNDED_SPATIAL_FILTER_DESIGN"
            if verified
            else "DISCOVER_OFFICIAL_HMLR_WMS_PROXY_OR_CURRENT_CAPABILITIES_SNAPSHOT"
        ),
        "raw_response_body_copied": False,
        "geometry_copied": False,
        "authority_membership_inferred": False,
        "score_written": False,
        "fake_data": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--task-continuation-key", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    validate_continuation_key(args.task_continuation_key)
    if not 15 <= args.timeout_seconds <= 60:
        raise ValueError("timeout must be between 15 and 60 seconds")

    token = load_candidate(Path(args.candidate_input))
    url = build_url(token)
    receipt = None
    error = None

    if args.self_test:
        assert classify_response(200, "image/png", PNG_SIGNATURE + b"fixture")["current_layer_availability_verified"] is True
        assert classify_response(200, "text/xml", b"<ServiceException/>")["current_layer_availability_verified"] is False
        assert classify_response(404, "image/png", PNG_SIGNATURE + b"fixture")["current_layer_availability_verified"] is False
        validate_final_url(url, token)
        assert urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["LAYERS"] == [token]
        receipt = {
            "accessed_at_utc": utc_now(),
            "request_url": url,
            "final_url": url,
            **classify_response(200, "image/png", PNG_SIGNATURE + b"fixture"),
            "fixture_only": True,
        }
    else:
        try:
            receipt = fetch_validation(url, token, args.timeout_seconds)
        except Exception as exc:
            error = f"{type(exc).__name__}:{str(exc)[:1000]}"

    output = build_output(token, args.task_continuation_key, receipt, error)
    atomic_write(Path(args.output), output)
    print(json.dumps({
        "state": output["state"],
        "completed_count": output["completed_count"],
        "target_count": output["target_count"],
        "current_layer_availability_verified": output["current_layer_availability_verified"],
        "output": args.output,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
