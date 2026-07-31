from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

try:
    import lxml
    from lxml import etree
except ImportError as exc:
    raise RuntimeError("XML_SECURE_LXML_BACKEND_UNAVAILABLE") from exc

_MIN_LXML = (6, 1, 0, 0)
_MIN_LIBXML = (2, 14, 0)
_UTF8_BOM = b"\xef\xbb\xbf"
_FORBIDDEN_MARKERS = (b"<!doctype", b"<!entity")
_DECLARATION_ENCODING = re.compile(
    br"<\?xml\s+[^>]*\bencoding\s*=\s*(['\"])([^'\"]+)\1",
    re.IGNORECASE,
)


def _version(value: Iterable[int], width: int) -> tuple[int, ...]:
    parts = tuple(int(part) for part in value)
    return (parts + (0,) * width)[:width]


def runtime_versions() -> dict:
    return {
        "lxml": _version(etree.LXML_VERSION, 4),
        "libxml_runtime": _version(etree.LIBXML_VERSION, 3),
        "libxml_compiled": _version(etree.LIBXML_COMPILED_VERSION, 3),
    }


def require_supported_backend(
    *,
    lxml_version: Iterable[int] | None = None,
    libxml_runtime: Iterable[int] | None = None,
    libxml_compiled: Iterable[int] | None = None,
) -> dict:
    current = runtime_versions()
    lxml_value = _version(lxml_version or current["lxml"], 4)
    runtime_value = _version(libxml_runtime or current["libxml_runtime"], 3)
    compiled_value = _version(libxml_compiled or current["libxml_compiled"], 3)
    if lxml_value < _MIN_LXML:
        raise RuntimeError("XML_LXML_VERSION_BELOW_6_1_0:" + ".".join(map(str, lxml_value)))
    if runtime_value < _MIN_LIBXML:
        raise RuntimeError("XML_LIBXML_RUNTIME_BELOW_2_14_0:" + ".".join(map(str, runtime_value)))
    if compiled_value < _MIN_LIBXML:
        raise RuntimeError("XML_LIBXML_COMPILED_BELOW_2_14_0:" + ".".join(map(str, compiled_value)))
    if runtime_value != compiled_value:
        raise RuntimeError(
            "XML_LIBXML_RUNTIME_COMPILED_MISMATCH:"
            + ".".join(map(str, runtime_value))
            + ":"
            + ".".join(map(str, compiled_value))
        )
    return {
        "xml_backend": "lxml.etree/libxml2",
        "xml_backend_lxml_version": ".".join(map(str, lxml_value)),
        "xml_backend_libxml_runtime_version": ".".join(map(str, runtime_value)),
        "xml_backend_libxml_compiled_version": ".".join(map(str, compiled_value)),
        "xml_backend_minimum_lxml_version": "6.1.0",
        "xml_backend_minimum_libxml_version": "2.14.0",
        "xml_backend_runtime_compiled_match": True,
    }


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


def validate_xml_lexical_security(path: Path, *, chunk_size: int = 64 * 1024) -> dict:
    source = Path(path)
    try:
        size = source.stat().st_size
    except OSError as exc:
        raise RuntimeError(f"XML_SECURITY_SOURCE_STAT_FAILED:{source}") from exc
    if size <= 0:
        raise RuntimeError("XML_SECURITY_EMPTY_DOCUMENT")
    if chunk_size < 64:
        raise ValueError("chunk_size must be at least 64")
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
        "xml_security_doctype_forbidden": True,
        "xml_security_entity_declaration_forbidden": True,
        "xml_security_nul_forbidden": True,
    }


def _parser_options() -> dict:
    return {
        "encoding": "UTF-8",
        "attribute_defaults": False,
        "dtd_validation": False,
        "load_dtd": False,
        "no_network": True,
        "decompress": False,
        "recover": False,
        "huge_tree": False,
        "resolve_entities": False,
        "remove_comments": False,
        "remove_pis": False,
        "strip_cdata": True,
        "collect_ids": False,
        "compact": True,
    }


