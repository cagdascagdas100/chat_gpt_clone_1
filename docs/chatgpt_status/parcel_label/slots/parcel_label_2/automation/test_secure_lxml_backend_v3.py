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


legacy = load("secure_lxml_backend_v2_tests", "test_secure_lxml_backend_v2.py")
checks = legacy.checks


def ok(value) -> None:
    global checks
    assert value
    checks += 1


backend = load("secure_lxml_backend_v3", "secure_lxml_backend_v3.py")
options = backend._parser_options()
ok(options["remove_comments"] is True)
ok(options["remove_pis"] is True)
ok(options["huge_tree"] is False)
ok(options["resolve_entities"] is False)

path = temp(b"<root><x>1234<!--split--><?p x?>56789</x></root>")
try:
    expect(
        "XML_ELEMENT_TEXT_LIMIT_EXCEEDED",
        lambda: backend.validate_xml_structure(
            path,
            chunk_size=64,
            max_text_chars_per_segment=64,
            max_text_chars_per_element=8,
            max_total_text_chars=64,
        ),
    )
finally:
    path.unlink(missing_ok=True)

path = temp(b"<root><a>12345</a><b>67890</b></root>")
try:
    expect(
        "XML_TOTAL_TEXT_LIMIT_EXCEEDED",
        lambda: backend.validate_xml_structure(
            path,
            chunk_size=64,
            max_text_chars_per_segment=64,
            max_text_chars_per_element=8,
            max_total_text_chars=9,
        ),
    )
finally:
    path.unlink(missing_ok=True)

path = temp(b"<root>                                                                 <a>x</a>                                                                 </root>")
try:
    summary = backend.validate_xml_structure(
        path,
        chunk_size=64,
        max_text_chars_per_segment=128,
        max_text_chars_per_element=1,
        max_total_text_chars=1,
    )
    ok(summary["xml_structure_total_text_chars"] == 1)
    ok(summary["xml_structure_max_text_chars_per_element"] == 1)
    ok(summary["xml_cumulative_text_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

path = temp(b"<root><a>1234</a><b>5678</b></root>")
try:
    summary = backend.validate_xml_structure(
        path,
        chunk_size=64,
        max_text_chars_per_segment=64,
        max_text_chars_per_element=4,
        max_total_text_chars=8,
    )
    ok(summary["xml_structure_total_text_chars"] == 8)
    ok(summary["xml_structure_max_text_chars_per_element"] == 4)
    ok(summary["xml_structure_text_element_limit"] == 4)
    ok(summary["xml_structure_total_text_limit"] == 8)
finally:
    path.unlink(missing_ok=True)

for name in ("max_text_chars_per_element", "max_total_text_chars"):
    path = temp(b"<root>x</root>")
    try:
        expect(name, lambda n=name: backend.validate_xml_structure(path, **{n: 0}))
    finally:
        path.unlink(missing_ok=True)

validator = load("validator_v15", "validate_inspire_cadastral_parcel_v15.py")
legacy_gml = load("v9tests_for_text_bounds", "test_validate_inspire_cadastral_parcel_v9.py")
xml = legacy_gml.wfs([legacy_gml.cp()], "numberReturned='1' numberMatched='1'").encode()
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["xml_cumulative_text_validation_passed"] is True)
    ok(summary["xml_structure_total_text_chars"] > 0)
    ok(summary["xml_structure_max_text_chars_per_element"] > 0)
    ok(summary["xml_parser_huge_tree"] is False)
finally:
    path.unlink(missing_ok=True)

predefined_xml = f"<ogr:FeatureCollection xmlns:ogr='{legacy_gml.legacy.OGR}' xmlns:gml='{legacy_gml.GML}'><gml:featureMember>{legacy_gml.legacy.predefined()}</gml:featureMember></ogr:FeatureCollection>".encode()
path = temp(predefined_xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["feature_schema"] == "HMLR_PREDEFINED_FLATTENED")
    ok(summary["xml_cumulative_text_validation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v28", "bind_inspire_enfield_batch_v28.py")
ok(worker.base.TASK_VERSION == "8.7-lxml-cumulative-text-bounds-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave36_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
ok(worker._ALLOWED_WRITES == {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()})

print(f"PARCEL_LABEL_2_SECURE_LXML_CUMULATIVE_TEXT_TESTS={checks}/{checks}")
print("FINAL_READY=false")
