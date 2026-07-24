# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
PARTITION_START = 30762
PARTITION_END = 61522
SAMPLE_SIZE_PER_WAVE = 12
ONSPD_SNAPSHOT = "2026-05"
ONSPD_LAYER_URL = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services/"
    "ONSPD_Online_latest_Postcode_Centroids/FeatureServer/0/query"
)
OFCom_SNAPSHOT = "2026-01"
OFCom_RELEASE = "Connected Nations Spring 2026 v2 (postcode correction 2026-07-07)"
OFCom_LANDING = (
    "https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/"
    "connected-nations-update-spring-2026"
)
OFCom_ZIP_URLS = [
    (
        "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
        "multi-sector/infrastructure-research/connected-nations-spring-2026/"
        "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
    ),
    (
        "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
        "multi-sector/infrastructure-research/connected-nations-spring-2026/"
        "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
    ),
]
ABOUT_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "about-this-data-fixed-broadband-coverage-and-full-fibre-take-up-2026.pdf?v=422757"
)


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


def postcode_area(value: str) -> str:
    match = re.match(r"^[A-Z]+", value)
    return match.group(0) if match else ""


def norm_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def parse_percent(value: Any) -> float | None:
    text = str(value or "").strip().replace("%", "")
    if not text or text.casefold() in {"na", "n/a", "null", "none", "-"}:
        return None
    try:
        return round(float(text), 4)
    except ValueError:
        return None


def pick(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    normalized = {norm_header(str(k)): v for k, v in row.items() if k is not None}
    for alias in aliases:
        key = norm_header(alias)
        if key in normalized:
            return normalized[key]
    return None


def parse_legacy_value(text: Any) -> dict[str, Any]:
    raw = str(text or "")
    patterns = {
        "postcode": r"postcode=([^;]+)",
        "gigabit_available_pct": r"gigabit=([0-9.]+)%",
        "ultrafast_100mbps_available_pct": r"ufbb100=([0-9.]+)%",
        "superfast_30mbps_available_pct": r"sfbb=([0-9.]+)%",
        "unable_30mbps_pct": r"unable30=([0-9.]+)%",
    }
    result: dict[str, Any] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if not match:
            result[key] = None
        elif key == "postcode":
            result[key] = norm_postcode(match.group(1))
        else:
            result[key] = parse_percent(match.group(1))
    return result


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def deterministic_sample(features: list[dict[str, Any]], size: int, phase: float) -> list[dict[str, Any]]:
    if not features:
        return []
    selected: list[dict[str, Any]] = []
    used: set[int] = set()
    for index in range(size):
        fraction = (index + phase) / size
        position = min(len(features) - 1, max(0, round(fraction * (len(features) - 1))))
        feature = features[position]
        row_no = int((feature.get("properties") or {}).get("row_no") or 0)
        if row_no and row_no not in used:
            selected.append(feature)
            used.add(row_no)
    for feature in features:
        if len(selected) >= size:
            break
        row_no = int((feature.get("properties") or {}).get("row_no") or 0)
        if row_no and row_no not in used:
            selected.append(feature)
            used.add(row_no)
    return selected[:size]


def candidate_from_feature(feature: dict[str, Any], wave: int) -> dict[str, Any]:
    props = feature.get("properties") or {}
    legacy = parse_legacy_value(props.get("internet_level_value"))
    return {
        "sample_wave": wave,
        "row_no": int(props.get("row_no") or 0),
        "parcel_id": props.get("parcel_id"),
        "hmlr_inspire_id": props.get("hmlr_inspire_id"),
        "hmlr_geometry_accuracy": props.get("hmlr_geometry_accuracy"),
        "postcode": legacy.get("postcode"),
        "legacy_metrics": legacy,
    }


def query_onspd(postcodes: set[str]) -> tuple[dict[str, dict[str, Any]], str | None, str]:
    where = "PCD7 IN (" + ",".join("'" + value.replace("'", "''") + "'" for value in sorted(postcodes)) + ")"
    params = {
        "where": where,
        "outFields": "PCD7,PCDS,DOINTR,DOTERM,LAT,LONG,LAD25CD,CTRY25CD",
        "returnGeometry": "false",
        "f": "json",
    }
    url = ONSPD_LAYER_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 AAYS-TerraYield official-postcode-validation",
            "Accept": "application/json,text/plain,*/*",
            "Referer": "https://www.arcgis.com/",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(json.dumps(payload["error"], ensure_ascii=False))
        found: dict[str, dict[str, Any]] = {}
        for feature in payload.get("features") or []:
            attributes = feature.get("attributes") or {}
            postcode = norm_postcode(attributes.get("PCD7") or attributes.get("PCDS"))
            if postcode:
                found[postcode] = attributes
        return found, None, url
    except Exception as exc:
        return {}, f"ONSPD_ARCGIS_QUERY_BLOCKED: {type(exc).__name__}: {exc}", url


def browser_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Referer": OFCom_LANDING,
        "Connection": "keep-alive",
    }


