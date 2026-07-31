from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_lxml_backend_v4.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_secure_lxml_backend_v4", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("XML_SECURE_LXML_BACKEND_V4_IMPORT_FAILED")
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


class _MiscNodeBoundedStructureTarget(previous._NamespaceBoundedStructureTarget):
    """Bound XML comments and processing instructions before discarding them."""

    def __init__(self, limits: dict[str, int]) -> None:
        super().__init__(limits)
        self.comments = 0
        self.total_comment_chars = 0
        self.max_comment_chars_seen = 0
        self.processing_instructions = 0
        self.total_pi_chars = 0
        self.max_pi_target_chars_seen = 0
        self.max_pi_data_chars_seen = 0

    def comment(self, text: str | None) -> None:
        value = "" if text is None else str(text)
        length = len(value)
        self.comments += 1
        if self.comments > self.limits["max_comments"]:
            self._fail(f"XML_COMMENT_COUNT_LIMIT_EXCEEDED:{self.comments}:{self.limits['max_comments']}")
        if length > self.limits["max_comment_chars"]:
            self._fail(f"XML_COMMENT_CHAR_LIMIT_EXCEEDED:{length}:{self.limits['max_comment_chars']}")
        self.total_comment_chars += length
        if self.total_comment_chars > self.limits["max_total_comment_chars"]:
            self._fail(
                f"XML_TOTAL_COMMENT_CHAR_LIMIT_EXCEEDED:{self.total_comment_chars}:{self.limits['max_total_comment_chars']}"
            )
        self.max_comment_chars_seen = max(self.max_comment_chars_seen, length)

    def pi(self, target: str | None, data: str | None) -> None:
        target_value = "" if target is None else str(target)
        data_value = "" if data is None else str(data)
        target_length = len(target_value)
        data_length = len(data_value)
        if target_length <= 0:
            self._fail("XML_PI_TARGET_EMPTY")
        self.processing_instructions += 1
        if self.processing_instructions > self.limits["max_processing_instructions"]:
            self._fail(
                "XML_PI_COUNT_LIMIT_EXCEEDED:"
                f"{self.processing_instructions}:{self.limits['max_processing_instructions']}"
            )
        if target_length > self.limits["max_pi_target_chars"]:
            self._fail(
                f"XML_PI_TARGET_CHAR_LIMIT_EXCEEDED:{target_length}:{self.limits['max_pi_target_chars']}"
            )
        if data_length > self.limits["max_pi_data_chars"]:
            self._fail(f"XML_PI_DATA_CHAR_LIMIT_EXCEEDED:{data_length}:{self.limits['max_pi_data_chars']}")
        self.total_pi_chars += target_length + data_length
        if self.total_pi_chars > self.limits["max_total_pi_chars"]:
            self._fail(f"XML_TOTAL_PI_CHAR_LIMIT_EXCEEDED:{self.total_pi_chars}:{self.limits['max_total_pi_chars']}")
        self.max_pi_target_chars_seen = max(self.max_pi_target_chars_seen, target_length)
        self.max_pi_data_chars_seen = max(self.max_pi_data_chars_seen, data_length)

    def close(self):
        output = super().close()
        return output | {
            "xml_structure_comment_count": self.comments,
            "xml_structure_total_comment_chars": self.total_comment_chars,
            "xml_structure_max_comment_chars": self.max_comment_chars_seen,
            "xml_structure_processing_instruction_count": self.processing_instructions,
            "xml_structure_total_pi_chars": self.total_pi_chars,
            "xml_structure_max_pi_target_chars": self.max_pi_target_chars_seen,
            "xml_structure_max_pi_data_chars": self.max_pi_data_chars_seen,
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
    max_comments: int = 1_000_000,
    max_comment_chars: int = 1 * 1024 * 1024,
    max_total_comment_chars: int = 64 * 1024 * 1024,
    max_processing_instructions: int = 1_000_000,
    max_pi_target_chars: int = 256,
    max_pi_data_chars: int = 1 * 1024 * 1024,
    max_total_pi_chars: int = 64 * 1024 * 1024,
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
        "max_comments": _positive("max_comments", max_comments),
        "max_comment_chars": _positive("max_comment_chars", max_comment_chars),
        "max_total_comment_chars": _positive("max_total_comment_chars", max_total_comment_chars),
        "max_processing_instructions": _positive("max_processing_instructions", max_processing_instructions),
        "max_pi_target_chars": _positive("max_pi_target_chars", max_pi_target_chars),
        "max_pi_data_chars": _positive("max_pi_data_chars", max_pi_data_chars),
        "max_total_pi_chars": _positive("max_total_pi_chars", max_total_pi_chars),
    }
    backend = require_supported_backend()
    lexical = validate_xml_lexical_security(Path(path), chunk_size=limits["chunk_size"])
    target = _MiscNodeBoundedStructureTarget(limits)
    options = _parser_options().copy()
    options["remove_comments"] = False
    options["remove_pis"] = False
    parser = etree.XMLParser(target=target, **options)
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
        "xml_structure_comment_count_limit": limits["max_comments"],
        "xml_structure_comment_char_limit": limits["max_comment_chars"],
        "xml_structure_total_comment_char_limit": limits["max_total_comment_chars"],
        "xml_structure_pi_count_limit": limits["max_processing_instructions"],
        "xml_structure_pi_target_char_limit": limits["max_pi_target_chars"],
        "xml_structure_pi_data_char_limit": limits["max_pi_data_chars"],
        "xml_structure_total_pi_char_limit": limits["max_total_pi_chars"],
        "xml_misc_node_validation_passed": True,
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
        "xml_structure_parser_observes_comments_and_pis": True,
        "xml_non_element_nodes_normalised": True,
    }
