from __future__ import annotations

import argparse
import html
import importlib.util
import ipaddress
import json
import os
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
POLICE_LATEST_URL = "https://data.police.uk/api/crime-last-updated"
MPS_DATASET_PAGE = "https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/"
BASE_FILENAME = "security_public_safety_2_official_source_bootstrap.py"
MAX_RESOURCE_PAGES = 16
MIN_MPS_PERIOD_END = "2026-06-30"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_base() -> Any:
    path = Path(__file__).resolve().with_name(BASE_FILENAME)
    spec = importlib.util.spec_from_file_location("security_slot2_source_bootstrap_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BASE_BOOTSTRAP_IMPORT_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_public_https_url(url: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {"url": url, "pass": False, "failure": None, "host": None}
    if not url:
        result["failure"] = "URL_MISSING"
        return result
    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception as exc:
        result["failure"] = f"URL_PARSE:{type(exc).__name__}:{exc}"
        return result
    host = (parsed.hostname or "").rstrip(".").lower()
    result["host"] = host
    if parsed.scheme.lower() != "https":
        result["failure"] = "HTTPS_REQUIRED"
        return result
    if not host:
        result["failure"] = "HOST_MISSING"
        return result
    if parsed.username or parsed.password:
        result["failure"] = "URL_CREDENTIALS_FORBIDDEN"
        return result
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        result["failure"] = "LOCALHOST_FORBIDDEN"
        return result
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        result["failure"] = "NON_PUBLIC_IP_FORBIDDEN"
        return result
    result["pass"] = True
    return result


def extract_resource_page_urls(page_text: str, base_url: str = MPS_DATASET_PAGE) -> list[str]:
    decoded = html.unescape(page_text).replace("\\/", "/")
    patterns = [
        r'(?:href|url)\s*[:=]\s*["\']([^"\']+/resource/[0-9a-fA-F-]{36}[^"\']*)["\']',
        r'(https?://[^"\'<>\s]+/resource/[0-9a-fA-F-]{36}[^"\'<>\s]*)',
        r'(/[^"\'<>\s]+/resource/[0-9a-fA-F-]{36}[^"\'<>\s]*)',
    ]
    output: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, decoded, flags=re.I):
            value = urllib.parse.urljoin(base_url, match.group(1))
            check = validate_public_https_url(value)
            if check["pass"] and value not in output:
                output.append(value)
    return output


def extract_download_urls(page_text: str, base_url: str) -> list[str]:
    decoded = html.unescape(page_text).replace("\\/", "/")
    patterns = [
        r'(?:href|url|download_url)\s*[:=]\s*["\']([^"\']+(?:\.csv(?:\?[^"\']*)?|/download/[^"\']*|download[^"\']*))["\']',
        r'(https?://[^"\'<>\s]+\.csv(?:\?[^"\'<>\s]*)?)',
    ]
    output: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, decoded, flags=re.I):
            value = urllib.parse.urljoin(base_url, match.group(1))
            check = validate_public_https_url(value)
            if check["pass"] and value not in output:
                output.append(value)
    return output


def plain_text(value: str) -> str:
    value = html.unescape(value).replace("\\/", "/")
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def iso_date(day: str, month: str, year: str) -> str | None:
    try:
        return datetime(int(year), int(month), int(day), tzinfo=timezone.utc).date().isoformat()
    except Exception:
        return None


