from __future__ import annotations

import hashlib
import json
import mmap
import os
import tempfile
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterable

_CHUNK = 1024 * 1024
_FEATURE_KEY = b'"features"'
_ACTIVE_XML_PATTERNS = (b"<!doctype", b"<!entity")
_GML_PROBE_TOKENS = (b"featurecollection", b"cadastralparcel", b"predefined", b"xmlns:gml", b"opengis.net/gml")


class MappedPayloadPool:
    def __init__(self) -> None:
        self._items: list[tuple[mmap.mmap, int, Path]] = []
        self._hashes: dict[int, str] = {}

    def map_file(self, path: Path, sha256_hex: str) -> mmap.mmap:
        fd = os.open(path, os.O_RDONLY)
        try:
            mapped = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        except Exception:
            os.close(fd)
            raise
        self._items.append((mapped, fd, path))
        self._hashes[id(mapped)] = sha256_hex
        return mapped

    def sha256(self, payload) -> str:
        return self._hashes.get(id(payload)) or hashlib.sha256(payload).hexdigest()

    def cleanup(self) -> None:
        while self._items:
            mapped, fd, path = self._items.pop()
            self._hashes.pop(id(mapped), None)
            try:
                mapped.close()
            finally:
                try:
                    os.close(fd)
                finally:
                    path.unlink(missing_ok=True)


def git_blob_sha1(path: Path, chunk_size: int = _CHUNK) -> str:
    digest = hashlib.sha1(f"blob {path.stat().st_size}\0".encode("ascii"))
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _locate_features_array(mapped: mmap.mmap) -> int:
    key = mapped.find(_FEATURE_KEY)
    if key < 0:
        raise RuntimeError("CANONICAL_FEATURES_KEY_MISSING")
    cursor = key + len(_FEATURE_KEY)
    while cursor < len(mapped) and mapped[cursor] in b" \t\r\n": cursor += 1
    if cursor >= len(mapped) or mapped[cursor] != ord(":"):
        raise RuntimeError("CANONICAL_FEATURES_COLON_MISSING")
    cursor += 1
    while cursor < len(mapped) and mapped[cursor] in b" \t\r\n": cursor += 1
    if cursor >= len(mapped) or mapped[cursor] != ord("["):
        raise RuntimeError("CANONICAL_FEATURES_ARRAY_MISSING")
    return cursor + 1


def _scan_json_object(mapped: mmap.mmap, start: int) -> int:
    depth = 0; in_string = False; escaped = False; cursor = start
    while cursor < len(mapped):
        value = mapped[cursor]
        if in_string:
            if escaped: escaped = False
            elif value == ord("\\"): escaped = True
            elif value == ord('"'): in_string = False
        else:
            if value == ord('"'): in_string = True
            elif value == ord("{"): depth += 1
            elif value == ord("}"):
                depth -= 1
                if depth == 0: return cursor + 1
                if depth < 0: break
        cursor += 1
    raise RuntimeError("CANONICAL_FEATURE_OBJECT_UNTERMINATED")


