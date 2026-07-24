#!/usr/bin/env python3
"""Revision-7 slot-local geometry shim for future_growth_1."""
from __future__ import annotations
import importlib.util, os, sys
from pathlib import Path

REPO=Path(os.environ.get('AAYS_REPO_ROOT','.')).resolve()
LEGACY=REPO/'docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v4.py'
LOCAL_HMLR=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/automation/012_prepare_hmlr_inspire_sources.py'

def main()->int:
    if not LEGACY.is_file() or not LOCAL_HMLR.is_file():
        print('missing revision-7 geometry dependency',file=sys.stderr); return 2
    spec=importlib.util.spec_from_file_location('future_growth_1_geometry_v4_runtime',LEGACY)
    if spec is None or spec.loader is None: return 2
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.HMLR_PREPARER=LOCAL_HMLR
    return int(module.main())
if __name__=='__main__': raise SystemExit(main())
