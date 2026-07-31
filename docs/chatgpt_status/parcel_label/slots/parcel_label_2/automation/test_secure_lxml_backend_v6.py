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
    global checks, new_checks
    try:
        action()
    except (RuntimeError, ValueError) as exc:
        assert fragment in str(exc), exc
        checks += 1
        new_checks += 1
    else:
        raise AssertionError(f"expected {fragment}")


def ok(value) -> None:
    global checks, new_checks
    assert value
    checks += 1
    new_checks += 1


legacy = load("secure_lxml_backend_v5_tests", "test_secure_lxml_backend_v5.py")
checks = legacy.checks
new_checks = 0
backend = load("secure_lxml_backend_v6", "secure_lxml_backend_v6.py")

path = temp(b"<root><x/><y/></root>")
try:
    summary = backend.validate_xml_structure(path)
    ok(summary["xml_structure_total_element_name_chars"] == len("root") + len("x") + len("y"))
    ok(summary["xml_structure_max_element_name_chars"] == len("root"))
    ok(summary["xml_element_name_cumulative_validation_passed"] is True)
    ok(summary["xml_structure_total_element_name_char_limit"] == 64 * 1024 * 1024)
finally:
    path.unlink(missing_ok=True)

uri = "urn:test"
expanded = f"{{{uri}}}x"
expected_total = len("r") + 2 * len(expanded)
path = temp(f"<r xmlns:a='{uri}'><a:x/><a:x/></r>".encode())
try:
    summary = backend.validate_xml_structure(path, max_total_element_name_chars=expected_total)
    ok(summary["xml_structure_total_element_name_chars"] == expected_total)
    ok(summary["xml_structure_max_element_name_chars"] == len(expanded))
    expect(
        "XML_TOTAL_ELEMENT_NAME_CHAR_LIMIT_EXCEEDED",
        lambda: backend.validate_xml_structure(path, max_total_element_name_chars=expected_total - 1),
    )
finally:
    path.unlink(missing_ok=True)

long_uri = "urn:" + "n" * 900
expanded_long = f"{{{long_uri}}}x"
path = temp((f"<r xmlns:a='{long_uri}'>" + "<a:x/>" * 4 + "</r>").encode())
try:
    total = len("r") + 4 * len(expanded_long)
    ok(backend.validate_xml_structure(path, max_total_element_name_chars=total)["xml_structure_total_element_name_chars"] == total)
    expect(
        "XML_TOTAL_ELEMENT_NAME_CHAR_LIMIT_EXCEEDED",
        lambda: backend.validate_xml_structure(path, max_total_element_name_chars=total - 1),
    )
finally:
    path.unlink(missing_ok=True)

path = temp(b"<root/>")
try:
    expect("max_total_element_name_chars", lambda: backend.validate_xml_structure(path, max_total_element_name_chars=0))
finally:
    path.unlink(missing_ok=True)

path = temp(b"<?audit ok?><r xmlns:a='urn:x'><!--c--><a:x>value</a:x></r>")
try:
    summary = backend.validate_xml_structure(path)
    ok(summary["xml_structure_comment_count"] == 1)
    ok(summary["xml_structure_processing_instruction_count"] == 1)
    ok(summary["xml_structure_total_namespaces"] == 1)
    ok(summary["xml_structure_total_text_chars"] == len("value"))
finally:
    path.unlink(missing_ok=True)

validator = load("validator_v18", "validate_inspire_cadastral_parcel_v18.py")
legacy_gml = load("v9tests_for_element_names", "test_validate_inspire_cadastral_parcel_v9.py")
path = temp(legacy_gml.wfs([legacy_gml.cp()], "numberReturned='1' numberMatched='1'").encode())
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["xml_element_name_cumulative_validation_passed"] is True)
    ok(summary["xml_structure_total_element_name_chars"] > 0)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v31", "bind_inspire_enfield_batch_v31.py")
ok(worker.base.TASK_VERSION == "9.0-lxml-cumulative-expanded-element-name-bounds-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave39_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
ok(worker._ALLOWED_WRITES == {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()})

print(f"PARCEL_LABEL_2_SECURE_LXML_ELEMENT_NAME_TESTS={checks}/{checks}")
print(f"PARCEL_LABEL_2_NEW_ELEMENT_NAME_TESTS={new_checks}/{new_checks}")
print("FINAL_READY=false")
