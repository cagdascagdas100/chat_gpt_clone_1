#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import os
from pathlib import Path

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
PAYLOAD = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/008_height_difference_1_official_api_evidence_reconciled_20260721.py.gz.b64"


def main() -> None:
    encoded = PAYLOAD.read_text(encoding="utf-8").strip()
    source = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    code = compile(source, str(PAYLOAD.with_suffix("")), "exec")
    scope = {"__name__": "__main__", "__file__": str(PAYLOAD.with_suffix(""))}
    exec(code, scope, scope)


if __name__ == "__main__":
    main()
