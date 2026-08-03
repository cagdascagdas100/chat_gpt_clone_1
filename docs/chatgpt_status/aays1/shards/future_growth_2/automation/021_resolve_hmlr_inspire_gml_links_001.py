#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SLOT = "future_growth_2"
WORKSTREAM = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
DEFAULT_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
TARGETS = (
    {"row_no": 30762, "lpa": "Enfield", "authority": "London Borough of Enfield"},
    {"row_no": 46142, "lpa": "Havering", "authority": "London Borough of Havering"},
    {"row_no": 61522, "lpa": "Lambeth", "authority": "London Borough of Lambeth"},
)
MAX_PAGE_BYTES = 5_000_000
PROBE_BYTES = 4096


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def validate_page_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != OFFICIAL_HOST:
        raise ValueError("download page must be the official HMLR HTTPS host")


def fetch_page(url: str, timeout: int) -> tuple[int, str, bytes, dict[str, str]]:
    validate_page_url(url)
    request = urllib.request.Request(
        url,
        headers={"Accept": "text/html,application/xhtml+xml", "User-Agent": "TerraYield-AAYS/1.0 future_growth_2"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(response.status)
        body = response.read(MAX_PAGE_BYTES + 1)
        final_url = response.geturl()
        headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    if len(body) > MAX_PAGE_BYTES:
        raise ValueError("download page exceeds bounded size")
    return status, final_url, body, headers


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value)


def extract_links(page_body: bytes, base_url: str) -> dict[int, str | None]:
    text = html.unescape(page_body.decode("utf-8", errors="replace"))
    results: dict[int, str | None] = {}
    for target in TARGETS:
        authority = target["authority"]
        match = re.search(re.escape(authority), text, flags=re.IGNORECASE)
        link: str | None = None
        if match:
            window = text[match.start(): match.start() + 2500]
            for href, label in re.findall(
                r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
                window,
                flags=re.IGNORECASE | re.DOTALL,
            ):
                label_text = " ".join(strip_tags(label).split()).lower()
                if "gml" in label_text or ".gml" in href.lower():
                    link = urllib.parse.urljoin(base_url, href)
                    break
        results[int(target["row_no"])] = link
    return results


def probe_link(url: str, timeout: int) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("GML link must use HTTPS")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/gml+xml,application/xml,text/xml,*/*",
            "Range": f"bytes=0-{PROBE_BYTES - 1}",
            "User-Agent": "TerraYield-AAYS/1.0 future_growth_2",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(response.status)
        prefix = response.read(PROBE_BYTES)
        final_url = response.geturl()
        headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    return {
        "http_status": status,
        "final_url": final_url,
        "content_type": headers.get("content-type"),
        "content_length_header": headers.get("content-length"),
        "content_range_header": headers.get("content-range"),
        "byte_count_hashed": len(prefix),
        "content_sha256": hashlib.sha256(prefix).hexdigest() if prefix else None,
        "hash_scope": f"bounded_first_{PROBE_BYTES}_bytes",
    }


def run(
    page_url: str,
    continuation_key: str,
    timeout: int,
    fetch_fn: Callable[[str, int], tuple[int, str, bytes, dict[str, str]]] = fetch_page,
    probe_fn: Callable[[str, int], dict[str, Any]] = probe_link,
) -> dict[str, Any]:
    if len(continuation_key) != 64 or any(ch not in "0123456789abcdef" for ch in continuation_key):
        raise ValueError("continuation key must be lowercase SHA-256")
    validate_page_url(page_url)
    fetched_at = utc_now()
    status, final_page_url, body, page_headers = fetch_fn(page_url, timeout)
    page_sha256 = hashlib.sha256(body).hexdigest()
    links = extract_links(body, final_page_url)

    records: list[dict[str, Any]] = []
    verified = 0
    for target in TARGETS:
        row_no = int(target["row_no"])
        link = links.get(row_no)
        base = {
            **target,
            "download_page_url": page_url,
            "download_page_final_url": final_page_url,
            "download_page_http_status": status,
            "download_page_byte_count": len(body),
            "download_page_sha256": page_sha256,
            "download_page_content_type": page_headers.get("content-type"),
            "fetched_at_utc": fetched_at,
            "gml_url": link,
            "discovered_from_official_page": True,
            "raw_body_copied": False,
            "geometry_copied": False,
            "membership_inferred": False,
            "score_written": False,
            "fake_data": False,
        }
        if not link:
            records.append({**base, "data_status": "SOURCE_LINK_NOT_FOUND", "error": "No GML link found near official local-authority label"})
            continue
        try:
            probe = probe_fn(link, timeout)
            ok = probe.get("http_status") in {200, 206} and int(probe.get("byte_count_hashed") or 0) > 0 and bool(probe.get("content_sha256"))
            verified += int(ok)
            records.append({
                **base,
                **probe,
                "data_status": "VERIFIED_OFFICIAL_GML_LINK" if ok else "SOURCE_READ_FAILED",
                "error": None if ok else "Probe did not return a bounded non-empty response",
            })
        except Exception as exc:
            records.append({
                **base,
                "http_status": None,
                "final_url": None,
                "content_type": None,
                "content_length_header": None,
                "content_range_header": None,
                "byte_count_hashed": 0,
                "content_sha256": None,
                "hash_scope": f"bounded_first_{PROBE_BYTES}_bytes",
                "data_status": "SOURCE_READ_FAILED",
                "error": f"{type(exc).__name__}:{str(exc)[:500]}",
            })

    state = "PUBLISHED" if verified == len(TARGETS) else "NO_DATA_CONTINUE"
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "task_continuation_key": continuation_key,
        "state": state,
        "panel_status": "PUBLISHED" if state == "PUBLISHED" else "BİLGİ TOPLANIYOR",
        "generated_at": utc_now(),
        "completed_count": len(records),
        "target_count": len(TARGETS),
        "progress_percent": round(len(records) / len(TARGETS) * 100.0, 6),
        "verified_link_count": verified,
        "failed_link_count": len(TARGETS) - verified,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "records": records,
        "large_raw_files_written": False,
        "raw_bodies_copied": False,
        "geometry_copied": False,
        "membership_inferred": False,
        "scores_written": False,
        "fake_data": False,
    }


def fixture_fetch(url: str, timeout: int) -> tuple[int, str, bytes, dict[str, str]]:
    del timeout
    fixture = """
    <html><body><table>
      <tr><td>London Borough of Enfield</td><td><a href='/files/enfield.gml'>Download .gml</a></td></tr>
      <tr><td>London Borough of Havering</td><td><a href='/files/havering.gml'>Download .gml</a></td></tr>
      <tr><td>London Borough of Lambeth</td><td><a href='/files/lambeth.gml'>Download .gml</a></td></tr>
    </table></body></html>
    """.encode("utf-8")
    return 200, url, fixture, {"content-type": "text/html; charset=utf-8"}


def fixture_probe(url: str, timeout: int) -> dict[str, Any]:
    del timeout
    payload = ("<gml:FeatureCollection source='" + url + "'/>").encode("utf-8")
    return {
        "http_status": 206,
        "final_url": url,
        "content_type": "application/gml+xml",
        "content_length_header": str(len(payload)),
        "content_range_header": f"bytes 0-{len(payload)-1}/{len(payload)}",
        "byte_count_hashed": len(payload),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "hash_scope": f"bounded_first_{PROBE_BYTES}_bytes",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-page-url", default=DEFAULT_PAGE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task-continuation-key", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not 5 <= args.timeout_seconds <= 120:
        raise ValueError("timeout must be 5..120 seconds")
    result = run(
        args.download_page_url,
        args.task_continuation_key,
        args.timeout_seconds,
        fixture_fetch if args.self_test else fetch_page,
        fixture_probe if args.self_test else probe_link,
    )
    atomic_write(args.output, result)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "verified_link_count": result["verified_link_count"],
        "failed_link_count": result["failed_link_count"],
        "output": str(args.output),
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
