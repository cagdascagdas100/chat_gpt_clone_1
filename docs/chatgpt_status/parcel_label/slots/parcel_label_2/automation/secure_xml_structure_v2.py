from __future__ import annotations

import importlib.util
import pyexpat
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_xml_preflight_v1.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_xml_security_v1", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_SECURITY_V1_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


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
    max_text_chars_per_element: int = 32 * 1024 * 1024,
    max_name_chars: int = 1024,
) -> dict:
    """Fail-closed structural preflight without materialising an XML tree."""
    limits = {
        "chunk_size": _positive("chunk_size", chunk_size),
        "max_depth": _positive("max_depth", max_depth),
        "max_elements": _positive("max_elements", max_elements),
        "max_attributes_per_element": _positive("max_attributes_per_element", max_attributes_per_element),
        "max_total_attributes": _positive("max_total_attributes", max_total_attributes),
        "max_attribute_value_chars": _positive("max_attribute_value_chars", max_attribute_value_chars),
        "max_total_attribute_chars": _positive("max_total_attribute_chars", max_total_attribute_chars),
        "max_text_chars_per_element": _positive("max_text_chars_per_element", max_text_chars_per_element),
        "max_name_chars": _positive("max_name_chars", max_name_chars),
    }
    security = previous.validate_xml_security(Path(path), chunk_size=limits["chunk_size"])

    parser = pyexpat.ParserCreate(encoding="UTF-8")
    parser.buffer_text = False
    depth = 0
    max_depth_seen = 0
    elements = 0
    total_attributes = 0
    total_attribute_chars = 0
    max_attributes_seen = 0
    max_text_seen = 0
    root_count = 0
    text_stack: list[int] = []

    def reject_doctype(*_args):
        raise RuntimeError("XML_DOCTYPE_DECLARATION_FORBIDDEN")

    def reject_entity(*_args):
        raise RuntimeError("XML_ENTITY_DECLARATION_FORBIDDEN")

    def reject_external(*_args):
        raise RuntimeError("XML_EXTERNAL_ENTITY_REFERENCE_FORBIDDEN")

    def start(name: str, attrs: dict[str, str]) -> None:
        nonlocal depth, max_depth_seen, elements, total_attributes
        nonlocal total_attribute_chars, max_attributes_seen, root_count
        if len(name) > limits["max_name_chars"]:
            raise RuntimeError(f"XML_ELEMENT_NAME_LIMIT_EXCEEDED:{len(name)}")
        depth += 1
        if depth == 1:
            root_count += 1
            if root_count > 1:
                raise RuntimeError("XML_ROOT_ELEMENT_COUNT_NOT_ONE")
        if depth > limits["max_depth"]:
            raise RuntimeError(f"XML_DEPTH_LIMIT_EXCEEDED:{depth}:{limits['max_depth']}")
        max_depth_seen = max(max_depth_seen, depth)
        elements += 1
        if elements > limits["max_elements"]:
            raise RuntimeError(f"XML_ELEMENT_LIMIT_EXCEEDED:{elements}:{limits['max_elements']}")
        attribute_count = len(attrs)
        if attribute_count > limits["max_attributes_per_element"]:
            raise RuntimeError(
                f"XML_ATTRIBUTES_PER_ELEMENT_LIMIT_EXCEEDED:{attribute_count}:{limits['max_attributes_per_element']}"
            )
        max_attributes_seen = max(max_attributes_seen, attribute_count)
        total_attributes += attribute_count
        if total_attributes > limits["max_total_attributes"]:
            raise RuntimeError(
                f"XML_TOTAL_ATTRIBUTE_LIMIT_EXCEEDED:{total_attributes}:{limits['max_total_attributes']}"
            )
        for key, value in attrs.items():
            if len(key) > limits["max_name_chars"]:
                raise RuntimeError(f"XML_ATTRIBUTE_NAME_LIMIT_EXCEEDED:{len(key)}")
            if len(value) > limits["max_attribute_value_chars"]:
                raise RuntimeError(
                    f"XML_ATTRIBUTE_VALUE_LIMIT_EXCEEDED:{len(value)}:{limits['max_attribute_value_chars']}"
                )
            total_attribute_chars += len(key) + len(value)
            if total_attribute_chars > limits["max_total_attribute_chars"]:
                raise RuntimeError(
                    f"XML_TOTAL_ATTRIBUTE_CHAR_LIMIT_EXCEEDED:{total_attribute_chars}:{limits['max_total_attribute_chars']}"
                )
        text_stack.append(0)

    def character(data: str) -> None:
        nonlocal max_text_seen
        if not text_stack:
            if data.strip():
                raise RuntimeError("XML_CHARACTER_DATA_OUTSIDE_ROOT")
            return
        text_stack[-1] += len(data)
        if text_stack[-1] > limits["max_text_chars_per_element"]:
            raise RuntimeError(
                f"XML_TEXT_NODE_LIMIT_EXCEEDED:{text_stack[-1]}:{limits['max_text_chars_per_element']}"
            )
        max_text_seen = max(max_text_seen, text_stack[-1])

    def end(_name: str) -> None:
        nonlocal depth
        if depth <= 0 or not text_stack:
            raise RuntimeError("XML_STRUCTURE_STACK_UNDERFLOW")
        text_stack.pop()
        depth -= 1

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = character
    parser.StartDoctypeDeclHandler = reject_doctype
    parser.EntityDeclHandler = reject_entity
    parser.ExternalEntityRefHandler = reject_external
    parser.SkippedEntityHandler = reject_external

    source = Path(path)
    try:
        with source.open("rb") as handle:
            while True:
                chunk = handle.read(limits["chunk_size"])
                if not chunk:
                    break
                parser.Parse(chunk, False)
        parser.Parse(b"", True)
    except RuntimeError:
        raise
    except pyexpat.ExpatError as exc:
        raise RuntimeError(
            f"XML_STRUCTURE_PARSE_FAILED:{exc.code}:{exc.lineno}:{exc.offset}:{exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"XML_STRUCTURE_SOURCE_READ_FAILED:{source}") from exc

    if root_count != 1:
        raise RuntimeError(f"XML_ROOT_ELEMENT_COUNT_NOT_ONE:{root_count}")
    if depth != 0 or text_stack:
        raise RuntimeError(f"XML_STRUCTURE_UNBALANCED:{depth}:{len(text_stack)}")
    if elements <= 0:
        raise RuntimeError("XML_STRUCTURE_NO_ELEMENTS")

    return security | {
        "xml_structure_preflight_passed": True,
        "xml_structure_root_count": root_count,
        "xml_structure_element_count": elements,
        "xml_structure_max_depth": max_depth_seen,
        "xml_structure_total_attributes": total_attributes,
        "xml_structure_max_attributes_per_element": max_attributes_seen,
        "xml_structure_total_attribute_chars": total_attribute_chars,
        "xml_structure_max_text_chars_per_element": max_text_seen,
        "xml_structure_depth_limit": limits["max_depth"],
        "xml_structure_element_limit": limits["max_elements"],
        "xml_structure_attribute_limit_per_element": limits["max_attributes_per_element"],
        "xml_structure_text_limit_per_element": limits["max_text_chars_per_element"],
    }
