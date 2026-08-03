#!/usr/bin/env python3
"""Discover and scan the official UK ETS Registry compliance workbook, fail-closed."""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import io
import json
import posixpath
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
    parser.add_argument("--fixture-html", type=Path)
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


class ComplianceLinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_tag: str | None = None
        self.heading_parts: list[str] = []
        self.current_heading = ""
        self.link_href: str | None = None
        self.link_parts: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4"}:
            self.heading_tag = tag
            self.heading_parts = []
        if tag == "a":
            self.link_href = dict(attrs).get("href")
            self.link_parts = []

    def handle_data(self, data: str) -> None:
        if self.heading_tag:
            self.heading_parts.append(data)
        if self.link_href is not None:
            self.link_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.heading_tag == tag:
            self.current_heading = " ".join("".join(self.heading_parts).split())
            self.heading_tag = None
            self.heading_parts = []
        if tag == "a" and self.link_href is not None:
            self.links.append({"heading": self.current_heading, "href": self.link_href, "text": " ".join("".join(self.link_parts).split())})
            self.link_href = None
            self.link_parts = []


def discover_compliance_xlsx(page_bytes: bytes, page_url: str) -> tuple[str, list[dict[str, str]]]:
    parser = ComplianceLinkParser()
    parser.feed(page_bytes.decode("utf-8", errors="replace"))
    candidates: list[dict[str, str]] = []
    for item in parser.links:
        absolute = urllib.parse.urljoin(page_url, item["href"])
        joined = normalize(" ".join([item["heading"], item["text"], absolute]))
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme == "https" and re.search(r"\.(xlsx|xls)(?:$|[?#])", parsed.path, flags=re.I) and all(term in joined for term in ("compliance", "emission", "surrender")):
            candidates.append({**item, "absolute_url": absolute})
    require(len(candidates) == 1, f"expected exactly one compliance workbook link, found {len(candidates)}")
    return candidates[0]["absolute_url"], candidates


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


