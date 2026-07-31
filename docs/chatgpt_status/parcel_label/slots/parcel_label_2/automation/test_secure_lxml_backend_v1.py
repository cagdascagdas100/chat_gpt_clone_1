from __future__ import annotations

import importlib.util
import pyexpat
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
checks = 0


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"TEST_IMPORT_FAILED:{filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ok(value):
    global checks
    assert value
    checks += 1


def temp(payload: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
    handle.write(payload)
    handle.close()
    return Path(handle.name)


def expect(fragment: str, call):
    try:
        call()
    except (RuntimeError, ValueError) as exc:
        ok(fragment in str(exc))
    else:
        raise AssertionError(fragment)


backend = load("secure_lxml_backend", "secure_lxml_backend_v1.py")
versions = backend.require_supported_backend()
ok(versions["xml_backend"] == "lxml.etree/libxml2")
ok(versions["xml_backend_runtime_compiled_match"] is True)
ok(versions["xml_backend_lxml_version"].startswith("6.1.1"))
ok(versions["xml_backend_libxml_runtime_version"] == "2.14.6")
expect("XML_LXML_VERSION_BELOW_6_1_0", lambda: backend.require_supported_backend(lxml_version=(6, 0, 9, 0)))
expect("XML_LIBXML_RUNTIME_BELOW_2_14_0", lambda: backend.require_supported_backend(libxml_runtime=(2, 13, 9)))
expect(
    "XML_LIBXML_RUNTIME_COMPILED_MISMATCH",
    lambda: backend.require_supported_backend(libxml_runtime=(2, 14, 6), libxml_compiled=(2, 14, 5)),
)
ok(tuple(int(v) for v in pyexpat.version_info) == (2, 7, 1))

p = temp(b"<?xml version='1.0' encoding='UTF-8'?><root a='1'><child>abc</child></root>")
try:
    result = backend.validate_xml_structure(p, chunk_size=64)
    ok(result["xml_structure_preflight_passed"] is True)
    ok(result["xml_structure_element_count"] == 2)
    ok(result["xml_parser_load_dtd"] is False)
    ok(result["xml_parser_resolve_entities"] is False)
    ok(result["xml_parser_no_network"] is True)
    ok(result["xml_parser_huge_tree"] is False)
    ok(result["xml_parser_recover"] is False)
    ok(result["xml_parser_decompress"] is False)
finally:
    p.unlink(missing_ok=True)

for fragment, payload in [
    ("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!DOCTYPE root><root/>"),
    ("XML_ENTITY_DECLARATION_FORBIDDEN", b"<!ENTITY x 'y'><root/>"),
    ("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!DOCTYPE root [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><root>&x;</root>"),
    ("XML_NUL_BYTE_FORBIDDEN", b"<root>\x00</root>"),
    ("XML_ENCODING_UTF16_FORBIDDEN", b"\xff\xfe<\x00r\x00/\x00>\x00"),
    ("XML_DECLARED_ENCODING_UNSUPPORTED", b"<?xml version='1.0' encoding='latin1'?><root/>"),
]:
    path = temp(payload)
    try:
        expect(fragment, lambda path=path: backend.validate_xml_structure(path, chunk_size=64))
    finally:
        path.unlink(missing_ok=True)

path = temp(("<r>" * 6 + "x" + "</r>" * 6).encode())
try:
    expect("XML_DEPTH_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_depth=5, chunk_size=64))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<root>abcdefgh</root>")
try:
    expect("XML_TEXT_SEGMENT_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_text_chars_per_segment=4, chunk_size=64))
finally:
    path.unlink(missing_ok=True)

validator = load("validator_v13", "validate_inspire_cadastral_parcel_v13.py")
ok(len(validator._patched_modules) >= 6)
current = validator.previous
patched_seen = 0
seen = set()
while current is not None and id(current) not in seen:
    seen.add(id(current))
    if hasattr(current, "ET"):
        ok(current.ET is validator.backend.ADAPTER)
        patched_seen += 1
    current = getattr(current, "previous", None)
ok(patched_seen >= 6)
legacy = load("v9tests", "test_validate_inspire_cadastral_parcel_v9.py")
xml = legacy.wfs([legacy.cp()], "numberReturned='1' numberMatched='1'").encode()
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy.TARGET, "46037757"})
    ok(len(found[legacy.TARGET]) == 1)
    ok(summary["feature_membership_validation_passed"] is True)
    ok(summary["feature_collection_cardinality_validation_passed"] is True)
    ok(summary["xml_backend_expat_required"] is False)
    ok(summary["xml_backend_lxml_version"].startswith("6.1.1"))
    ok(summary["xml_backend_libxml_runtime_version"] == "2.14.6")
    ok(summary["xml_security_doctype_forbidden"] is True)
    ok(summary["geometry_validation_passed"] if "geometry_validation_passed" in summary else True)
finally:
    path.unlink(missing_ok=True)

# Prove the accepted parse path does not call the vulnerable Expat backend.
original_parser_create = pyexpat.ParserCreate
pyexpat.ParserCreate = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("EXPAT_MUST_NOT_BE_CALLED"))
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy.TARGET, "46037757"})
    ok(len(found[legacy.TARGET]) == 1)
    ok(summary["xml_backend_expat_required"] is False)
finally:
    pyexpat.ParserCreate = original_parser_create
    path.unlink(missing_ok=True)

# PREDEFINED compatibility remains valid through the lxml backend.
predefined_xml = f"<ogr:FeatureCollection xmlns:ogr='{legacy.legacy.OGR}' xmlns:gml='{legacy.GML}'><gml:featureMember>{legacy.legacy.predefined()}</gml:featureMember></ogr:FeatureCollection>".encode()
path = temp(predefined_xml)
try:
    found, summary = validator.parse(path, {legacy.TARGET, "46037757"})
    ok(len(found[legacy.TARGET]) == 1)
    ok(found[legacy.TARGET][0]["feature_schema"] == "HMLR_PREDEFINED_FLATTENED")
    ok(found[legacy.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["feature_membership_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

# Orphan features and cardinality mismatches remain fail-closed.
path = temp(f"<root xmlns:cp='{legacy.CP}' xmlns:gml='{legacy.GML}'>{legacy.cp()}</root>".encode())
try:
    expect("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED", lambda: validator.parse(path, {legacy.TARGET}))
finally:
    path.unlink(missing_ok=True)

path = temp(legacy.wfs([legacy.cp()], "numberReturned='2' numberMatched='2'").encode())
try:
    expect("FEATURE_COLLECTION_NUMBERRETURNED_MISMATCH", lambda: validator.parse(path, {legacy.TARGET}))
finally:
    path.unlink(missing_ok=True)

invalid_polygon = legacy.cp().replace("0 0 2 0 2 2 0 0", "0 0 2 0 2 2 1 1")
path = temp(legacy.wfs([invalid_polygon], "numberReturned='1' numberMatched='1'").encode())
try:
    found, _summary = validator.parse(path, {legacy.TARGET})
    ok(found[legacy.TARGET][0]["geometry_validation_passed"] is False)
    ok(found[legacy.TARGET][0]["coordinate_pair_count"] == 0)
finally:
    path.unlink(missing_ok=True)


worker = load("worker_v26", "bind_inspire_enfield_batch_v26.py")
ok(worker.base.TASK_VERSION == "8.5-secure-lxml-libxml2-backend-fallback-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave34_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
for target in worker._ALLOWED_WRITES:
    ok(target in {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()})

print(f"PARCEL_LABEL_2_SECURE_LXML_BACKEND_TESTS={checks}/{checks}")
print("FINAL_READY=false")
