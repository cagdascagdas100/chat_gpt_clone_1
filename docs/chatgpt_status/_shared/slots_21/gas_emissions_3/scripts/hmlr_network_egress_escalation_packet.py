#!/usr/bin/env python3
"""Build a fail-closed escalation packet from verified HMLR network-egress evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-slot", default="gas_emissions_3")
    parser.add_argument("--expected-target-count", type=int, default=2)
    parser.add_argument("--expected-input-sha256", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    args = parse_args()
    input_bytes = args.input.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    require(sha256_bytes(input_bytes) == args.expected_input_sha256, "input SHA mismatch")
    require(sha256_bytes(manifest_bytes) == args.expected_manifest_sha256, "manifest SHA mismatch")

    previous: dict[str, Any] = json.loads(input_bytes)
    manifest: dict[str, Any] = json.loads(manifest_bytes)

    require(previous.get("slot_id") == args.expected_slot, "slot mismatch")
    require(previous.get("state") == "NO_DATA_CONTINUE", "input must be NO_DATA_CONTINUE")
    require(
        previous.get("next_unverified_step")
        == "ESCALATE_OFFICIAL_HMLR_NETWORK_EGRESS_OR_CONTACT_DATA_SERVICES",
        "unexpected prerequisite",
    )
    counts = previous.get("counts") or {}
    require(counts.get("completed_count") == args.expected_target_count, "input completed count mismatch")
    require(counts.get("target_count") == args.expected_target_count, "input target count mismatch")
    require(counts.get("official_endpoint_receipts_verified") == 0, "receipt count must be zero")
    require((previous.get("decision") or {}).get("fake_data") is False, "fake-data flag mismatch")
    require((previous.get("decision") or {}).get("inferred_values") == 0, "inference flag mismatch")

    dns = previous.get("dns_receipt") or {}
    require(dns.get("decision") == "NO_DATA_CONTINUE", "DNS decision must be NO_DATA_CONTINUE")
    require(isinstance(dns.get("curl_exit_code"), int) and dns.get("curl_exit_code") != 0, "missing DNS failure")
    require(dns.get("answer_ipv4") == [], "DNS answers must be empty")

    require(manifest.get("schema_version") == 3, "manifest schema mismatch")
    require(manifest.get("slot_id") == args.expected_slot, "manifest slot mismatch")
    require(manifest.get("input_sha256") == args.expected_input_sha256, "manifest input SHA mismatch")
    channels = manifest.get("escalation_channels")
    require(isinstance(channels, list) and len(channels) == 2, "two escalation channels required")

    targets = previous.get("targets") or []
    require(isinstance(targets, list) and len(targets) == args.expected_target_count, "target records mismatch")
    endpoints = [item.get("endpoint_url") for item in targets]
    authorities = [item.get("authority_name") for item in targets]
    require(all(isinstance(url, str) and url.startswith("https://") for url in endpoints), "bad endpoint")
    require(all(isinstance(name, str) and name for name in authorities), "bad authority")

    technical_summary = {
        "source_output_path": manifest["input_path"],
        "source_output_sha256": args.expected_input_sha256,
        "dns_resolver_url": dns.get("resolver_url"),
        "dns_resolver_tls_hostname": dns.get("resolver_tls_hostname"),
        "dns_bootstrap_ipv4": dns.get("resolver_bootstrap_ipv4"),
        "dns_curl_exit_code": dns.get("curl_exit_code"),
        "dns_error": dns.get("error"),
        "dns_answer_ipv4_count": 0,
        "official_endpoint_attempts": counts.get("official_endpoint_attempts"),
        "official_endpoint_receipts_verified": 0,
        "target_authorities": authorities,
        "target_endpoints": endpoints,
    }

    prepared_channels: list[dict[str, Any]] = []
    for channel in channels:
        channel_id = channel.get("channel_id")
        if channel_id == "INTERNAL_NETWORK_EGRESS":
            prepared_channels.append(
                {
                    "channel_id": channel_id,
                    "state": "PACKET_PREPARED_NOT_SUBMITTED",
                    "requires_operator_action": True,
                    "request": {
                        "purpose": "Permit bounded HTTPS receipt validation for official HM Land Registry INSPIRE downloads.",
                        "destinations": channel["destinations"],
                        "controls": {
                            "outbound_tcp_port": 443,
                            "tls_verification_required": True,
                            "maximum_endpoint_body_bytes": 4,
                            "full_archive_download_forbidden": True,
                        },
                        "evidence": technical_summary,
                    },
                }
            )
        elif channel_id == "HMLR_DATA_SERVICES":
            contact = channel["contact"]
            prepared_channels.append(
                {
                    "channel_id": channel_id,
                    "state": "CONTACT_DRAFT_PREPARED_NOT_SENT",
                    "requires_operator_action": True,
                    "contact": contact,
                    "subject": "INSPIRE download endpoint access failure for Cumberland and Gwynedd",
                    "message": (
                        "We are validating the official HM Land Registry INSPIRE download entries for "
                        "Cumberland Council and Gwynedd Council. The published HTTPS endpoint paths were "
                        "attempted twice, including a bounded four-byte receipt check and a Google Public "
                        "DNS-over-HTTPS bootstrap. The execution environment could not establish outbound "
                        "TCP 443 to dns.google, so no DNS answer, redirect receipt, ZIP magic, archive, GML, "
                        "geometry, INSPIRE ID or parcel binding was obtained. Please confirm whether the "
                        "published download service is available and whether there is an official direct "
                        "download or service-status route for these two authority files."
                    ),
                    "evidence": technical_summary,
                }
            )
        else:
            raise ValueError(f"unsupported escalation channel: {channel_id}")

    completed = len(prepared_channels)
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "task_batch": 263,
        "state": "ESCALATION_PACKET_READY",
        "result": "NETWORK_EGRESS_AND_HMLR_DATA_SERVICES_ESCALATION_PACKET_PREPARED",
        "first_unverified_step_completed": "ESCALATE_OFFICIAL_HMLR_NETWORK_EGRESS_OR_CONTACT_DATA_SERVICES",
        "next_unverified_step": "AWAIT_NETWORK_EGRESS_APPROVAL_OR_HMLR_DATA_SERVICES_RESPONSE",
        "input": {
            "path": manifest["input_path"],
            "sha256": args.expected_input_sha256,
            "manifest_path": args.manifest.as_posix(),
            "manifest_sha256": args.expected_manifest_sha256,
        },
        "counts": {
            "completed_count": completed,
            "target_count": 2,
            "escalation_channels_prepared": completed,
            "contacts_sent": 0,
            "network_changes_applied": 0,
            "official_endpoint_receipts_verified": 0,
            "raw_gml_archives_downloaded": 0,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "parcel_bindings": 0,
        },
        "technical_evidence": technical_summary,
        "escalation_channels": prepared_channels,
        "decision": {
            "manual_action_required": True,
            "contact_sent": False,
            "network_change_applied": False,
            "inferred_values": 0,
            "fake_data": False,
        },
    }

    require(completed == 2, "packet preparation incomplete")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
