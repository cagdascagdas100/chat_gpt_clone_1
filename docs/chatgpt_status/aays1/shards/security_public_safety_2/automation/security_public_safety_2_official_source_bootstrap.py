from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
IOD25_PAGE = "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025"
IOD25_FILE7_V2_URL = (
    "https://assets.publishing.service.gov.uk/media/691ded56d140bbbaa59a2a7d/"
    "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators.csv"
)
MPS_DATASET_PAGE = "https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/"
MAX_DOWNLOAD_BYTES = 128 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def inspect_csv(path: Path, source: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": source,
        "path": str(path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "sha256": sha256_file(path) if path.is_file() else None,
        "pass": False,
        "rows_sampled": 0,
        "headers": [],
        "failures": [],
    }
    if not path.is_file() or path.stat().st_size <= 0:
        result["failures"].append("FILE_MISSING_OR_EMPTY")
        return result
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            result["headers"] = headers
            normalized = {normalize_header(header) for header in headers}
            for _ in range(3):
                if next(reader, None) is None:
                    break
                result["rows_sampled"] += 1
    except Exception as exc:
        result["failures"].append(f"CSV_READ:{type(exc).__name__}:{exc}")
        return result

    if source == "iod25_file7_v2":
        aliases = {
            "lsoa": {"lsoa code (2021)", "lsoa code", "lsoa_code", "lsoa21cd"},
            "score": {"crime score", "crime_score"},
            "rank": {"crime rank (where 1 is most deprived)", "crime rank", "crime_rank"},
            "decile": {
                "crime decile (where 1 is most deprived 10% of lsoas)",
                "crime decile",
                "crime_decile",
            },
        }
        for name, values in aliases.items():
            if not normalized.intersection(values):
                result["failures"].append(f"MISSING_{name.upper()}_HEADER")
        if "v2" not in path.name.lower() and "file_7_iod2025" not in path.name.lower():
            result["failures"].append("IOD25_V2_FILENAME_NOT_RECOGNISED")
    elif source == "mps_lsoa":
        code_aliases = {"lsoa code (2021)", "lsoa code", "lsoa_code", "lsoa21cd", "lsoa11cd"}
        if not normalized.intersection(code_aliases):
            result["failures"].append("MISSING_LSOA_HEADER")
        month_pattern = re.compile(
            r"^(?:20\d{2}[-_/ ]?(?:0[1-9]|1[0-2])|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-_ /]?20\d{2})$",
            re.I,
        )
        explicit_counts = {"count", "crime count", "offence count", "offences", "number of crimes"}
        if not any(month_pattern.match(header.strip()) for header in headers) and not normalized.intersection(explicit_counts):
            result["failures"].append("MISSING_MONTH_OR_COUNT_HEADER")
    else:
        result["failures"].append("UNKNOWN_SOURCE_TYPE")

    if result["rows_sampled"] == 0:
        result["failures"].append("NO_DATA_ROWS")
    result["pass"] = not result["failures"]
    return result


def _candidate_urls(text: str, base_url: str) -> list[str]:
    decoded = html.unescape(text).replace("\\/", "/")
    candidates: list[str] = []
    patterns = [
        r'https?://[^"\'<>\s]+(?:MPS|mps)[^"\'<>\s]*LSOA[^"\'<>\s]*Crime[^"\'<>\s]*\.csv(?:\?[^"\'<>\s]*)?',
        r'(?:href|url|download_url)\s*[:=]\s*["\']([^"\']+\.csv(?:\?[^"\']*)?)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, decoded, flags=re.I):
            value = match.group(1) if match.lastindex else match.group(0)
            value = urllib.parse.urljoin(base_url, value)
            lower = urllib.parse.unquote(value).lower()
            if "lsoa" in lower and "crime" in lower and value not in candidates:
                candidates.append(value)
    return candidates


def discover_mps_lsoa_url(page_text: str, base_url: str = MPS_DATASET_PAGE) -> dict[str, Any]:
    candidates = _candidate_urls(page_text, base_url)
    ranked = sorted(
        candidates,
        key=lambda value: (
            "2026" in urllib.parse.unquote(value),
            "lsoa level crime" in urllib.parse.unquote(value).lower(),
            -len(value),
        ),
        reverse=True,
    )
    return {
        "pass": bool(ranked),
        "selected_url": ranked[0] if ranked else None,
        "candidates": ranked,
        "dataset_page": base_url,
        "selection_rule": "newest official page order; URL must contain LSOA and Crime and end in CSV",
    }


def http_bytes(url: str, timeout: int, max_bytes: int = MAX_DOWNLOAD_BYTES) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-security-public-safety-slot2-source-bootstrap/1.0",
            "Accept": "text/csv,text/html,application/octet-stream,*/*;q=0.5",
            "Cache-Control": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"DOWNLOAD_TOO_LARGE:{total}>{max_bytes}")
            chunks.append(chunk)
        body = b"".join(chunks)
        return body, {
            "url": url,
            "final_url": response.geturl(),
            "http_status": int(response.status),
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }


def materialize_source(*, source: str, explicit_path: str | None, explicit_url: str | None, default_url: str | None, output_path: Path, timeout: int) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    if explicit_path:
        path = Path(explicit_path)
        validation = inspect_csv(path, source)
        attempts.append({"method": "explicit_path", "validation": validation})
        if validation["pass"]:
            return {"pass": True, "method": "explicit_path", "path": str(path), "validation": validation, "attempts": attempts}
    if output_path.is_file():
        validation = inspect_csv(output_path, source)
        attempts.append({"method": "cached_path", "validation": validation})
        if validation["pass"]:
            return {"pass": True, "method": "cached_path", "path": str(output_path), "validation": validation, "attempts": attempts}
    url = explicit_url or default_url
    if not url:
        return {"pass": False, "method": None, "path": None, "attempts": attempts, "blocker": f"{source.upper()}_URL_NOT_RESOLVED"}
    try:
        body, http = http_bytes(url, timeout)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output_path.with_suffix(output_path.suffix + ".tmp")
        temporary.write_bytes(body)
        validation = inspect_csv(temporary, source)
        attempts.append({"method": "download", "http": http, "validation": validation})
        if not validation["pass"]:
            temporary.unlink(missing_ok=True)
            return {"pass": False, "method": "download", "path": None, "attempts": attempts, "blocker": f"{source.upper()}_VALIDATION_FAILED"}
        shutil.move(str(temporary), str(output_path))
        validation = inspect_csv(output_path, source)
        return {"pass": True, "method": "download", "path": str(output_path), "url": url, "http": http, "validation": validation, "attempts": attempts}
    except Exception as exc:
        attempts.append({"method": "download", "url": url, "error": f"{type(exc).__name__}:{exc}"})
        return {"pass": False, "method": "download", "path": None, "attempts": attempts, "blocker": f"{source.upper()}_DOWNLOAD_FAILED"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    cache = out / "official_source_cache"
    manifest_path = out / "security_public_safety_2_official_source_manifest_latest.json"
    result: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "source_bootstrap_version": "1.0",
        "contract": {"slot": slot, "branch": branch, "pass": slot == SLOT_ID and branch == TARGET_BRANCH},
        "sources": {},
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    if not result["contract"]["pass"]:
        result.update({"pass": False, "blocker": f"WRONG_CONTRACT:slot={slot};branch={branch}"})
        out.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    mps_url = args.mps_url or os.environ.get("AAYS_MPS_LSOA_URL")
    discovery: dict[str, Any] | None = None
    if not mps_url and not (args.mps_path or os.environ.get("AAYS_MPS_LSOA_CSV")):
        try:
            page_body, page_http = http_bytes(MPS_DATASET_PAGE, args.timeout, max_bytes=8 * 1024 * 1024)
            discovery = discover_mps_lsoa_url(page_body.decode("utf-8", errors="replace"))
            discovery["page_http"] = page_http
            mps_url = discovery.get("selected_url")
        except Exception as exc:
            discovery = {"pass": False, "selected_url": None, "error": f"{type(exc).__name__}:{exc}", "dataset_page": MPS_DATASET_PAGE}
    iod = materialize_source(source="iod25_file7_v2", explicit_path=args.iod25_path or os.environ.get("AAYS_IOD25_V2_CSV"), explicit_url=args.iod25_url or os.environ.get("AAYS_IOD25_V2_URL"), default_url=IOD25_FILE7_V2_URL, output_path=cache / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators_v2.csv", timeout=args.timeout)
    mps = materialize_source(source="mps_lsoa", explicit_path=args.mps_path or os.environ.get("AAYS_MPS_LSOA_CSV"), explicit_url=mps_url, default_url=None, output_path=cache / "MPS_LSOA_Level_Crime_latest.csv", timeout=args.timeout)
    result["sources"] = {"iod25_file7_v2": iod, "mps_lsoa": mps}
    result["mps_discovery"] = discovery
    result["official_pages"] = {"iod25": IOD25_PAGE, "iod25_file7_v2": IOD25_FILE7_V2_URL, "mps_dataset": MPS_DATASET_PAGE}
    result["pass"] = bool(iod.get("pass") and mps.get("pass"))
    result["resolved_env"] = {"AAYS_IOD25_V2_CSV": iod.get("path") if iod.get("pass") else None, "AAYS_MPS_LSOA_CSV": mps.get("path") if mps.get("pass") else None}
    result["blocker"] = None if result["pass"] else "OFFICIAL_SOURCE_BOOTSTRAP_INCOMPLETE"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--iod25-path")
    parser.add_argument("--mps-path")
    parser.add_argument("--iod25-url")
    parser.add_argument("--mps-url")
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


if __name__ == "__main__":
    payload = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "pass": payload.get("pass"), "blocker": payload.get("blocker"), "resolved_env": payload.get("resolved_env"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(0 if payload.get("pass") else 2)
