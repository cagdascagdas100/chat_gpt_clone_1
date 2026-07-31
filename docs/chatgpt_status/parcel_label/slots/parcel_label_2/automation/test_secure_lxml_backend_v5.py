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


legacy = load("secure_lxml_backend_v4_tests", "test_secure_lxml_backend_v4.py")
checks = legacy.checks
backend = load("secure_lxml_backend_v5", "secure_lxml_backend_v5.py")

path = temp(b"<?audit ok?><r><!--alpha--><x/><!--beta--></r><?tail done?>")
try:
    summary = backend.validate_xml_structure(path)
    for value in (
        summary["xml_structure_comment_count"] == 2,
        summary["xml_structure_total_comment_chars"] == 9,
        summary["xml_structure_max_comment_chars"] == 5,
        summary["xml_structure_processing_instruction_count"] == 2,
        summary["xml_structure_total_pi_chars"] == 15,
        summary["xml_structure_max_pi_target_chars"] == 5,
        summary["xml_structure_max_pi_data_chars"] == 4,
        summary["xml_structure_parser_observes_comments_and_pis"] is True,
        summary["xml_parser_remove_comments"] is True,
        summary["xml_parser_remove_processing_instructions"] is True,
    ):
        ok(value)
finally:
    path.unlink(missing_ok=True)

cases = [
    (b"<r><!--a--><!--b--></r>", {"max_comments": 2}, "xml_structure_comment_count", 2, "XML_COMMENT_COUNT_LIMIT_EXCEEDED", {"max_comments": 1}),
    (b"<r><!--abcd--></r>", {"max_comment_chars": 4}, "xml_structure_max_comment_chars", 4, "XML_COMMENT_CHAR_LIMIT_EXCEEDED", {"max_comment_chars": 3}),
    (b"<r><!--abc--><!--def--></r>", {"max_total_comment_chars": 6}, "xml_structure_total_comment_chars", 6, "XML_TOTAL_COMMENT_CHAR_LIMIT_EXCEEDED", {"max_total_comment_chars": 5}),
    (b"<?a x?><r/><?b y?>", {"max_processing_instructions": 2}, "xml_structure_processing_instruction_count", 2, "XML_PI_COUNT_LIMIT_EXCEEDED", {"max_processing_instructions": 1}),
    (b"<?abcd x?><r/>", {"max_pi_target_chars": 4}, "xml_structure_max_pi_target_chars", 4, "XML_PI_TARGET_CHAR_LIMIT_EXCEEDED", {"max_pi_target_chars": 3}),
    (b"<?a abcd?><r/>", {"max_pi_data_chars": 4}, "xml_structure_max_pi_data_chars", 4, "XML_PI_DATA_CHAR_LIMIT_EXCEEDED", {"max_pi_data_chars": 3}),
    (b"<?a bc?><r/><?d ef?>", {"max_total_pi_chars": 6}, "xml_structure_total_pi_chars", 6, "XML_TOTAL_PI_CHAR_LIMIT_EXCEEDED", {"max_total_pi_chars": 5}),
]
for payload, good_args, key, expected_value, fragment, bad_args in cases:
    path = temp(payload)
    try:
        ok(backend.validate_xml_structure(path, **good_args)[key] == expected_value)
        expect(fragment, lambda p=path, a=bad_args: backend.validate_xml_structure(p, **a))
    finally:
        path.unlink(missing_ok=True)

for name in (
    "max_comments",
    "max_comment_chars",
    "max_total_comment_chars",
    "max_processing_instructions",
    "max_pi_target_chars",
    "max_pi_data_chars",
    "max_total_pi_chars",
):
    path = temp(b"<root/>")
    try:
        expect(name, lambda n=name: backend.validate_xml_structure(path, **{n: 0}))
    finally:
        path.unlink(missing_ok=True)

validator = load("validator_v17", "validate_inspire_cadastral_parcel_v17.py")
legacy_gml = load("v9tests_for_misc_bounds", "test_validate_inspire_cadastral_parcel_v9.py")
cp = legacy_gml.cp().replace("<cp:geometry>", "<!--inside--><?audit ok?><cp:geometry>", 1)
xml = ("<?before x?>" + legacy_gml.wfs([cp], "numberReturned='1' numberMatched='1'") + "<?after y?>").encode()
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    for value in (
        len(found[legacy_gml.TARGET]) == 1,
        found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True,
        summary["xml_structure_comment_count"] == 1,
        summary["xml_structure_processing_instruction_count"] == 3,
        summary["xml_misc_node_validation_passed"] is True,
        summary["xml_comment_and_pi_normalisation_passed"] is True,
    ):
        ok(value)
finally:
    path.unlink(missing_ok=True)

predefined = legacy_gml.legacy.predefined().replace("<gml:Polygon", "<!--p--><?audit ok?><gml:Polygon", 1)
predefined_xml = f"<?before x?><ogr:FeatureCollection xmlns:ogr='{legacy_gml.legacy.OGR}' xmlns:gml='{legacy_gml.GML}'><gml:featureMember>{predefined}</gml:featureMember></ogr:FeatureCollection>".encode()
path = temp(predefined_xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    for value in (
        len(found[legacy_gml.TARGET]) == 1,
        found[legacy_gml.TARGET][0]["feature_schema"] == "HMLR_PREDEFINED_FLATTENED",
        summary["xml_structure_comment_count"] == 1,
        summary["xml_structure_processing_instruction_count"] == 2,
    ):
        ok(value)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v30", "bind_inspire_enfield_batch_v30.py")
for value in (
    worker.base.TASK_VERSION == "8.9-lxml-comment-and-processing-instruction-bounds-batch",
    worker.base.parse is worker.validator.parse,
    worker.base.geometry is worker.validator.geometry,
    worker.EXACT_WEB.name == "progress_wave38_exact_result_latest.json",
    worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION,
    worker._POOL is worker.previous._POOL,
    worker._ALLOWED_WRITES == {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()},
):
    ok(value)

print(f"PARCEL_LABEL_2_SECURE_LXML_MISC_NODE_TESTS={checks}/{checks}")
print("FINAL_READY=false")
