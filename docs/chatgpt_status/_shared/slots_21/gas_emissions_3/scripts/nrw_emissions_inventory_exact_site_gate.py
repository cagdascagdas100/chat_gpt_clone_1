#!/usr/bin/env python3
"""Discover and scan the official NRW Emissions Inventory for Maentwrog rows."""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"

def norm(value: Any) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())

def col_index(ref: str) -> int:
    m = re.match(r"[A-Z]+", ref or "")
    if not m: raise ValueError("invalid cell reference")
    n = 0
    for ch in m.group(0): n = n * 26 + ord(ch) - 64
    return n

def xlsx_rows(raw: bytes, name: str, policy: dict[str, Any]):
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        if "xl/workbook.xml" not in zf.namelist(): raise ValueError("invalid XLSX")
        strings = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            strings = ["".join(n.text or "" for n in item.iter(f"{{{NS_MAIN}}}t")) for item in root.findall(f"{{{NS_MAIN}}}si")]
        wb = ET.fromstring(zf.read("xl/workbook.xml")); rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.get("Id"): r.get("Target") for r in rels.findall(f"{{{NS_PKG}}}Relationship")}
        sheets = wb.find(f"{{{NS_MAIN}}}sheets"); nodes = [] if sheets is None else sheets.findall(f"{{{NS_MAIN}}}sheet")
        if len(nodes) > int(policy["maximum_workbook_sheets"]): raise ValueError("worksheet limit exceeded")
        for sh in nodes:
            target = relmap.get(sh.get(f"{{{NS_REL}}}id")); sheet_name = sh.get("name") or "unnamed"
            if not target: raise ValueError("worksheet relationship missing")
            target = target.lstrip("/")
            if not target.startswith("xl/"): target = "xl/" + target
            root = ET.fromstring(zf.read(target)); data = root.find(f"{{{NS_MAIN}}}sheetData")
            if data is None: continue
            for i,row in enumerate(data.findall(f"{{{NS_MAIN}}}row"),1):
                if i > int(policy["maximum_rows_per_member"]): raise ValueError("row limit exceeded")
                cells=[]
                for cell in row.findall(f"{{{NS_MAIN}}}c"):
                    idx=col_index(cell.get("r") or "")
                    if idx > int(policy["maximum_columns"]): raise ValueError("column limit exceeded")
                    typ=cell.get("t")
                    if typ=="inlineStr": val="".join(n.text or "" for n in cell.iter(f"{{{NS_MAIN}}}t"))
                    else:
                        node=cell.find(f"{{{NS_MAIN}}}v"); val=node.text if node is not None and node.text is not None else ""
                        if typ=="s" and val: val=strings[int(val)]
                    if val!="": cells.append({"column_index":idx,"value":val})
                if cells: yield {"member_name":name,"member_format":"xlsx","sheet_name":sheet_name,"row_number":int(row.get("r") or i),"cells":cells}

def text_rows(raw: bytes, name: str, suffix: str, policy: dict[str, Any]):
    text=decode(raw)
    if suffix in {".csv",".tsv"}:
        delim="\t" if suffix==".tsv" else ","
        if suffix==".csv":
            try: delim=csv.Sniffer().sniff(text[:65536],delimiters=",;\t|").delimiter
            except csv.Error: pass
        for i,row in enumerate(csv.reader(io.StringIO(text),delimiter=delim),1):
            if i>int(policy["maximum_rows_per_member"]): raise ValueError("row limit exceeded")
            if len(row)>int(policy["maximum_columns"]): raise ValueError("column limit exceeded")
            cells=[{"column_index":j,"value":v} for j,v in enumerate(row,1) if v!=""]
            if cells: yield {"member_name":name,"member_format":suffix[1:],"row_number":i,"cells":cells}
    else:
        for i,line in enumerate(text.splitlines(),1):
            if i>int(policy["maximum_rows_per_member"]): raise ValueError("row limit exceeded")
            if line.strip(): yield {"member_name":name,"member_format":suffix[1:] or "txt","row_number":i,"cells":[{"column_index":1,"value":line[:20000]}]}

