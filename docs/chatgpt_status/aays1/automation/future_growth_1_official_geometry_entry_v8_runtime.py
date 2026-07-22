#!/usr/bin/env python3
"""Revision-8 runtime wrapper selecting the current queue/request v2 gates."""
from __future__ import annotations
import importlib.util, os
from pathlib import Path

REPO=Path(os.environ.get("AAYS_REPO_ROOT",".")).resolve()
CORE=REPO/"docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v8.py"
QUEUE_VALIDATOR=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/030_validate_revision8_queue_request_contract_v2.py"
QUEUE_SELFTEST=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/031_selftest_revision8_queue_request_contract_v2.py"

def main()->int:
    required=[CORE,QUEUE_VALIDATOR,QUEUE_SELFTEST]
    if any(not path.is_file() for path in required): return 2
    spec=importlib.util.spec_from_file_location("future_growth_1_entry_v8_core",CORE)
    if spec is None or spec.loader is None: return 2
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR
    module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST
    return int(module.main())
if __name__=="__main__": raise SystemExit(main())
