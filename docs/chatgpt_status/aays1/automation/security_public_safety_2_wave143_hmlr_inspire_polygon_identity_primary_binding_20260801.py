from __future__ import annotations

import hashlib
import os

import requests

SOURCE_COMMIT = "1f77cae7588561ec47f280db9a845d6666abf9d8"
SOURCE_BLOB_SHA1 = "80839cc10a367077046d6e67cd614140a9b11aaf"
SOURCE_URL = (
    "https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/"
    f"{SOURCE_COMMIT}/docs/chatgpt_status/aays1/automation/"
    "security_public_safety_2_wave143_hmlr_inspire_polygon_identity_primary_binding_20260801.py"
)
EXPECTED_PREVIOUS_CONTINUATION = (
    "fe1d2a0b5bcf7a6f8c14e5f5f83f1226d221d19de1ae934e6fae33c6ebc7f7df"
)


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def main() -> None:
    response = requests.get(
        SOURCE_URL,
        headers={"User-Agent": "AAYS-Wave143-Recovery/1.0"},
        timeout=(15, 90),
    )
    response.raise_for_status()
    source = response.content
    actual_blob_sha1 = git_blob_sha1(source)
    if actual_blob_sha1 != SOURCE_BLOB_SHA1:
        raise RuntimeError(
            f"IMMUTABLE_SOURCE_BLOB_MISMATCH:{actual_blob_sha1}:{SOURCE_BLOB_SHA1}"
        )

    namespace: dict[str, object] = {
        "__name__": "security_public_safety_2_wave143_recovered",
        "__file__": SOURCE_URL,
    }
    exec(compile(source, SOURCE_URL, "exec"), namespace)
    namespace["PREVIOUS_CONTINUATION"] = EXPECTED_PREVIOUS_CONTINUATION
    recovered_main = namespace.get("main")
    if not callable(recovered_main):
        raise RuntimeError("WAVE143_MAIN_NOT_CALLABLE")
    recovered_main()


if __name__ == "__main__":
    required = os.environ.get("AAYS_SOURCE_HEAD")
    if not required:
        raise RuntimeError("AAYS_SOURCE_HEAD_REQUIRED")
    main()