def canonical_targets(path: Path, *, expected_blob_sha: str, expected_feature_count: int, target_ids: Iterable[str]) -> tuple[dict[str, dict], dict]:
    observed = git_blob_sha1(path)
    if observed != expected_blob_sha:
        raise RuntimeError(f"CANONICAL_BLOB_MISMATCH:{observed}")
    wanted = set(target_ids); rows: dict[str, dict] = {}; inspire_ids: set[str] = set(); feature_count = 0; maximum_feature_bytes = 0
    fd = os.open(path, os.O_RDONLY)
    try:
        mapped = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        try:
            cursor = _locate_features_array(mapped)
            while True:
                while cursor < len(mapped) and mapped[cursor] in b" \t\r\n,": cursor += 1
                if cursor >= len(mapped): raise RuntimeError("CANONICAL_FEATURES_ARRAY_UNTERMINATED")
                if mapped[cursor] == ord("]"): break
                if mapped[cursor] != ord("{"): raise RuntimeError(f"CANONICAL_FEATURE_OBJECT_EXPECTED_AT:{cursor}")
                end = _scan_json_object(mapped, cursor); raw = mapped[cursor:end]; maximum_feature_bytes = max(maximum_feature_bytes, len(raw))
                try: feature = json.loads(raw)
                except json.JSONDecodeError as exc: raise RuntimeError(f"CANONICAL_FEATURE_JSON_INVALID:{feature_count + 1}:{exc.msg}") from exc
                feature_count += 1; properties = feature.get("properties") or {}; parcel_id = properties.get("parcel_id") or properties.get("security_parcel_id")
                if parcel_id in wanted:
                    if parcel_id in rows: raise RuntimeError(f"TARGET_DUPLICATE:{parcel_id}")
                    row_no = int(parcel_id.removeprefix("parcel_"))
                    if int(properties.get("row_no")) != row_no: raise RuntimeError(f"ROW_NO_MISMATCH:{parcel_id}")
                    inspire_id = str(properties.get("hmlr_inspire_id") or "").strip()
                    if not inspire_id.isdigit() or inspire_id in inspire_ids: raise RuntimeError(f"INSPIRE_ID_INVALID_OR_DUPLICATE:{parcel_id}")
                    inspire_ids.add(inspire_id)
                    rows[parcel_id] = {"parcel_id": parcel_id, "row_no": row_no, "hmlr_inspire_id": inspire_id, "hmlr_lon": properties.get("hmlr_lon"), "hmlr_lat": properties.get("hmlr_lat"), "hmlr_area_m2": properties.get("hmlr_area_m2"), "london_authority": properties.get("london_authority")}
                cursor = end
        finally: mapped.close()
    finally: os.close(fd)
    if feature_count != expected_feature_count: raise RuntimeError(f"CANONICAL_FEATURE_COUNT_MISMATCH:{feature_count}")
    if set(rows) != wanted: raise RuntimeError(f"TARGETS_MISSING:{sorted(wanted - set(rows))}")
    return rows, {"observed_git_blob_sha": observed, "feature_count": feature_count, "target_count": len(rows), "unique_inspire_id_count": len(inspire_ids), "canonical_streaming_mmap": True, "maximum_feature_object_bytes": maximum_feature_bytes}


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/")); return not path.is_absolute() and ".." not in path.parts and bool(path.name)


def _scan_active_xml(state: bytes, chunk: bytes) -> bytes:
    probe = (state + chunk).lower()
    if any(pattern in probe for pattern in _ACTIVE_XML_PATTERNS): raise RuntimeError("GML_ACTIVE_XML_FORBIDDEN")
    return probe[-32:]


def _looks_like_gml(probe: bytes) -> bool:
    lowered = probe.lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower(); return lowered.startswith(b"<") and any(token in lowered for token in _GML_PROBE_TOKENS)


def _copy_stream(source: BinaryIO, destination: BinaryIO, *, limit: int, scan_xml: bool, chunk_size: int = _CHUNK) -> tuple[int, str, bytes]:
    total = 0; digest = hashlib.sha256(); prefix = bytearray(); scan_state = b""
    while chunk := source.read(chunk_size):
        total += len(chunk)
        if total > limit: raise RuntimeError(f"PAYLOAD_SIZE_LIMIT_EXCEEDED:{limit}")
        digest.update(chunk)
        if len(prefix) < 8192: prefix.extend(chunk[:8192-len(prefix)])
        if scan_xml: scan_state = _scan_active_xml(scan_state, chunk)
        destination.write(chunk)
    destination.flush(); return total, digest.hexdigest(), bytes(prefix)


def _new_temp(suffix: str) -> tuple[BinaryIO, Path]:
    handle = tempfile.NamedTemporaryFile(prefix="parcel_label_2_stream_", suffix=suffix, delete=False); return handle, Path(handle.name)


