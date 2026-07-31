from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_lxml_backend_v2.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_secure_lxml_backend_v2", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("XML_SECURE_LXML_BACKEND_V2_IMPORT_FAILED")
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


class _CumulativeTextStructureTarget(previous.previous._StructureTarget):
    """Add cumulative text limits to the existing bounded structure target."""

    def __init__(self, limits: dict[str, int]) -> None:
        super().__init__(limits)
        self.total_text_chars = 0
        self.max_text_chars_per_element_seen = 0
        self._element_text_chars: list[int] = []

    def start(self, tag: str, attrs: dict[str, str]):
        result = super().start(tag, attrs)
        self._element_text_chars.append(0)
        return result

    def data(self, data: str) -> None:
        super().data(data)
        # Formatting-only whitespace between features is not retained as
        # meaningful payload. Coordinate/text values remain fully counted.
        length = len(data) if data.strip() else 0
        if length == 0:
            return
        if not self._element_text_chars:
            self._fail("XML_MEANINGFUL_TEXT_OUTSIDE_ROOT")
        self.total_text_chars += length
        if self.total_text_chars > self.limits["max_total_text_chars"]:
            self._fail(
                f"XML_TOTAL_TEXT_LIMIT_EXCEEDED:{self.total_text_chars}:{self.limits['max_total_text_chars']}"
            )
        current = self._element_text_chars[-1] + length
        self._element_text_chars[-1] = current
        self.max_text_chars_per_element_seen = max(self.max_text_chars_per_element_seen, current)
        if current > self.limits["max_text_chars_per_element"]:
            self._fail(
                f"XML_ELEMENT_TEXT_LIMIT_EXCEEDED:{current}:{self.limits['max_text_chars_per_element']}"
            )

    def end(self, tag: str) -> None:
        if not self._element_text_chars:
            self._fail("XML_TEXT_STACK_UNDERFLOW")
        self._element_text_chars.pop()
        super().end(tag)

    def close(self):
        output = super().close()
        if self._element_text_chars:
            self._fail(f"XML_TEXT_STACK_UNBALANCED:{len(self._element_text_chars)}")
        return output | {
            "xml_structure_total_text_chars": self.total_text_chars,
            "xml_structure_max_text_chars_per_element": self.max_text_chars_per_element_seen,
        }


def _positive(name: str, value: int) -> int:
    return previous.previous._positive(name, value)


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
    }
    backend = require_supported_backend()
    lexical = validate_xml_lexical_security(Path(path), chunk_size=limits["chunk_size"])
    target = _CumulativeTextStructureTarget(limits)
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