def parse_resource_page(page_url: str, page_text: str) -> dict[str, Any]:
    plain = plain_text(page_text)
    title_match = re.search(r"MPS\s+LSOA\s+Level\s+Crime(?:\s+\(Historical\))?\.csv", plain, flags=re.I)
    title = title_match.group(0) if title_match else None
    historical = bool(title and "historical" in title.lower())
    to_match = re.search(r"\bTo\s+(\d{2})/(\d{2})/(\d{4})\b", plain, flags=re.I)
    period_end = iso_date(*to_match.groups()) if to_match else None
    if period_end is None:
        range_match = re.search(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[–-]\s*"
            r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\b",
            plain,
            flags=re.I,
        )
        if range_match:
            month_number = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }[range_match.group(1).lower()]
            year = int(range_match.group(2))
            next_month = datetime(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1, tzinfo=timezone.utc)
            period_end = (next_month.date() - timedelta(days=1)).isoformat()
    downloads = extract_download_urls(page_text, page_url)
    ranked_downloads = sorted(
        downloads,
        key=lambda value: (
            value.lower().split("?", 1)[0].endswith(".csv"),
            "lsoa" in urllib.parse.unquote(value).lower(),
            "crime" in urllib.parse.unquote(value).lower(),
            "download" in value.lower(),
        ),
        reverse=True,
    )
    selected = ranked_downloads[0] if ranked_downloads else None
    return {
        "resource_page": page_url,
        "title": title,
        "historical": historical,
        "period_end": period_end,
        "download_urls": ranked_downloads,
        "selected_url": selected,
        "pass": bool(title and not historical and selected and period_end),
    }


def discover_mps_lsoa_url_v2(
    dataset_text: str,
    *,
    base_url: str = MPS_DATASET_PAGE,
    fetcher: Callable[[str], tuple[bytes, dict[str, Any]]] | None = None,
    max_resource_pages: int = MAX_RESOURCE_PAGES,
) -> dict[str, Any]:
    base = load_base()
    direct = base.discover_mps_lsoa_url(dataset_text, base_url)
    safe_direct = [value for value in (direct.get("candidates") or []) if validate_public_https_url(value)["pass"]]
    if safe_direct:
        return {
            "pass": True,
            "method": "DIRECT_CSV_ON_OFFICIAL_DATASET_PAGE",
            "selected_url": safe_direct[0],
            "period_end": None,
            "direct_candidates": safe_direct,
            "resource_pages": [],
            "resource_results": [],
            "dataset_page": base_url,
            "selection_rule": "official dataset page direct CSV; public HTTPS; newest-ranked candidate",
        }
    resource_pages = extract_resource_page_urls(dataset_text, base_url)[:max_resource_pages]
    resource_results: list[dict[str, Any]] = []
    if fetcher:
        for index, resource_url in enumerate(resource_pages):
            try:
                body, http = fetcher(resource_url)
                parsed = parse_resource_page(resource_url, body.decode("utf-8", errors="replace"))
                parsed["resource_index"] = index
                parsed["http"] = http
                resource_results.append(parsed)
            except Exception as exc:
                resource_results.append({
                    "resource_page": resource_url,
                    "resource_index": index,
                    "pass": False,
                    "error": f"{type(exc).__name__}:{exc}",
                })
    passing = [item for item in resource_results if item.get("pass") and validate_public_https_url(item.get("selected_url"))["pass"]]
    ranked = sorted(
        passing,
        key=lambda item: (item.get("period_end") or "0000-00-00", -int(item.get("resource_index") or 0)),
        reverse=True,
    )
    selected = ranked[0] if ranked else None
    return {
        "pass": bool(selected),
        "method": "OFFICIAL_RESOURCE_PAGE_FALLBACK" if selected else None,
        "selected_url": selected.get("selected_url") if selected else None,
        "period_end": selected.get("period_end") if selected else None,
        "selected_resource_page": selected.get("resource_page") if selected else None,
        "direct_candidates": safe_direct,
        "resource_pages": resource_pages,
        "resource_results": resource_results,
        "dataset_page": base_url,
        "selection_rule": "non-historical MPS LSOA Level Crime resource with newest parsed period end; public HTTPS download",
    }