def secure_iterparse(path: Path, *, events=("end",)):
    require_supported_backend()
    options = _parser_options().copy()
    options.pop("decompress", None)
    return etree.iterparse(str(Path(path)), events=events, **options)


class SecureElementTreeAdapter:
    Element = etree._Element
    ParseError = etree.XMLSyntaxError

    @staticmethod
    def iterparse(path: Path, events=("end",)):
        return secure_iterparse(path, events=events)

    @staticmethod
    def tostring(element, encoding="utf-8"):
        return etree.tostring(element, encoding=encoding, with_tail=False)


ADAPTER = SecureElementTreeAdapter()


def patch_validator_chain(module) -> list[str]:
    patched: list[str] = []
    seen: set[int] = set()
    current = module
    for _ in range(32):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if hasattr(current, "ET"):
            current.ET = ADAPTER
            patched.append(getattr(current, "__name__", "<module>"))
        current = getattr(current, "previous", None)
    if not patched:
        raise RuntimeError("XML_LXML_VALIDATOR_CHAIN_NOT_PATCHED")
    return patched


class _StructureTarget:
    def __init__(self, limits: dict[str, int]) -> None:
        self.limits = limits
        self.depth = 0
        self.root_count = 0
        self.elements = 0
        self.max_depth_seen = 0
        self.total_attributes = 0
        self.max_attributes_seen = 0
        self.total_attribute_chars = 0
        self.max_text_segment_seen = 0
        self.failure: str | None = None

    def _fail(self, message: str):
        self.failure = message
        raise RuntimeError(message)

    def start(self, tag: str, attrs: dict[str, str]):
        if len(tag) > self.limits["max_name_chars"]:
            self._fail(f"XML_ELEMENT_NAME_LIMIT_EXCEEDED:{len(tag)}")
        self.depth += 1
        if self.depth == 1:
            self.root_count += 1
            if self.root_count > 1:
                self._fail("XML_ROOT_ELEMENT_COUNT_NOT_ONE")
        if self.depth > self.limits["max_depth"]:
            self._fail(f"XML_DEPTH_LIMIT_EXCEEDED:{self.depth}:{self.limits['max_depth']}")
        self.max_depth_seen = max(self.max_depth_seen, self.depth)
        self.elements += 1
        if self.elements > self.limits["max_elements"]:
            self._fail(f"XML_ELEMENT_LIMIT_EXCEEDED:{self.elements}:{self.limits['max_elements']}")
        count = len(attrs)
        if count > self.limits["max_attributes_per_element"]:
            self._fail(
                f"XML_ATTRIBUTES_PER_ELEMENT_LIMIT_EXCEEDED:{count}:{self.limits['max_attributes_per_element']}"
            )
        self.max_attributes_seen = max(self.max_attributes_seen, count)
        self.total_attributes += count
        if self.total_attributes > self.limits["max_total_attributes"]:
            self._fail(
                f"XML_TOTAL_ATTRIBUTE_LIMIT_EXCEEDED:{self.total_attributes}:{self.limits['max_total_attributes']}"
            )
        for key, value in attrs.items():
            if len(key) > self.limits["max_name_chars"]:
                self._fail(f"XML_ATTRIBUTE_NAME_LIMIT_EXCEEDED:{len(key)}")
            if len(value) > self.limits["max_attribute_value_chars"]:
                self._fail(
                    f"XML_ATTRIBUTE_VALUE_LIMIT_EXCEEDED:{len(value)}:{self.limits['max_attribute_value_chars']}"
                )
            self.total_attribute_chars += len(key) + len(value)
            if self.total_attribute_chars > self.limits["max_total_attribute_chars"]:
                self._fail(
                    f"XML_TOTAL_ATTRIBUTE_CHAR_LIMIT_EXCEEDED:{self.total_attribute_chars}:{self.limits['max_total_attribute_chars']}"
                )
        return None

    def data(self, data: str) -> None:
        length = len(data)
        if length > self.limits["max_text_chars_per_segment"]:
            self._fail(
                f"XML_TEXT_SEGMENT_LIMIT_EXCEEDED:{length}:{self.limits['max_text_chars_per_segment']}"
            )
        self.max_text_segment_seen = max(self.max_text_segment_seen, length)

    def end(self, _tag: str) -> None:
        if self.depth <= 0:
            self._fail("XML_STRUCTURE_STACK_UNDERFLOW")
        self.depth -= 1

    def close(self):
        if self.failure is not None:
            raise RuntimeError(self.failure)
        if self.root_count != 1:
            raise RuntimeError(f"XML_ROOT_ELEMENT_COUNT_NOT_ONE:{self.root_count}")
        if self.depth != 0:
            raise RuntimeError(f"XML_STRUCTURE_UNBALANCED:{self.depth}")
        if self.elements <= 0:
            raise RuntimeError("XML_STRUCTURE_NO_ELEMENTS")
        return {
            "xml_structure_root_count": self.root_count,
            "xml_structure_element_count": self.elements,
            "xml_structure_max_depth": self.max_depth_seen,
            "xml_structure_total_attributes": self.total_attributes,
            "xml_structure_max_attributes_per_element": self.max_attributes_seen,
            "xml_structure_total_attribute_chars": self.total_attribute_chars,
            "xml_structure_max_text_segment_chars": self.max_text_segment_seen,
        }


