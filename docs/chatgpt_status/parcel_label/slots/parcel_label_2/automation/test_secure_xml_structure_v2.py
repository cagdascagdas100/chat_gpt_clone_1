from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("structure", HERE / "secure_xml_structure_v2.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
checks = 0


def ok(value):
    global checks
    assert value
    checks += 1


def path_for(payload: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
    handle.write(payload)
    handle.close()
    return Path(handle.name)


def accept(payload: bytes, **kwargs):
    path = path_for(payload)
    try:
        return mod.validate_xml_structure(path, **kwargs)
    finally:
        path.unlink(missing_ok=True)


def reject(fragment: str, payload: bytes, **kwargs):
    path = path_for(payload)
    try:
        try:
            mod.validate_xml_structure(path, **kwargs)
        except (RuntimeError, ValueError) as exc:
            ok(fragment in str(exc))
        else:
            raise AssertionError(fragment)
    finally:
        path.unlink(missing_ok=True)


summary = accept(b"<?xml version='1.0' encoding='UTF-8'?><root a='1'><child>abc</child></root>", chunk_size=64)
ok(summary["xml_structure_preflight_passed"])
ok(summary["xml_structure_root_count"] == 1)
ok(summary["xml_structure_element_count"] == 2)
ok(summary["xml_structure_max_depth"] == 2)
ok(summary["xml_structure_total_attributes"] == 1)
ok(summary["xml_structure_max_text_chars_per_element"] == 3)

accept(b"<a><b><c/></b></a>", max_depth=3)
reject("XML_DEPTH_LIMIT_EXCEEDED", b"<a><b><c/></b></a>", max_depth=2)
reject("XML_ELEMENT_LIMIT_EXCEEDED", b"<a><b/><c/></a>", max_elements=2)
reject("XML_ATTRIBUTES_PER_ELEMENT_LIMIT_EXCEEDED", b"<a x='1' y='2'/>", max_attributes_per_element=1)
reject("XML_TOTAL_ATTRIBUTE_LIMIT_EXCEEDED", b"<a x='1'><b y='2'/></a>", max_total_attributes=1)
reject("XML_ATTRIBUTE_VALUE_LIMIT_EXCEEDED", b"<a x='1234'/>", max_attribute_value_chars=3)
reject("XML_TOTAL_ATTRIBUTE_CHAR_LIMIT_EXCEEDED", b"<a x='1234'/>", max_total_attribute_chars=4)
reject("XML_TEXT_NODE_LIMIT_EXCEEDED", b"<a>123456</a>", max_text_chars_per_element=5, chunk_size=64)
reject("XML_ELEMENT_NAME_LIMIT_EXCEEDED", b"<abcdef/>", max_name_chars=5)
reject("XML_ATTRIBUTE_NAME_LIMIT_EXCEEDED", b"<a abcdef='1'/>", max_name_chars=5)
reject("XML_STRUCTURE_PARSE_FAILED", b"<a><b></a>")
reject("XML_STRUCTURE_PARSE_FAILED", b"<a/><b/>")
reject("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!DOCTYPE a><a/>")
reject("XML_ENTITY_DECLARATION_FORBIDDEN", b"<!ENTITY x 'y'><a/>")
reject("must be a positive integer", b"<a/>", max_depth=0)
reject("chunk_size must be at least 64", b"<a/>", chunk_size=32)

print(f"PARCEL_LABEL_2_XML_STRUCTURE_HELPER_TESTS={checks}/{checks}")
print("FINAL_READY=false")
