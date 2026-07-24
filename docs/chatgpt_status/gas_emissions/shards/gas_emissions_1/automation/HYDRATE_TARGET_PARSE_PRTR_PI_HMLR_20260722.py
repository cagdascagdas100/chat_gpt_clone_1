#!/usr/bin/env python3
"""Read-only official binary hydration and target-record extraction for gas_emissions_1.

Downloads current official UK PRTR, Environment Agency Pollution Inventory and
HMLR INSPIRE sources. It extracts only records mentioning the configured target
facility/title identities. Candidate records are evidence, never parcel values.
"""
from __future__ import annotations

import csv
import hashlib
import html.parser
import io
import json
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_1"
PRTR_URL = "https://assets.publishing.service.gov.uk/media/6a3d096c4c7605ab56723a63/uk_prtr_dataset_2024.xml"
PRTR_REGISTRY_URL = "https://assets.publishing.service.gov.uk/media/6a3e316cd52550a19950f59a/UK_Registry_data.zip"
PI_URL = "https://environment.data.gov.uk/api/file/download?fileDataSetId=4faa4a52-7df2-4047-bc3f-877dd04222d8&fileName=2024+Pollution+Inventory+Dataset.zip"
HMLR_INDEX_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
TARGET_TOKENS = (
    "thames gateway waste to energy",
    "thames gateway energy facility",
    "london sustainable industries park",
    "choats road",
    "rm9 6lf",
    "epr/hp3504ma",
    "hp3504ma",
    "epr/cp3737cv",
    "cp3737cv",
    "tgl419520",
    "cory barking operations",
    "mcgrath bros",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, path: Path, attempts: int = 3) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AAYS-gas_emissions_1-official-source-audit/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, path.open("wb") as output:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    output.write(block)
            size = path.stat().st_size
            if size == 0:
                raise RuntimeError("ZERO_BYTE_DOWNLOAD")
            return {"url": url, "path": str(path), "size_bytes": size, "sha256": sha256_file(path), "attempt": attempt, "error": None}
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            time.sleep(attempt * 2)
    return {"url": url, "path": str(path), "size_bytes": 0, "sha256": None, "attempt": attempts, "error": error}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def flatten_xml(element: ET.Element, limit: int = 160) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for child in element.iter():
        text = (child.text or "").strip()
        if not text:
            continue
        key = local_name(child.tag)
        if key in result:
            current = result[key]
            values = current if isinstance(current, list) else [current]
            if text not in values:
                values.append(text)
            result[key] = values[:10]
        else:
            result[key] = text
        if len(result) >= limit:
            break
    return result


def contains_target(text: str) -> bool:
    lowered = text.casefold()
    return any(token in lowered for token in TARGET_TOKENS)