def normalise_download_file(raw_path: Path, *, final_url: str, media_type: str, pool: MappedPayloadPool, max_gml_bytes: int = 256*1024*1024, max_zip_members: int = 128, max_zip_ratio: float = 250.0) -> tuple[mmap.mmap, str]:
    with raw_path.open("rb") as raw: signature = raw.read(4)
    is_zip = signature.startswith(b"PK\x03\x04") or zipfile.is_zipfile(raw_path)
    if is_zip:
        with zipfile.ZipFile(raw_path) as archive:
            all_infos = archive.infolist()
            if len(all_infos) > max_zip_members: raise RuntimeError(f"ZIP_MEMBER_COUNT_EXCEEDED:{len(all_infos)}")
            infos = [info for info in all_infos if not info.is_dir() and info.filename.lower().endswith(".gml")]
            if len(infos) != 1: raise RuntimeError(f"ZIP_GML_MEMBER_COUNT:{len(infos)}")
            info = infos[0]
            if not _safe_member_name(info.filename): raise RuntimeError("ZIP_GML_MEMBER_PATH_UNSAFE")
            if info.file_size > max_gml_bytes: raise RuntimeError(f"ZIP_GML_SIZE_LIMIT_EXCEEDED:{max_gml_bytes}")
            if info.file_size and info.compress_size == 0: raise RuntimeError("ZIP_GML_COMPRESSION_RATIO_INVALID")
            ratio = info.file_size/info.compress_size if info.compress_size else 0.0
            if ratio > max_zip_ratio: raise RuntimeError(f"ZIP_GML_COMPRESSION_RATIO_EXCEEDED:{ratio:.1f}")
            extracted_handle, extracted_path = _new_temp(".gml")
            try:
                with extracted_handle, archive.open(info, "r") as member: _, digest, probe = _copy_stream(member, extracted_handle, limit=max_gml_bytes, scan_xml=True)
                if not _looks_like_gml(probe): raise RuntimeError("ZIP_MEMBER_NOT_RECOGNISED_GML")
                return pool.map_file(extracted_path, digest), final_url + "#" + info.filename
            except Exception:
                extracted_path.unlink(missing_ok=True); raise
    with raw_path.open("rb") as raw: probe = raw.read(8192)
    lowered = probe.lower()
    if "html" in media_type or b"<html" in lowered or b"<!doctype html" in lowered: raise RuntimeError("BINARY_ROUTE_RETURNED_HTML")
    if not _looks_like_gml(probe): raise RuntimeError(f"UNEXPECTED_HMLR_PAYLOAD:{media_type or 'unknown'}")
    digest = hashlib.sha256(); scan_state = b""; total = 0
    with raw_path.open("rb") as raw:
        while chunk := raw.read(_CHUNK):
            total += len(chunk)
            if total > max_gml_bytes: raise RuntimeError(f"GML_SIZE_LIMIT_EXCEEDED:{max_gml_bytes}")
            digest.update(chunk); scan_state = _scan_active_xml(scan_state, chunk)
    return pool.map_file(raw_path, digest.hexdigest()), final_url


def stream_response_to_file(response, *, limit: int, suffix: str = ".download") -> Path:
    handle, path = _new_temp(suffix)
    try:
        with handle: _copy_stream(response, handle, limit=limit, scan_xml=False)
        return path
    except Exception:
        path.unlink(missing_ok=True); raise


def validate_https_url(url: str, *, primary_host: str | None = None, same_origin: bool = False) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.casefold() != "https": raise RuntimeError("OFFICIAL_DOWNLOAD_URL_NOT_HTTPS")
    if parsed.username is not None or parsed.password is not None: raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_USERINFO")
    if parsed.fragment: raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_FRAGMENT")
    host = (parsed.hostname or "").casefold()
    if not host: raise RuntimeError("OFFICIAL_DOWNLOAD_URL_HOST_MISSING")
    if same_origin and primary_host and host != primary_host.casefold(): raise RuntimeError(f"OFFICIAL_DOWNLOAD_URL_CROSS_ORIGIN:{host}")
    return url