def parse_workbook_rows(raw: bytes, policy: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    sheet_names: list[str] = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require("xl/workbook.xml" in archive.namelist(), "not a valid XLSX workbook")
        strings = shared_strings(archive)
        sheets = workbook_sheets(archive)
        require(len(sheets) <= int(policy["maximum_sheets"]), "workbook exceeds sheet limit")
        for sheet_name, sheet_path in sheets:
            sheet_names.append(sheet_name)
            root = ET.fromstring(archive.read(sheet_path))
            sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
            if sheet_data is None:
                continue
            sheet_count = 0
            for row in sheet_data.findall(f"{{{NS_MAIN}}}row"):
                sheet_count += 1
                require(sheet_count <= int(policy["maximum_rows_per_sheet"]), "sheet exceeds row limit")
                cells: dict[int, str] = {}
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    index = column_index(cell.get("r") or "")
                    require(index <= int(policy["maximum_columns"]), "column limit exceeded")
                    value = cell_text(cell, strings)
                    if value != "":
                        cells[index] = value
                if cells:
                    rows.append({"sheet_name": sheet_name, "row_number": int(row.get("r") or sheet_count), "cells": cells})
                require(len(rows) <= int(policy["maximum_total_rows"]), "workbook exceeds total row limit")
    return rows, sheet_names


def project_row(row: dict[str, Any]) -> dict[str, Any]:
    ordered = [{"column_index": index, "value": row["cells"][index]} for index in sorted(row["cells"])]
    return {"sheet_name": row["sheet_name"], "row_number": row["row_number"], "cells": ordered, "normalized_row_text": normalize(" | ".join(str(item["value"]) for item in ordered))}


def match_target(rows: list[dict[str, Any]], target: dict[str, Any], source_error: str | None) -> dict[str, Any]:
    aliases = [(alias, normalize(alias)) for alias in target["exact_aliases"]]
    matches: list[dict[str, Any]] = []
    for row in rows:
        projection = project_row(row)
        matched = [original for original, alias in aliases if alias and alias in projection["normalized_row_text"]]
        if matched:
            projection["matched_exact_aliases"] = matched
            matches.append(projection)
            require(len(matches) <= int(target["maximum_matches"]), "target match limit exceeded")
    return {"target_id": target["target_id"], "site_name": target["site_name"], "attempt_completed": True, "exact_aliases": target["exact_aliases"], "matched_rows": len(matches), "matches": matches, "decision": "EXACT_SITE_COMPLIANCE_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE", "error": source_error}


def fetch_bytes(url: str, timeout: int, maximum_bytes: int, accept: str) -> tuple[bytes, int]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-UK-ETS-Registry-Compliance-Gate/1.0", "Accept": accept}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(getattr(response, "status", response.getcode()))
        raw = response.read(maximum_bytes + 1)
    require(status == 200, f"unexpected HTTP status {status}")
    require(len(raw) <= maximum_bytes, "response exceeds byte limit")
    return raw, status


def load_sources(contract: dict[str, Any], fixture_html: Path | None, fixture_xlsx: Path | None) -> dict[str, Any]:
    manifest = contract["source_evidence_manifest"]
    policy = contract["network_policy"]
    result: dict[str, Any] = {"page_bytes": None, "page_status": None, "page_error": None, "discovered_workbook_url": None, "link_candidates": [], "workbook_bytes": None, "workbook_status": None, "workbook_error": None, "rows": [], "sheet_names": []}
    try:
        page_url = manifest["source_url"]
        if fixture_html:
            page_raw, page_status = fixture_html.read_bytes(), 200
        else:
            parsed = urllib.parse.urlparse(page_url)
            require(parsed.scheme == "https", "report page must use HTTPS")
            require(parsed.netloc == "reports.view-emissions-trading-registry.service.gov.uk", "report page host mismatch")
            page_raw, page_status = fetch_bytes(page_url, int(policy["page_timeout_seconds"]), int(policy["maximum_page_bytes"]), "text/html,*/*;q=0.5")
        result["page_bytes"], result["page_status"] = page_raw, page_status
        workbook_url, candidates = discover_compliance_xlsx(page_raw, page_url)
        result["discovered_workbook_url"], result["link_candidates"] = workbook_url, candidates
    except urllib.error.HTTPError as exc:
        result["page_status"] = int(exc.code)
        result["page_error"] = f"HTTPError: {exc.code} {exc.reason}"[:500]
        return result
    except Exception as exc:
        result["page_error"] = f"{type(exc).__name__}: {exc}"[:500]
        return result
    try:
        if fixture_xlsx:
            workbook_raw, workbook_status = fixture_xlsx.read_bytes(), 200
        else:
            workbook_url = str(result["discovered_workbook_url"])
            parsed = urllib.parse.urlparse(workbook_url)
            require(parsed.scheme == "https", "workbook URL must use HTTPS")
            require(parsed.netloc.endswith("service.gov.uk") or parsed.netloc == "assets.publishing.service.gov.uk", "workbook host not allowed")
            workbook_raw, workbook_status = fetch_bytes(workbook_url, int(policy["workbook_timeout_seconds"]), int(policy["maximum_workbook_bytes"]), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.5")
        result["workbook_bytes"], result["workbook_status"] = workbook_raw, workbook_status
        result["rows"], result["sheet_names"] = parse_workbook_rows(workbook_raw, policy)
    except urllib.error.HTTPError as exc:
        result["workbook_status"] = int(exc.code)
        result["workbook_error"] = f"HTTPError: {exc.code} {exc.reason}"[:500]
    except Exception as exc:
        result["workbook_error"] = f"{type(exc).__name__}: {exc}"[:500]
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
    for field in ("source_url", "collection_url", "accessed_at", "content_sha256", "supports_fields", "relevant_record_ids_or_excerpt", "license_or_terms_url"):
        require(manifest.get(field), f"missing source evidence field: {field}")
    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 2, "exactly two targets required")
    source = load_sources(contract, args.fixture_html, args.fixture_xlsx)
    source_error = source["page_error"] or source["workbook_error"]
    rows = source["rows"]
    results = [match_target(rows, target, source_error) for target in targets]
    completed = sum(bool(item["attempt_completed"]) for item in results)
    target_count = len(targets)
    matched_targets = sum(bool(item["matched_rows"]) for item in results)
    matched_rows = sum(int(item["matched_rows"]) for item in results)
    if matched_targets == target_count:
        state, next_step = "MATCHES_VERIFIED", "VALIDATE_UK_ETS_REGISTRY_COMPLIANCE_EMISSIONS_FIELDS_FOR_GAS_EMISSIONS_BINDING"
    elif matched_targets:
        state, next_step = "PARTIAL_MATCH_CONTINUE", "ADVANCE_UNMATCHED_TARGET_AND_VALIDATE_MATCHED_UK_ETS_REGISTRY_COMPLIANCE_ROWS"
    else:
        state, next_step = "NO_DATA_CONTINUE", "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_UK_ETS_REGISTRY_COMPLIANCE_NO_DATA"
    output = {"schema_version": 3, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_3", "task_id": contract["task_id"], "continuation_key": contract["continuation_key"], "state": state, "panel_status": "PUBLISHED", "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_html or args.fixture_xlsx else "LIVE_NETWORK", "first_unverified_step_completed": contract["first_unverified_step"], "next_unverified_step": next_step, "input": {"contract_path": args.contract.as_posix(), "contract_sha256": sha256_bytes(contract_bytes), "prior_output_path": args.prior.as_posix(), "prior_output_sha256": sha256_bytes(prior_bytes), "report_page_url": manifest["source_url"], "report_page_http_status": source["page_status"], "report_page_sha256": sha256_bytes(source["page_bytes"]) if source["page_bytes"] is not None else None, "report_page_bytes": len(source["page_bytes"]) if source["page_bytes"] is not None else 0, "report_page_error": source["page_error"], "discovered_workbook_url": source["discovered_workbook_url"], "workbook_http_status": source["workbook_status"], "workbook_sha256": sha256_bytes(source["workbook_bytes"]) if source["workbook_bytes"] is not None else None, "workbook_bytes": len(source["workbook_bytes"]) if source["workbook_bytes"] is not None else 0, "workbook_error": source["workbook_error"]}, "counts": {"completed_count": completed, "target_count": target_count, "report_page_fetch_attempts": 1, "workbook_fetch_attempts": 1 if source["discovered_workbook_url"] else 0, "compliance_workbook_links_discovered": len(source["link_candidates"]), "workbook_sheets_scanned": len(source["sheet_names"]), "workbook_rows_scanned": len(rows), "matched_targets": matched_targets, "matched_rows": matched_rows, "produced_business_rows": matched_rows, "produced_source_evidence_records": target_count}, "progress_percent": round(completed / target_count * 100, 6), "sheet_names": source["sheet_names"], "targets": results, "decision": {"stable_report_page_link_discovery_required": True, "exact_normalized_alias_gate_required": True, "source_cells_preserved_without_inference": True, "inferred_values": 0, "fake_data": False}}
    require(completed == target_count, "not all target assessments completed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
