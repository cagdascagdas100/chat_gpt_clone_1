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


security = load("security_v2", "secure_xml_preflight_v2.py")
ok(security.require_supported_expat((2, 7, 2)) == (2, 7, 2))
ok(security.require_supported_expat((3,)) == (3, 0, 0))
expect("XML_EXPAT_VERSION_BELOW_2_7_2", lambda: security.require_supported_expat((2, 7, 1)))
expect("XML_EXPAT_VERSION_BELOW_2_7_2", lambda: security.require_supported_expat((2, 6, 9)))
actual = security.runtime_expat_version()
ok(actual == tuple(int(v) for v in pyexpat.version_info))
if actual < (2, 7, 2):
    expect("XML_EXPAT_VERSION_BELOW_2_7_2", lambda: security.require_supported_expat())
else:
    ok(security.require_supported_expat() >= (2, 7, 2))

path = temp(b"<?xml version='1.0' encoding='UTF-8'?><root/>")
try:
    summary = security.validate_xml_security(path, expat_version=(2, 7, 2))
    ok(summary["xml_security_preflight_passed"] is True)
    ok(summary["xml_security_minimum_expat_version"] == "2.7.2")
finally:
    path.unlink(missing_ok=True)

for fragment, payload in [
    ("XML_DOCTYPE_DECLARATION_FORBIDDEN", b"<!DOCTYPE root><root/>"),
    ("XML_ENTITY_DECLARATION_FORBIDDEN", b"<!ENTITY x 'y'><root/>"),
    ("XML_NUL_BYTE_FORBIDDEN", b"<root>\x00</root>"),
    ("XML_ENCODING_UTF16_FORBIDDEN", b"\xff\xfe<\x00r\x00/\x00>\x00"),
    ("XML_DECLARED_ENCODING_UNSUPPORTED", b"<?xml version='1.0' encoding='latin1'?><root/>"),
]:
    path = temp(payload)
    try:
        expect(fragment, lambda path=path: security.validate_xml_security(path, expat_version=(2, 7, 2), chunk_size=64))
    finally:
        path.unlink(missing_ok=True)

structure = load("structure_v3", "secure_xml_structure_v3.py")
real_security = structure.security.validate_xml_security
structure.security.validate_xml_security = lambda path, **kwargs: real_security(path, expat_version=(2, 7, 2), **kwargs)
path = temp(b"<root a='1'><child>abc</child></root>")
try:
    result = structure.validate_xml_structure(path, chunk_size=64)
    ok(result["xml_structure_preflight_passed"] is True)
    ok(result["xml_structure_element_count"] == 2)
    ok(result["xml_security_minimum_expat_version"] == "2.7.2")
finally:
    path.unlink(missing_ok=True)

validator = load("validator_v12", "validate_inspire_cadastral_parcel_v12.py")
real_structure = validator.structure.validate_xml_structure
validator.structure.validate_xml_structure = lambda path, **kwargs: (
    setattr(validator.structure.security, "validate_xml_security", lambda source, **inner: real_security(source, expat_version=(2, 7, 2), **inner))
    or real_structure(path, **kwargs)
)
legacy = load("v9tests", "test_validate_inspire_cadastral_parcel_v9.py")
xml = legacy.wfs([legacy.cp()], "numberReturned='1' numberMatched='1'").encode()
path = temp(xml)
try:
    found, result = validator.parse(path, {legacy.TARGET, "46037757"})
    ok(len(found[legacy.TARGET]) == 1)
    ok(result["xml_security_expat_version"] == "2.7.2")
    ok(result["feature_collection_cardinality_validation_passed"] is True)
    ok(result["feature_membership_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v25", "bind_inspire_enfield_batch_v25.py")
ok(worker.base.TASK_VERSION == "8.4-expat-2.7.2-security-floor-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave33_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
allowed = {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()}
ok(worker._ALLOWED_WRITES == allowed)
ok(worker.previous.streaming.normalise_download_file is worker.previous.normalise_download_file)
ok(worker.validator.structure.security._MIN_EXPAT == (2, 7, 2))
ok(worker.validator.validate_collection_cardinality is worker.validator.previous.validate_collection_cardinality)

print(f"PARCEL_LABEL_2_EXPAT_272_SECURITY_TESTS={checks}/{checks}")
print("FINAL_READY=false")
