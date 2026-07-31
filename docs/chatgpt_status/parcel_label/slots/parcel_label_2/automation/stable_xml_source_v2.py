from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path
from typing import Callable, NamedTuple, TypeVar

_T = TypeVar("_T")
_DEFAULT_CHUNK = 1024 * 1024


class DescriptorEvidence(NamedTuple):
    source_device: int
    source_inode: int
    source_size: int
    source_sha256: str
    parser_source_mode: str


def _regular_single_link(result: os.stat_result, *, prefix: str) -> None:
    if not stat.S_ISREG(result.st_mode):
        raise RuntimeError(f"{prefix}_NOT_REGULAR_FILE")
    if result.st_size <= 0:
        raise RuntimeError(f"{prefix}_EMPTY")
    if result.st_nlink != 1:
        raise RuntimeError(f"{prefix}_LINK_COUNT_NOT_ONE:{result.st_nlink}")


def _open_source(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"XML_SOURCE_DESCRIPTOR_OPEN_FAILED:{path}") from exc
    try:
        info = os.fstat(descriptor)
        _regular_single_link(info, prefix="XML_SOURCE")
        if not hasattr(os, "O_NOFOLLOW"):
            try:
                link_info = os.lstat(path)
            except OSError as exc:
                raise RuntimeError(f"XML_SOURCE_LSTAT_FAILED:{path}") from exc
            if stat.S_ISLNK(link_info.st_mode):
                raise RuntimeError("XML_SOURCE_SYMLINK_FORBIDDEN")
            if (link_info.st_dev, link_info.st_ino) != (info.st_dev, info.st_ino):
                raise RuntimeError("XML_SOURCE_PATH_DESCRIPTOR_MISMATCH")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _hash_descriptor(descriptor: int, *, chunk_size: int) -> str:
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while True:
        chunk = os.read(descriptor, chunk_size)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(descriptor, 0, os.SEEK_SET)
    return digest.hexdigest()


def _hash_path(path: Path, *, chunk_size: int) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb", buffering=0) as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _normalise_expected(value: str) -> str:
    candidate = str(value).strip().lower()
    if len(candidate) != 64 or any(char not in "0123456789abcdef" for char in candidate):
        raise RuntimeError("XML_EXPECTED_SHA256_INVALID")
    return candidate


def _proc_descriptor_path(descriptor: int) -> Path | None:
    candidate = Path(f"/proc/self/fd/{descriptor}")
    if not candidate.exists():
        return None
    try:
        target = os.stat(candidate)
        source = os.fstat(descriptor)
    except OSError:
        return None
    if (target.st_dev, target.st_ino, target.st_size) != (source.st_dev, source.st_ino, source.st_size):
        return None
    return candidate


def _copy_descriptor_to_private_path(descriptor: int, *, chunk_size: int):
    directory = tempfile.TemporaryDirectory(prefix="parcel-label-2-xml-")
    root = Path(directory.name)
    try:
        os.chmod(root, 0o700)
        target = root / "source.gml"
        out_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600)
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            while True:
                chunk = os.read(descriptor, chunk_size)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    written = os.write(out_fd, view)
                    if written <= 0:
                        raise RuntimeError("XML_PRIVATE_COPY_WRITE_ZERO")
                    view = view[written:]
            os.fsync(out_fd)
        finally:
            os.close(out_fd)
            os.lseek(descriptor, 0, os.SEEK_SET)
        copied = os.stat(target, follow_symlinks=False)
        _regular_single_link(copied, prefix="XML_PRIVATE_COPY")
        os.chmod(target, 0o400)
        return directory, target
    except Exception:
        directory.cleanup()
        raise


def guarded_descriptor_call(
    path: Path,
    *,
    expected_sha256: str,
    operation: Callable[[Path], _T],
    chunk_size: int = _DEFAULT_CHUNK,
    force_private_copy: bool = False,
) -> tuple[_T, dict]:
    expected = _normalise_expected(expected_sha256)
    source_path = Path(path)
    descriptor = _open_source(source_path)
    private_directory = None
    try:
        before = os.fstat(descriptor)
        before_digest = _hash_descriptor(descriptor, chunk_size=chunk_size)
        if before_digest != expected:
            raise RuntimeError(f"XML_SOURCE_SHA256_MISMATCH:{before_digest}:{expected}")

        stable_path = None if force_private_copy else _proc_descriptor_path(descriptor)
        private_before = None
        if stable_path is None:
            private_directory, stable_path = _copy_descriptor_to_private_path(descriptor, chunk_size=chunk_size)
            mode = "PRIVATE_SECURE_COPY"
            private_before = os.stat(stable_path, follow_symlinks=False)
            copied_digest = _hash_path(stable_path, chunk_size=chunk_size)
            if copied_digest != expected:
                raise RuntimeError(f"XML_PRIVATE_COPY_SHA256_MISMATCH:{copied_digest}:{expected}")
        else:
            mode = "PROC_DESCRIPTOR_PATH"

        result = operation(stable_path)

        if private_before is not None:
            private_after = os.stat(stable_path, follow_symlinks=False)
            if (
                private_before.st_dev, private_before.st_ino, private_before.st_mode,
                private_before.st_nlink, private_before.st_size, private_before.st_mtime_ns, private_before.st_ctime_ns,
            ) != (
                private_after.st_dev, private_after.st_ino, private_after.st_mode,
                private_after.st_nlink, private_after.st_size, private_after.st_mtime_ns, private_after.st_ctime_ns,
            ):
                raise RuntimeError("XML_PRIVATE_COPY_METADATA_CHANGED_DURING_PARSE")
            private_after_digest = _hash_path(stable_path, chunk_size=chunk_size)
            if private_after_digest != expected:
                raise RuntimeError("XML_PRIVATE_COPY_SHA256_CHANGED_DURING_PARSE")

        after = os.fstat(descriptor)
        after_digest = _hash_descriptor(descriptor, chunk_size=chunk_size)
        if (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_nlink,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise RuntimeError("XML_SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE")
        if after_digest != before_digest:
            raise RuntimeError("XML_SOURCE_DESCRIPTOR_SHA256_CHANGED_DURING_PARSE")

        try:
            path_after = os.lstat(source_path)
        except OSError as exc:
            raise RuntimeError("XML_SOURCE_PATH_MISSING_AFTER_PARSE") from exc
        if stat.S_ISLNK(path_after.st_mode):
            raise RuntimeError("XML_SOURCE_PATH_SYMLINK_AFTER_PARSE")
        if (path_after.st_dev, path_after.st_ino) != (before.st_dev, before.st_ino):
            raise RuntimeError("XML_SOURCE_PATH_REPLACED_DURING_PARSE")

        return result, {
            "xml_descriptor_pinning_validation_passed": True,
            "xml_parser_source_mode": mode,
            "xml_parser_source_bound_to_open_descriptor": True,
            "xml_parser_source_path_reopen_forbidden": True,
            "xml_source_expected_sha256": expected,
            "xml_source_observed_sha256": before_digest,
            "xml_source_device": int(before.st_dev),
            "xml_source_inode": int(before.st_ino),
            "xml_source_size_bytes": int(before.st_size),
        }
    finally:
        if private_directory is not None:
            private_directory.cleanup()
        os.close(descriptor)
