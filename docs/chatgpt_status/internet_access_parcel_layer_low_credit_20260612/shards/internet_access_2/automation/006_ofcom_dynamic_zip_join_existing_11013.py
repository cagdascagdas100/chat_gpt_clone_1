# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import http.cookiejar
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from datetime import datetime, timezone

SLOT_ID = "internet_access_2"
PARTITION_START = 30762
PARTITION_END = 61522
EXPECTED_ROWS = 11013
WEB_CHUNK_SIZE = 500
OFCom_SNAPSHOT = "2026-01"
OFCom_RELEASE = "Connected Nations Spring 2026 v2 (postcode correction 2026-07-07)"
LANDING_URL = "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026"
KNOWN_ZIP_URLS = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/"
    "infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620",
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/"
    "infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip",
)
SHARD_REL = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_2"
)
INPUT_REL = SHARD_REL + "/data/005_existing_11013_postcode_identity_candidates.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_root() -> Path:
    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def norm_postcode(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def postcode_area(value: Any) -> str:
    match = re.match(r"^[A-Z]+", norm_postcode(value))
    return match.group(0) if match else ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_progress(path: Path, step: int, operation: str, state: str, **extra: Any) -> None:
    row = {"at": utc_now(), "step": step, "operation": operation, "state": state, **extra}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(row, ensure_ascii=False), flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def browser_headers(referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive",
    }
    if referer:
        headers["Referer"] = referer
    return headers


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def make_opener() -> urllib.request.OpenerDirector:
    cookie_jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPRedirectHandler(),
    )


def discover_zip_urls(opener: urllib.request.OpenerDirector) -> tuple[list[str], str | None]:
    try:
        request = urllib.request.Request(LANDING_URL, headers=browser_headers())
        with opener.open(request, timeout=90) as response:
            html = response.read().decode("utf-8", errors="replace")
        parser = LinkParser()
        parser.feed(html)
        discovered: list[str] = []
        for href in parser.links:
            absolute = urllib.parse.urljoin(LANDING_URL, href)
            lower = absolute.casefold()
            if ".zip" in lower and "fixed_broadband_coverage" in lower:
                discovered.append(absolute)
        ordered: list[str] = []
        for url in [*discovered, *KNOWN_ZIP_URLS]:
            if url not in ordered:
                ordered.append(url)
        return ordered, None
    except Exception as exc:
        return list(KNOWN_ZIP_URLS), f"LANDING_DISCOVERY_BLOCKED: {type(exc).__name__}: {exc}"


def urllib_download(opener: urllib.request.OpenerDirector, url: str, target: Path) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers=browser_headers(LANDING_URL))
        with opener.open(request, timeout=360) as response, target.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if target.stat().st_size < 1_000_000 or not zipfile.is_zipfile(target):
            raise RuntimeError(f"INVALID_ZIP:{target.stat().st_size}")
        return True, "urllib_cookie_session"
    except Exception as exc:
        target.unlink(missing_ok=True)
        return False, f"urllib:{type(exc).__name__}:{exc}"


