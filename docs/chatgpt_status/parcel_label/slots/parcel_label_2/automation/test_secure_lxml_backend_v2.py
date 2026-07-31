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


legacy = load("secure_lxml_backend_v1_tests", "test_secure_lxml_backend_v1.py")
checks = legacy.checks


def ok(value):
    global checks
    assert value
    checks += 1


backend = load("secure_lxml_backend_v2", "secure_lxml_backend_v2.py")
options = backend._parser_options()
ok(options["remove_comments"] is True)
ok(options["remove_pis"] is True)
ok(options["load_dtd"] is False)
ok(options["resolve_entities"] is False)
ok(options["no_network"] is True)
ok(options["huge_tree"] is False)
ok(options["recover"] is False)

xml = b"<?xml version='1.0' encoding='UTF-8'?><root><!--outer--><?outer test?><child><!--inner--><?inner x?>ok</child></root>"
path = temp(xml)
try:
    summary = backend.validate_xml_structure(path, chunk_size=64)
    ok(summary["xml_parser_remove_comments"] is True)
    ok(summary["xml_parser_remove_processing_instructions"] is True)
    ok(summary["xml_non_element_nodes_normalised"] is True)
    nodes = [element for _event, element in backend.secure_iterparse(path, events=("end",))]
    ok(all(isinstance(node.tag, str) for node in nodes))
    ok([node.tag for node in nodes] == ["child", "root"])
finally:
    path.unlink(missing_ok=True)

validator = load("validator_v14", "validate_inspire_cadastral_parcel_v14.py")
legacy_gml = load("v9tests_for_comment_pi", "test_validate_inspire_cadastral_parcel_v9.py")
cp = legacy_gml.cp().replace(
    "<cp:CadastralParcel",
    "<!--before-feature--><?feature start?><cp:CadastralParcel",
    1,
).replace(
    "<cp:geometry>",
    "<cp:geometry><!--inside-geometry--><?geometry ok?>",
    1,
)
xml = legacy_gml.wfs([cp], "numberReturned='1' numberMatched='1'").replace(
    "<wfs:FeatureCollection",
    "<?collection safe?><wfs:FeatureCollection",
    1,
).encode()
path = temp(xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["feature_membership_validation_passed"] is True)
    ok(summary["feature_collection_cardinality_validation_passed"] is True)
    ok(summary["xml_comment_and_pi_normalisation_passed"] is True)
    ok(summary["xml_parser_remove_comments"] is True)
    ok(summary["xml_parser_remove_processing_instructions"] is True)
finally:
    path.unlink(missing_ok=True)

predefined = legacy_gml.legacy.predefined().replace(
    "<PREDEFINED",
    "<!--before-predefined--><?predefined start?><PREDEFINED",
    1,
).replace(
    "<gml:Polygon",
    "<!--before-polygon--><?polygon safe?><gml:Polygon",
    1,
)
predefined_xml = f"<ogr:FeatureCollection xmlns:ogr='{legacy_gml.legacy.OGR}' xmlns:gml='{legacy_gml.GML}'><gml:featureMember>{predefined}</gml:featureMember></ogr:FeatureCollection>".encode()
path = temp(predefined_xml)
try:
    found, summary = validator.parse(path, {legacy_gml.TARGET, "46037757"})
    ok(len(found[legacy_gml.TARGET]) == 1)
    ok(found[legacy_gml.TARGET][0]["feature_schema"] == "HMLR_PREDEFINED_FLATTENED")
    ok(found[legacy_gml.TARGET][0]["geometry_validation_passed"] is True)
    ok(summary["xml_comment_and_pi_normalisation_passed"] is True)
finally:
    path.unlink(missing_ok=True)

worker = load("worker_v27", "bind_inspire_enfield_batch_v27.py")
ok(worker.base.TASK_VERSION == "8.6-lxml-comment-and-processing-instruction-normalisation-batch")
ok(worker.base.parse is worker.validator.parse)
ok(worker.base.geometry is worker.validator.geometry)
ok(worker.EXACT_WEB.name == "progress_wave35_exact_result_latest.json")
ok(worker.previous.base.TASK_VERSION == worker.base.TASK_VERSION)
ok(worker._POOL is worker.previous._POOL)
ok(worker._ALLOWED_WRITES == {worker.base.RESULT.resolve(), worker.base.RECON.resolve(), worker.EXACT_WEB.resolve()})

print(f"PARCEL_LABEL_2_SECURE_LXML_NORMALISATION_TESTS={checks}/{checks}")
print("FINAL_READY=false")
