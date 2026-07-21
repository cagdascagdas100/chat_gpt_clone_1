from __future__ import annotations

import base64
import gzip
from pathlib import Path


def main() -> None:
    payload = Path(__file__).with_name(
        "006_official_direct_tile_fallback_payload_20260721.b64"
    )
    source = gzip.decompress(base64.b64decode(payload.read_text(encoding="utf-8").strip())).decode("utf-8")
    decoded_path = payload.with_suffix(".decoded.py")
    code = compile(source, str(decoded_path), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(decoded_path)})


if __name__ == "__main__":
    main()