def curl_download(url: str, target: Path) -> tuple[bool, str]:
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if not executable:
        return False, "curl:not_available"
    completed = subprocess.run(
        [
            executable, "--location", "--fail", "--retry", "3",
            "--connect-timeout", "30", "--max-time", "480",
            "--user-agent", browser_headers()["User-Agent"],
            "--referer", LANDING_URL,
            "--header", "Accept: application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
            "--output", str(target), url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode == 0 and target.is_file() and target.stat().st_size >= 1_000_000 and zipfile.is_zipfile(target):
        return True, "curl_landing_referer"
    target.unlink(missing_ok=True)
    return False, f"curl:exit={completed.returncode}:{completed.stderr.strip()[-500:]}"


def obtain_zip(cache_path: Path) -> tuple[Path | None, dict[str, Any]]:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.is_file() and cache_path.stat().st_size >= 1_000_000 and zipfile.is_zipfile(cache_path):
        return cache_path, {"state": "CACHE_HIT", "attempts": []}
    opener = make_opener()
    urls, discovery_blocker = discover_zip_urls(opener)
    attempts: list[dict[str, str]] = []
    for url in urls:
        temporary = cache_path.with_suffix(".download")
        for name, downloader in (
            ("urllib_cookie_session", lambda: urllib_download(opener, url, temporary)),
            ("curl_landing_referer", lambda: curl_download(url, temporary)),
        ):
            ok, detail = downloader()
            attempts.append({"url": url, "method": name, "detail": detail})
            if ok:
                temporary.replace(cache_path)
                return cache_path, {
                    "state": "DOWNLOADED",
                    "discovery_blocker": discovery_blocker,
                    "selected_url": url,
                    "method": name,
                    "attempts": attempts,
                }
    return None, {
        "state": "BLOCKED",
        "discovery_blocker": discovery_blocker,
        "attempts": attempts,
        "blocker": "OFCom_2026_BINARY_ACCESS_BLOCKED_AFTER_LANDING_COOKIE_AND_CURL_RETRY",
    }


def pick(row: dict[str, Any], aliases: list[str]) -> Any:
    lookup = {re.sub(r"[^a-z0-9]+", "", str(key).casefold()): value for key, value in row.items()}
    for alias in aliases:
        key = re.sub(r"[^a-z0-9]+", "", alias.casefold())
        if key in lookup:
            return lookup[key]
    return None


def parse_percent(value: Any) -> float | None:
    text = str(value or "").strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def official_metrics(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "superfast_30mbps_available_pct": parse_percent(pick(row, [
            "SFBB availability (% premises)", "SFBB availability"
        ])),
        "ultrafast_100mbps_available_pct": parse_percent(pick(row, [
            "UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"
        ])),
        "ultrafast_300mbps_available_pct": parse_percent(pick(row, [
            "UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"
        ])),
        "gigabit_available_pct": parse_percent(pick(row, [
            "Gigabit availability (% premises)", "Gigabit availability"
        ])),
        "unable_30mbps_pct": parse_percent(pick(row, [
            "% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"
        ])),
        "decent_broadband_unavailable_fixed_or_fwa_pct": parse_percent(pick(row, [
            "% of premises unable to receive decent broadband from fixed or FWA"
        ])),
    }


def find_member(names: list[str], area: str) -> str | None:
    pattern = re.compile(rf"202601_fixed_postcode_coverage_r2_{re.escape(area)}\.csv$", re.I)
    for name in names:
        if pattern.search(name.replace("\\", "/")):
            return name
    return None


def load_exact_rows(archive: zipfile.ZipFile, postcodes: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    by_area: dict[str, set[str]] = {}
    for postcode in postcodes:
        by_area.setdefault(postcode_area(postcode), set()).add(postcode)
    names = archive.namelist()
    found: dict[str, dict[str, Any]] = {}
    missing_areas: list[str] = []
    for area, targets in sorted(by_area.items()):
        member = find_member(names, area)
        if not member:
            missing_areas.append(area)
            continue
        with archive.open(member, "r") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
            for row in reader:
                postcode = norm_postcode(pick(row, ["postcode", "postcode_space"]))
                if postcode in targets:
                    found[postcode] = row
    return found, missing_areas


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / SHARD_REL
    progress_path = shard / "progress/006_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    append_progress(progress_path, 1, "slot_partition_guard", "PASS",
                    partition=[PARTITION_START, PARTITION_END])

    rows = load_jsonl(root / INPUT_REL)
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"EXPECTED_{EXPECTED_ROWS}_INPUT_ROWS_GOT_{len(rows)}")
    if any(not (PARTITION_START <= int(row.get("row_no") or 0) <= PARTITION_END) for row in rows):
        raise RuntimeError("INPUT_ROW_OUTSIDE_SLOT_PARTITION")
    postcodes = {norm_postcode(row.get("postcode")) for row in rows if norm_postcode(row.get("postcode"))}
    append_progress(progress_path, 2, "wave005_identity_readback", "PASS",
                    rows=len(rows), distinct_postcodes=len(postcodes))

    portable_root = Path(os.environ.get("AAYS_PORTABLE_ROOT") or tempfile.gettempdir()).resolve()
    cache_path = portable_root / "state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip"
    zip_path, access = obtain_zip(cache_path)
    exact: dict[str, dict[str, Any]] = {}
    missing_areas: list[str] = []
    if zip_path:
        with zipfile.ZipFile(zip_path, "r") as archive:
            exact, missing_areas = load_exact_rows(archive, postcodes)
        append_progress(
            progress_path, 3, "official_ofcom_r2_exact_row_resolution",
            "PASS" if not missing_areas else "PARTIAL",
            zip_bytes=zip_path.stat().st_size,
            zip_sha256=sha256_file(zip_path),
            exact_postcodes=len(exact),
            missing_areas=missing_areas,
        )
    else:
        append_progress(
            progress_path, 3, "official_ofcom_binary_access",
            "BLOCKED", blocker=access.get("blocker"), attempts=len(access.get("attempts") or []),
        )

    output: list[dict[str, Any]] = []
    verified = coverage_missing = identity_missing = 0
    for line_no, row in enumerate(rows, start=1):
        postcode = norm_postcode(row.get("postcode"))
        official_row = exact.get(postcode)
        metrics = official_metrics(official_row) if official_row else None
        core_complete = bool(metrics) and all(metrics.get(key) is not None for key in (
            "gigabit_available_pct", "ultrafast_100mbps_available_pct",
            "superfast_30mbps_available_pct", "unable_30mbps_pct"
        ))
        live_identity = row.get("onspd_status") == "ONSPD_CONFIRMED_LIVE_COVERAGE_PENDING"
        if core_complete and live_identity:
            status = "VERIFIED_POSTCODE_PROXY_CANDIDATE"
            accuracy = "3/4"
            confidence = 0.75
            verified += 1
        elif live_identity:
            status = "POSTCODE_IDENTITY_CONFIRMED_COVERAGE_PENDING"
            accuracy = "2/4"
            confidence = 0.0
            coverage_missing += 1
        else:
            status = row.get("candidate_status") or "NO_DATA_NOT_INFERRED"
            accuracy = row.get("internet_accuracy") or "0/4"
            confidence = 0.0
            identity_missing += 1
        output.append({
            **row,
            "line": line_no,
            "ofcom_snapshot_date": OFCom_SNAPSHOT,
            "ofcom_release": OFCom_RELEASE,
            "official_metrics": metrics,
            "official_coverage_verified": bool(core_complete and live_identity),
            "candidate_status": status,
            "internet_accuracy": accuracy,
            "match_confidence": confidence,
            "source_level": "POSTCODE_PROXY" if core_complete else "POSTCODE_IDENTITY_ONLY",
            "parcel_measured_speed": False,
            "fake_data": False,
            "final_ready": False,
        })

    data_path = shard / "data/006_existing_11013_official_coverage_candidates.jsonl"
    write_jsonl(data_path, output)
    web_root = shard / "web/006_chunks"
    manifest: list[dict[str, Any]] = []
    for chunk_no, start in enumerate(range(0, len(output), WEB_CHUNK_SIZE), start=1):
        chunk_rows = output[start:start + WEB_CHUNK_SIZE]
        path = web_root / f"part_{chunk_no:03d}.json"
        write_json(path, {
            "slot_id": SLOT_ID,
            "chunk": chunk_no,
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "rows": chunk_rows,
            "final_ready": False,
        })
        manifest.append({
            "chunk": chunk_no,
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "row_start": start + 1,
            "row_end": start + len(chunk_rows),
            "count": len(chunk_rows),
        })

    blocker = None if zip_path else access.get("blocker")
    validation = {
        "slot_id": SLOT_ID,
        "existing_shard2_rows": len(output),
        "distinct_postcodes": len(postcodes),
        "official_coverage_verified_candidates": verified,
        "postcode_identity_confirmed_coverage_pending": coverage_missing,
        "identity_missing_or_review": identity_missing,
        "maximum_accuracy": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "zip_access": access,
        "missing_postcode_areas": missing_areas,
        "blocker": blocker,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    }
    validation_path = shard / "validation/006_existing_11013_coverage_validation.json"
    manifest_path = shard / "web/006_existing_11013_rows_manifest.json"
    source_path = shard / "source_snapshots/006_ofcom_binary_readback.json"
    status_path = shard / "status/006_status.json"
    report_path = shard / "reports/006_existing_11013_ofcom_coverage.md"
    write_json(validation_path, validation)
    write_json(manifest_path, {
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "total_rows": len(output),
        "chunk_size": WEB_CHUNK_SIZE,
        "chunks": manifest,
        "counts": {
            "verified_3_of_4": verified,
            "identity_2_of_4_coverage_pending": coverage_missing,
            "identity_missing_or_review": identity_missing,
        },
        "final_ready": False,
    })
    write_json(source_path, {
        "slot_id": SLOT_ID,
        "landing_url": LANDING_URL,
        "known_zip_urls": list(KNOWN_ZIP_URLS),
        "snapshot": OFCom_SNAPSHOT,
        "release": OFCom_RELEASE,
        "access": access,
        "exact_rows_returned": len(exact),
        "missing_postcode_areas": missing_areas,
        "final_ready": False,
    })
    write_json(status_path, {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "OFFICIAL_COVERAGE_JOIN_COMPLETE" if verified else "OFFICIAL_COVERAGE_SOURCE_BLOCKED",
        "completed_operations": 5,
        "total_operations": 6 if not verified else 5,
        "progress_percent": 100.0 if verified else 83.33,
        **validation,
        "next_step": (
            "REVIEW_MATERIAL_DELTAS_THEN_PUBLISH_CANONICAL_SHARD2_CANDIDATES"
            if verified
            else "PROVISION_OFFICIAL_OFCom_ZIP_OR_SUBSCRIPTION_KEY_THEN_RETRY_EXACT_COVERAGE_JOIN"
        ),
        "updated_at": utc_now(),
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — 11,013-row Ofcom exact coverage join\n\n"
        f"- Input rows: {len(output)}\n"
        f"- Official 3/4 postcode-proxy candidates: {verified}\n"
        f"- Identity confirmed, coverage pending: {coverage_missing}\n"
        f"- Identity missing/review: {identity_missing}\n"
        f"- Web chunks: {len(manifest)}\n"
        f"- Blocker: {blocker or 'none'}\n"
        "- Parcel-measured values written: 0\n"
        "- final_ready: false\n",
        encoding="utf-8",
    )
    append_progress(
        progress_path, 4, "web_and_remote_artifacts_written", "PASS",
        rows=len(output), chunks=len(manifest), verified=verified,
        coverage_pending=coverage_missing, blocker=blocker,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
