#!/usr/bin/env python3
"""Bounded exact-row extraction from the official GOV.UK RIFE 30 HTML report."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-html", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", html.unescape(str(value or "")))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_stack: list[str] = []
        self.current_heading_tag: str | None = None
        self.current_heading_parts: list[str] = []
        self.in_table = False
        self.table_context = ""
        self.in_row = False
        self.in_cell = False
        self.cell_is_header = False
        self.cell_parts: list[str] = []
        self.row: list[dict[str, Any]] = []
        self.current_rows: list[list[dict[str, Any]]] = []
        self.tables: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "caption"}:
            self.current_heading_tag = tag
            self.current_heading_parts = []
        elif tag == "table":
            self.in_table = True
            self.table_context = " | ".join(self.heading_stack[-4:])
            self.current_rows = []
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.row = []
        elif self.in_row and tag in {"th", "td"}:
            self.in_cell = True
            self.cell_is_header = tag == "th"
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.current_heading_tag is not None:
            self.current_heading_parts.append(data)
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current_heading_tag == tag:
            text = " ".join("".join(self.current_heading_parts).split())
            if text:
                if tag == "caption" and self.in_table:
                    self.table_context = " | ".join(x for x in [self.table_context, text] if x)
                else:
                    self.heading_stack.append(text)
                    self.heading_stack = self.heading_stack[-8:]
            self.current_heading_tag = None
            self.current_heading_parts = []
        elif self.in_cell and tag in {"th", "td"}:
            value = " ".join("".join(self.cell_parts).split())
            self.row.append({"value": value, "is_header": self.cell_is_header})
            self.in_cell = False
            self.cell_parts = []
        elif self.in_row and tag == "tr":
            if any(cell["value"] for cell in self.row):
                self.current_rows.append(self.row)
            self.in_row = False
            self.row = []
        elif self.in_table and tag == "table":
            self.tables.append({"context": self.table_context, "rows": self.current_rows})
            self.in_table = False
            self.current_rows = []
            self.table_context = ""


def fetch_html(contract: dict[str, Any], fixture_html: Path | None) -> dict[str, Any]:
    manifest = contract["source_evidence_manifest"]
    policy = contract["network_policy"]
    result: dict[str, Any] = {"status": None, "raw": None, "error": None}
    try:
        if fixture_html:
            raw = fixture_html.read_bytes()
            status = 200
        else:
            url = manifest["source_url"]
            parsed = urllib.parse.urlparse(url)
            require(parsed.scheme == "https", "source URL must use HTTPS")
            require(parsed.netloc == "www.gov.uk", "source host mismatch")
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "AAYS-RIFE30-LLWR-Gate/1.0", "Accept": "text/html,*/*;q=0.5"},
                method="GET",
            )
            with urllib.request.urlopen(request, timeout=int(policy["page_timeout_seconds"])) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read(int(policy["maximum_html_bytes"]) + 1)
        require(status == 200, f"unexpected HTTP status {status}")
        require(len(raw) <= int(policy["maximum_html_bytes"]), "HTML exceeds byte limit")
        result.update({"status": status, "raw": raw})
    except urllib.error.HTTPError as exc:
        result.update({"status": int(exc.code), "error": f"HTTPError: {exc.code} {exc.reason}"[:500]})
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return result


def parse_tables(raw: bytes, policy: dict[str, Any]) -> list[dict[str, Any]]:
    text = raw.decode("utf-8-sig")
    parser = TableParser()
    parser.feed(text)
    require(len(parser.tables) <= int(policy["maximum_tables"]), "table limit exceeded")
    total_rows = sum(len(table["rows"]) for table in parser.tables)
    require(total_rows <= int(policy["maximum_total_rows"]), "row limit exceeded")
    for table in parser.tables:
        require(all(len(row) <= int(policy["maximum_columns"]) for row in table["rows"]), "column limit exceeded")
    return parser.tables


def extract_matches(tables: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    aliases = {normalize(alias): alias for alias in target["exact_aliases"]}
    matches: list[dict[str, Any]] = []
    rows_scanned = 0
    qualifying_table_indexes: set[int] = set()
    for table_index, table in enumerate(tables, start=1):
        context_norm = normalize(table["context"])
        headers: list[str] = []
        for row in table["rows"]:
            rows_scanned += 1
            values = [cell["value"] for cell in row]
            if any(cell["is_header"] for cell in row):
                headers = values
            header_norm = normalize(" | ".join(headers))
            qualifies = "gaseous discharges" in context_norm or "gaseous discharges" in header_norm
            if not qualifies or not values:
                continue
            qualifying_table_indexes.add(table_index)
            site_norm = normalize(values[0])
            if site_norm not in aliases:
                continue
            require(len(values) >= 2, "matched row lacks dose value")
            match = {
                "table_index": table_index,
                "table_context": table["context"],
                "headers": headers,
                "row_values": values,
                "matched_alias": aliases[site_norm],
                "site_name_source": values[0],
                "dose_value_source": values[1],
                "dose_unit_source": headers[1] if len(headers) > 1 else None,
            }
            matches.append(match)
            require(len(matches) <= int(target["maximum_matches"]), "match limit exceeded")
    return {
        "tables_scanned": len(tables),
        "rows_scanned": rows_scanned,
        "qualifying_tables": len(qualifying_table_indexes),
        "matches": matches,
    }


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
    pre = contract["precondition"]
    require(sha256_bytes(prior_bytes) == pre["prior_output_sha256"], "prior SHA mismatch")
    require(prior.get("task_id") == pre["required_prior_task_id"], "unexpected prior task")
    require(prior.get("state") == pre["required_prior_state"], "unexpected prior state")
    require(prior.get("next_unverified_step") == pre["required_prior_next_unverified_step"], "unexpected prior next step")
    manifest = contract["source_evidence_manifest"]
    for key in ("source_url", "publication_page_url", "accessed_at", "content_sha256", "supports_fields", "relevant_record_ids_or_excerpt", "license_or_terms_url"):
        require(manifest.get(key), f"missing source evidence field: {key}")
    targets = contract["runtime_targets"]
    require(isinstance(targets, list) and len(targets) == 1, "exactly one target required")
    target = targets[0]
    fetched = fetch_html(contract, args.fixture_html)
    scan = {"tables_scanned": 0, "rows_scanned": 0, "qualifying_tables": 0, "matches": []}
    error = fetched["error"]
    html_sha = None
    html_bytes = 0
    if fetched["raw"] is not None:
        html_sha = sha256_bytes(fetched["raw"])
        html_bytes = len(fetched["raw"])
        try:
            scan = extract_matches(parse_tables(fetched["raw"], contract["network_policy"]), target)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:500]
    matches = scan["matches"]
    verified = len(matches) > 0 and error is None
    state = "EXACT_SITE_GASEOUS_DISCHARGE_DOSE_VERIFIED" if verified else "NO_DATA_CONTINUE"
    next_step = (
        "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_RIFE30_LLWR_ROW_VERIFIED"
        if verified
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_RIFE30_NO_DATA"
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
        "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_html else "LIVE_NETWORK",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "source_url": manifest["source_url"],
            "http_status": fetched["status"],
            "html_sha256": html_sha,
            "html_bytes": html_bytes,
            "source_error": error,
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "html_fetch_attempts": 1,
            "tables_scanned": scan["tables_scanned"],
            "rows_scanned": scan["rows_scanned"],
            "qualifying_tables": scan["qualifying_tables"],
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": 1,
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": target["target_id"],
            "site_name": target["site_name"],
            "attempt_completed": True,
            "exact_aliases": target["exact_aliases"],
            "matched_rows": len(matches),
            "matches": matches,
            "decision": state,
            "error": error,
        }],
        "decision": {
            "exact_site_cell_gate_required": True,
            "gaseous_discharge_table_context_required": True,
            "source_cells_preserved_without_inference": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
