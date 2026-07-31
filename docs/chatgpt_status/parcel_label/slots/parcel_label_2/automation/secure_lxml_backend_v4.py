from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_lxml_backend_v3.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_secure_lxml_backend_v3", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("XML_SECURE_LXML_BACKEND_V3_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

etree = previous.etree
runtime_versions = previous.runtime_versions
require_supported_backend = previous.require_supported_backend
validate_xml_lexical_security = previous.validate_xml_lexical_security
_parser_options = previous._parser_options
secure_iterparse = previous.secure_iterparse
ADAPTER = previous.ADAPTER
patch_validator_chain = previous.patch_validator_chain


class _NamespaceBoundedStructureTarget(previous._CumulativeTextStructureTarget):
    """Bound namespace declarations that are not exposed in the attrs mapping."""

    def __init__(self, limits: dict[str, int]) -> None:
        super().__init__(limits)
        self.total_namespaces = 0
        self.total_namespace_chars = 0
        self.max_namespaces_per_element_seen = 0
        self.max_namespace_prefix_chars_seen = 0
        self.max_namespace_uri_chars_seen = 0
        self._pending_namespaces: list[tuple[str, str]] = []
        self._active_namespace_prefixes: list[str] = []
        self._namespace_counts_by_element: list[int] = []

    def start_ns(self, prefix: str | None, uri: str | None) -> None:
        normalised_prefix = "" if prefix is None else str(prefix)
        normalised_uri = "" if uri is None else str(uri)
        prefix_length = len(normalised_prefix)
        uri_length = len(normalised_uri)
        if prefix_length > self.limits["max_namespace_prefix_chars"]:
            self._fail(
                f"XML_NAMESPACE_PREFIX_LIMIT_EXCEEDED:{prefix_length}:{self.limits['max_namespace_prefix_chars']}"
            )
        if uri_length <= 0:
            self._fail("XML_NAMESPACE_URI_EMPTY")
        if uri_length > self.limits["max_namespace_uri_chars"]:
            self._fail(
                f"XML_NAMESPACE_URI_LIMIT_EXCEEDED:{uri_length}:{self.limits['max_namespace_uri_chars']}"
            )
        self.total_namespaces += 1
        if self.total_namespaces > self.limits["max_total_namespaces"]:
            self._fail(
                f"XML_TOTAL_NAMESPACE_LIMIT_EXCEEDED:{self.total_namespaces}:{self.limits['max_total_namespaces']}"
            )
        self.total_namespace_chars += prefix_length + uri_length
        if self.total_namespace_chars > self.limits["max_total_namespace_chars"]:
            self._fail(
                f"XML_TOTAL_NAMESPACE_CHAR_LIMIT_EXCEEDED:{self.total_namespace_chars}:{self.limits['max_total_namespace_chars']}"
            )
        self.max_namespace_prefix_chars_seen = max(self.max_namespace_prefix_chars_seen, prefix_length)
        self.max_namespace_uri_chars_seen = max(self.max_namespace_uri_chars_seen, uri_length)
        self._pending_namespaces.append((normalised_prefix, normalised_uri))
        self._active_namespace_prefixes.append(normalised_prefix)

    def start(self, tag: str, attrs: dict[str, str]):
        count = len(self._pending_namespaces)
        if count > self.limits["max_namespaces_per_element"]:
            self._fail(
                f"XML_NAMESPACES_PER_ELEMENT_LIMIT_EXCEEDED:{count}:{self.limits['max_namespaces_per_element']}"
            )
        self.max_namespaces_per_element_seen = max(self.max_namespaces_per_element_seen, count)
        self._namespace_counts_by_element.append(count)
        self._pending_namespaces.clear()
        try:
            return super().start(tag, attrs)
        except Exception:
            self._namespace_counts_by_element.pop()
            raise

    def end(self, tag: str) -> None:
        if not self._namespace_counts_by_element:
            self._fail("XML_NAMESPACE_ELEMENT_STACK_UNDERFLOW")
        self._namespace_counts_by_element.pop()
        super().end(tag)

    def end_ns(self, prefix: str | None) -> None:
        normalised_prefix = "" if prefix is None else str(prefix)
        if not self._active_namespace_prefixes:
            self._fail("XML_NAMESPACE_STACK_UNDERFLOW")
        expected = self._active_namespace_prefixes.pop()
        if expected != normalised_prefix:
            self._fail(f"XML_NAMESPACE_STACK_MISMATCH:{expected}:{normalised_prefix}")

    def close(self):
        output = super().close()
        if self._pending_namespaces:
            self._fail(f"XML_NAMESPACE_PENDING_WITHOUT_ELEMENT:{len(self._pending_namespaces)}")
        if self._active_namespace_prefixes:
            self._fail(f"XML_NAMESPACE_STACK_UNBALANCED:{len(self._active_namespace_prefixes)}")
        if self._namespace_counts_by_element:
            self._fail(f"XML_NAMESPACE_ELEMENT_STACK_UNBALANCED:{len(self._namespace_counts_by_element)}")
        return output | {
            "xml_structure_total_namespaces": self.total_namespaces,
            "xml_structure_max_namespaces_per_element": self.max_namespaces_per_element_seen,
            "xml_structure_total_namespace_chars": self.total_namespace_chars,
            "xml_structure_max_namespace_prefix_chars": self.max_namespace_prefix_chars_seen,
            "xml_structure_max_namespace_uri_chars": self.max_namespace_uri_chars_seen,
        }