def parse_police_latest(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except Exception as exc:
        return {"pass": False, "date": None, "failure": f"JSON:{type(exc).__name__}:{exc}"}
    value = str(payload.get("date") or "")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except Exception as exc:
        return {"pass": False, "date": value or None, "failure": f"DATE:{type(exc).__name__}:{exc}"}
    return {"pass": parsed.isoformat() == value, "date": value, "failure": None}


def run(args: argparse.Namespace) -> dict[str, Any]:
    base = load_base()
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    cache = out / "official_source_cache"
    manifest_path = out / "security_public_safety_2_official_source_manifest_latest.json"
    result: dict[str, Any] = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "source_bootstrap_version": "2.0-provenance-guarded",
        "contract": {"slot": slot, "branch": branch, "pass": slot == SLOT_ID and branch == TARGET_BRANCH},
        "sources": {},
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    out.mkdir(parents=True, exist_ok=True)
    if not result["contract"]["pass"]:
        result.update({"pass": False, "blocker": f"WRONG_CONTRACT:slot={slot};branch={branch}"})
        manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    try:
        police_body, police_http = base.http_bytes(POLICE_LATEST_URL, args.timeout, max_bytes=1 << 20)
        police = parse_police_latest(police_body)
        police["http"] = police_http
        police["url_guard"] = validate_public_https_url(police_http.get("final_url") or POLICE_LATEST_URL)
        police["pass"] = bool(police.get("pass") and police_http.get("http_status") == 200 and police["url_guard"]["pass"])
    except Exception as exc:
        police = {"pass": False, "date": None, "error": f"{type(exc).__name__}:{exc}"}

    mps_url = args.mps_url or os.environ.get("AAYS_MPS_LSOA_URL")
    discovery: dict[str, Any] | None = None
    if mps_url:
        discovery = {
            "pass": validate_public_https_url(mps_url)["pass"],
            "method": "EXPLICIT_URL",
            "selected_url": mps_url,
            "period_end": None,
            "dataset_page": MPS_DATASET_PAGE,
        }
    elif not (args.mps_path or os.environ.get("AAYS_MPS_LSOA_CSV")):
        try:
            page_body, page_http = base.http_bytes(MPS_DATASET_PAGE, args.timeout, max_bytes=8 * 1024 * 1024)
            page_guard = validate_public_https_url(page_http.get("final_url") or MPS_DATASET_PAGE)
            if page_http.get("http_status") != 200 or not page_guard["pass"]:
                raise RuntimeError("MPS_DATASET_PAGE_HTTP_OR_URL_GUARD_FAILED")

            def resource_fetcher(url: str) -> tuple[bytes, dict[str, Any]]:
                guard = validate_public_https_url(url)
                if not guard["pass"]:
                    raise RuntimeError(f"RESOURCE_URL_REJECTED:{guard.get('failure')}")
                return base.http_bytes(url, args.timeout, max_bytes=8 * 1024 * 1024)

            discovery = discover_mps_lsoa_url_v2(
                page_body.decode("utf-8", errors="replace"),
                base_url=MPS_DATASET_PAGE,
                fetcher=resource_fetcher,
            )
            discovery["page_http"] = page_http
            discovery["page_url_guard"] = page_guard
            mps_url = discovery.get("selected_url")
        except Exception as exc:
            discovery = {"pass": False, "selected_url": None, "error": f"{type(exc).__name__}:{exc}", "dataset_page": MPS_DATASET_PAGE}

    iod = base.materialize_source(
        source="iod25_file7_v2",
        explicit_path=args.iod25_path or os.environ.get("AAYS_IOD25_V2_CSV"),
        explicit_url=args.iod25_url or os.environ.get("AAYS_IOD25_V2_URL"),
        default_url=base.IOD25_FILE7_V2_URL,
        output_path=cache / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators_v2.csv",
        timeout=args.timeout,
    )
    mps = base.materialize_source(
        source="mps_lsoa",
        explicit_path=args.mps_path or os.environ.get("AAYS_MPS_LSOA_CSV"),
        explicit_url=mps_url,
        default_url=None,
        output_path=cache / "MPS_LSOA_Level_Crime_latest.csv",
        timeout=args.timeout,
    )

    iod_final_url = ((iod.get("http") or {}).get("final_url") or iod.get("url") or base.IOD25_FILE7_V2_URL) if iod.get("method") == "download" else None
    mps_final_url = ((mps.get("http") or {}).get("final_url") or mps.get("url") or mps_url) if mps.get("method") == "download" else None
    provenance = {
        "police_latest": {"source_page": POLICE_LATEST_URL, "observed_date": police.get("date"), "pass": police.get("pass") is True},
        "iod25_file7_v2": {
            "source_page": base.IOD25_PAGE,
            "download_url": iod_final_url,
            "url_guard": validate_public_https_url(iod_final_url) if iod_final_url else {"pass": iod.get("method") in {"explicit_path", "cached_path"}, "failure": None},
            "sha256": ((iod.get("validation") or {}).get("sha256")),
            "pass": iod.get("pass") is True,
        },
        "mps_lsoa": {
            "source_page": MPS_DATASET_PAGE,
            "resource_page": (discovery or {}).get("selected_resource_page"),
            "discovery_method": (discovery or {}).get("method"),
            "period_end": (discovery or {}).get("period_end"),
            "download_url": mps_final_url,
            "url_guard": validate_public_https_url(mps_final_url) if mps_final_url else {"pass": mps.get("method") in {"explicit_path", "cached_path"}, "failure": None},
            "sha256": ((mps.get("validation") or {}).get("sha256")),
            "pass": mps.get("pass") is True,
        },
    }
    freshness_pass = bool(
        police.get("pass")
        and ((discovery or {}).get("period_end") is None or (discovery or {}).get("period_end") >= MIN_MPS_PERIOD_END)
    )
    provenance_pass = bool(
        provenance["police_latest"]["pass"]
        and provenance["iod25_file7_v2"]["pass"]
        and provenance["iod25_file7_v2"]["url_guard"].get("pass")
        and provenance["iod25_file7_v2"]["sha256"]
        and provenance["mps_lsoa"]["pass"]
        and provenance["mps_lsoa"]["url_guard"].get("pass")
        and provenance["mps_lsoa"]["sha256"]
        and freshness_pass
    )
    result["sources"] = {"police_latest": police, "iod25_file7_v2": iod, "mps_lsoa": mps}
    result["mps_discovery"] = discovery
    result["provenance"] = provenance
    result["freshness_gate"] = {"minimum_mps_period_end": MIN_MPS_PERIOD_END, "pass": freshness_pass}
    result["official_pages"] = {
        "police_latest": POLICE_LATEST_URL,
        "iod25": base.IOD25_PAGE,
        "iod25_file7_v2": base.IOD25_FILE7_V2_URL,
        "mps_dataset": MPS_DATASET_PAGE,
    }
    result["resolved_env"] = {
        "AAYS_IOD25_V2_CSV": iod.get("path") if iod.get("pass") else None,
        "AAYS_MPS_LSOA_CSV": mps.get("path") if mps.get("pass") else None,
    }
    result["pass"] = provenance_pass
    result["blocker"] = None if result["pass"] else "OFFICIAL_SOURCE_PROVENANCE_OR_FRESHNESS_INCOMPLETE"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--iod25-path")
    parser.add_argument("--iod25-url")
    parser.add_argument("--mps-path")
    parser.add_argument("--mps-url")
    parser.add_argument("--timeout", type=int, default=300)
    return parser.parse_args()


if __name__ == "__main__":
    payload = run(parse_args())
    print(json.dumps({
        "slot_id": SLOT_ID,
        "source_bootstrap_version": "2.0-provenance-guarded",
        "pass": payload.get("pass"),
        "blocker": payload.get("blocker"),
        "police_latest": ((payload.get("sources") or {}).get("police_latest") or {}).get("date"),
        "mps_period_end": ((payload.get("mps_discovery") or {}).get("period_end")),
        "actual_business_rows_written": 0,
        "final_ready": False,
    }))
    raise SystemExit(0 if payload.get("pass") else 2)
