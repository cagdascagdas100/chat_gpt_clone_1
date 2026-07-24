#!/usr/bin/env python3
"""Bounded-bootstrap target for the revision-8 future_growth_1 core entry."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
CORE = REPO / "docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v8.py"
QUEUE_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/030_validate_revision8_queue_request_contract_v2.py"
QUEUE_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/031_selftest_revision8_queue_request_contract_v2.py"


def main() -> int:
    missing = [str(path) for path in (CORE, QUEUE_VALIDATOR, QUEUE_SELFTEST) if not path.is_file()]
    if missing:
        print({"result": "BLOCKED", "status": "BOOTSTRAP_REQUIRED_FILE_MISSING", "missing": missing})
        return 2
    spec = importlib.util.spec_from_file_location("future_growth_1_entry_v8_core", CORE)
    if spec is None or spec.loader is None:
        print({"result": "BLOCKED", "status": "BOOTSTRAP_CORE_IMPORT_SPEC"})
        return 2
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.QUEUE_REQUEST_VALIDATOR = QUEUE_VALIDATOR
    module.QUEUE_REQUEST_SELFTEST = QUEUE_SELFTEST
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
