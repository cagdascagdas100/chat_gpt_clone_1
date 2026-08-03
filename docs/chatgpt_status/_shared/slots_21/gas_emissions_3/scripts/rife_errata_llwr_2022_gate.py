#!/usr/bin/env python3
"""Verify the official RIFE errata correction for the LLWR 2022 gaseous/direct dose."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9.<]+", " ", text.lower()).split())


class BlockParser(HTMLParser):
    BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "caption", "th", "td"}

    def __init__(self, max_blocks: int, max_chars: int) -> None:
        super().__init__(convert_charrefs=True)
        self.max_blocks = max_blocks
        self.max_chars = max_chars
        self.stack: list[dict[str, Any]] = []
        self.blocks: list[dict[str, str]] = []
        self.total_chars = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.BLOCK_TAGS:
            self.stack.append({"tag": tag, "parts": []})

    def handle_data(self, data: str) -> None:
        if not self.stack:
            return
        for item in self.stack:
            item["parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            item = self.stack[index]
            if item["tag"] != tag:
                continue
            self.stack = self.stack[:index]
            text = " ".join(html.unescape("".join(item["parts"])).split())
            if text:
                self.total_chars += len(text)
                if len(self.blocks) >= self.max_blocks:
                    raise ValueError("HTML block limit exceeded")
                if self.total_chars > self.max_chars:
                    raise ValueError("HTML text limit exceeded")
                self.blocks.append({"tag": tag, "text": text})
            return


def fetch(url: str, timeout: int, limit: int) -> dict[str, Any]:
    result: dict[str, Any] = {"status": None, "raw": None, "content_type": None, "error": None}
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "www.gov.uk":
            raise ValueError("source URL host or scheme mismatch")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AAYS-RIFE-Errata-Gate/1.0", "Accept": "text/html,*/*;q=0.5"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            raw = response.read(limit + 1)
            content_type = response.headers.get("Content-Type")
        if status != 200:
            raise ValueError(f"unexpected HTTP status {status}")
        if len(raw) > limit:
            raise ValueError("HTML response exceeds byte limit")
        result.update({"status": status, "raw": raw, "content_type": content_type})
    except urllib.error.HTTPError as exc:
        result.update({"status": int(exc.code), "error": f"HTTPError: {exc.code} {exc.reason}"[:500]})
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return result


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("HTML payload could not be decoded")


def extract(blocks: list[dict[str, str]], target: dict[str, Any]) -> dict[str, Any]:
    heading_phrase = norm(target["required_section_heading"])
    total_phrase = norm(target["required_total_dose_phrase"])
    source_phrase = norm(target["required_source_specific_phrase"])
    heading_index: int | None = None
    should_read_index: int | None = None
    paragraph_index: int | None = None

    for i, block in enumerate(blocks):
        if block["tag"].startswith("h") and heading_phrase in norm(block["text"]):
            heading_index = i
            break
    if heading_index is None:
        return {"matched": False, "error": "required LLWR errata section heading not found", "match": None}

    section_end = len(blocks)
    heading_level = int(blocks[heading_index]["tag"][1])
    for i in range(heading_index + 1, len(blocks)):
        tag = blocks[i]["tag"]
        if tag.startswith("h") and int(tag[1]) <= heading_level:
            section_end = i
            break

    for i in range(heading_index + 1, section_end):
        if norm(blocks[i]["text"]) == "should read":
            should_read_index = i
            break
    if should_read_index is None:
        return {"matched": False, "error": "Should read marker not found in LLWR errata section", "match": None}

    for i in range(should_read_index + 1, section_end):
        block_norm = norm(blocks[i]["text"])
        if total_phrase in block_norm and source_phrase in block_norm:
            paragraph_index = i
            break
    if paragraph_index is None:
        return {"matched": False, "error": "corrected LLWR paragraph with both required values not found", "match": None}

    paragraph = blocks[paragraph_index]["text"]
    return {
        "matched": True,
        "error": None,
        "match": {
            "section_heading": blocks[heading_index]["text"],
            "marker": blocks[should_read_index]["text"],
            "corrected_paragraph": paragraph,
            "verified_source_values": {
                "inventory_year": "2022",
                "llwr_total_dose_from_gaseous_releases_and_direct_radiation_mSv": "0.030",
                "source_specific_exposure_mSv": "<0.005",
            },
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-html", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)

    if contract.get("schema_version") != 3 or contract.get("slot_id") != "gas_emissions_3":
        raise ValueError("contract identity mismatch")
    if contract.get("state") != "READY" or contract.get("status") != "ready":
        raise ValueError("contract is not READY")
    if not contract.get("claimable") or not contract.get("ready_for_claim"):
        raise ValueError("contract is not claimable")

    pre = contract["precondition"]
    if hashlib.sha256(prior_bytes).hexdigest() != pre["prior_output_sha256"]:
        raise ValueError("prior SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    if prior.get("state") != pre["required_prior_state"]:
        raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")

    manifest = contract["source_evidence_manifest"]
    for field in (
        "source_url",
        "publication_page_url",
        "accessed_at",
        "content_sha256",
        "supports_fields",
        "relevant_record_ids_or_excerpt",
        "license_or_terms_url",
    ):
        if not manifest.get(field):
            raise ValueError(f"missing source evidence field: {field}")

    targets = contract["runtime_targets"]
    if len(targets) != 1:
        raise ValueError("exactly one LLWR target required")
    target = targets[0]
    policy = contract["network_policy"]

    fetch_attempts = 1
    if args.fixture_html:
        result = {"status": 200, "raw": args.fixture_html.read_bytes(), "content_type": "text/html", "error": None}
        execution_mode = "SYNTHETIC_FIXTURE"
    else:
        result = fetch(manifest["source_url"], int(policy["page_timeout_seconds"]), int(policy["maximum_html_bytes"]))
        execution_mode = "LIVE_NETWORK"

    blocks: list[dict[str, str]] = []
    match_result = {"matched": False, "error": result["error"], "match": None}
    parse_error: str | None = result["error"]
    if result["raw"] is not None:
        try:
            parser = BlockParser(int(policy["maximum_blocks"]), int(policy["maximum_text_chars"]))
            parser.feed(decode(result["raw"]))
            parser.close()
            blocks = parser.blocks
            match_result = extract(blocks, target)
            parse_error = match_result["error"]
        except Exception as exc:
            parse_error = f"{type(exc).__name__}: {exc}"[:500]

    matched = bool(match_result["matched"])
    state = "EXACT_CORRECTION_VERIFIED" if matched else "NO_DATA_CONTINUE"
    next_step = (
        "VALIDATE_RIFE_ERRATA_LLWR_2022_CORRECTION_FOR_GAS_EMISSIONS_MODEL"
        if matched
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_RIFE_ERRATA_NO_DATA"
    )
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": execution_mode,
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": str(args.contract).replace("\\", "/"),
            "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
            "prior_output_path": str(args.prior).replace("\\", "/"),
            "prior_output_sha256": hashlib.sha256(prior_bytes).hexdigest(),
            "source_url": manifest["source_url"],
            "http_status": result["status"],
            "html_sha256": hashlib.sha256(result["raw"]).hexdigest() if result["raw"] is not None else None,
            "html_bytes": len(result["raw"]) if result["raw"] is not None else 0,
            "source_error": parse_error,
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "html_fetch_attempts": fetch_attempts,
            "blocks_scanned": len(blocks),
            "matched_targets": 1 if matched else 0,
            "matched_rows": 1 if matched else 0,
            "produced_business_rows": 1 if matched else 0,
            "produced_source_evidence_records": 1,
        },
        "progress_percent": 100.0,
        "targets": [
            {
                "target_id": target["target_id"],
                "site_name": target["site_name"],
                "attempt_completed": True,
                "matched_rows": 1 if matched else 0,
                "matches": [match_result["match"]] if matched else [],
                "decision": state,
                "error": parse_error,
            }
        ],
        "decision": {
            "exact_section_heading_required": True,
            "should_read_marker_required": True,
            "both_corrected_values_required": True,
            "source_text_preserved_without_inference": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
