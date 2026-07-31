from __future__ import annotations

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Callable, NamedTuple, TypeVar

_T = TypeVar("_T")
_SHA256_RE = re.compile(r"[0-9a-fA-F]{64}\Z")
_DEFAULT_CHUNK = 1024 * 1024


class FileSnapshot(NamedTuple):
    device: int
    inode: int
    mode: int
    links: int
    size: int
    mtime_ns: int
    ctime_ns: int
    sha256: str


def normalise_sha256(value: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value.strip()) is None:
        raise RuntimeError("XML_EXPECTED_SHA256_INVALID")
    return value.strip().lower()


def _metadata(result: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        int(result.st_dev),
        int(result.st_ino),
        int(result.st_mode),
        int(result.st_nlink),
        int(result.st_size),
        int(result.st_mtime_ns),
        int(result.st_ctime_ns),
    )


def _validate_regular(result: os.stat_result) -> None:
    if not stat.S_ISREG(result.st_mode):
        raise RuntimeError("XML_SOURCE_NOT_REGULAR_FILE")
    if result.st_size <= 0:
        raise RuntimeError("XML_SOURCE_EMPTY")
    if result.st_nlink != 1:
        raise RuntimeError(f"XML_SOURCE_LINK_COUNT_NOT_ONE:{result.st_nlink}")


def capture(path: Path, *, chunk_size: int = _DEFAULT_CHUNK) -> FileSnapshot:
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    source = Path(path)
    try:
        path_before = os.lstat(source)
    except OSError as exc:
        raise RuntimeError(f"XML_SOURCE_LSTAT_FAILED:{source}") from exc
    if stat.S_ISLNK(path_before.st_mode):
        raise RuntimeError("XML_SOURCE_SYMLINK_FORBIDDEN")
    _validate_regular(path_before)

    digest = hashlib.sha256()
    try:
        with source.open("rb", buffering=0) as handle:
            fd_before = os.fstat(handle.fileno())
            _validate_regular(fd_before)
            if _metadata(fd_before) != _metadata(path_before):
                raise RuntimeError("XML_SOURCE_PATH_DESCRIPTOR_MISMATCH_BEFORE_HASH")
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
            fd_after = os.fstat(handle.fileno())
    except RuntimeError:
        raise
    except OSError as exc:
        raise RuntimeError(f"XML_SOURCE_READ_FAILED:{source}") from exc

    try:
        path_after = os.lstat(source)
    except OSError as exc:
        raise RuntimeError(f"XML_SOURCE_LSTAT_AFTER_HASH_FAILED:{source}") from exc
    if _metadata(fd_before) != _metadata(fd_after):
        raise RuntimeError("XML_SOURCE_DESCRIPTOR_CHANGED_DURING_HASH")
    if _metadata(fd_after) != _metadata(path_after):
        raise RuntimeError("XML_SOURCE_PATH_REPLACED_DURING_HASH")

    return FileSnapshot(*_metadata(path_after), digest.hexdigest())


def _assert_same(before: FileSnapshot, after: FileSnapshot, stage: str) -> None:
    if before[:7] != after[:7]:
        raise RuntimeError(f"XML_SOURCE_METADATA_CHANGED:{stage}")
    if before.sha256 != after.sha256:
        raise RuntimeError(f"XML_SOURCE_SHA256_CHANGED:{stage}")


def guarded_call(
    path: Path,
    *,
    expected_sha256: str,
    operation: Callable[[], _T],
    chunk_size: int = _DEFAULT_CHUNK,
) -> tuple[_T, dict]:
    expected = normalise_sha256(expected_sha256)
    before = capture(path, chunk_size=chunk_size)
    if before.sha256 != expected:
        raise RuntimeError(f"XML_SOURCE_SHA256_MISMATCH:{before.sha256}:{expected}")
    try:
        result = operation()
    except Exception as exc:
        try:
            after_error = capture(path, chunk_size=chunk_size)
            _assert_same(before, after_error, "operation_error")
        except Exception as stability_exc:
            raise stability_exc from exc
        raise
    after = capture(path, chunk_size=chunk_size)
    _assert_same(before, after, "operation_complete")
    return result, {
        "xml_source_stability_validation_passed": True,
        "xml_source_expected_sha256": expected,
        "xml_source_observed_sha256": before.sha256,
        "xml_source_regular_file": True,
        "xml_source_symlink_forbidden": True,
        "xml_source_single_link_required": True,
        "xml_source_metadata_stable": True,
        "xml_source_digest_stable": True,
        "xml_source_size_bytes": before.size,
        "xml_source_device": before.device,
        "xml_source_inode": before.inode,
    }