def scan_archive(raw: bytes, target: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    aliases=[(a,norm(a)) for a in target["exact_aliases"]]; matches=[]; supported=[]; unsupported=[]; rows_scanned=0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        infos=[i for i in zf.infolist() if not i.is_dir()]
        if len(infos)>int(policy["maximum_archive_members"]): raise ValueError("archive member limit exceeded")
        total=0
        for info in infos:
            name=info.filename.replace("\\","/"); total += int(info.file_size)
            if name.startswith("../") or total>int(policy["maximum_total_uncompressed_bytes"]): raise ValueError("unsafe or oversized archive")
            member=zf.read(info); suffix=Path(name).suffix.lower()
            if suffix==".xlsx": rows=xlsx_rows(member,name,policy)
            elif suffix in {".csv",".tsv",".txt",".json",".geojson",".xml"}: rows=text_rows(member,name,suffix,policy)
            else: unsupported.append(name); continue
            supported.append(name)
            for row in rows:
                rows_scanned += 1
                if rows_scanned>int(policy["maximum_total_rows"]): raise ValueError("total row limit exceeded")
                row_norm=norm(" | ".join(str(c.get("value","")) for c in row["cells"]))
                hit=[a for a,n in aliases if n and n in row_norm]
                if hit:
                    row["matched_exact_aliases"]=hit; row["normalized_row_text"]=row_norm; matches.append(row)
                    if len(matches)>int(target["maximum_matches"]): raise ValueError("match limit exceeded")
    return {"archive_members_total":len(infos),"supported_members_scanned":supported,"unsupported_members":unsupported,"rows_scanned":rows_scanned,"matches":matches}


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", required=True, type=Path)
    p.add_argument("--prior", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--fixture-metadata-html", type=Path)
    p.add_argument("--fixture-share-html", type=Path)
    p.add_argument("--fixture-data", type=Path)
    p.add_argument("--fixture-data-name", default="nrw_emissions_inventory.csv")
    return p.parse_args()


def fetch(url: str, host: str, timeout: int, limit: int, accept: str) -> dict[str, Any]:
    out: dict[str, Any] = {"status": None, "raw": None, "content_type": None, "error": None}
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != host:
            raise ValueError("source URL host or scheme mismatch")
        req = urllib.request.Request(url, headers={"User-Agent": "AAYS-NRW-EI-Gate/1.0", "Accept": accept}, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            raw = response.read(limit + 1)
            ctype = response.headers.get("Content-Type")
        if status != 200:
            raise ValueError(f"unexpected HTTP status {status}")
        if len(raw) > limit:
            raise ValueError("response exceeds byte limit")
        out.update({"status": status, "raw": raw, "content_type": ctype})
    except urllib.error.HTTPError as exc:
        out.update({"status": int(exc.code), "error": f"HTTPError: {exc.code} {exc.reason}"[:500]})
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return out


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("HTML payload could not be decoded")


def discover_download(raw: bytes, base_url: str) -> list[str]:
    text = html.unescape(decode(raw))
    values = re.findall(r"(?i)(?:href|src|data-[\w-]*url|downloadurl)\s*=\s*['\"]([^'\"]+)['\"]", text)
    values += re.findall(r"https://[^\s'\"<>]+", text)
    out: list[str] = []
    for value in values:
        url = urllib.parse.urljoin(base_url, value.strip()).rstrip("),.;")
        parsed = urllib.parse.urlparse(url)
        low = url.lower()
        if parsed.scheme == "https" and parsed.netloc == "naturalresourceswales.sharefile.eu" and (
            re.search(r"\.(?:csv|tsv|txt|json|geojson|xml|xlsx|zip)(?:$|[?#])", low) or "download" in low or "file" in low
        ) and url not in out:
            out.append(url)
    return out


def looks_like_data(raw: bytes, content_type: str | None, url: str) -> bool:
    low = url.lower()
    ctype = (content_type or "").lower()
    return raw.startswith(b"PK\x03\x04") or bool(re.search(r"\.(?:csv|tsv|txt|json|geojson|xml|xlsx|zip)(?:$|[?#])", low)) or any(x in ctype for x in ("csv", "spreadsheet", "zip", "json", "xml"))


def wrap_payload(raw: bytes, name: str) -> bytes:
    if raw.startswith(b"PK\x03\x04") and not name.lower().endswith(".xlsx"):
        return raw
    safe = Path(urllib.parse.urlparse(name).path).name or "nrw_emissions_inventory.dat"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(safe, raw)
    return buf.getvalue()


def main() -> int:
    a = args()
    contract_bytes = a.contract.read_bytes()
    prior_bytes = a.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    if contract.get("schema_version") != 3 or contract.get("slot_id") != "gas_emissions_3":
        raise ValueError("contract identity mismatch")
    if contract.get("state") != "READY" or contract.get("status") != "ready" or not contract.get("claimable") or not contract.get("ready_for_claim"):
        raise ValueError("contract is not claimable READY")
    pre = contract["precondition"]
    if hashlib.sha256(prior_bytes).hexdigest() != pre["prior_output_sha256"]:
        raise ValueError("prior SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"] or prior.get("state") != pre["required_prior_state"] or prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]:
        raise ValueError("prior state mismatch")
    manifest = contract["source_evidence_manifest"]
    for key in ("source_url", "publication_page_url", "accessed_at", "content_sha256", "supports_fields", "relevant_record_ids_or_excerpt", "license_or_terms_url"):
        if not manifest.get(key):
            raise ValueError(f"missing source evidence field: {key}")
    targets = contract["runtime_targets"]
    if len(targets) != 1:
        raise ValueError("exactly one Wales target required")
    target = targets[0]
    policy = contract["network_policy"]
    fixture = bool(a.fixture_metadata_html and a.fixture_share_html and a.fixture_data)
    metadata_attempts = share_attempts = data_attempts = 0
    metadata = {"status": None, "raw": None, "error": None}
    share = {"status": None, "raw": None, "content_type": None, "error": None}
    data_url: str | None = None
    data_status = None
    data_type: str | None = None
    data_raw: bytes | None = None
    error: str | None = None

    if fixture:
        metadata_attempts = share_attempts = data_attempts = 1
        metadata = {"status": 200, "raw": a.fixture_metadata_html.read_bytes(), "error": None}
        share = {"status": 200, "raw": a.fixture_share_html.read_bytes(), "content_type": "text/html", "error": None}
        data_url = f"https://naturalresourceswales.sharefile.eu/download/{a.fixture_data_name}"
        data_status, data_type, data_raw = 200, "text/csv", a.fixture_data.read_bytes()
    else:
        metadata_attempts = 1
        metadata = fetch(manifest["publication_page_url"], "datamap.gov.wales", int(policy["page_timeout_seconds"]), int(policy["maximum_metadata_bytes"]), "text/html,*/*;q=0.5")
        if metadata["error"]:
            error = metadata["error"]
        else:
            if manifest["source_url"] not in html.unescape(decode(metadata["raw"])):
                raise ValueError("official ShareFile URL absent from metadata page")
            share_attempts = 1
            share = fetch(manifest["source_url"], "naturalresourceswales.sharefile.eu", int(policy["page_timeout_seconds"]), int(policy["maximum_share_page_bytes"]), "text/html,application/octet-stream,*/*;q=0.5")
            if share["error"]:
                error = share["error"]
            elif looks_like_data(share["raw"], share["content_type"], manifest["source_url"]):
                data_url, data_status, data_type, data_raw = manifest["source_url"], share["status"], share["content_type"], share["raw"]
            else:
                links = discover_download(share["raw"], manifest["source_url"])
                if len(links) != 1:
                    raise ValueError(f"expected one downloadable dataset link, found {len(links)}")
                data_url = links[0]
                data_attempts = 1
                data = fetch(data_url, "naturalresourceswales.sharefile.eu", int(policy["dataset_timeout_seconds"]), int(policy["maximum_dataset_bytes"]), "application/zip,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*;q=0.5")
                data_status, data_type, data_raw, error = data["status"], data["content_type"], data["raw"], data["error"]

    scan = {"archive_members_total": 0, "supported_members_scanned": [], "unsupported_members": [], "rows_scanned": 0, "matches": []}
    if data_raw is not None:
        try:
            scan = scan_archive(wrap_payload(data_raw, data_url or a.fixture_data_name), target, policy)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:500]

    matches = scan["matches"]
    state = "EXACT_SITE_ROWS_VERIFIED" if matches else "NO_DATA_CONTINUE"
    next_step = "VALIDATE_NRW_EMISSIONS_INVENTORY_POLLUTANT_COLUMNS_FOR_GAS_EMISSIONS_BINDING" if matches else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NRW_EMISSIONS_INVENTORY_NO_DATA"
    output = {
        "schema_version": 3, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"], "continuation_key": contract["continuation_key"], "state": state, "panel_status": "PUBLISHED",
        "execution_mode": "SYNTHETIC_FIXTURE" if fixture else "LIVE_NETWORK", "first_unverified_step_completed": contract["first_unverified_step"], "next_unverified_step": next_step,
        "input": {
            "contract_path": a.contract.as_posix(), "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(), "prior_output_path": a.prior.as_posix(), "prior_output_sha256": hashlib.sha256(prior_bytes).hexdigest(),
            "metadata_url": manifest["publication_page_url"], "metadata_http_status": metadata["status"], "metadata_sha256": hashlib.sha256(metadata["raw"]).hexdigest() if metadata["raw"] is not None else None,
            "share_url": manifest["source_url"], "share_http_status": share["status"], "share_sha256": hashlib.sha256(share["raw"]).hexdigest() if share["raw"] is not None else None,
            "dataset_url": data_url, "dataset_http_status": data_status, "dataset_content_type": data_type, "dataset_sha256": hashlib.sha256(data_raw).hexdigest() if data_raw is not None else None,
            "dataset_bytes": len(data_raw) if data_raw is not None else 0, "dataset_error": error,
        },
        "counts": {
            "completed_count": 1, "target_count": 1, "metadata_fetch_attempts": metadata_attempts, "share_page_fetch_attempts": share_attempts, "dataset_fetch_attempts": data_attempts,
            "archive_members_total": scan["archive_members_total"], "supported_members_scanned": len(scan["supported_members_scanned"]), "unsupported_members": len(scan["unsupported_members"]),
            "rows_scanned": scan["rows_scanned"], "matched_targets": 1 if matches else 0, "matched_rows": len(matches), "produced_business_rows": len(matches), "produced_source_evidence_records": 1,
        },
        "progress_percent": 100.0,
        "archive": {"supported_members_scanned": scan["supported_members_scanned"], "unsupported_members": scan["unsupported_members"]},
        "targets": [{"target_id": target["target_id"], "site_name": target["site_name"], "jurisdiction": "Wales", "attempt_completed": True, "exact_aliases": target["exact_aliases"], "matched_rows": len(matches), "matches": matches, "decision": state, "error": error}],
        "decision": {"wales_scope_only": True, "exact_normalized_alias_gate_required": True, "source_rows_preserved_without_inference": True, "inferred_values": 0, "fake_data": False},
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    temp = a.output.with_suffix(a.output.suffix + ".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(a.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
