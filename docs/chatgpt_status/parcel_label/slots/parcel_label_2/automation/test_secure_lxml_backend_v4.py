from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"TEST_IMPORT_FAILED:{filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def temp(payload: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=".gml", delete=False)
    handle.write(payload)
    handle.close()
    return Path(handle.name)


def expect(fragment: str, action) -> None:
    global checks
    try:
        action()
    except (RuntimeError, ValueError) as exc:
        assert fragment in str(exc), exc
        checks += 1
    else:
        raise AssertionError(f"expected {fragment}")


def ok(value) -> None:
    global checks
    assert value
    checks += 1


legacy = load("secure_lxml_backend_v3_tests", "test_secure_lxml_backend_v3.py")
checks = legacy.checks
backend = load("secure_lxml_backend_v4", "secure_lxml_backend_v4.py")

path = temp(b"<r xmlns='urn:d' xmlns:a='urn:a'><a:x/></r>")
try:
    summary = backend.validate_xml_structure(path)
    ok(summary["xml_structure_total_namespaces"] == 2)
    ok(summary["xml_structure_max_namespaces_per_element"] == 2)
    ok(summary["xml_structure_total_namespace_chars"] == len("urn:d") + len("a") + len("urn:a"))
    ok(summary["xml_namespace_declaration_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

path = temp(b"<r xmlns:a='urn:a' xmlns:b='urn:b'><a:x/></r>")
try:
    expect("XML_NAMESPACES_PER_ELEMENT_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_namespaces_per_element=1))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<r xmlns:a='urn:a'><x xmlns:b='urn:b'/></r>")
try:
    expect("XML_TOTAL_NAMESPACE_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_total_namespaces=1))
finally:
    path.unlink(missing_ok=True)

prefix = "p" * 9
path = temp(f"<r xmlns:{prefix}='urn:a'/>>".replace('/>>','/>').encode())
try:
    expect("XML_NAMESPACE_PREFIX_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_namespace_prefix_chars=8))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<r xmlns:a='urn:123456789'/>")
try:
    expect("XML_NAMESPACE_URI_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_namespace_uri_chars=8))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<r xmlns:a='urn:a'><x xmlns:b='urn:b'/></r>")
try:
    expect("XML_TOTAL_NAMESPACE_CHAR_LIMIT_EXCEEDED", lambda: backend.validate_xml_structure(path, max_total_namespace_chars=10))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<r xmlns:a='urn:a'><x xmlns:a='urn:b'><a:y/></x></r>")
try:
    summary = backend.validate_xml_structure(path, max_namespaces_per_element=1, max_total_namespaces=2, max_namespace_prefix_chars=1, max_namespace_uri_chars=5, max_total_namespace_chars=12)
    ok(summary["xml_structure_total_namespaces"] == 2)
    ok(summary["xml_structure_max_namespace_prefix_chars"] == 1)
    ok(summary["xml_structure_max_namespace_uri_chars"] == 5)
finally:
    path.unlink(missing_ok=True)

for name in ("max_namespaces_per_element", "max_total_namespaces", "max_namespace_prefix_chars", "max_namespace_uri_chars", "max_total_namespace_chars"):
    path = temp(b"<root/>")
    try:
        expect(name, lambda n=name: backend.validate_xml_structure(path, **{n: 0}))
    finally:
        path.unlink(missing_ok=True)

validator = load("validator_v16", "validate_inspire_cadastral_parcel_v16.py")
legacy_gml = load("v9tests_for_namespace_bounds", "test_validate_inspire_cadastral_parcel_v9.py")
xml = legacy_gml.wfs([legacy_gml.cp()], "numberReturned='1' numberMatched='1'").encode()
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["xml_namespace_declaration_validation_passed"] is True)
    ok(summary["xml_structure_total_namespaces"] > 0)
    ok(summary["xml_structure_max_namespaces_per_element"] > 0)
finally:
    path.unlink(missing_ok=True)

predefined_xml = f"<ogr:FeatureCollection xmlns:ogr='{legacy_gml.legacy.OGR}' xmlns:gml='{legacy_gml.GML}'><gml:featureMember>{legacy_gml.legacy.predefined()}</gml:featureMember></ogr:FeatureCollection>".encode()
path = temp(predefined_xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["feature_schema"] == "HMLR_PREDEFINED_FLATTENED")
    ok(summary["xml_namespace_declaration_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v29", "bind_inspire_enfield_batch_v29.py")
ok(worker.base.TASK_VERSION == "8.8-lxml-namespace-declaration-bounds-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave37_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
ok(worker._ALLOWED_WRITES == {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()})

print(f"PARCEL_LABEL_2_SECURE_LXML_NAMESPACE_TESTS={checks}/{checks}")
print("FINAL_READY=false")
