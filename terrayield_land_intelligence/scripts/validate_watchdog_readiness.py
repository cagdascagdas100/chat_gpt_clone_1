from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "docs/chatgpt_handoff/local_runner_queue/AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1",
    "docs/cloud_ready/SAFE_RUNNER_TASK_PROTOCOL_20260518.md",
    "docs/cloud_ready/PERSISTENT_RUNNER_WATCHDOG_DESIGN_20260518.md",
    "docs/cloud_ready/WATCHDOG_RUNNER_USAGE_TR_20260518.md",
    "docs/cloud_ready/WATCHDOG_EVIDENCE_TEMPLATE_20260518.txt",
    "docs/cloud_ready/PERSISTENT_RUNNER_UPGRADE_PACKAGE_20260518.md",
    "docs/cloud_ready/AUTONOMY_ESCALATION_PLAN_20260518.md",
    "docs/cloud_ready/CURRENT_STATUS_20260517.md",
]

REQUIRED_SAFETY_MARKERS = [
    "db_write=none",
    "ddl=none",
    "migration_apply=none",
    "prod_deploy=none",
    "secret_values_printed=false",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8-sig")


def main() -> int:
    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    marker_failures: list[str] = []

    if not missing:
        watchdog = read("docs/chatgpt_handoff/local_runner_queue/AAYS_LOCAL_RUNNER_WATCHDOG_SAFE.ps1")
        for marker in REQUIRED_SAFETY_MARKERS:
            if marker not in watchdog:
                marker_failures.append(f"watchdog missing safety marker: {marker}")

        status = read("docs/cloud_ready/CURRENT_STATUS_20260517.md")
        if "CLOUD_READY_PENDING_PROVIDER" not in status:
            marker_failures.append("current status missing CLOUD_READY_PENDING_PROVIDER")
        if "WAIT_FOR_USER_PROVIDER_DECISION" not in status:
            marker_failures.append("current status missing WAIT_FOR_USER_PROVIDER_DECISION")

    payload = {
        "classification": "WATCHDOG_READY_FOR_MANUAL_ENABLEMENT" if not missing and not marker_failures else "WATCHDOG_READINESS_BLOCKED",
        "current_project_classification": "CLOUD_READY_PENDING_PROVIDER",
        "next_single_action": "WAIT_FOR_USER_PROVIDER_DECISION",
        "missing_files": missing,
        "marker_failures": marker_failures,
        "safety": {
            "db_write": "none",
            "ddl": "none",
            "migration_apply": "none",
            "prod_deploy": "none",
            "secret_values_printed": False,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["classification"] == "WATCHDOG_READY_FOR_MANUAL_ENABLEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
