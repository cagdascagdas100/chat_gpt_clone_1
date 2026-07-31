from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("secure_lxml_backend_v1.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_secure_lxml_backend_v1", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("XML_SECURE_LXML_BACKEND_V1_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

etree = previous.etree
runtime_versions = previous.runtime_versions
require_supported_backend = previous.require_supported_backend
validate_xml_lexical_security = previous.validate_xml_lexical_security
_original_parser_options = previous._parser_options


def _parser_options() -> dict:
    """Preserve every v1 security option and discard non-element nodes."""
    options = _original_parser_options().copy()
    options["remove_comments"] = True
    options["remove_pis"] = True
    return options


# v1 functions resolve this name from their module globals at call time.
previous._parser_options = _parser_options


def secure_iterparse(path: Path, *, events=("end",)):
    require_supported_backend()
    options = _parser_options().copy()
    options.pop("decompress", None)
    return etree.iterparse(str(Path(path)), events=events, **options)


# Ensure any v1 adapter references that survive an import use the normalised parser.
previous.secure_iterparse = secure_iterparse


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


def validate_xml_structure(path: Path, **kwargs) -> dict:
    output = previous.validate_xml_structure(path, **kwargs)
    return output | {
        "xml_parser_remove_comments": True,
        "xml_parser_remove_processing_instructions": True,
        "xml_non_element_nodes_normalised": True,
    }
