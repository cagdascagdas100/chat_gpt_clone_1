from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def fetch(url: str, timeout: int = 15) -> dict[str, object]:
    start = time.perf_counter()
    try:
        req = Request(url, headers={"User-Agent": "TerraYieldCloudSmoke/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "url": url,
                "status": "ok",
                "status_code": resp.status,
                "elapsed_ms": elapsed_ms,
            }
    except HTTPError as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "url": url,
            "status": "http_error",
            "status_code": exc.code,
            "elapsed_ms": elapsed_ms,
        }
    except URLError:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "url": url,
            "status": "connection_error",
            "status_code": None,
            "elapsed_ms": elapsed_ms,
        }


def main() -> int:
    base_url = os.environ.get("TERRAYIELD_PUBLIC_API_URL", "").strip().rstrip("/")
    if not base_url:
        print(json.dumps({"status": "blocked", "reason": "TERRAYIELD_PUBLIC_API_URL missing"}))
        return 2

    endpoints = [
        "/",
        "/ops/storage-registry",
        "/ops/consistency-check",
        "/handoff/status",
        "/map/listings?limit=1",
        "/map/sales-history/combined?limit=1",
    ]
    ok = 0
    results = []
    for endpoint in endpoints:
        result = fetch(base_url + endpoint)
        results.append(result)
        if result["status"] == "ok" and int(result["status_code"] or 0) < 500:
            ok += 1

    payload = {
        "base_url": base_url,
        "ok_count": ok,
        "total": len(endpoints),
        "classification": "CLOUD_RUNTIME_READY" if ok == len(endpoints) else "CLOUD_RUNTIME_BLOCKED",
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok == len(endpoints) else 1


if __name__ == "__main__":
    raise SystemExit(main())