def extract_xml_candidates(path: Path, max_records: int = 100) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for _, element in ET.iterparse(path, events=("end",)):
        if not list(element):
            continue
        text = " ".join(value.strip() for value in element.itertext() if value and value.strip())
        if 20 <= len(text) <= 250000 and contains_target(text):
            record = flatten_xml(element)
            fingerprint = hashlib.sha256(json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
            if fingerprint not in fingerprints:
                fingerprints.add(fingerprint)
                found.append({"element": local_name(element.tag), "fields": record})
                if len(found) >= max_records:
                    break
        element.clear()
    return found


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def extract_delimited(data: bytes, name: str, max_records: int = 100) -> list[dict[str, Any]]:
    text = decode_text(data)
    sample = text[:65536]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    found = []
    for row_number, row in enumerate(reader, start=2):
        joined = " ".join(str(value or "") for value in row.values())
        if contains_target(joined):
            found.append({"member": name, "row_number": row_number, "fields": {str(key): value for key, value in row.items()}})
            if len(found) >= max_records:
                break
    return found


def xlsx_rows(data: bytes):
    with zipfile.ZipFile(io.BytesIO(data)) as book:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            for item in root.iter():
                if local_name(item.tag) == "si":
                    shared.append("".join(item.itertext()))
        sheets = sorted(name for name in book.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"))
        for sheet_name in sheets:
            root = ET.fromstring(book.read(sheet_name))
            for row in root.iter():
                if local_name(row.tag) != "row":
                    continue
                cells = []
                for cell in row:
                    if local_name(cell.tag) != "c":
                        continue
                    cell_type = cell.attrib.get("t")
                    value = next((node.text for node in cell if local_name(node.tag) == "v"), "") or ""
                    if cell_type == "s" and value.isdigit() and int(value) < len(shared):
                        value = shared[int(value)]
                    cells.append(value)
                yield sheet_name, row.attrib.get("r"), cells


def extract_xlsx(data: bytes, name: str, max_records: int = 100) -> list[dict[str, Any]]:
    found = []
    for sheet, row_number, cells in xlsx_rows(data):
        if contains_target(" ".join(cells)):
            found.append({"member": name, "sheet": sheet, "row_number": row_number, "cells": cells})
            if len(found) >= max_records:
                break
    return found


def extract_zip_candidates(path: Path, max_records: int = 150) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    members = []
    found: list[dict[str, Any]] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            members.append({"name": info.filename, "size_bytes": info.file_size, "compressed_size_bytes": info.compress_size})
            if info.is_dir() or len(found) >= max_records:
                continue
            lowered = info.filename.casefold()
            if not lowered.endswith((".csv", ".txt", ".tsv", ".xlsx", ".xml", ".gml")):
                continue
            data = archive.read(info)
            try:
                if lowered.endswith((".csv", ".txt", ".tsv")):
                    rows = extract_delimited(data, info.filename, max_records - len(found))
                elif lowered.endswith(".xlsx"):
                    rows = extract_xlsx(data, info.filename, max_records - len(found))
                else:
                    temp = Path(tempfile.mkstemp(suffix=Path(info.filename).suffix)[1])
                    try:
                        temp.write_bytes(data)
                        rows = [{"member": info.filename, **record} for record in extract_xml_candidates(temp, max_records - len(found))]
                    finally:
                        temp.unlink(missing_ok=True)
                found.extend(rows)
            except Exception as exc:
                found.append({"member": info.filename, "parse_error": f"{type(exc).__name__}: {exc}"})
    return members, found


def resolve_hmlr_gml() -> dict[str, Any]:
    try:
        request = urllib.request.Request(HMLR_INDEX_URL, headers={"User-Agent": "AAYS-gas_emissions_1-official-source-audit/1.0"})
        html = urllib.request.urlopen(request, timeout=60).read().decode("utf-8", errors="replace")
        patterns = (
            r"<tr[^>]*>.*?London Borough of Barking and Dagenham.*?<a[^>]+href=[\"']([^\"']+)[\"']",
            r"London Borough of Barking and Dagenham.{0,1000}?href=[\"']([^\"']+\.gml[^\"']*)[\"']",
        )
        for pattern in patterns:
            match = re.search(pattern, html, flags=re.I | re.S)
            if match:
                return {"index_url": HMLR_INDEX_URL, "gml_url": urllib.parse.urljoin(HMLR_INDEX_URL, match.group(1)), "error": None}
        return {"index_url": HMLR_INDEX_URL, "gml_url": None, "error": "BARKING_DAGENHAM_GML_LINK_NOT_RESOLVED"}
    except Exception as exc:
        return {"index_url": HMLR_INDEX_URL, "gml_url": None, "error": f"{type(exc).__name__}: {exc}"}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")
    root = Path.cwd()
    task_id = os.environ.get("AAYS_TASK_ID", "gas_emissions_1_binary_hydration_target_parse_20260722")
    report_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_binary_hydration_target_parse_latest.json"
    status_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_binary_hydration_target_parse_latest.json"
    web_path = root / "england_map_web/data/aays_21_slots/gas_emissions_1/binary_target_parse_result_latest.json"

    with tempfile.TemporaryDirectory(prefix="gas_emissions_1_official_") as temp_dir:
        temp = Path(temp_dir)
        downloads = {
            "uk_prtr_2024_xml": download(PRTR_URL, temp / "uk_prtr_dataset_2024.xml"),
            "uk_prtr_registry_zip": download(PRTR_REGISTRY_URL, temp / "UK_Registry_data.zip"),
            "ea_pi_2024_zip": download(PI_URL, temp / "2024_Pollution_Inventory_Dataset.zip"),
        }
        extracts: dict[str, Any] = {}
        for key, meta in downloads.items():
            if meta["error"]:
                extracts[key] = {"candidate_count": 0, "error": meta["error"]}
                continue
            path = Path(meta["path"])
            try:
                if path.suffix.casefold() in (".xml", ".gml"):
                    candidates = extract_xml_candidates(path)
                    extracts[key] = {"candidate_count": len(candidates), "candidates": candidates, "error": None}
                else:
                    members, candidates = extract_zip_candidates(path)
                    extracts[key] = {"member_count": len(members), "members": members, "candidate_count": len(candidates), "candidates": candidates, "error": None}
            except Exception as exc:
                extracts[key] = {"candidate_count": 0, "error": f"{type(exc).__name__}: {exc}"}

        hmlr = resolve_hmlr_gml()
        if hmlr.get("gml_url"):
            hmlr_download = download(str(hmlr["gml_url"]), temp / "barking_dagenham_inspire.gml")
            hmlr["download"] = hmlr_download
            if not hmlr_download["error"]:
                hmlr_candidates = extract_xml_candidates(Path(hmlr_download["path"]))
                hmlr["candidate_count"] = len(hmlr_candidates)
                hmlr["candidates"] = hmlr_candidates
            else:
                hmlr["candidate_count"] = 0
        else:
            hmlr["candidate_count"] = 0

    successful_downloads = sum(1 for item in downloads.values() if not item["error"])
    target_candidate_count = sum(int(item.get("candidate_count", 0)) for item in extracts.values()) + int(hmlr.get("candidate_count", 0))
    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "slot_id": SLOT_ID,
        "task_id": task_id,
        "generated_at": utc_now(),
        "status": "PASS_OFFICIAL_BINARY_TARGET_CANDIDATES_EXTRACTED" if successful_downloads == 3 else "BLOCKED_OFFICIAL_BINARY_HYDRATION_PARTIAL_OR_FAILED",
        "official_downloads_succeeded": successful_downloads,
        "official_downloads_expected": 3,
        "downloads": downloads,
        "extracts": extracts,
        "hmlr": hmlr,
        "target_candidate_count": target_candidate_count,
        "measured_parcel_emission_rows": 0,
        "verified_parcel_bindings": 0,
        "candidate_semantics": "RAW_OFFICIAL_TARGET_RECORD_CANDIDATES_REQUIRE_SCHEMA_AND_IDENTITY_REVIEW",
        "no_data_policy": "NO_DATA_NOT_ZERO",
        "blocker": None if successful_downloads == 3 else "ONE_OR_MORE_OFFICIAL_BINARIES_COULD_NOT_BE_DOWNLOADED_OR_PARSED",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    for path in (report_path, status_path, web_path):
        write_json(path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if successful_downloads == 3 else 2


if __name__ == "__main__":
    raise SystemExit(main())
