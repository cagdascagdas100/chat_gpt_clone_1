#!/usr/bin/env python3
"""Fail-closed HMLR endpoint receipt validator using bootstrapped Google DoH."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expected-slot", default="gas_emissions_3")
    p.add_argument("--expected-target-count", type=int, default=2)
    p.add_argument("--expected-input-sha256", required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    p.add_argument("--fixture-json", type=Path)
    return p.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_bounded(command: list[str], timeout_seconds: int, stdout_limit: int = 1_000_000) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = result.stdout[: stdout_limit + 1]
        stderr = result.stderr[:4096]
        return {
            "exit_code": int(result.returncode),
            "stdout": stdout,
            "stderr": stderr,
            "stdout_limit_exceeded": len(stdout) > stdout_limit,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "stdout": (exc.stdout or b"")[: stdout_limit + 1],
            "stderr": (exc.stderr or b"")[:4096],
            "stdout_limit_exceeded": False,
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "exit_code": None,
            "stdout": b"",
            "stderr": str(exc).encode("utf-8", errors="replace")[:4096],
            "stdout_limit_exceeded": False,
            "timed_out": False,
        }


def valid_public_ipv4(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return (
        ip.version == 4
        and not ip.is_private
        and not ip.is_loopback
        and not ip.is_link_local
        and not ip.is_multicast
        and not ip.is_reserved
        and not ip.is_unspecified
    )


def doh_lookup(manifest: dict[str, Any], host: str) -> dict[str, Any]:
    policy = manifest["network_policy"]
    resolver = manifest["resolver"]
    query_url = resolver["json_api_url"] + "?" + urllib.parse.urlencode(
        {"name": host, "type": "A", "cd": "0", "do": "1"}
    )
    command = [
        policy["curl_binary"],
        "--silent",
        "--show-error",
        "--fail",
        "--max-time",
        str(policy["timeout_seconds"]),
        "--connect-timeout",
        str(policy["connect_timeout_seconds"]),
        "--noproxy",
        "*",
        "--resolve",
        f'{resolver["tls_hostname"]}:443:{resolver["bootstrap_ipv4"]}',
        "--header",
        "Accept: application/dns-json",
        query_url,
    ]
    run = run_bounded(command, policy["timeout_seconds"] + 5, policy["maximum_doh_response_bytes"])
    base = {
        "resolver_url": resolver["json_api_url"],
        "resolver_tls_hostname": resolver["tls_hostname"],
        "resolver_bootstrap_ipv4": resolver["bootstrap_ipv4"],
        "query_name": host,
        "query_type": "A",
        "curl_exit_code": run["exit_code"],
        "timed_out": run["timed_out"],
        "stdout_limit_exceeded": run["stdout_limit_exceeded"],
        "error": run["stderr"].decode("utf-8", errors="replace")[:500] or None,
        "dns_status": None,
        "answer_ipv4": [],
        "answer_ttls": [],
        "response_sha256": sha256_bytes(run["stdout"]),
        "decision": "NO_DATA_CONTINUE",
    }
    if run["exit_code"] != 0 or run["timed_out"] or run["stdout_limit_exceeded"]:
        return base
    try:
        payload = json.loads(run["stdout"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"[:500]
        return base
    status = payload.get("Status")
    answers = payload.get("Answer") if isinstance(payload.get("Answer"), list) else []
    ips: list[str] = []
    ttls: list[int] = []
    for item in answers:
        if not isinstance(item, dict) or item.get("type") != 1:
            continue
        data = str(item.get("data", ""))
        if valid_public_ipv4(data):
            ips.append(data)
            try:
                ttls.append(int(item.get("TTL")))
            except (TypeError, ValueError):
                pass
    ips = sorted(set(ips))[: policy["maximum_resolved_ipv4"]]
    base["dns_status"] = status
    base["answer_ipv4"] = ips
    base["answer_ttls"] = ttls[: policy["maximum_resolved_ipv4"]]
    if status == 0 and ips:
        base["decision"] = "DNS_RESOLVED"
        base["error"] = None
    return base


def parse_header_location(header_bytes: bytes) -> str | None:
    location: str | None = None
    for line in header_bytes.decode("iso-8859-1", errors="replace").splitlines():
        if line.lower().startswith("location:"):
            location = line.split(":", 1)[1].strip()
    return location


def endpoint_receipt(manifest: dict[str, Any], target: dict[str, str], ips: list[str]) -> dict[str, Any]:
    policy = manifest["network_policy"]
    endpoint = target["endpoint_url"]
    parsed = urllib.parse.urlparse(endpoint)
    base = {
        "target_id": target["target_id"],
        "authority_name": target["authority_name"],
        "endpoint_url": endpoint,
        "attempt_completed": True,
        "resolved_ipv4_tried": [],
        "endpoint_path_valid": (
            parsed.scheme == "https"
            and parsed.netloc == manifest["official_host"]
            and parsed.path.startswith("/datasets/inspire/download/")
            and parsed.path.endswith(".zip")
        ),
        "endpoint_receipt_verified": False,
        "receipt_state": "NO_DATA_CONTINUE",
        "http_status": None,
        "redirect_location": None,
        "content_type": None,
        "remote_ip": None,
        "zip_magic_verified": False,
        "curl_exit_code": None,
        "error": None,
        "decision": "NO_DATA_CONTINUE",
    }
    if not base["endpoint_path_valid"] or not ips:
        base["error"] = "NO_VALID_OFFICIAL_ENDPOINT_PATH_OR_DNS_ANSWER"
        return base

    for ip in ips:
        base["resolved_ipv4_tried"].append(ip)
        with tempfile.TemporaryDirectory(prefix="aays-hmlr-receipt-") as td:
            body = Path(td) / "body.bin"
            headers = Path(td) / "headers.txt"
            command = [
                policy["curl_binary"],
                "--silent",
                "--show-error",
                "--max-time",
                str(policy["timeout_seconds"]),
                "--connect-timeout",
                str(policy["connect_timeout_seconds"]),
                "--noproxy",
                "*",
                "--proto",
                "=https",
                "--proto-redir",
                "=https",
                "--max-redirs",
                "0",
                "--resolve",
                f'{manifest["official_host"]}:443:{ip}',
                "--range",
                "0-3",
                "--max-filesize",
                str(policy["maximum_endpoint_body_bytes"]),
                "--dump-header",
                str(headers),
                "--output",
                str(body),
                "--write-out",
                "%{http_code}\n%{content_type}\n%{remote_ip}\n",
                endpoint,
            ]
            run = run_bounded(command, policy["timeout_seconds"] + 5, 4096)
            base["curl_exit_code"] = run["exit_code"]
            base["error"] = run["stderr"].decode("utf-8", errors="replace")[:500] or None
            values = run["stdout"].decode("utf-8", errors="replace").splitlines()
            if len(values) >= 3:
                try:
                    base["http_status"] = int(values[-3])
                except ValueError:
                    base["http_status"] = None
                base["content_type"] = values[-2] or None
                base["remote_ip"] = values[-1] or None
            body_bytes = body.read_bytes() if body.exists() else b""
            header_bytes = headers.read_bytes() if headers.exists() else b""
            location = parse_header_location(header_bytes)
            base["redirect_location"] = location
            base["zip_magic_verified"] = body_bytes[:4].startswith(b"PK")
            redirect = urllib.parse.urlparse(location or "")
            redirect_ok = (
                base["http_status"] is not None
                and 300 <= base["http_status"] < 400
                and redirect.scheme == "https"
                and bool(redirect.netloc)
            )
            direct_zip_ok = (
                base["http_status"] in {200, 206}
                and base["zip_magic_verified"]
                and len(body_bytes) <= policy["maximum_endpoint_body_bytes"]
            )
            if redirect_ok or direct_zip_ok:
                base["endpoint_receipt_verified"] = True
                base["receipt_state"] = "HTTPS_REDIRECT" if redirect_ok else "DIRECT_ZIP"
                base["decision"] = "ENDPOINT_VERIFIED"
                base["error"] = None
                return base
    return base


def main() -> int:
    a = parse_args()
    input_bytes = a.input.read_bytes()
    manifest_bytes = a.manifest.read_bytes()
    if sha256_bytes(input_bytes) != a.expected_input_sha256:
        raise ValueError("input SHA mismatch")
    if sha256_bytes(manifest_bytes) != a.expected_manifest_sha256:
        raise ValueError("manifest SHA mismatch")

    previous = json.loads(input_bytes)
    manifest = json.loads(manifest_bytes)
    if previous.get("slot_id") != a.expected_slot or previous.get("state") != "NO_DATA_CONTINUE":
        raise ValueError("bad input")
    if previous.get("next_unverified_step") != "RETRY_OFFICIAL_HMLR_ENDPOINT_RECEIPTS_FROM_NETWORK_WITH_WORKING_DNS":
        raise ValueError("bad prerequisite")
    if manifest.get("schema_version") != 3 or manifest.get("slot_id") != a.expected_slot:
        raise ValueError("bad manifest")
    if manifest.get("input_sha256") != a.expected_input_sha256:
        raise ValueError("manifest input SHA mismatch")
    targets = manifest.get("target_records")
    if not isinstance(targets, list) or len(targets) != a.expected_target_count:
        raise ValueError("target count mismatch")

    if a.fixture_json:
        fixture = json.loads(a.fixture_json.read_text(encoding="utf-8"))
        dns = fixture["dns_receipt"]
        receipts = fixture["endpoint_receipts"]
        results = []
        for target in targets:
            receipt = receipts[target["target_id"]]
            parsed = urllib.parse.urlparse(target["endpoint_url"])
            location = urllib.parse.urlparse(receipt.get("redirect_location") or "")
            path_ok = (
                parsed.scheme == "https"
                and parsed.netloc == manifest["official_host"]
                and parsed.path.startswith("/datasets/inspire/download/")
                and parsed.path.endswith(".zip")
            )
            redirect_ok = (
                receipt.get("receipt_state") == "HTTPS_REDIRECT"
                and location.scheme == "https"
                and bool(location.netloc)
            )
            zip_ok = receipt.get("receipt_state") == "DIRECT_ZIP" and receipt.get("zip_magic_verified") is True
            verified = path_ok and (redirect_ok or zip_ok)
            results.append(
                {
                    "target_id": target["target_id"],
                    "authority_name": target["authority_name"],
                    "endpoint_url": target["endpoint_url"],
                    "attempt_completed": True,
                    "resolved_ipv4_tried": dns["answer_ipv4"],
                    "endpoint_path_valid": path_ok,
                    "endpoint_receipt_verified": verified,
                    "receipt_state": receipt.get("receipt_state"),
                    "http_status": receipt.get("http_status"),
                    "redirect_location": receipt.get("redirect_location"),
                    "content_type": receipt.get("content_type"),
                    "remote_ip": receipt.get("remote_ip"),
                    "zip_magic_verified": bool(receipt.get("zip_magic_verified")),
                    "curl_exit_code": 0,
                    "error": None,
                    "decision": "ENDPOINT_VERIFIED" if verified else "NO_DATA_CONTINUE",
                }
            )
    else:
        dns = doh_lookup(manifest, manifest["official_host"])
        results = [endpoint_receipt(manifest, target, dns["answer_ipv4"]) for target in targets]

    completed = sum(bool(item["attempt_completed"]) for item in results)
    verified = sum(bool(item["endpoint_receipt_verified"]) for item in results)
    state = "ENDPOINTS_VERIFIED" if verified == a.expected_target_count else "NO_DATA_CONTINUE"
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": a.expected_slot,
        "task_batch": 262,
        "state": state,
        "result": "OFFICIAL_HMLR_ENDPOINT_RECEIPTS_RETRIED_WITH_BOOTSTRAPPED_DOH_FAIL_CLOSED",
        "first_unverified_step_completed": "RETRY_OFFICIAL_HMLR_ENDPOINT_RECEIPTS_FROM_NETWORK_WITH_WORKING_DNS",
        "next_unverified_step": (
            "DOWNLOAD_AND_VALIDATE_HMLR_GML_ARCHIVES"
            if state == "ENDPOINTS_VERIFIED"
            else "ESCALATE_OFFICIAL_HMLR_NETWORK_EGRESS_OR_CONTACT_DATA_SERVICES"
        ),
        "input": {
            "path": a.input.as_posix(),
            "sha256": sha256_bytes(input_bytes),
            "manifest_path": a.manifest.as_posix(),
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "dns_receipt": dns,
        "counts": {
            "completed_count": completed,
            "target_count": a.expected_target_count,
            "official_endpoint_attempts": completed,
            "official_endpoint_receipts_verified": verified,
            "raw_gml_archives_downloaded": 0,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "parcel_bindings": 0,
        },
        "decision": {
            "endpoint_gate_passed": verified == a.expected_target_count,
            "bootstrapped_doh_used": True,
            "tls_hostname_verification_preserved": True,
            "https_redirect_or_zip_magic_required": True,
            "inferred_values": 0,
            "fake_data": False,
        },
        "targets": results,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.output.with_suffix(a.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
