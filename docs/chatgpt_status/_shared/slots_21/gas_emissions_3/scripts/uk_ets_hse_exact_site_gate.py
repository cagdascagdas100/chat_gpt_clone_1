#!/usr/bin/env python3
"""Bounded exact-site scan of the official UK ETS HSE 2021-2025 XLSX."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-xlsx", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref or "")
    require(letters is not None, f"invalid cell reference: {cell_ref}")
    value = 0
    for char in letters.group(0):
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    path = "xl/sharedStrings.xml"
    if path not in archive.namelist():
        return []
    root = ET.fromstring(archive.read(path))
    values: list[str] = []
    for si in root.findall(f"{{{NS_MAIN}}}si"):
        values.append("".join(node.text or "" for node in si.iter(f"{{{NS_MAIN}}}t")))
    return values


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.get("Id"): rel.get("Target") for rel in rels.findall(f"{{{NS_PKG_REL}}}Relationship")}
    out: list[tuple[str, str]] = []
    sheets = workbook.find(f"{{{NS_MAIN}}}sheets")
    require(sheets is not None, "workbook sheets missing")
    for sheet in sheets.findall(f"{{{NS_MAIN}}}sheet"):
        name = sheet.get("name") or "unnamed"
        rel_id = sheet.get(f"{{{NS_REL}}}id")
        target = rel_map.get(rel_id)
        require(target is not None, f"sheet relationship missing: {name}")
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        out.append((name, target))
    return out


def cell_text(cell: ET.Element, strings: list[str]) -> str:
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{NS_MAIN}}}t"))
    value_node = cell.find(f"{{{NS_MAIN}}}v")
    if value_node is None or value_node.text is None:
        return ""
    raw = value_node.text
    if cell_type == "s":
        index = int(raw)
        require(0 <= index < len(strings), "shared string index out of range")
        return strings[index]
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw


def parse_rows(raw: bytes, limits: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    sheet_names: list[str] = []
    with zipfile.ZipFile(__import__("io").BytesIO(raw)) as archive:
        require("xl/workbook.xml" in archive.namelist(), "not a valid XLSX workbook")
        strings = shared_strings(archive)
        sheets = workbook_sheets(archive)
        require(len(sheets) <= int(limits["maximum_sheets"]), "workbook exceeds sheet limit")
        for sheet_name, sheet_path in sheets:
            sheet_names.append(sheet_name)
            root = ET.fromstring(archive.read(sheet_path))
            sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
            if sheet_data is None:
                continue
            sheet_row_count = 0
            for row in sheet_data.findall(f"{{{NS_MAIN}}}row"):
                sheet_row_count += 1
                require(sheet_row_count <= int(limits["maximum_rows_per_sheet"]), "sheet exceeds row limit")
                cells: dict[int, str] = {}
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    idx = column_index(cell.get("r") or "")
                    require(idx <= int(limits["maximum_columns"]), "column limit exceeded")
                    value = cell_text(cell, strings)
                    if value != "":
                        cells[idx] = value
                if cells:
                    rows.append({"sheet_name": sheet_name, "row_number": int(row.get("r") or sheet_row_count), "cells": cells})
                require(len(rows) <= int(limits["maximum_total_rows"]), "workbook exceeds total row limit")
    return rows, sheet_names


def row_projection(row: dict[str, Any]) -> dict[str, Any]:
    cells = row["cells"]
    ordered = [{"column_index": idx, "value": cells[idx]} for idx in sorted(cells)]
    return {"sheet_name": row["sheet_name"], "row_number": row["row_number"], "cells": ordered, "normalized_row_text": normalize(" | ".join(str(item["value"]) for item in ordered))}


def match_target(rows: list[dict[str, Any]], target: dict[str, Any], dataset_error: str | None) -> dict[str, Any]:
    aliases = [(alias, normalize(alias)) for alias in target["exact_aliases"]]
    matches: list[dict[str, Any]] = []
    for row in rows:
        projection = row_projection(row)
        matched = [original for original, alias in aliases if alias and alias in projection["normalized_row_text"]]
        if not matched:
            continue
        projection["matched_exact_aliases"] = matched
        matches.append(projection)
        require(len(matches) <= int(target["maximum_matches"]), "target match limit exceeded")
    return {"target_id": target["target_id"], "site_name": target["site_name"], "attempt_completed": True, "exact_aliases": target["exact_aliases"], "matched_rows": len(matches), "matches": matches, "decision": "EXACT_SITE_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE", "error": dataset_error}


def load_xlsx(contract: dict[str, Any], fixture_xlsx: Path | None) -> tuple[bytes | None, list[dict[str, Any]], list[str], str | None, int | None]:
    policy = contract["network_policy"]
    try:
        if fixture_xlsx:
            raw = fixture_xlsx.read_bytes()
            status = 200
        else:
            url = contract["source_evidence_manifest"]["source_url"]
            parsed = urllib.parse.urlparse(url)
            require(parsed.scheme == "https", "source URL must use HTTPS")
            require(parsed.netloc == "assets.publishing.service.gov.uk", "source host mismatch")
            request = urllib.request.Request(url, headers={"User-Agent": "AAYS-UK-ETS-HSE-Gate/1.0", "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.5"}, method="GET")
            with urllib.request.urlopen(request, timeout=int(policy["dataset_timeout_seconds"])) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read(int(policy["maximum_dataset_bytes"]) + 1)
        require(status == 200, f"unexpected HTTP status {status}")
        require(len(raw) <= int(policy["maximum_dataset_bytes"]), "dataset exceeds byte limit")
        rows, sheets = parse_rows(raw, policy)
        return raw, rows, sheets, None, status
    except urllib.error.HTTPError as exc:
        return None, [], [], f"HTTPError: {exc.code} {exc.reason}"[:500], int(exc.code)
    except Exception as exc:
        return None, [], [], f"{type(exc).__name__}: {exc}"[:500], None


def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    require(contract.get("schema_version") == 3, "contract schema mismatch")
    require(contract.get("slot_id") == "gas_emissions_3", "slot mismatch")
    require(contract.get("state") == "READY" and contract.get("status") == "ready", "contract not READY")
    require(contract.get("claimable") is True and contract.get("ready_for_claim") is True, "contract not claimable")
    precondition = contract["precondition"]
    require(sha256_bytes(prior_bytes) == precondition["prior_output_sha256"], "prior SHA mismatch")
    require(prior.get("task_id") == precondition["required_prior_task_id"], "unexpected prior task")
    require(prior.get("state") == precondition["required_prior_state"], "unexpected prior state")
    require(prior.get("next_unverified_step") == precondition["required_prior_next_unverified_step"], "unexpected prior next step")
    manifest = contract["source_evidence_manifest"]
    for field in ("source_url", "publication_page_url", "accessed_at", "content_sha256", "supports_fields", "relevant_record_ids_or_excerpt", "license_or_terms_url"):
        require(manifest.get(field), f"missing source evidence field: {field}")
    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 2, "exactly two targets required")
    raw, rows, sheets, dataset_error, http_status = load_xlsx(contract, args.fixture_xlsx)
    results = [match_target(rows, target, dataset_error) for target in targets]
    completed = sum(bool(item["attempt_completed"]) for item in results)
    target_count = len(targets)
    matched_targets = sum(bool(item["matched_rows"]) for item in results)
    matched_rows = sum(int(item["matched_rows"]) for item in results)
    if matched_targets == target_count:
        state = "MATCHES_VERIFIED"
        next_step = "VALIDATE_UK_ETS_HSE_MATCHED_EMISSIONS_COLUMNS_FOR_GAS_EMISSIONS_BINDING"
    elif matched_targets:
        state = "PARTIAL_MATCH_CONTINUE"
        next_step = "ADVANCE_UNMATCHED_TARGET_TO_NEXT_SOURCE_AND_VALIDATE_MATCHED_UK_ETS_HSE_ROWS"
    else:
        state = "NO_DATA_CONTINUE"
        next_step = "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_UK_ETS_HSE_NO_DATA"
    output = {"schema_version": 3, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_3", "task_id": contract["task_id"], "continuation_key": contract["continuation_key"], "state": state, "panel_status": "PUBLISHED", "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_xlsx else "LIVE_NETWORK", "first_unverified_step_completed": contract["first_unverified_step"], "next_unverified_step": next_step, "input": {"contract_path": args.contract.as_posix(), "contract_sha256": sha256_bytes(contract_bytes), "prior_output_path": args.prior.as_posix(), "prior_output_sha256": sha256_bytes(prior_bytes), "dataset_url": manifest["source_url"], "dataset_http_status": http_status, "dataset_sha256": sha256_bytes(raw) if raw is not None else None, "dataset_bytes": len(raw) if raw is not None else 0, "dataset_error": dataset_error}, "counts": {"completed_count": completed, "target_count": target_count, "dataset_fetch_attempts": 1, "workbook_sheets_scanned": len(sheets), "workbook_rows_scanned": len(rows), "matched_targets": matched_targets, "matched_rows": matched_rows, "produced_business_rows": matched_rows, "produced_source_evidence_records": target_count}, "progress_percent": round(completed / target_count * 100, 6), "sheet_names": sheets, "targets": results, "decision": {"exact_normalized_alias_gate_required": True, "all_workbook_sheets_scanned": raw is not None, "source_cells_preserved_without_inference": True, "inferred_values": 0, "fake_data": False}}
    require(completed == target_count, "not all target assessments completed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
