from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path
from typing import Callable, TypeVar

_T = TypeVar("_T")
_DEFAULT_CHUNK = 1024 * 1024


def _regular_single_link(result: os.stat_result, *, prefix: str) -> None:
    if not stat.S_ISREG(result.st_mode):
        raise RuntimeError(f"{prefix}_NOT_REGULAR_FILE")
    if result.st_size <= 0:
        raise RuntimeError(f"{prefix}_EMPTY")
    if result.st_nlink != 1:
        raise RuntimeError(f"{prefix}_LINK_COUNT_NOT_ONE:{result.st_nlink}")


def _normalise_expected(value: str) -> str:
    candidate = str(value).strip().lower()
    if len(candidate) != 64 or any(char not in "0123456789abcdef" for char in candidate):
        raise RuntimeError("XML_EXPECTED_SHA256_INVALID")
    return candidate


def _validate_chunk_size(chunk_size: int) -> None:
    if not isinstance(chunk_size, int) or isinstance(chunk_size, bool) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")


def _open_readonly(path: Path, *, prefix: str) -> int:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"{prefix}_DESCRIPTOR_OPEN_FAILED:{path}") from exc
    try:
        info = os.fstat(descriptor)
        _regular_single_link(info, prefix=prefix)
        if not hasattr(os, "O_NOFOLLOW"):
            link_info = os.lstat(path)
            if stat.S_ISLNK(link_info.st_mode):
                raise RuntimeError(f"{prefix}_SYMLINK_FORBIDDEN")
            if (link_info.st_dev, link_info.st_ino) != (info.st_dev, info.st_ino):
                raise RuntimeError(f"{prefix}_PATH_DESCRIPTOR_MISMATCH")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _hash_descriptor(descriptor: int, *, chunk_size: int) -> str:
    _validate_chunk_size(chunk_size)
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while True:
        chunk = os.read(descriptor, chunk_size)
        if not chunk:
            break
        digest.update(chunk)
    os.lseek(descriptor, 0, os.SEEK_SET)
    return digest.hexdigest()


