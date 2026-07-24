#!/usr/bin/env python3
from __future__ import annotations
import base64, gzip, os, runpy, tempfile
from pathlib import Path

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
PAYLOAD = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/041_height_difference_1_revision_14_direct_hmlr_monthly_gml_refresh_20260721.py.gz.b64"
if not PAYLOAD.exists():
    raise SystemExit(f"revision_14_payload_missing:{PAYLOAD}")
raw = gzip.decompress(base64.b64decode(PAYLOAD.read_text(encoding="ascii")))
with tempfile.TemporaryDirectory(prefix="aays_hd1_rev14_entry_") as td:
    script = Path(td) / "revision_14.py"
    script.write_bytes(raw)
    runpy.run_path(str(script), run_name="__main__")
