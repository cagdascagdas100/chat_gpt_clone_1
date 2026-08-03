#!/usr/bin/env python3
"""Scan the official EA annual regulated-installation CO2 XLSX for exact LLWR rows."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import unicodedata
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MAX_BYTES = 64 * 1024 * 1024
MAX_SHEETS = 100
MAX_ROWS_PER_SHEET = 500_000
MAX_TOTAL_ROWS = 1_000_000
MAX_COLS = 256

def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def col_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "")
    if not letters:
        return 0
    value = 0
    for ch in letters.group(0):
        value = value * 26 + (ord(ch) - 64)
    return value - 1

def shared_strings(zf: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(name))
    values = []
    for si in root.findall(f"{NS_MAIN}si"):
        values.append("".join(t.text or "" for t in si.iter(f"{NS_MAIN}t")))
    return values

def workbook_sheets(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall(f"{NS_PKG_REL}Relationship")}
    out = []
    sheets = wb.find(f"{NS_MAIN}sheets")
    if sheets is None:
        return out
    for sheet in sheets.findall(f"{NS_MAIN}sheet")[:MAX_SHEETS]:
        rid = sheet.attrib.get(f"{NS_REL}id")
        target = rel_map.get(rid, "")
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = "xl/" + target.lstrip("/")
        out.append((sheet.attrib.get("name", ""), path))
    return out

def cell_value(cell: ET.Element, shared: list[str]) -> str:
    typ = cell.attrib.get("t")
    if typ == "inlineStr":
        return "".join(t.text or "" for t in cell.iter(f"{NS_MAIN}t"))
    v = cell.find(f"{NS_MAIN}v")
    raw = "" if v is None else (v.text or "")
    if typ == "s" and raw.isdigit():
        idx = int(raw)
        return shared[idx] if 0 <= idx < len(shared) else raw
    if typ == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw

def scan_xlsx(data: bytes, aliases: list[str]) -> dict[str, Any]:
    aliases_n = {norm(a) for a in aliases}
    matched = []
    sheets_scanned = 0
    rows_scanned = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared = shared_strings(zf)
        for sheet_name, path in workbook_sheets(zf):
            if path not in zf.namelist():
                continue
            sheets_scanned += 1
            header_context: list[list[str]] = []
            with zf.open(path) as fh:
                for event, elem in ET.iterparse(fh, events=("end",)):
                    if elem.tag != f"{NS_MAIN}row":
                        continue
                    rows_scanned += 1
                    if rows_scanned > MAX_TOTAL_ROWS:
                        raise ValueError("total row limit exceeded")
                    row_no = int(elem.attrib.get("r", rows_scanned))
                    if row_no > MAX_ROWS_PER_SHEET:
                        raise ValueError("sheet row limit exceeded")
                    cells = [""] * MAX_COLS
                    populated = 0
                    for cell in elem.findall(f"{NS_MAIN}c"):
                        idx = col_index(cell.attrib.get("r", ""))
                        if 0 <= idx < MAX_COLS:
                            value = cell_value(cell, shared)
                            cells[idx] = value
                            if value != "":
                                populated += 1
                    while cells and cells[-1] == "":
                        cells.pop()
                    if row_no <= 25 and populated:
                        header_context.append(cells)
                    row_norm = [norm(x) for x in cells]
                    alias_hit = any(v in aliases_n for v in row_norm)
                    numeric_cells = [
                        {"column_index": i, "value": v}
                        for i, v in enumerate(cells)
                        if re.fullmatch(r"[-+]?\d+(?:[.,]\d+)?", str(v).strip())
                    ]
                    header_text = norm(" ".join(" ".join(r) for r in header_context))
                    emissions_context = any(term in header_text for term in (
                        "co2", "carbon dioxide", "emission", "tonnes", "tco2e"
                    ))
                    if alias_hit and numeric_cells and emissions_context:
                        matched.append({
                            "sheet": sheet_name,
                            "row_number": row_no,
                            "source_cells": [
                                {"column_index": i, "value": v}
                                for i, v in enumerate(cells) if v != ""
                            ],
                            "numeric_cells": numeric_cells,
                            "header_context": header_context,
                        })
                    elem.clear()
    return {
        "sheets_scanned": sheets_scanned,
        "rows_scanned": rows_scanned,
        "matched_rows": matched,
    }

def fetch(url: str, timeout: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "AAYS-gas-emissions-3/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("download size limit exceeded")
    return data

def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    if contract.get("schema_version") != 3 or contract.get("state") != "READY":
        raise ValueError("contract is not schema-v3 READY")
    if sha256_bytes(prior_bytes) != contract["precondition"]["prior_output_sha256"]:
        raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != contract["precondition"]["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    target = contract["runtime_targets"][0]
    url = contract["source_evidence_manifest"]["download_url"]
    attempts = 1
    error = None
    workbook_sha = None
    workbook_bytes = 0
    scan = {"sheets_scanned": 0, "rows_scanned": 0, "matched_rows": []}
    try:
        data = fetch(url, int(contract["network_policy"]["request_timeout_seconds"]))
        workbook_sha = sha256_bytes(data)
        workbook_bytes = len(data)
        scan = scan_xlsx(data, target["exact_aliases"])
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    matches = scan["matched_rows"]
    state = "EXACT_SITE_CO2_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE"
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "LIVE_NETWORK",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": (
            "VALIDATE_AND_PUBLISH_EA_ANNUAL_CO2_EXACT_LLWR_ROWS"
            if matches else
            "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_EA_ANNUAL_CO2_NO_DATA"
        ),
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "source_url": url,
            "workbook_sha256": workbook_sha,
            "workbook_bytes": workbook_bytes,
            "source_error": error,
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "download_attempts": attempts,
            "sheets_scanned": scan["sheets_scanned"],
            "rows_scanned": scan["rows_scanned"],
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": 1 + len(matches),
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": target["target_id"],
            "site_name": target["site_name"],
            "attempt_completed": True,
            "matched_rows": len(matches),
            "matches": matches,
            "decision": state,
            "error": error,
        }],
        "decision": {
            "exact_alias_required": True,
            "numeric_cell_required": True,
            "emissions_header_context_required": True,
            "source_cells_preserved_without_field_inference": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