def _copy_descriptor_snapshot(descriptor: int, *, chunk_size: int):
    _validate_chunk_size(chunk_size)
    directory = tempfile.TemporaryDirectory(prefix="parcel-label-2-xml-snapshot-")
    root = Path(directory.name)
    target = root / "snapshot.gml"
    try:
        os.chmod(root, 0o700)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
        out_fd = os.open(target, flags, 0o600)
        digest = hashlib.sha256()
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            while True:
                chunk = os.read(descriptor, chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(out_fd, view)
                    if written <= 0:
                        raise RuntimeError("XML_SNAPSHOT_WRITE_ZERO")
                    view = view[written:]
            os.fsync(out_fd)
            os.fchmod(out_fd, 0o400)
        finally:
            os.close(out_fd)
            os.lseek(descriptor, 0, os.SEEK_SET)
        info = os.stat(target, follow_symlinks=False)
        _regular_single_link(info, prefix="XML_SNAPSHOT")
        if stat.S_IMODE(info.st_mode) != 0o400:
            raise RuntimeError(f"XML_SNAPSHOT_MODE_INVALID:{oct(stat.S_IMODE(info.st_mode))}")
        return directory, target, digest.hexdigest()
    except Exception:
        directory.cleanup()
        raise


def _proc_descriptor_path(descriptor: int) -> Path | None:
    candidate = Path(f"/proc/self/fd/{descriptor}")
    try:
        target = os.stat(candidate)
        source = os.fstat(descriptor)
    except OSError:
        return None
    if (target.st_dev, target.st_ino, target.st_size) != (source.st_dev, source.st_ino, source.st_size):
        return None
    return candidate


def _metadata_tuple(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def guarded_immutable_snapshot_call(
    path: Path,
    *,
    expected_sha256: str,
    operation: Callable[[Path], _T],
    chunk_size: int = _DEFAULT_CHUNK,
    force_linked_snapshot: bool = False,
) -> tuple[_T, dict]:
    """Parse only a verified private snapshot, never the mutable original source."""
    expected = _normalise_expected(expected_sha256)
    _validate_chunk_size(chunk_size)
    source_path = Path(path)
    source_fd = _open_readonly(source_path, prefix="XML_SOURCE")
    snapshot_directory = None
    snapshot_fd = None
    snapshot_path: Path | None = None
    try:
        source_before = os.fstat(source_fd)
        source_digest = _hash_descriptor(source_fd, chunk_size=chunk_size)
        if source_digest != expected:
            raise RuntimeError(f"XML_SOURCE_SHA256_MISMATCH:{source_digest}:{expected}")

        snapshot_directory, snapshot_path, copied_digest = _copy_descriptor_snapshot(
            source_fd,
            chunk_size=chunk_size,
        )
        if copied_digest != expected:
            raise RuntimeError(f"XML_SNAPSHOT_COPY_SHA256_MISMATCH:{copied_digest}:{expected}")

        snapshot_fd = _open_readonly(snapshot_path, prefix="XML_SNAPSHOT")
        snapshot_digest = _hash_descriptor(snapshot_fd, chunk_size=chunk_size)
        if snapshot_digest != expected:
            raise RuntimeError(f"XML_SNAPSHOT_DESCRIPTOR_SHA256_MISMATCH:{snapshot_digest}:{expected}")

        proc_path = None if force_linked_snapshot else _proc_descriptor_path(snapshot_fd)
        if proc_path is not None:
            os.unlink(snapshot_path)
            parser_path = proc_path
            snapshot_mode = "UNLINKED_PRIVATE_DESCRIPTOR"
            snapshot_unlinked = True
        else:
            parser_path = snapshot_path
            snapshot_mode = "PRIVATE_READ_ONLY_PATH"
            snapshot_unlinked = False
        snapshot_before = os.fstat(snapshot_fd)

        result = operation(parser_path)

        snapshot_after = os.fstat(snapshot_fd)
        if _metadata_tuple(snapshot_before) != _metadata_tuple(snapshot_after):
            raise RuntimeError("XML_SNAPSHOT_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE")
        snapshot_after_digest = _hash_descriptor(snapshot_fd, chunk_size=chunk_size)
        if snapshot_after_digest != expected:
            raise RuntimeError("XML_SNAPSHOT_DESCRIPTOR_SHA256_CHANGED_DURING_PARSE")

        if not snapshot_unlinked:
            try:
                linked_after = os.lstat(snapshot_path)
            except OSError as exc:
                raise RuntimeError("XML_SNAPSHOT_PATH_MISSING_AFTER_PARSE") from exc
            if stat.S_ISLNK(linked_after.st_mode):
                raise RuntimeError("XML_SNAPSHOT_PATH_SYMLINK_AFTER_PARSE")
            if (linked_after.st_dev, linked_after.st_ino) != (snapshot_before.st_dev, snapshot_before.st_ino):
                raise RuntimeError("XML_SNAPSHOT_PATH_REPLACED_DURING_PARSE")
            if stat.S_IMODE(linked_after.st_mode) != 0o400:
                raise RuntimeError("XML_SNAPSHOT_PATH_MODE_CHANGED_DURING_PARSE")

        source_after = os.fstat(source_fd)
        if _metadata_tuple(source_before) != _metadata_tuple(source_after):
            raise RuntimeError("XML_SOURCE_DESCRIPTOR_METADATA_CHANGED_DURING_PARSE")
        source_after_digest = _hash_descriptor(source_fd, chunk_size=chunk_size)
        if source_after_digest != expected:
            raise RuntimeError("XML_SOURCE_DESCRIPTOR_SHA256_CHANGED_DURING_PARSE")
        try:
            path_after = os.lstat(source_path)
        except OSError as exc:
            raise RuntimeError("XML_SOURCE_PATH_MISSING_AFTER_PARSE") from exc
        if stat.S_ISLNK(path_after.st_mode):
            raise RuntimeError("XML_SOURCE_PATH_SYMLINK_AFTER_PARSE")
        if (path_after.st_dev, path_after.st_ino) != (source_before.st_dev, source_before.st_ino):
            raise RuntimeError("XML_SOURCE_PATH_REPLACED_DURING_PARSE")

        return result, {
            "xml_immutable_snapshot_validation_passed": True,
            "xml_parser_source_mode": snapshot_mode,
            "xml_parser_uses_private_snapshot": True,
            "xml_parser_uses_original_descriptor": False,
            "xml_snapshot_unlinked_before_parse": snapshot_unlinked,
            "xml_source_expected_sha256": expected,
            "xml_source_observed_sha256": source_digest,
            "xml_snapshot_observed_sha256": snapshot_digest,
            "xml_source_device": int(source_before.st_dev),
            "xml_source_inode": int(source_before.st_ino),
            "xml_source_size_bytes": int(source_before.st_size),
            "xml_snapshot_device": int(snapshot_before.st_dev),
            "xml_snapshot_inode": int(snapshot_before.st_ino),
            "xml_snapshot_size_bytes": int(snapshot_before.st_size),
        }
    finally:
        if snapshot_fd is not None:
            os.close(snapshot_fd)
        if snapshot_directory is not None:
            snapshot_directory.cleanup()
        os.close(source_fd)
