from __future__ import annotations

import json
import os
import time
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


PRIVATE_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def fetch(url: str, timeout: int = 15) -> dict[str, object]:
    start = time.perf_counter()
    try:
        req = Request(url, headers={"User-Agent": "TerraYieldCloudSmoke/1.1"})
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


def env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "y"}


def public_https_ok(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and bool(host) and host not in PRIVATE_HOSTS


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

    public_url_verified = public_https_ok(base_url)
    cloud_db_verified = env_true("TERRAYIELD_CLOUD_DB_VERIFIED")
    frontend_url = os.environ.get("TERRAYIELD_FRONTEND_PUBLIC_URL", "").strip().rstrip("/")
    frontend_public_url_verified = public_https_ok(frontend_url) if frontend_url else False
    hosted_smoke_passed = ok == len(endpoints)

    blockers = []
    if not public_url_verified:
        blockers.append("public_backend_https_url_not_verified")
    if not cloud_db_verified:
        blockers.append("cloud_db_postgis_not_verified")
    if not hosted_smoke_passed:
        blockers.append("hosted_smoke_not_6_of_6")
    if not frontend_public_url_verified:
        blockers.append("frontend_public_url_not_verified")

    classification = "CLOUD_RUNTIME_READY" if not blockers else "CLOUD_READY_PENDING_PROVIDER"
    next_single_action = "RECORD_HOSTED_RUNTIME_PROOF" if not blockers else "RESOLVE_HOSTED_RUNTIME_BLOCKERS"

    payload = {
        "base_url": base_url,
        "public_url_verified": public_url_verified,
        "cloud_db_verified": cloud_db_verified,
        "frontend_public_url_verified": frontend_public_url_verified,
        "hosted_smoke_status": "passed" if hosted_smoke_passed else "failed",
        "ok_count": ok,
        "total": len(endpoints),
        "classification": classification,
        "next_single_action": next_single_action,
        "blockers": blockers or ["none"],
        "secret_values_printed": False,
        "db_write": "none",
        "ddl": "none",
        "migration_apply": "none",
        "prod_deploy": "none",
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
