from __future__ import annotations

import re
from pathlib import Path
import pyexpat

_MIN_EXPAT = (2, 7, 2)
_UTF8_BOM = b"\xef\xbb\xbf"
_FORBIDDEN_MARKERS = (b"<!doctype", b"<!entity")
_DECLARATION_ENCODING = re.compile(
    br"<\?xml\s+[^>]*\bencoding\s*=\s*(['\"])([^'\"]+)\1",
    re.IGNORECASE,
)


def _normalise_version(value: tuple[int, ...] | list[int] | None) -> tuple[int, int, int]:
    if value is None:
        raw = getattr(pyexpat, "version_info", None)
        if raw is None:
            match = re.search(r"(\d+)\.(\d+)\.(\d+)", str(getattr(pyexpat, "EXPAT_VERSION", "")))
            if not match:
                raise RuntimeError("XML_EXPAT_VERSION_UNAVAILABLE")
            value = tuple(int(part) for part in match.groups())
        else:
            value = tuple(int(part) for part in raw)
    parts = tuple(int(part) for part in value)
    return (parts + (0, 0, 0))[:3]


def runtime_expat_version() -> tuple[int, int, int]:
    return _normalise_version(None)


def require_supported_expat(value: tuple[int, ...] | list[int] | None = None) -> tuple[int, int, int]:
    version = _normalise_version(value)
    if version < _MIN_EXPAT:
        raise RuntimeError(
            "XML_EXPAT_VERSION_BELOW_2_7_2:" + ".".join(str(part) for part in version)
        )
    return version


def _validate_encoding(prefix: bytes) -> str:
    if prefix.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        raise RuntimeError("XML_ENCODING_UTF32_FORBIDDEN")
    if prefix.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise RuntimeError("XML_ENCODING_UTF16_FORBIDDEN")
    probe = prefix[len(_UTF8_BOM):] if prefix.startswith(_UTF8_BOM) else prefix
    if b"\x00" in probe:
        raise RuntimeError("XML_NUL_BYTE_FORBIDDEN")
    declaration = _DECLARATION_ENCODING.search(probe[:4096])
    if declaration is None:
        return "UTF-8"
    try:
        raw = declaration.group(2).decode("ascii", errors="strict").strip().casefold().replace("_", "-")
    except UnicodeDecodeError as exc:
        raise RuntimeError("XML_DECLARED_ENCODING_NON_ASCII") from exc
    if raw not in {"utf-8", "utf8"}:
        raise RuntimeError(f"XML_DECLARED_ENCODING_UNSUPPORTED:{raw}")
    return "UTF-8"


def validate_xml_security(
    path: Path,
    *,
    expat_version: tuple[int, ...] | list[int] | None = None,
    chunk_size: int = 64 * 1024,
) -> dict:
    source = Path(path)
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise RuntimeError(f"XML_SECURITY_SOURCE_STAT_FAILED:{source}") from exc
    if size <= 0:
        raise RuntimeError("XML_SECURITY_EMPTY_DOCUMENT")
    if chunk_size < 64:
        raise ValueError("chunk_size must be at least 64")

    version = require_supported_expat(expat_version)
    try:
        with source.open("rb") as handle:
            prefix = handle.read(min(4096, size))
            encoding = _validate_encoding(prefix)
            handle.seek(0)
            tail = b""
            scanned = 0
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                scanned += len(chunk)
                if b"\x00" in chunk:
                    raise RuntimeError("XML_NUL_BYTE_FORBIDDEN")
                window = (tail + chunk).lower()
                for marker in _FORBIDDEN_MARKERS:
                    if marker in window:
                        name = marker[2:].decode("ascii").upper()
                        raise RuntimeError(f"XML_{name}_DECLARATION_FORBIDDEN")
                tail = window[-64:]
    except RuntimeError:
        raise
    except OSError as exc:
        raise RuntimeError(f"XML_SECURITY_SOURCE_READ_FAILED:{source}") from exc

    if scanned != size:
        raise RuntimeError(f"XML_SECURITY_SCAN_SIZE_MISMATCH:{scanned}:{size}")

    return {
        "xml_security_preflight_passed": True,
        "xml_security_file_size": size,
        "xml_security_encoding": encoding,
        "xml_security_expat_version": ".".join(str(part) for part in version),
        "xml_security_minimum_expat_version": "2.7.2",
        "xml_security_doctype_forbidden": True,
        "xml_security_entity_declaration_forbidden": True,
        "xml_security_nul_forbidden": True,
    }