def _positive(name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def validate_xml_structure(
    path: Path,
    *,
    chunk_size: int = 64 * 1024,
    max_depth: int = 128,
    max_elements: int = 5_000_000,
    max_attributes_per_element: int = 128,
    max_total_attributes: int = 10_000_000,
    max_attribute_value_chars: int = 1 * 1024 * 1024,
    max_total_attribute_chars: int = 64 * 1024 * 1024,
    max_text_chars_per_segment: int = 8 * 1024 * 1024,
    max_name_chars: int = 1024,
) -> dict:
    limits = {
        "chunk_size": _positive("chunk_size", chunk_size),
        "max_depth": _positive("max_depth", max_depth),
        "max_elements": _positive("max_elements", max_elements),
        "max_attributes_per_element": _positive("max_attributes_per_element", max_attributes_per_element),
        "max_total_attributes": _positive("max_total_attributes", max_total_attributes),
        "max_attribute_value_chars": _positive("max_attribute_value_chars", max_attribute_value_chars),
        "max_total_attribute_chars": _positive("max_total_attribute_chars", max_total_attribute_chars),
        "max_text_chars_per_segment": _positive("max_text_chars_per_segment", max_text_chars_per_segment),
        "max_name_chars": _positive("max_name_chars", max_name_chars),
    }
    backend = require_supported_backend()
    lexical = validate_xml_lexical_security(Path(path), chunk_size=limits["chunk_size"])
    target = _StructureTarget(limits)
    parser = etree.XMLParser(target=target, **_parser_options())
    source = Path(path)
    try:
        with source.open("rb") as handle:
            while True:
                chunk = handle.read(limits["chunk_size"])
                if not chunk:
                    break
                parser.feed(chunk)
        structure = parser.close()
    except RuntimeError:
        raise
    except etree.XMLSyntaxError as exc:
        raise RuntimeError(f"XML_LXML_STRUCTURE_PARSE_FAILED:{exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"XML_STRUCTURE_SOURCE_READ_FAILED:{source}") from exc
    return backend | lexical | structure | {
        "xml_structure_preflight_passed": True,
        "xml_structure_depth_limit": limits["max_depth"],
        "xml_structure_element_limit": limits["max_elements"],
        "xml_structure_attribute_limit_per_element": limits["max_attributes_per_element"],
        "xml_structure_text_segment_limit": limits["max_text_chars_per_segment"],
        "xml_parser_load_dtd": False,
        "xml_parser_resolve_entities": False,
        "xml_parser_no_network": True,
        "xml_parser_huge_tree": False,
        "xml_parser_recover": False,
        "xml_parser_decompress": False,
    }
