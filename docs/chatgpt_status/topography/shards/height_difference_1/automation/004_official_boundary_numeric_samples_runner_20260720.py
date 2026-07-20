from __future__ import annotations

import base64
import gzip
from pathlib import Path


def main() -> None:
    payload = Path(__file__).with_name(
        "004_official_boundary_numeric_samples_payload_20260720.b64"
    )
    encoded = payload.read_text(encoding="utf-8").strip()
    source = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")
    decoded_path = payload.with_suffix(".decoded.py")
    code = compile(source, str(decoded_path), "exec")
    exec(code, {"__name__": "__main__", "__file__": str(decoded_path)})


if __name__ == "__main__":
    main()
