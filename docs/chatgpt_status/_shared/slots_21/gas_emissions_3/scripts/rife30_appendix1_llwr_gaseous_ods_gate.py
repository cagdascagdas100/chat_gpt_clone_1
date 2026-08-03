#!/usr/bin/env python3
"""Scan the official RIFE 30 Appendix 1 ODS for explicit LLWR gaseous disposal rows."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

MAX_ASSET_BYTES = 2 * 1024 * 1024
MAX_CONTENT_XML_BYTES = 12 * 1024 * 1024
MAX_SHEETS = 32
MAX_ROWS = 25000
MAX_CELLS_PER_ROW = 256
ALLOWED_HOST = "assets.publishing.service.gov.uk"
ODS_MIMETYPE = "application/vnd.oasis.opendocument.spreadsheet"
NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
}
GAS_TERMS = ("gaseous", "gas discharge", "gaseous discharge", "discharge to air", "air discharge")
UNIT_RE = re.compile(r"(?i)\b(?:bq|kbq|mbq|gbq|tbq|pbq)(?:\s*(?:y|yr|year)\s*[-/]?\s*1)?\b")
NUMBER_RE = re.compile(r"(?<![A-Za-z])(?:<|≤|~|approximately\s+|around\s+)?\d[\d,]*(?:\.\d+)?(?:\s*[Ee][+-]?\d+)?")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--source-manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def norm(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())

def read_repeated_int(element: ET.Element, attr: str, default: int = 1, maximum: int = 10000) -> int:
    raw = element.attrib.get(f"{{{NS['table']}}}{attr}")
    if raw is None:
        return default
    value = int(raw)
    if value < 1 or value > maximum:
        raise ValueError(f"invalid {attr}")
    return value

def cell_text(cell: ET.Element) -> str:
    parts = []
    for node in cell.iter():
        if node.tag == f"{{{NS['text']}}}p":
            text = "".join(node.itertext()).strip()
            if text:
                parts.append(text)
    if not parts:
        value = cell.attrib.get(f"{{{NS['office']}}}string-value")
        if value:
            parts.append(value.strip())
    return " ".join(parts)

def parse_ods_rows(data: bytes) -> tuple[list[dict[str, Any]], int]:
    if len(data) > MAX_ASSET_BYTES:
        raise ValueError("ODS asset exceeds byte limit")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = set(zf.namelist())
        if "content.xml" not in names:
            raise ValueError("ODS content.xml missing")
        if "mimetype" in names:
            mime = zf.read("mimetype").decode("ascii", errors="strict").strip()
            if mime != ODS_MIMETYPE:
                raise ValueError("unexpected ODS mimetype")
        info = zf.getinfo("content.xml")
        if info.file_size > MAX_CONTENT_XML_BYTES:
            raise ValueError("content.xml exceeds byte limit")
        content = zf.read("content.xml")
    root = ET.fromstring(content)
    results: list[dict[str, Any]] = []
    total_rows = 0
    tables = root.findall(".//table:table", NS)
    if len(tables) > MAX_SHEETS:
        raise ValueError("sheet limit exceeded")
    for table in tables:
        sheet = table.attrib.get(f"{{{NS['table']}}}name", "")
        physical_row = 0
        for row in table.findall("table:table-row", NS):
            repeat_rows = read_repeated_int(row, "number-rows-repeated", maximum=5000)
            cells: list[str] = []
            for cell in list(row):
                if cell.tag not in {
                    f"{{{NS['table']}}}table-cell",
                    f"{{{NS['table']}}}covered-table-cell",
                }:
                    continue
                repeat_cells = read_repeated_int(cell, "number-columns-repeated", maximum=MAX_CELLS_PER_ROW)
                text = cell_text(cell)
                remaining = MAX_CELLS_PER_ROW - len(cells)
                if remaining <= 0:
                    break
                cells.extend([text] * min(repeat_cells, remaining))
            while cells and not cells[-1]:
                cells.pop()
            row_text = " | ".join(cells)
            for _ in range(repeat_rows):
                physical_row += 1
                total_rows += 1
                if total_rows > MAX_ROWS:
                    raise ValueError("row limit exceeded")
                if row_text:
                    results.append({"sheet": sheet, "row_index": physical_row, "cells": cells, "row_text": row_text})
    return results, len(tables)

def fetch_asset(url: str, timeout_seconds: int) -> tuple[bytes | None, dict[str, Any]]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise ValueError("source asset URL is not allowed")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-gas-emissions-3-rife30-appendix1-gate/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type")
            data = response.read(MAX_ASSET_BYTES + 1)
            if len(data) > MAX_ASSET_BYTES:
                raise ValueError("response exceeds byte limit")
            return data, {
                "attempted": True,
                "status": status,
                "content_type": content_type,
                "bytes_received": len(data),
                "asset_sha256": sha256_bytes(data),
                "error_type": None,
                "error": None,
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout, OSError) as exc:
        return None, {
            "attempted": True,
            "status": getattr(exc, "code", None),
            "content_type": None,
            "bytes_received": 0,
            "asset_sha256": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    manifest_bytes = args.source_manifest.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    manifest = json.loads(manifest_bytes)

    if contract.get("schema_version") != 3 or contract.get("state") != "READY":
        raise ValueError("contract is not schema-v3 READY")
    pre = contract["precondition"]
    if sha256_bytes(prior_bytes) != pre["prior_output_sha256"]:
        raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    if prior.get("state") != pre["required_prior_state"]:
        raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")
    if sha256_bytes(manifest_bytes) != contract["source_evidence_manifest"]["source_manifest_sha256"]:
        raise ValueError("source manifest SHA mismatch")
    for record in manifest.get("records", []):
        if sha256_bytes(record["text"].encode("utf-8")) != record["sha256"]:
            raise ValueError("source evidence record SHA mismatch")

    asset_url = manifest["source_asset_url"]
    asset_data, fetch = fetch_asset(asset_url, int(contract["network_policy"]["request_timeout_seconds"]))
    rows: list[dict[str, Any]] = []
    sheet_count = 0
    parse_error = None
    if asset_data is not None:
        try:
            rows, sheet_count = parse_ods_rows(asset_data)
        except (ValueError, zipfile.BadZipFile, ET.ParseError, UnicodeError) as exc:
            parse_error = f"{type(exc).__name__}: {exc}"

    matches: list[dict[str, Any]] = []
    candidate_rows = 0
    if asset_data is not None and parse_error is None:
        for row in rows:
            n = norm(row["row_text"])
            site_ok = "low level waste repository" in n or re.search(r"\bllwr\b", n) is not None
            gas_ok = any(term in n for term in GAS_TERMS)
            numeric_ok = NUMBER_RE.search(row["row_text"]) is not None
            unit_match = UNIT_RE.search(row["row_text"])
            if site_ok and gas_ok:
                candidate_rows += 1
            if site_ok and gas_ok and numeric_ok and unit_match:
                matches.append({
                    "row_id": f"RIFE30_APPENDIX1_LLWR_GASEOUS_{len(matches)+1}",
                    "metric_type": "radioactive_gaseous_disposal_or_discharge",
                    "sheet": row["sheet"],
                    "row_index": row["row_index"],
                    "source_row_text": row["row_text"],
                    "source_cells": row["cells"],
                    "source_unit_token": unit_match.group(0),
                    "unit_conversion_applied": False,
                    "value_inferred": False,
                })

    state = "EXACT_LLWR_GASEOUS_DISPOSAL_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE"
    blocker = "NONE"
    if not matches:
        if fetch["error"]:
            blocker = "OFFICIAL_RIFE30_APPENDIX1_ODS_FETCH_FAILED"
        elif parse_error:
            blocker = "OFFICIAL_RIFE30_APPENDIX1_ODS_PARSE_FAILED"
        else:
            blocker = "OFFICIAL_RIFE30_APPENDIX1_ODS_HAS_NO_EXPLICIT_LLWR_GASEOUS_NUMERIC_ROW"

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "BOUNDED_OFFICIAL_ODS_NETWORK_FETCH_AND_XML_SCAN",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": (
            "VALIDATE_AND_PUBLISH_RIFE30_APPENDIX1_EXACT_LLWR_GASEOUS_ROWS"
            if matches
            else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_RIFE30_APPENDIX1_NO_DATA"
        ),
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "source_manifest_path": str(args.source_manifest),
            "source_manifest_sha256": sha256_bytes(manifest_bytes),
            "source_page_url": manifest["source_page_url"],
            "source_asset_url": asset_url,
        },
        "fetch": fetch,
        "parse": {
            "parse_error": parse_error,
            "sheet_count": sheet_count,
            "rows_scanned": len(rows),
            "candidate_rows": candidate_rows,
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "records_scanned": len(rows),
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": len(manifest.get("records", [])),
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": contract["runtime_targets"][0]["target_id"],
            "site_name": "Low Level Waste Repository",
            "attempt_completed": True,
            "decision": state,
            "matched_rows": len(matches),
            "matches": matches,
        }],
        "decision": {
            "blocker": blocker,
            "official_asset_only": True,
            "explicit_site_gas_numeric_row_required": True,
            "no_unit_conversion": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
