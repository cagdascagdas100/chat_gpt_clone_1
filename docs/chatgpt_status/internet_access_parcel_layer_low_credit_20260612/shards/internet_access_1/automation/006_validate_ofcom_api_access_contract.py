#!/usr/bin/env python3
"""Validate the official Ofcom API subscription contract fail-closed.

This tool does not sign in, request a key, call the API, or write business rows.
It validates an evidence manifest captured from the official Ofcom developer portal.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

EXPECTED = {
    "api_name": "Ofcom Connected Nations Broadband API",
    "signup_required": True,
    "api_key_required": True,
    "basic_calls_per_minute": 100,
    "basic_monthly_requests": 50000,
    "premium_calls_per_minute": 500,
    "premium_monthly_requests": 150000,
    "guardrail_decision": "REJECT_LOGIN_OR_SUBSCRIPTION_KEY_REQUIRED",
}


def validate(payload: dict) -> list[dict]:
    checks = []
    for key, expected in EXPECTED.items():
        actual = payload.get(key)
        checks.append({"name": key, "expected": expected, "actual": actual, "pass": actual == expected})
    checks.append({
        "name": "no_business_write",
        "expected": True,
        "actual": payload.get("business_rows_written") == 0 and payload.get("api_calls_executed") == 0,
        "pass": payload.get("business_rows_written") == 0 and payload.get("api_calls_executed") == 0,
    })
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.contract.read_text(encoding="utf-8"))
    checks = validate(payload)
    result = {
        "schema_version": 1,
        "slot_id": "internet_access_1",
        "status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
        "checks_passed": sum(c["pass"] for c in checks),
        "checks_failed": sum(not c["pass"] for c in checks),
        "checks": checks,
        "api_calls_executed": 0,
        "business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "checks_passed", "checks_failed")}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED_FAIL_CLOSED","error":f"{type(exc).__name__}: {exc}","final_ready":False}), file=sys.stderr)
        raise
