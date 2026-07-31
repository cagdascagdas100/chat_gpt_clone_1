from __future__ import annotations

import binascii
import hashlib
import stat
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Callable

_MAX_MEMBER_NAME_CHARS = 1024
_ENCRYPTED_FLAG = 0x1


def _allowed_compression_methods() -> set[int]:
    names = ("ZIP_STORED", "ZIP_DEFLATED", "ZIP_BZIP2", "ZIP_LZMA", "ZIP_ZSTANDARD")
    return {getattr(zipfile, name) for name in names if hasattr(zipfile, name)}


def _normalise_name(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise RuntimeError("ZIP_MEMBER_NAME_EMPTY")
    if len(name) > _MAX_MEMBER_NAME_CHARS:
        raise RuntimeError(f"ZIP_MEMBER_NAME_LIMIT_EXCEEDED:{len(name)}")
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise RuntimeError("ZIP_MEMBER_NAME_CONTROL_CHARACTER")
    normalised = name.replace("\\", "/")
    path = PurePosixPath(normalised)
    if path.is_absolute() or ".." in path.parts or not path.name:
        raise RuntimeError("ZIP_MEMBER_PATH_UNSAFE")
    return normalised


def _validate_member_type(info: zipfile.ZipInfo) -> None:
    if info.is_dir():
        return
    if info.create_system != 3:
        return
    mode = (info.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG):
        raise RuntimeError(f"ZIP_MEMBER_NOT_REGULAR_FILE:{info.filename}")


def validate_archive_members(
    infos: list[zipfile.ZipInfo],
    *,
    archive_size: int,
    max_zip_members: int,
    max_gml_bytes: int,
    max_zip_ratio: float,
) -> zipfile.ZipInfo:
    if len(infos) > max_zip_members:
        raise RuntimeError(f"ZIP_MEMBER_COUNT_EXCEEDED:{len(infos)}")
    seen: set[str] = set()
    gml_members: list[zipfile.ZipInfo] = []
    allowed_methods = _allowed_compression_methods()
    for info in infos:
        normalised = _normalise_name(info.filename)
        key = normalised.casefold()
        if key in seen:
            raise RuntimeError(f"ZIP_MEMBER_NAME_DUPLICATE:{normalised}")
        seen.add(key)
        if info.reserved != 0:
            raise RuntimeError(f"ZIP_MEMBER_RESERVED_FLAG_NONZERO:{normalised}")
        if info.volume != 0:
            raise RuntimeError(f"ZIP_MEMBER_MULTIDISK_FORBIDDEN:{normalised}")
        if info.header_offset < 0 or info.header_offset >= archive_size:
            raise RuntimeError(f"ZIP_MEMBER_HEADER_OFFSET_INVALID:{normalised}")
        if info.flag_bits & _ENCRYPTED_FLAG:
            raise RuntimeError(f"ZIP_ENCRYPTED_MEMBER_FORBIDDEN:{normalised}")
        _validate_member_type(info)
        if info.is_dir():
            continue
        if info.compress_type not in allowed_methods:
            raise RuntimeError(f"ZIP_COMPRESSION_METHOD_UNSUPPORTED:{info.compress_type}:{normalised}")
        if normalised.casefold().endswith(".gml"):
            gml_members.append(info)
    if len(gml_members) != 1:
        raise RuntimeError(f"ZIP_GML_MEMBER_COUNT:{len(gml_members)}")
    selected = gml_members[0]
    if selected.file_size <= 0:
        raise RuntimeError("ZIP_GML_MEMBER_EMPTY")
    if selected.file_size > max_gml_bytes:
        raise RuntimeError(f"ZIP_GML_SIZE_LIMIT_EXCEEDED:{max_gml_bytes}")
    if selected.compress_size <= 0:
        raise RuntimeError("ZIP_GML_COMPRESSION_RATIO_INVALID")
    ratio = selected.file_size / selected.compress_size
    if ratio > max_zip_ratio:
        raise RuntimeError(f"ZIP_GML_COMPRESSION_RATIO_EXCEEDED:{ratio:.1f}")
    return selected


def _copy_verified_member(source, destination, *, info: zipfile.ZipInfo, base: ModuleType, limit: int) -> tuple[str, bytes]:
    total = 0
    digest = hashlib.sha256()
    crc = 0
    prefix = bytearray()
    scan_state = b""
    try:
        while chunk := source.read(1024 * 1024):
            total += len(chunk)
            if total > limit:
                raise RuntimeError(f"PAYLOAD_SIZE_LIMIT_EXCEEDED:{limit}")
            digest.update(chunk)
            crc = binascii.crc32(chunk, crc)
            if len(prefix) < 8192:
                prefix.extend(chunk[: 8192 - len(prefix)])
            scan_state = base._scan_active_xml(scan_state, chunk)
            destination.write(chunk)
        destination.flush()
    except RuntimeError:
        raise
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"ZIP_MEMBER_DECOMPRESSION_FAILED:{info.filename}:{exc}") from exc
    if total != info.file_size:
        raise RuntimeError(f"ZIP_GML_EXTRACTED_SIZE_MISMATCH:{total}:{info.file_size}")
    observed_crc = crc & 0xFFFFFFFF
    if observed_crc != info.CRC:
        raise RuntimeError(f"ZIP_GML_CRC_MISMATCH:{observed_crc:08x}:{info.CRC:08x}")
    return digest.hexdigest(), bytes(prefix)


def normalise_download_file(
    raw_path: Path,
    *,
    final_url: str,
    media_type: str,
    pool,
    base: ModuleType,
    fallback: Callable,
    max_gml_bytes: int = 256 * 1024 * 1024,
    max_zip_members: int = 128,
    max_zip_ratio: float = 250.0,
):
    source_path = Path(raw_path)
    with source_path.open("rb") as handle:
        signature = handle.read(4)
    is_zip = signature.startswith(b"PK\x03\x04") or zipfile.is_zipfile(source_path)
    if not is_zip:
        return fallback(
            source_path,
            final_url=final_url,
            media_type=media_type,
            pool=pool,
            max_gml_bytes=max_gml_bytes,
            max_zip_members=max_zip_members,
            max_zip_ratio=max_zip_ratio,
        )

    archive_size = source_path.stat().st_size
    try:
        with zipfile.ZipFile(source_path) as archive:
            info = validate_archive_members(
                archive.infolist(),
                archive_size=archive_size,
                max_zip_members=max_zip_members,
                max_gml_bytes=max_gml_bytes,
                max_zip_ratio=max_zip_ratio,
            )
            extracted_handle, extracted_path = base._new_temp(".gml")
            try:
                with extracted_handle, archive.open(info, "r") as member:
                    digest, probe = _copy_verified_member(
                        member,
                        extracted_handle,
                        info=info,
                        base=base,
                        limit=max_gml_bytes,
                    )
                if not base._looks_like_gml(probe):
                    raise RuntimeError("ZIP_MEMBER_NOT_RECOGNISED_GML")
                fragment = urllib.parse.quote(_normalise_name(info.filename), safe="/")
                return pool.map_file(extracted_path, digest), final_url + "#" + fragment
            except Exception:
                extracted_path.unlink(missing_ok=True)
                raise
    except RuntimeError:
        raise
    except (zipfile.BadZipFile, NotImplementedError) as exc:
        raise RuntimeError(f"ZIP_ARCHIVE_VALIDATION_FAILED:{exc}") from exc