def try_urllib_download(url: str, target: Path) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers=browser_headers())
        with urllib.request.urlopen(request, timeout=300) as response, target.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if target.stat().st_size < 1_000_000 or not zipfile.is_zipfile(target):
            raise RuntimeError(f"INVALID_ZIP_SIZE_OR_SIGNATURE:{target.stat().st_size}")
        return True, "urllib_browser_headers"
    except Exception as exc:
        target.unlink(missing_ok=True)
        return False, f"urllib:{type(exc).__name__}:{exc}"


def try_curl_download(url: str, target: Path) -> tuple[bool, str]:
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if not executable:
        return False, "curl:not_available"
    completed = subprocess.run(
        [
            executable,
            "--location",
            "--fail",
            "--retry",
            "2",
            "--connect-timeout",
            "30",
            "--max-time",
            "360",
            "--user-agent",
            browser_headers()["User-Agent"],
            "--referer",
            OFCom_LANDING,
            "--header",
            "Accept: application/zip,application/octet-stream;q=0.9,*/*;q=0.8",
            "--output",
            str(target),
            url,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode == 0 and target.is_file() and target.stat().st_size >= 1_000_000 and zipfile.is_zipfile(target):
        return True, "curl_browser_headers"
    target.unlink(missing_ok=True)
    return False, f"curl:exit={completed.returncode}:{completed.stderr.strip()[-500:]}"


def download_ofcom_zip(cache_path: Path) -> tuple[Path | None, list[str], str | None]:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.is_file() and cache_path.stat().st_size >= 1_000_000 and zipfile.is_zipfile(cache_path):
        return cache_path, ["cache_hit"], None
    errors: list[str] = []
    for url in OFCom_ZIP_URLS:
        temporary = cache_path.with_suffix(".download")
        for downloader in (try_urllib_download, try_curl_download):
            ok, detail = downloader(url, temporary)
            errors.append(f"{url}|{detail}")
            if ok:
                temporary.replace(cache_path)
                return cache_path, errors, None
    return None, errors, "OFCom_2026_DOWNLOAD_BLOCKED_AFTER_BROWSER_AND_CURL_FALLBACKS"


def find_area_member(names: list[str], area: str) -> str | None:
    pattern = re.compile(rf"202601_fixed_postcode_coverage_r2_{re.escape(area)}\.csv$", re.I)
    for name in names:
        if pattern.search(name.replace("\\", "/")):
            return name
    return None


def load_ofcom_rows(archive: zipfile.ZipFile, postcodes: set[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    names = archive.namelist()
    by_area: dict[str, set[str]] = {}
    for postcode in postcodes:
        by_area.setdefault(postcode_area(postcode), set()).add(postcode)
    found: dict[str, dict[str, Any]] = {}
    missing_areas: list[str] = []
    for area, targets in sorted(by_area.items()):
        member = find_area_member(names, area)
        if not member:
            missing_areas.append(area)
            continue
        with archive.open(member, "r") as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline=""))
            for row in reader:
                postcode = norm_postcode(pick(row, ["postcode", "postcode_space"]))
                if postcode in targets:
                    found[postcode] = row
                    if targets.issubset(found.keys()):
                        break
    return found, missing_areas


def official_metrics(row: dict[str, Any]) -> dict[str, float | None]:
    return {
        "superfast_30mbps_available_pct": parse_percent(pick(row, ["SFBB availability (% premises)", "SFBB availability"])),
        "ultrafast_100mbps_available_pct": parse_percent(pick(row, ["UFBB (100Mbit/s) availability (% premises)", "UFBB100 availability (% premises)"])),
        "ultrafast_300mbps_available_pct": parse_percent(pick(row, ["UFBB availability (% premises)", "UFBB (300Mbit/s) availability (% premises)"])),
        "gigabit_available_pct": parse_percent(pick(row, ["Gigabit availability (% premises)", "Gigabit availability"])),
        "unable_30mbps_pct": parse_percent(pick(row, ["% of premises unable to receive 30Mbit/s", "unable to receive 30Mbit/s"])),
        "decent_broadband_unavailable_fixed_or_fwa_pct": parse_percent(pick(row, ["% of premises unable to receive decent broadband from fixed or FWA"])),
    }


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")
    root = repo_root()
    shard = root / "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards" / SLOT_ID
    progress_path = shard / "progress/003_progress.jsonl"
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text("", encoding="utf-8")
    append_progress(progress_path, 1, "slot_partition_guard", "PASS", partition=[PARTITION_START, PARTITION_END])

    matrix_path = root / "england_map_web/data/program_layer_matrix/internet.geojson"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
    all_features = matrix.get("features") or []
    shard_features = sorted(
        [f for f in all_features if PARTITION_START <= int((f.get("properties") or {}).get("row_no") or 0) <= PARTITION_END],
        key=lambda f: int((f.get("properties") or {}).get("row_no") or 0),
    )
    append_progress(progress_path, 2, "shard2_existing_feature_filter", "PASS", total_existing=len(all_features), shard2_existing=len(shard_features))

    wave1 = deterministic_sample(shard_features, SAMPLE_SIZE_PER_WAVE, 0.0)
    wave2 = deterministic_sample(shard_features, SAMPLE_SIZE_PER_WAVE, 0.5)
    used_rows = {int((f.get("properties") or {}).get("row_no") or 0) for f in wave1}
    wave2 = [f for f in wave2 if int((f.get("properties") or {}).get("row_no") or 0) not in used_rows]
    if len(wave2) < SAMPLE_SIZE_PER_WAVE:
        for feature in shard_features:
            row_no = int((feature.get("properties") or {}).get("row_no") or 0)
            if row_no not in used_rows and all(int((x.get("properties") or {}).get("row_no") or 0) != row_no for x in wave2):
                wave2.append(feature)
                if len(wave2) == SAMPLE_SIZE_PER_WAVE:
                    break
    candidates = [candidate_from_feature(f, 1) for f in wave1] + [candidate_from_feature(f, 2) for f in wave2[:SAMPLE_SIZE_PER_WAVE]]
    postcodes = {norm_postcode(row.get("postcode")) for row in candidates if norm_postcode(row.get("postcode"))}
    append_progress(progress_path, 3, "two_wave_24_sample_selection", "PASS", candidates=len(candidates), distinct_postcodes=len(postcodes))

    onspd, onspd_blocker, onspd_query_url = query_onspd(postcodes)
    append_progress(progress_path, 4, "official_onspd_may_2026_arcgis_query", "PASS" if not onspd_blocker else "BLOCKED", requested=len(postcodes), found=len(onspd), blocker=onspd_blocker)

    portable_root = Path(os.environ.get("AAYS_PORTABLE_ROOT") or tempfile.gettempdir()).resolve()
    ofcom_cache = portable_root / "state/source_cache/ofcom_spring_2026/ofcom_fixed_coverage_202601_v2.zip"
    zip_path, download_attempts, ofcom_blocker = download_ofcom_zip(ofcom_cache)
    ofcom_rows: dict[str, dict[str, Any]] = {}
    missing_areas: list[str] = []
    if zip_path:
        with zipfile.ZipFile(zip_path, "r") as archive:
            ofcom_rows, missing_areas = load_ofcom_rows(archive, postcodes)
        append_progress(progress_path, 5, "official_ofcom_zip_and_r2_row_resolution", "PASS" if not missing_areas else "PARTIAL", zip_bytes=zip_path.stat().st_size, zip_sha256=sha256_file(zip_path), exact_postcodes=len(ofcom_rows), missing_areas=missing_areas)
    else:
        append_progress(progress_path, 5, "official_ofcom_zip_download_fallbacks", "BLOCKED", blocker=ofcom_blocker, attempts=download_attempts)

    rows: list[dict[str, Any]] = []
    postcode_identity_confirmed = 0
    postcode_live = 0
    postcode_terminated = 0
    coverage_verified = 0
    for line_no, candidate in enumerate(candidates, start=1):
        postcode = norm_postcode(candidate.get("postcode"))
        ons = onspd.get(postcode)
        if ons:
            postcode_identity_confirmed += 1
            terminated = bool(str(ons.get("DOTERM") or "").strip())
            if terminated:
                postcode_terminated += 1
                onspd_status = "TERMINATED_REVIEW_REQUIRED"
            else:
                postcode_live += 1
                onspd_status = "CONFIRMED_LIVE"
        else:
            onspd_status = "NOT_CONFIRMED"
        official_row = ofcom_rows.get(postcode)
        metrics = official_metrics(official_row) if official_row else None
        core_complete = bool(metrics) and all(metrics.get(key) is not None for key in (
            "gigabit_available_pct", "ultrafast_100mbps_available_pct", "superfast_30mbps_available_pct", "unable_30mbps_pct"
        ))
        if core_complete and onspd_status == "CONFIRMED_LIVE":
            coverage_verified += 1
            candidate_status = "VERIFIED_POSTCODE_PROXY_CANDIDATE"
            accuracy = "3/4"
            confidence = 0.75
        elif onspd_status == "CONFIRMED_LIVE":
            candidate_status = "POSTCODE_IDENTITY_CONFIRMED_COVERAGE_PENDING"
            accuracy = "2/4"
            confidence = 0.0
        elif onspd_status == "TERMINATED_REVIEW_REQUIRED":
            candidate_status = "POSTCODE_TERMINATED_REVIEW_REQUIRED"
            accuracy = "1/4"
            confidence = 0.0
        else:
            candidate_status = "NO_DATA_NOT_INFERRED"
            accuracy = "0/4"
            confidence = 0.0
        row = {
            "line": line_no,
            **candidate,
            "onspd_snapshot_date": ONSPD_SNAPSHOT,
            "onspd_status": onspd_status,
            "onspd": ons,
            "ofcom_snapshot_date": OFCom_SNAPSHOT,
            "ofcom_release": OFCom_RELEASE,
            "official_metrics": metrics,
            "source_level": "POSTCODE_PROXY" if core_complete else "POSTCODE_IDENTITY_ONLY",
            "candidate_status": candidate_status,
            "internet_accuracy": accuracy,
            "match_confidence": confidence,
            "parcel_measured_speed": False,
            "fake_data": False,
            "final_ready": False,
        }
        rows.append(row)
        append_progress(progress_path, 5 + line_no, "candidate_row", candidate_status, line=line_no, row_no=row["row_no"], postcode=postcode, accuracy=accuracy, onspd_status=onspd_status, ofcom_exact=core_complete)

    data_path = shard / "data/003_24_sample_identity_and_coverage_candidates.jsonl"
    web_path = shard / "web/003_24_sample_rows_latest.json"
    validation_path = shard / "validation/003_24_sample_validation.json"
    source_path = shard / "source_snapshots/003_official_source_readback.json"
    status_path = shard / "status/003_status.json"
    report_path = shard / "reports/003_onspd_arcgis_ofcom_retry_24_sample.md"
    write_jsonl(data_path, rows)
    write_json(web_path, {"slot_id": SLOT_ID, "rows": rows, "generated_at": utc_now(), "final_ready": False})
    write_json(source_path, {
        "slot_id": SLOT_ID,
        "onspd": {"snapshot": ONSPD_SNAPSHOT, "layer_url": ONSPD_LAYER_URL, "query_url": onspd_query_url, "blocker": onspd_blocker, "returned": len(onspd)},
        "ofcom": {"snapshot": OFCom_SNAPSHOT, "release": OFCom_RELEASE, "landing_url": OFCom_LANDING, "zip_urls": OFCom_ZIP_URLS, "about_url": ABOUT_URL, "download_attempts": download_attempts, "blocker": ofcom_blocker, "exact_rows": len(ofcom_rows), "missing_areas": missing_areas},
        "final_ready": False,
    })
    validation = {
        "slot_id": SLOT_ID,
        "partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "existing_canonical_feature_count": len(all_features),
        "existing_shard2_feature_count": len(shard_features),
        "sample_rows": len(rows),
        "postcode_identity_confirmed": postcode_identity_confirmed,
        "postcode_live": postcode_live,
        "postcode_terminated_review_required": postcode_terminated,
        "official_coverage_verified_candidates": coverage_verified,
        "maximum_accuracy": "3/4_POSTCODE_PROXY",
        "parcel_measured_values_written": 0,
        "onspd_blocker": onspd_blocker,
        "ofcom_blocker": ofcom_blocker,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "validated_at": utc_now(),
    }
    write_json(validation_path, validation)
    completed_operations = 5 + len(rows) + 1
    total_operations = completed_operations + (0 if coverage_verified else 1)
    status = {
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "state": "SAMPLE_WAVE_VERIFIED" if coverage_verified else "POSTCODE_IDENTITY_VERIFIED_COVERAGE_SOURCE_BLOCKED",
        "completed_operations": completed_operations,
        "total_operations": total_operations,
        "progress_percent": round(100 * completed_operations / total_operations, 2),
        "postcode_identity_confirmed": postcode_identity_confirmed,
        "official_coverage_verified_candidates": coverage_verified,
        "sample_rows": len(rows),
        "next_step": "RETRY_OFFICIAL_OFCom_R2_DOWNLOAD_THEN_EXPAND_EXACT_POSTCODE_VALIDATION_ACROSS_11013_EXISTING_SHARD2_ROWS",
        "blockers": [value for value in (onspd_blocker, ofcom_blocker) if value],
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "updated_at": utc_now(),
    }
    write_json(status_path, status)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# internet_access_2 — ONSPD + Ofcom retry, 24-sample wave\n\n"
        f"- Existing shard-2 internet rows: {len(shard_features)}\n"
        f"- Sample rows: {len(rows)}\n"
        f"- ONSPD identity confirmed: {postcode_identity_confirmed}\n"
        f"- ONSPD live: {postcode_live}\n"
        f"- ONSPD terminated/review: {postcode_terminated}\n"
        f"- Ofcom exact coverage rows verified: {coverage_verified}\n"
        f"- Accuracy ceiling: 3/4 postcode proxy\n"
        f"- Parcel-measured values written: 0\n"
        f"- ONSPD blocker: {onspd_blocker or 'none'}\n"
        f"- Ofcom blocker: {ofcom_blocker or 'none'}\n"
        "- final_ready: false\n",
        encoding="utf-8",
    )
    append_progress(progress_path, 30, "web_and_remote_artifacts_written", "PASS", files=[str(path.relative_to(root)).replace("\\", "/") for path in (data_path, web_path, validation_path, source_path, status_path, report_path)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