def _positive(name: str, value: int) -> int:
    return previous._positive(name, value)


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
    max_text_chars_per_element: int = 10_000_000,
    max_total_text_chars: int = 128 * 1024 * 1024,
    max_name_chars: int = 1024,
    max_namespaces_per_element: int = 128,
    max_total_namespaces: int = 5_000_000,
    max_namespace_prefix_chars: int = 256,
    max_namespace_uri_chars: int = 4096,
    max_total_namespace_chars: int = 64 * 1024 * 1024,
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
        "max_text_chars_per_element": _positive("max_text_chars_per_element", max_text_chars_per_element),
        "max_total_text_chars": _positive("max_total_text_chars", max_total_text_chars),
        "max_name_chars": _positive("max_name_chars", max_name_chars),
        "max_namespaces_per_element": _positive("max_namespaces_per_element", max_namespaces_per_element),
        "max_total_namespaces": _positive("max_total_namespaces", max_total_namespaces),
        "max_namespace_prefix_chars": _positive("max_namespace_prefix_chars", max_namespace_prefix_chars),
        "max_namespace_uri_chars": _positive("max_namespace_uri_chars", max_namespace_uri_chars),
        "max_total_namespace_chars": _positive("max_total_namespace_chars", max_total_namespace_chars),
    }
    backend = require_supported_backend()
    lexical = validate_xml_lexical_security(Path(path), chunk_size=limits["chunk_size"])
    target = _NamespaceBoundedStructureTarget(limits)
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
        "xml_structure_text_element_limit": limits["max_text_chars_per_element"],
        "xml_structure_total_text_limit": limits["max_total_text_chars"],
        "xml_structure_namespace_limit_per_element": limits["max_namespaces_per_element"],
        "xml_structure_total_namespace_limit": limits["max_total_namespaces"],
        "xml_structure_namespace_prefix_char_limit": limits["max_namespace_prefix_chars"],
        "xml_structure_namespace_uri_char_limit": limits["max_namespace_uri_chars"],
        "xml_structure_total_namespace_char_limit": limits["max_total_namespace_chars"],
        "xml_namespace_declaration_validation_passed": True,
        "xml_cumulative_text_validation_passed": True,
        "xml_parser_load_dtd": False,
        "xml_parser_resolve_entities": False,
        "xml_parser_no_network": True,
        "xml_parser_huge_tree": False,
        "xml_parser_recover": False,
        "xml_parser_decompress": False,
        "xml_parser_remove_comments": True,
        "xml_parser_remove_processing_instructions": True,
        "xml_non_element_nodes_normalised": True,
    }
