from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
POLICE_URL = "https://data.police.uk/api/crime-last-updated"
IOD25_URL = "https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025"
MPS_URL = "https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/"
ALLOWED_HOSTS = {"data.police.uk", "www.gov.uk", "assets.publishing.service.gov.uk", "data.london.gov.uk"}
MAX_PAGE_BYTES = 10 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def validate_official_url(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        return False, "HTTPS_REQUIRED"
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        return False, f"HOST_NOT_ALLOWED:{host}"
    return True, "PASS"


def http_bytes(url: str, timeout: int, max_bytes: int = MAX_PAGE_BYTES) -> tuple[bytes, dict[str, Any]]:
    ok, detail = validate_official_url(url)
    if not ok:
        raise RuntimeError(detail)
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-security-public-safety-slot2-provenance/1.0", "Accept": "application/json,text/html,text/plain,*/*;q=0.5", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        final_ok, final_detail = validate_official_url(final_url)
        if not final_ok:
            raise RuntimeError(f"FINAL_URL_{final_detail}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"RESPONSE_TOO_LARGE:{total}>{max_bytes}")
            chunks.append(chunk)
        body = b"".join(chunks)
        return body, {"url": url, "final_url": final_url, "http_status": int(response.status), "content_type": response.headers.get("Content-Type"), "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"), "bytes": len(body), "sha256": sha256_bytes(body)}


def parse_police_latest(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except Exception as exc:
        return {"pass": False, "blocker": f"POLICE_JSON:{type(exc).__name__}:{exc}"}
    value = str(payload.get("date") or "")
    passed = bool(re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])-01", value))
    return {"pass": passed, "latest_date": value or None, "latest_month": value[:7] if passed else None, "blocker": None if passed else "POLICE_DATE_INVALID"}


def parse_iod25_page(text: str) -> dict[str, Any]:
    compact = re.sub(r"\s+", " ", text).lower()
    file7 = "file 7" in compact and "all ranks" in compact and "scores" in compact and "deciles" in compact
    corrected = "files 1 to 9" in compact and "corrected" in compact
    v2 = "updated ‘v2’" in compact or "updated 'v2'" in compact or "updated v2" in compact
    passed = file7 and corrected and v2
    return {"pass": passed, "file7_present": file7, "files_1_9_corrected": corrected, "v2_required": v2, "blocker": None if passed else "IOD25_PAGE_CONTRACT_INCOMPLETE"}


def parse_mps_page(text: str) -> dict[str, Any]:
    compact = re.sub(r"\s+", " ", text)
    lower = compact.lower()
    lsoa = "mps lsoa level crime.csv" in lower
    periods = re.findall(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) 20\d{2}\s*[–-]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) 20\d{2}", compact, flags=re.I)
    latest = periods[0] if periods else None
    connect = "connect system" in lower and "february 2024" in lower
    monthly = "monthly" in lower or len(periods) > 0
    passed = lsoa and bool(latest) and connect and monthly
    return {"pass": passed, "lsoa_file_present": lsoa, "latest_period": latest, "connect_caveat": connect, "monthly_evidence": monthly, "period_candidates": periods[:10], "blocker": None if passed else "MPS_PAGE_CONTRACT_INCOMPLETE"}


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    output = out / "security_public_safety_2_official_source_provenance_latest.json"
    result: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "generated_at": utc_now(), "provenance_version": "1.0", "contract": {"slot": slot, "branch": branch, "pass": slot == SLOT_ID and branch == TARGET_BRANCH}, "sources": {}, "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    if not result["contract"]["pass"]:
        result.update({"pass": False, "blocker": f"WRONG_CONTRACT:slot={slot};branch={branch}"})
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result
    for name, url, parser in (("police_latest", POLICE_URL, parse_police_latest), ("iod25_page", IOD25_URL, lambda body: parse_iod25_page(body.decode("utf-8", errors="replace"))), ("mps_page", MPS_URL, lambda body: parse_mps_page(body.decode("utf-8", errors="replace")))):
        try:
            body, http = http_bytes(url, args.timeout)
            parsed = parser(body)
            result["sources"][name] = {"pass": http["http_status"] == 200 and parsed.get("pass") is True, "http": http, "parsed": parsed}
        except Exception as exc:
            result["sources"][name] = {"pass": False, "error": f"{type(exc).__name__}:{exc}", "url": url}
    result["pass"] = all(source.get("pass") is True for source in result["sources"].values())
    result["blocker"] = None if result["pass"] else "OFFICIAL_SOURCE_PROVENANCE_INCOMPLETE"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


if __name__ == "__main__":
    payload = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "provenance_version": "1.0", "pass": payload.get("pass"), "blocker": payload.get("blocker"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(0 if payload.get("pass") else 3)
