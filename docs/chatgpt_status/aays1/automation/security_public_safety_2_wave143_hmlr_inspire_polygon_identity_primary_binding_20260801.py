from __future__ import annotations

import hashlib
import os
import subprocess

SOURCE_COMMIT = "1f77cae7588561ec47f280db9a845d6666abf9d8"
SOURCE_PATH = (
    "docs/chatgpt_status/aays1/automation/"
    "security_public_safety_2_wave143_hmlr_inspire_polygon_identity_primary_binding_20260801.py"
)
SOURCE_BLOB_SHA1 = "80839cc10a367077046d6e67cd614140a9b11aaf"
EXPECTED_PREVIOUS_CONTINUATION = (
    "fe1d2a0b5bcf7a6f8c14e5f5f83f1226d221d19de1ae934e6fae33c6ebc7f7df"
)


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def load_immutable_source() -> bytes:
    subprocess.run(
        ["git", "fetch", "--no-tags", "--depth=1", "origin", SOURCE_COMMIT],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    source = result.stdout
    actual_blob_sha1 = git_blob_sha1(source)
    if actual_blob_sha1 != SOURCE_BLOB_SHA1:
        raise RuntimeError(
            f"IMMUTABLE_SOURCE_BLOB_MISMATCH:{actual_blob_sha1}:{SOURCE_BLOB_SHA1}"
        )
    return source


def main() -> None:
    source = load_immutable_source()
    source_ref = f"{SOURCE_COMMIT}:{SOURCE_PATH}"
    namespace: dict[str, object] = {
        "__name__": "security_public_safety_2_wave143_recovered",
        "__file__": source_ref,
    }
    exec(compile(source, source_ref, "exec"), namespace)
    namespace["PREVIOUS_CONTINUATION"] = EXPECTED_PREVIOUS_CONTINUATION
    recovered_main = namespace.get("main")
    if not callable(recovered_main):
        raise RuntimeError("WAVE143_MAIN_NOT_CALLABLE")
    recovered_main()


if __name__ == "__main__":
    if not os.environ.get("AAYS_SOURCE_HEAD"):
        raise RuntimeError("AAYS_SOURCE_HEAD_REQUIRED")
    main()
