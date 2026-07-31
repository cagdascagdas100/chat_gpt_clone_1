from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("secure_xml", HERE / "secure_xml_preflight_v1.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

checks = 0


def ok(value):
    global checks
    assert value
    checks += 1


def write(payload: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
    handle.write(payload)
    handle.close()
    return Path(handle.name)


def passes(payload: bytes, **kwargs):
    path = write(payload)
    try:
        return module.validate_xml_security(path, **kwargs)
    finally:
        path.unlink(missing_ok=True)


def fails(fragment: str, payload: bytes, **kwargs):
    path = write(payload)
    try:
        try:
            module.validate_xml_security(path, **kwargs)
        except RuntimeError as exc:
            ok(fragment in str(exc))
        else:
            raise AssertionError(f"expected {fragment}")
    finally:
        path.unlink(missing_ok=True)


meta = passes(b"<root/>", expat_version=(2, 6, 0)); ok(meta["xml_security_preflight_passed"])
ok(meta["xml_security_encoding"] == "UTF-8")
ok(meta["xml_security_expat_version"] == "2.6.0")
meta = passes(b"\xef\xbb\xbf<?xml version='1.0' encoding='UTF-8'?><root/>", expat_version=(2, 7, 1)); ok(meta["xml_security_file_size"] > 0)
meta = passes(b"<?xml version='1.0' encoding='utf8'?><root/>", expat_version=(3,)); ok(meta["xml_security_expat_version"] == "3.0.0")
fails("XML_SECURITY_EMPTY_DOCUMENT", b"", expat_version=(2, 6, 0))
fails("XML_EXPAT_VERSION_BELOW_2_6_0", b"<root/>", expat_version=(2, 5, 9))
fails("XML_ENCODING_UTF16_FORBIDDEN", b"\xff\xfe<\x00r\x00/\x00>\x00", expat_version=(2, 6, 0))
fails("XML_ENCODING_UTF32_FORBIDDEN", b"\xff\xfe\x00\x00<\x00\x00\x00", expat_version=(2, 6, 0))
fails("XML_DECLARED_ENCODING_UNSUPPORTED", b"<?xml version='1.0' encoding='ISO-8859-1'?><root/>", expat_version=(2, 6, 0))
fails("XML_NUL_BYTE_FORBIDDEN", b"<root>\x00</root>", expat_version=(2, 6, 0))
fails("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!DOCTYPE root><root/>", expat_version=(2, 6, 0))
fails("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!doctype root><root/>", expat_version=(2, 6, 0))
fails("XML_ENTITY_DECLARATION_FORBIDDEN", b"<!ENTITY x 'y'><root/>", expat_version=(2, 6, 0))
fails("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!-- <!DOCTYPE root> --><root/>", expat_version=(2, 6, 0))
payload = b"<root>" + b"a" * 61 + b"<!DOCTYPE root>" + b"</root>"
fails("XML_DOCTYPE_DECLARATION_FORBIDDEN", payload, expat_version=(2, 6, 0), chunk_size=64)
try:
    passes(b"<root/>", expat_version=(2, 6, 0), chunk_size=32)
except ValueError as exc:
    ok("chunk_size" in str(exc))
else:
    raise AssertionError("expected chunk_size validation")

print(f"PARCEL_LABEL_2_XML_SECURITY_HELPER_TESTS={checks}/{checks}")
print("FINAL_READY=false")
