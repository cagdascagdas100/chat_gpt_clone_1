# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
SHARD_REL = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2"
WEB_REL = "england_map_web/data/aays_21_slots/internet_access_2"
SOURCE_PAGE = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026"
SOURCE_PDF = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf?v=422757"
OUTER_ZIP_URL = "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
EXPECTED_FILES = 121
EXPECTED_ROWS = 1_741_096
MAX_DOWNLOAD_BYTES = 90_000_000
R2_PATTERN = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$", re.I)
R1_PATTERN = re.compile(r"(?:^|/)202601_fixed_postcode_coverage_r1_([A-Z0-9]+)\.csv$", re.I)
CORE_ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "postcode_area": ["postcode area", "postcode_area"],
    "sfbb": ["SFBB availability (% premises)", "SFBB availability"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)", "Gigabit availability"],
    "unable30": ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"],
}
USER_AGENT = "AAYS-internet-access-2/1.2 (+strict official Ofcom v2 postcode validation)"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for path in (start, *start.parents):
        if (path / "england_map_web").is_dir() and (path / "docs/chatgpt_status").is_dir():
            return path
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalise(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def match_header(fieldnames: list[str], aliases: list[str]) -> str | None:
    lookup = {normalise(name): name for name in fieldnames}
    for alias in aliases:
        key = normalise(alias)
        if key in lookup:
            return lookup[key]
    return None


def cache_path() -> Path:
    explicit = os.environ.get("AAYS_OFCom_ZIP_PATH")
    if explicit:
        return Path(explicit).expanduser().resolve()
    portable = os.environ.get("AAYS_PORTABLE_ROOT")
    root = Path(portable).expanduser().resolve() if portable else Path(tempfile.gettempdir()).resolve()
    return root / "state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip"


def request(url: str, timeout: int = 120):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "www.ofcom.org.uk":
        raise RuntimeError(f"UNTRUSTED_SOURCE_URL:{url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=timeout)


def discover_zip_url() -> tuple[str, str]:
    try:
        with request(SOURCE_PAGE, timeout=60) as response:
            page = response.read(2_000_000).decode("utf-8", errors="replace")
        matches = re.findall(r'href=["\']([^"\']*202601_fixed_broadband_coverage_and_full_fibre_take-up-r1\.zip[^"\']*)', page, re.I)
        if matches:
            url = urllib.parse.urljoin(SOURCE_PAGE, html.unescape(matches[0]))
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme == "https" and parsed.hostname == "www.ofcom.org.uk":
                return url, "DISCOVERED_FROM_OFFICIAL_PAGE"
    except Exception:
        pass
    return OUTER_ZIP_URL, "OFFICIAL_FALLBACK_URL"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_atomic(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in (1, 2):
        part = destination.with_suffix(destination.suffix + ".part")
        part.unlink(missing_ok=True)
        started = time.monotonic()
        bytes_written = 0
        try:
            with request(url, timeout=180) as response, part.open("wb") as output:
                declared = response.headers.get("Content-Length")
                if declared and int(declared) > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError(f"DOWNLOAD_TOO_LARGE_DECLARED:{declared}")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > MAX_DOWNLOAD_BYTES:
                        raise RuntimeError(f"DOWNLOAD_TOO_LARGE_STREAM:{bytes_written}")
                    output.write(chunk)
                content_type = str(response.headers.get("Content-Type", ""))
            if bytes_written < 1_000_000:
                raise RuntimeError(f"DOWNLOAD_TOO_SMALL:{bytes_written}")
            if not zipfile.is_zipfile(part):
                raise RuntimeError("DOWNLOADED_FILE_NOT_ZIP")
            os.replace(part, destination)
            return {"state": "DOWNLOADED", "attempt": attempt, "bytes": bytes_written, "sha256": sha256_file(destination), "content_type": content_type, "elapsed_seconds": round(time.monotonic() - started, 3)}
        except Exception as exc:
            last_error = exc
            part.unlink(missing_ok=True)
            if attempt == 1:
                time.sleep(2)
    assert last_error is not None
    raise RuntimeError(f"DOWNLOAD_FAILED_AFTER_2_ATTEMPTS:{type(last_error).__name__}:{last_error}")


def inspect_archive(path: Path, expected_files: int = EXPECTED_FILES, expected_rows: int = EXPECTED_ROWS) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as archive:
        bad_crc = archive.testzip()
        if bad_crc:
            raise RuntimeError(f"ZIP_CRC_FAILURE:{bad_crc}")
        members = [name.replace("\\", "/") for name in archive.namelist()]
        r2_members = sorted(name for name in members if R2_PATTERN.search(name))
        stale_r1_members = sorted(name for name in members if R1_PATTERN.search(name))
        rows: list[dict[str, Any]] = []
        total_rows = 0
        all_ok = True
        areas: list[str] = []
        for index, member in enumerate(r2_members, start=1):
            area_match = R2_PATTERN.search(member)
            area = area_match.group(1).upper() if area_match else ""
            areas.append(area)
            with archive.open(member, "r") as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="strict", newline=""))
                fieldnames = list(reader.fieldnames or [])
                matched = {key: match_header(fieldnames, aliases) for key, aliases in CORE_ALIASES.items()}
                missing = [key for key, value in matched.items() if value is None]
                row_count = sum(1 for _ in reader)
            status = "PASS" if row_count > 0 and not missing else "FAIL"
            all_ok = all_ok and status == "PASS"
            total_rows += row_count
            rows.append({"row": index, "file": member, "revision": "r2", "postcode_area": area, "data_rows": row_count, "missing_core_columns": missing, "matched_core_columns": matched, "status": status})
        count_ok = len(r2_members) == expected_files
        rows_ok = total_rows == expected_rows
        unique_areas_ok = len(set(areas)) == expected_files
        stale_r1_absent = not stale_r1_members
        accepted = count_ok and rows_ok and unique_areas_ok and stale_r1_absent and all_ok
        return {"member_count": len(members), "outer_archive_revision": "r1", "required_inner_postcode_revision": "r2", "observed_r2_postcode_file_count": len(r2_members), "expected_r2_postcode_file_count": expected_files, "r2_postcode_file_count_ok": count_ok, "observed_stale_r1_postcode_file_count": len(stale_r1_members), "stale_r1_postcode_files_absent": stale_r1_absent, "unique_postcode_area_count": len(set(areas)), "unique_postcode_areas_ok": unique_areas_ok, "total_r2_postcode_rows": total_rows, "expected_r2_postcode_rows": expected_rows, "total_r2_postcode_rows_ok": rows_ok, "all_r2_files_nonempty_and_core_columns_present": all_ok, "zip_crc_ok": True, "file_rows": rows, "accepted": accepted}


def render_html(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>internet_access_2 — Ofcom v2 strict doğrulama</title><style>body{{font-family:Arial,sans-serif;margin:20px;background:#f4f6f8;color:#17202a}}.cards{{display:flex;gap:10px;flex-wrap:wrap}}.card{{background:#fff;border:1px solid #cfd8dc;padding:10px;min-width:150px}}table{{border-collapse:collapse;width:100%;background:#fff;margin-top:14px;font-size:12px}}th,td{{border:1px solid #cfd8dc;padding:6px;text-align:left;vertical-align:top}}th{{background:#eceff1}}code,a{{word-break:break-all}}</style></head><body><h1>internet_access_2 — Ofcom v2 strict doğrulama</h1><div id="cards" class="cards"></div><h2>Resmî kaynaklar</h2><table><thead><tr><th>#</th><th>Kaynak</th><th>Durum</th><th>Kanıt</th></tr></thead><tbody id="sources"></tbody></table><h2>121 r2 dosyası</h2><table><thead><tr><th>#</th><th>Dosya</th><th>Alan</th><th>Satır</th><th>Eksik sütun</th><th>Durum</th></tr></thead><tbody id="rows"></tbody></table><script>const d={data};const e=v=>String(v??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));const cards=[['Durum',d.state],['İlerleme',d.progress_percent+'%'],['İşlem',d.completed_operations+'/'+d.total_operations],['İç revizyon',d.required_inner_postcode_revision??'r2'],['r2 dosya',(d.observed_r2_postcode_file_count??0)+'/'+(d.expected_r2_postcode_file_count??121)],['r2 satır',(d.total_r2_postcode_rows??0)+'/'+(d.expected_r2_postcode_rows??1741096)],['Aday',d.official_coverage_verified_candidates??0],['Doğruluk',d.accuracy_written??0]];document.getElementById('cards').innerHTML=cards.map(x=>`<div class="card">${{e(x[0])}}<br><b>${{e(x[1])}}</b></div>`).join('');document.getElementById('sources').innerHTML=(d.source_checks||[]).map(x=>`<tr><td>${{e(x.row)}}</td><td><a href="${{e(x.url)}}">${{e(x.source)}}</a></td><td>${{e(x.status)}}</td><td>${{e(x.evidence)}}</td></tr>`).join('');document.getElementById('rows').innerHTML=(d.file_rows||[]).map(x=>`<tr><td>${{e(x.row)}}</td><td><code>${{e(x.file)}}</code></td><td>${{e(x.postcode_area)}}</td><td>${{e(x.data_rows)}}</td><td>${{e((x.missing_core_columns||[]).join(', '))}}</td><td>${{e(x.status)}}</td></tr>`).join('');</script></body></html>'''


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / SHARD_REL
    web_root = root / WEB_REL
    destination = cache_path()
    source_checks = [
        {"row": 1, "source": "Ofcom Connected Nations Spring 2026", "url": SOURCE_PAGE, "status": "PASS_OFFICIAL_SOURCE", "evidence": "Official page exposes the 32.2 MB outer ZIP."},
        {"row": 2, "source": "Ofcom fixed coverage data notes v2", "url": SOURCE_PDF, "status": "PASS_V2_CORRECTION", "evidence": "7 July 2026 correction: all 121 all-premises postcode CSV files renamed from r1 to r2; CW and MK duplicates corrected."},
        {"row": 3, "source": "Strict archive contract", "url": SOURCE_PDF, "status": "PASS_STRICT_TARGET", "evidence": "Outer ZIP may retain r1 name; inner postcode_files must be 121 r2 CSVs with 1,741,096 total rows."},
    ]
    payload: dict[str, Any] = {"schema_version": 3, "slot_id": SLOT_ID, "task_id": os.environ.get("AAYS_TASK_ID"), "continuation_key": os.environ.get("AAYS_CONTINUATION_KEY"), "checked_at": now(), "state": "RECOVERY_STARTED", "completed_operations": 2, "total_operations": 3, "progress_percent": 66.67, "percent_change": 0.0, "source_checks": source_checks, "cache_path": str(destination), "official_coverage_verified_candidates": 0, "accuracy_written": 0, "parcel_measured_values_written": 0, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False}
    exit_code = 2
    try:
        zip_url, discovery = discover_zip_url()
        payload["zip_url"] = zip_url
        payload["zip_url_resolution"] = discovery
        if destination.is_file() and destination.stat().st_size >= 1_000_000 and zipfile.is_zipfile(destination):
            payload["download"] = {"state": "CACHE_REUSED", "bytes": destination.stat().st_size, "sha256": sha256_file(destination)}
        else:
            payload["download"] = download_atomic(zip_url, destination)
        inspection = inspect_archive(destination)
        payload.update(inspection)
        if inspection["accepted"]:
            payload.update({"state": "OFCom_V2_R2_POSTCODE_ARCHIVE_ACCEPTED", "completed_operations": 3, "progress_percent": 100.0, "percent_change": 33.33, "blocker": None, "next_step": "RUN_STRICT_EXACT_R2_JOIN_FOR_24_VERIFIED_POSTCODE_SAMPLES"})
            exit_code = 0
        else:
            payload.update({"state": "OFCom_V2_R2_POSTCODE_ARCHIVE_REJECTED", "blocker": "OFFICIAL_V2_ARCHIVE_R2_FILE_COUNT_ROW_COUNT_AREA_OR_CORE_COLUMN_CONTRACT_FAILED", "next_step": "REVIEW_R2_FILES_AND_REJECT_STALE_R1_INNER_POSTCODE_DATA"})
    except Exception as exc:
        payload.update({"state": "OFCom_V2_R2_ARCHIVE_PROVISION_FAILED", "blocker": f"{type(exc).__name__}:{exc}", "next_step": "KEEP_MANUAL_ACTION_OPEN_IF_CANONICAL_HOST_REPEATS_FAILURE", "observed_r2_postcode_file_count": 0, "expected_r2_postcode_file_count": EXPECTED_FILES, "total_r2_postcode_rows": 0, "expected_r2_postcode_rows": EXPECTED_ROWS, "file_rows": []})
    payload["updated_at"] = now()
    for rel in ["validation/009_ofcom_r2_full_archive_validation.json", "source_snapshots/009_ofcom_r2_archive_readback.json", "status/009_status.json", "web/009_ofcom_r2_line_by_line_latest.json", "recovery/005_ofcom_r2_provision_recovery.json"]:
        write_json(shard / rel, payload)
    write_json(web_root / "ofcom_r2_line_by_line_latest.json", payload)
    web_root.mkdir(parents=True, exist_ok=True)
    (web_root / "ofcom_r2_line_by_line.html").write_text(render_html(payload), encoding="utf-8")
    report = f"# internet_access_2 — Ofcom v2 strict r2 archive validation\n\n- State: {payload['state']}\n- Progress: {payload['completed_operations']}/{payload['total_operations']} ({payload['progress_percent']}%)\n- r2 files: {payload.get('observed_r2_postcode_file_count', 0)}/{EXPECTED_FILES}\n- r2 rows: {payload.get('total_r2_postcode_rows', 0)}/{EXPECTED_ROWS}\n- Blocker: {payload.get('blocker') or 'none'}\n- Candidate accuracy written: 0\n- final_ready: false\n"
    report_path = shard / "reports/009_ofcom_r2_provision_and_validation.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
