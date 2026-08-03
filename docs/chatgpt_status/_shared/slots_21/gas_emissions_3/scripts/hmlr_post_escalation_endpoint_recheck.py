#!/usr/bin/env python3
"""Bounded post-escalation recheck for two official HMLR INSPIRE endpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior-output", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-json", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json_bytes(path: Path) -> tuple[bytes, dict[str, Any]]:
    data = path.read_bytes()
    return data, json.loads(data)


def bounded_receipt(target: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    endpoint = target["endpoint_url"]
    request = urllib.request.Request(
        endpoint,
        headers={
            "User-Agent": "AAYS-HMLR-Endpoint-Recheck/1.0",
            "Accept": "application/octet-stream,*/*;q=0.8",
            "Range": "bytes=0-3",
        },
        method="GET",
    )
    context = ssl.create_default_context()
    base: dict[str, Any] = {
        "target_id": target["target_id"],
        "authority_name": target["authority_name"],
        "endpoint_url": endpoint,
        "attempt_completed": True,
        "http_status": None,
        "final_url": None,
        "content_type": None,
        "content_range": None,
        "content_length": None,
        "first_four_bytes_hex": None,
        "zip_magic_verified": False,
        "endpoint_receipt_verified": False,
        "decision": "NO_DATA_CONTINUE",
        "error": None,
    }
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
            body = response.read(4)
            status = int(getattr(response, "status", response.getcode()))
            final_url = response.geturl()
            parsed_final = urllib.parse.urlparse(final_url)
            zip_magic = body.startswith(b"PK\x03\x04")
            base.update(
                {
                    "http_status": status,
                    "final_url": final_url,
                    "content_type": response.headers.get("Content-Type"),
                    "content_range": response.headers.get("Content-Range"),
                    "content_length": response.headers.get("Content-Length"),
                    "first_four_bytes_hex": body.hex(),
                    "zip_magic_verified": zip_magic,
                    "endpoint_receipt_verified": (
                        status in {200, 206}
                        and parsed_final.scheme == "https"
                        and zip_magic
                    ),
                }
            )
    except urllib.error.HTTPError as exc:
        body = exc.read(4)
        base.update(
            {
                "http_status": int(exc.code),
                "final_url": exc.geturl(),
                "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                "content_range": exc.headers.get("Content-Range") if exc.headers else None,
                "content_length": exc.headers.get("Content-Length") if exc.headers else None,
                "first_four_bytes_hex": body.hex(),
                "zip_magic_verified": body.startswith(b"PK\x03\x04"),
                "error": f"HTTPError: {exc.code} {exc.reason}"[:500],
            }
        )
    except Exception as exc:  # fail closed and preserve the exact technical reason
        base["error"] = f"{type(exc).__name__}: {exc}"[:500]

    if base["endpoint_receipt_verified"]:
        base["decision"] = "ENDPOINT_VERIFIED"
        base["error"] = None
    return base


def fixture_receipts(contract: dict[str, Any], fixture_path: Path) -> list[dict[str, Any]]:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    records = fixture.get("receipts")
    require(isinstance(records, dict), "fixture receipts missing")
    out: list[dict[str, Any]] = []
    for target in contract["runtime_targets"]:
        receipt = records[target["target_id"]]
        body_hex = str(receipt["first_four_bytes_hex"])
        final_url = str(receipt["final_url"])
        parsed_final = urllib.parse.urlparse(final_url)
        verified = (
            int(receipt["http_status"]) in {200, 206}
            and parsed_final.scheme == "https"
            and bytes.fromhex(body_hex).startswith(b"PK\x03\x04")
        )
        out.append(
            {
                "target_id": target["target_id"],
                "authority_name": target["authority_name"],
                "endpoint_url": target["endpoint_url"],
                "attempt_completed": True,
                "http_status": int(receipt["http_status"]),
                "final_url": final_url,
                "content_type": receipt.get("content_type"),
                "content_range": receipt.get("content_range"),
                "content_length": receipt.get("content_length"),
                "first_four_bytes_hex": body_hex,
                "zip_magic_verified": bytes.fromhex(body_hex).startswith(b"PK\x03\x04"),
                "endpoint_receipt_verified": verified,
                "decision": "ENDPOINT_VERIFIED" if verified else "NO_DATA_CONTINUE",
                "error": None if verified else "FIXTURE_RECEIPT_NOT_VERIFIED",
            }
        )
    return out


def main() -> int:
    args = parse_args()
    contract_bytes, contract = load_json_bytes(args.contract)
    prior_bytes, prior = load_json_bytes(args.prior_output)

    require(contract.get("schema_version") == 3, "contract schema mismatch")
    require(contract.get("slot_id") == "gas_emissions_3", "slot mismatch")
    require(contract.get("state") == "READY", "contract must be READY")
    require(contract.get("status") == "ready", "status must be ready")
    require(contract.get("claimable") is True, "contract must be claimable")
    require(contract.get("ready_for_claim") is True, "contract must be ready_for_claim")

    precondition = contract.get("precondition") or {}
    require(
        sha256_bytes(prior_bytes) == precondition.get("prior_output_sha256"),
        "prior output SHA mismatch",
    )
    require(prior.get("state") == "ESCALATION_PACKET_READY", "unexpected prior state")
    require(
        prior.get("next_unverified_step")
        == "AWAIT_NETWORK_EGRESS_APPROVAL_OR_HMLR_DATA_SERVICES_RESPONSE",
        "unexpected prior next step",
    )

    manifest = contract.get("source_evidence_manifest") or {}
    for field in (
        "source_url",
        "accessed_at",
        "content_sha256",
        "supports_fields",
        "relevant_record_ids_or_excerpt",
        "license_or_terms_url",
    ):
        require(manifest.get(field), f"missing source evidence field: {field}")

    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 2, "exactly two targets required")
    for target in targets:
        endpoint = urllib.parse.urlparse(str(target.get("endpoint_url", "")))
        require(endpoint.scheme == "https", "target endpoint must be HTTPS")
        require(
            endpoint.netloc == "use-land-property-data.service.gov.uk",
            "target host mismatch",
        )
        require(endpoint.path.endswith(".zip"), "target path must end in .zip")

    timeout_seconds = int(contract.get("network_policy", {}).get("per_target_timeout_seconds", 45))
    if args.fixture_json:
        receipts = fixture_receipts(contract, args.fixture_json)
        execution_mode = "SYNTHETIC_FIXTURE"
    else:
        receipts = [bounded_receipt(target, timeout_seconds) for target in targets]
        execution_mode = "LIVE_NETWORK"

    completed = sum(bool(item["attempt_completed"]) for item in receipts)
    verified = sum(bool(item["endpoint_receipt_verified"]) for item in receipts)
    target_count = len(targets)
    state = "ENDPOINTS_VERIFIED" if verified == target_count else "NO_DATA_CONTINUE"
    next_step = (
        "DOWNLOAD_AND_VALIDATE_CURRENT_HMLR_GML_ARCHIVES_FOR_CUMBERLAND_AND_GWYNEDD"
        if state == "ENDPOINTS_VERIFIED"
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_HMLR_NO_DATA"
    )

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED" if state == "ENDPOINTS_VERIFIED" else "BİLGİ TOPLANIYOR",
        "execution_mode": execution_mode,
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": args.contract.as_posix(),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": args.prior_output.as_posix(),
            "prior_output_sha256": sha256_bytes(prior_bytes),
        },
        "counts": {
            "completed_count": completed,
            "target_count": target_count,
            "official_endpoint_attempts": completed,
            "official_endpoint_receipts_verified": verified,
            "raw_gml_archives_downloaded": 0,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "parcel_bindings": 0,
        },
        "progress_percent": round(completed / target_count * 100, 6),
        "targets": receipts,
        "decision": {
            "endpoint_gate_passed": verified == target_count,
            "full_archive_downloaded": False,
            "bounded_read_bytes_per_target": 4,
            "inferred_values": 0,
            "fake_data": False,
        },
    }

    require(completed == target_count, "not all endpoint attempts completed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(
        json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
