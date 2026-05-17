from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "Dockerfile.cloud",
    "render.example.yaml",
    ".env.cloud.example",
    "scripts/cloud_smoke_check.py",
    "docs/cloud_ready/STATUS.md",
    "docs/cloud_ready/PROVIDER_CHECKLIST_TR.md",
    "docs/cloud_ready/HOSTED_SMOKE_USAGE_TR.md",
    "docs/cloud_ready/FINAL_CLOUD_READY_CLOSURE_TR.md",
    "docs/cloud_ready/STATIC_CLOUD_READINESS_VALIDATION_20260517.md",
    "docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt",
    "docs/chatgpt_handoff/cloud_ready_20260517/BLOCKERS.md",
    "docs/chatgpt_handoff/cloud_ready_20260517/LOCATION_EVIDENCE_SAMPLE.jsonl",
    "docs/chatgpt_handoff/cloud_ready_20260517/PERF_SUMMARY.txt",
    "docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt",
]

REQUIRED_EXECUTION_REPORT_MARKERS = [
    "final_classification=CLOUD_READY_PENDING_PROVIDER",
    "next_single_action=ADD_PROVIDER_PUBLIC_URL_AND_CLOUD_DB_SETTINGS_OUTSIDE_REPO",
    "public_hosted_url_verified=false",
    "cloud_db_provider_verified=false",
    "secret_values_printed=false",
    "db_write=none",
    "ddl=none",
    "migration_apply=none",
    "prod_deploy=none",
]

REQUIRED_SAFETY_MARKERS = [
    "db_write=none",
    "ddl=none",
    "migration_apply=none",
    "prod_deploy=none",
    "secret_values_printed=false",
]


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def main() -> int:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    marker_failures: list[str] = []

    if not missing:
        execution_report = read_text("docs/chatgpt_handoff/cloud_ready_20260517/EXECUTION_REPORT.txt")
        for marker in REQUIRED_EXECUTION_REPORT_MARKERS:
            if marker not in execution_report:
                marker_failures.append(f"EXECUTION_REPORT missing marker: {marker}")

        safety_summary = read_text("docs/chatgpt_handoff/cloud_ready_20260517/SAFETY_SUMMARY.txt")
        for marker in REQUIRED_SAFETY_MARKERS:
            if marker not in safety_summary:
                marker_failures.append(f"SAFETY_SUMMARY missing marker: {marker}")

    payload = {
        "classification": "STATIC_CLOUD_READINESS_VALID" if not missing and not marker_failures else "STATIC_CLOUD_READINESS_BLOCKED",
        "expected_runtime_classification": "CLOUD_READY_PENDING_PROVIDER",
        "public_hosted_url_verified": False,
        "cloud_db_provider_verified": False,
        "missing_files": missing,
        "marker_failures": marker_failures,
        "next_single_action": "ADD_PROVIDER_PUBLIC_URL_AND_CLOUD_DB_SETTINGS_OUTSIDE_REPO",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["classification"] == "STATIC_CLOUD_READINESS_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
