# -*- coding: utf-8 -*-
"""Canonical coordinator wrapper with active-branch publish readback hardening.

The original coordinator implementation is retained verbatim in
``AAYS_ADAPTIVE_15_WORKER_COORDINATOR_ORIGINAL.py``.  This wrapper loads the
narrow compatibility hook and then executes that original implementation as
``__main__``.  No scheduling, resource, safety, slot or task semantics are
changed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
HOOK = HERE / "sitecustomize.py"
ORIGINAL = HERE / "AAYS_ADAPTIVE_15_WORKER_COORDINATOR_ORIGINAL.py"

if not HOOK.is_file():
    raise RuntimeError(f"COORDINATOR_COMPAT_HOOK_MISSING: {HOOK}")
if not ORIGINAL.is_file():
    raise RuntimeError(f"COORDINATOR_ORIGINAL_MISSING: {ORIGINAL}")

spec = importlib.util.spec_from_file_location("aays_coordinator_sitecustomize", HOOK)
if spec is None or spec.loader is None:
    raise RuntimeError("COORDINATOR_COMPAT_HOOK_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

runpy.run_path(str(ORIGINAL), run_name="__main__")
