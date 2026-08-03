#!/usr/bin/env python3
"""Bounded exact-site scan of the official Environment Agency Pollution Inventory ZIP."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import posixpath
import re
import struct
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Iterable

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
TEXT_SUFFIXES = {".csv", ".tsv", ".txt", ".xml", ".json", ".geojson"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-zip", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def decode_text(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("text member cannot be decoded as utf-8-sig, utf-16 or cp1252")


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
    return ["".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t")) for item in root.findall(f"{{{NS_MAIN}}}si")]


def workbook_sheets(archive: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.get("Id"): rel.get("Target") for rel in rels.findall(f"{{{NS_PKG_REL}}}Relationship")}
    sheets_node = workbook.find(f"{{{NS_MAIN}}}sheets")
    require(sheets_node is not None, "workbook sheets missing")
    out: list[tuple[str, str]] = []
    for sheet in sheets_node.findall(f"{{{NS_MAIN}}}sheet"):
        name = sheet.get("name") or "unnamed"
        target = rel_map.get(sheet.get(f"{{{NS_REL}}}id"))
        require(target is not None, f"sheet relationship missing: {name}")
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = posixpath.normpath(posixpath.join("xl", target))
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


def parse_xlsx_rows(raw: bytes, member_name: str, policy: dict[str, Any]) -> Iterable[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require("xl/workbook.xml" in archive.namelist(), "not a valid XLSX workbook")
        strings = shared_strings(archive)
        sheets = workbook_sheets(archive)
        require(len(sheets) <= int(policy["maximum_workbook_sheets"]), "workbook exceeds sheet limit")
        for sheet_name, sheet_path in sheets:
            root = ET.fromstring(archive.read(sheet_path))
            sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
            if sheet_data is None:
                continue
            sheet_rows = 0
            for row in sheet_data.findall(f"{{{NS_MAIN}}}row"):
                sheet_rows += 1
                require(sheet_rows <= int(policy["maximum_rows_per_member"]), "XLSX sheet exceeds row limit")
                cells: list[dict[str, Any]] = []
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    index = column_index(cell.get("r") or "")
                    require(index <= int(policy["maximum_columns"]), "XLSX column limit exceeded")
                    value = cell_text(cell, strings)
                    if value != "":
                        cells.append({"column_index": index, "value": value})
                if cells:
                    yield {
                        "member_name": member_name,
                        "member_format": "xlsx",
                        "sheet_name": sheet_name,
                        "row_number": int(row.get("r") or sheet_rows),
                        "cells": cells,
                    }


def parse_text_rows(raw: bytes, member_name: str, suffix: str, policy: dict[str, Any]) -> Iterable[dict[str, Any]]:
    text, encoding = decode_text(raw)
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        if suffix == ".csv":
            try:
                delimiter = csv.Sniffer().sniff(text[:65536], delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        for row_number, row in enumerate(reader, start=1):
            require(row_number <= int(policy["maximum_rows_per_member"]), "text member exceeds row limit")
            require(len(row) <= int(policy["maximum_columns"]), "text member exceeds column limit")
            cells = [{"column_index": index, "value": value} for index, value in enumerate(row, start=1) if value != ""]
            if cells:
                yield {
                    "member_name": member_name,
                    "member_format": suffix.lstrip("."),
                    "encoding": encoding,
                    "row_number": row_number,
                    "cells": cells,
                }
        return
    for row_number, line in enumerate(text.splitlines(), start=1):
        require(row_number <= int(policy["maximum_rows_per_member"]), "text member exceeds row limit")
        if line.strip():
            yield {
                "member_name": member_name,
                "member_format": suffix.lstrip("."),
                "encoding": encoding,
                "row_number": row_number,
                "cells": [{"column_index": 1, "value": line[:10000]}],
            }


def parse_dbf_rows(raw: bytes, member_name: str, policy: dict[str, Any]) -> Iterable[dict[str, Any]]:
    require(len(raw) >= 33, "DBF member too short")
    record_count = struct.unpack_from("<I", raw, 4)[0]
    header_length = struct.unpack_from("<H", raw, 8)[0]
    record_length = struct.unpack_from("<H", raw, 10)[0]
    require(33 <= header_length <= len(raw), "invalid DBF header length")
    require(record_length > 1, "invalid DBF record length")
    require(record_count <= int(policy["maximum_rows_per_member"]), "DBF exceeds row limit")
    fields: list[tuple[str, int]] = []
    offset = 32
    while offset + 32 <= header_length and raw[offset] != 0x0D:
        descriptor = raw[offset : offset + 32]
        name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii", errors="replace") or f"field_{len(fields)+1}"
        length = int(descriptor[16])
        require(length > 0, "invalid DBF field length")
        fields.append((name, length))
        offset += 32
    require(len(fields) <= int(policy["maximum_columns"]), "DBF exceeds column limit")
    for record_index in range(record_count):
        start = header_length + record_index * record_length
        end = start + record_length
        if end > len(raw):
            break
        record = raw[start:end]
        if not record or record[0:1] == b"*":
            continue
        cells: list[dict[str, Any]] = []
        cursor = 1
        for column, (name, length) in enumerate(fields, start=1):
            value = record[cursor : cursor + length].decode("cp1252", errors="replace").strip()
            cursor += length
            if value:
                cells.append({"column_index": column, "field_name": name, "value": value})
        if cells:
            yield {
                "member_name": member_name,
                "member_format": "dbf",
                "row_number": record_index + 1,
                "cells": cells,
            }


def row_text(row: dict[str, Any]) -> str:
    return normalize(" | ".join(str(cell.get("value", "")) for cell in row["cells"]))


def scan_archive(raw: bytes, target: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    aliases = [(alias, normalize(alias)) for alias in target["exact_aliases"]]
    matches: list[dict[str, Any]] = []
    supported_members: list[str] = []
    unsupported_members: list[str] = []
    rows_scanned = 0
    total_uncompressed = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        require(len(infos) <= int(policy["maximum_members"]), "archive exceeds member limit")
        for info in infos:
            normalized_name = posixpath.normpath(info.filename.replace("\\", "/"))
            require(not normalized_name.startswith("../") and normalized_name != "..", "archive path traversal detected")
            require(info.file_size <= int(policy["maximum_member_bytes"]), "archive member exceeds byte limit")
            total_uncompressed += int(info.file_size)
            require(total_uncompressed <= int(policy["maximum_total_uncompressed_bytes"]), "archive exceeds total uncompressed byte limit")
            suffix = Path(normalized_name).suffix.lower()
            if suffix not in TEXT_SUFFIXES | {".xlsx", ".dbf"}:
                unsupported_members.append(normalized_name)
                continue
            supported_members.append(normalized_name)
            member_raw = archive.read(info)
            if suffix == ".xlsx":
                rows = parse_xlsx_rows(member_raw, normalized_name, policy)
            elif suffix == ".dbf":
                rows = parse_dbf_rows(member_raw, normalized_name, policy)
            else:
                rows = parse_text_rows(member_raw, normalized_name, suffix, policy)
            for row in rows:
                rows_scanned += 1
                require(rows_scanned <= int(policy["maximum_total_rows"]), "archive exceeds total row limit")
                normalized = row_text(row)
                matched_aliases = [original for original, alias in aliases if alias and alias in normalized]
                if matched_aliases:
                    row["matched_exact_aliases"] = matched_aliases
                    row["normalized_row_text"] = normalized
                    matches.append(row)
                    require(len(matches) <= int(target["maximum_matches"]), "target match limit exceeded")
    return {
        "archive_members_total": len(infos),
        "supported_members_scanned": supported_members,
        "unsupported_members": unsupported_members,
        "rows_scanned": rows_scanned,
        "matches": matches,
    }


def load_archive(contract: dict[str, Any], fixture_zip: Path | None) -> dict[str, Any]:
    manifest = contract["source_evidence_manifest"]
    policy = contract["network_policy"]
    result: dict[str, Any] = {"raw": None, "status": None, "error": None}
    try:
        if fixture_zip:
            raw, status = fixture_zip.read_bytes(), 200
        else:
            url = manifest["source_url"]
            parsed = urllib.parse.urlparse(url)
            require(parsed.scheme == "https", "source URL must use HTTPS")
            require(parsed.netloc == "environment.data.gov.uk", "source host mismatch")
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "AAYS-EA-Pollution-Inventory-Gate/1.0", "Accept": "application/zip,*/*;q=0.5"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=int(policy["archive_timeout_seconds"])) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read(int(policy["maximum_archive_bytes"]) + 1)
        require(status == 200, f"unexpected HTTP status {status}")
        require(len(raw) <= int(policy["maximum_archive_bytes"]), "archive exceeds byte limit")
        result.update({"raw": raw, "status": status})
    except urllib.error.HTTPError as exc:
        result["status"] = int(exc.code)
        result["error"] = f"HTTPError: {exc.code} {exc.reason}"[:500]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return result


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
    for field in (
        "source_url",
        "publication_page_url",
        "accessed_at",
        "content_sha256",
        "supports_fields",
        "relevant_record_ids_or_excerpt",
        "license_or_terms_url",
    ):
        require(manifest.get(field), f"missing source evidence field: {field}")
    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 1, "exactly one England target required")
    target = targets[0]
    source = load_archive(contract, args.fixture_zip)
    archive_scan = {
        "archive_members_total": 0,
        "supported_members_scanned": [],
        "unsupported_members": [],
        "rows_scanned": 0,
        "matches": [],
    }
    archive_error = source["error"]
    if source["raw"] is not None:
        try:
            archive_scan = scan_archive(source["raw"], target, contract["network_policy"])
        except Exception as exc:
            archive_error = f"{type(exc).__name__}: {exc}"[:500]
    matches = archive_scan["matches"] if archive_error is None else []
    state = "MATCHES_VERIFIED" if matches else "NO_DATA_CONTINUE"
    next_step = (
        "VALIDATE_EA_POLLUTION_INVENTORY_RELEASE_FIELDS_FOR_LLWR_GAS_EMISSIONS_BINDING"
        if matches
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_EA_POLLUTION_INVENTORY_NO_DATA"
    )
    raw = source["raw"]
    target_result = {
        "target_id": target["target_id"],
        "site_name": target["site_name"],
        "attempt_completed": True,
        "jurisdiction": "England",
        "exact_aliases": target["exact_aliases"],
        "matched_rows": len(matches),
        "matches": matches,
        "decision": "EXACT_SITE_POLLUTION_INVENTORY_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE",
        "error": archive_error,
    }
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_zip else "LIVE_NETWORK",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": args.contract.as_posix(),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": args.prior.as_posix(),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "dataset_url": manifest["source_url"],
            "dataset_http_status": source["status"],
            "dataset_sha256": sha256_bytes(raw) if raw is not None else None,
            "dataset_bytes": len(raw) if raw is not None else 0,
            "dataset_error": archive_error,
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "dataset_fetch_attempts": 1,
            "archive_members_total": archive_scan["archive_members_total"],
            "supported_members_scanned": len(archive_scan["supported_members_scanned"]),
            "unsupported_members": len(archive_scan["unsupported_members"]),
            "rows_scanned": archive_scan["rows_scanned"],
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": 1,
        },
        "progress_percent": 100.0,
        "archive": {
            "supported_members_scanned": archive_scan["supported_members_scanned"],
            "unsupported_members": archive_scan["unsupported_members"],
        },
        "targets": [target_result],
        "decision": {
            "england_scope_only": True,
            "exact_normalized_alias_gate_required": True,
            "source_rows_preserved_without_inference": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
