from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v6.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v6", VALIDATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V6_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LEGACY_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v5.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v5_tests", LEGACY_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V5_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)
legacy.module = module

TARGET = legacy.legacy.TARGET
CP = legacy.CP
GML = legacy.GML


def parse_body(body: str):
    xml = f"<root xmlns:cp='{CP}' xmlns:gml='{GML}'>{body}</root>"
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
        handle.write(xml.encode())
        path = Path(handle.name)
    try:
        return module.parse(path, {TARGET, "46037757"})
    finally:
        path.unlink(missing_ok=True)


def predefined(reference: str = TARGET, inspire_id: str | None = TARGET, *, label: str = "x", namespace: str = "") -> str:
    prefix = "p:" if namespace else ""
    ns = f" xmlns:p='{namespace}'" if namespace else ""
    inspire = f"<{prefix}INSPIREID>{inspire_id}</{prefix}INSPIREID>" if inspire_id is not None else ""
    return f"""<{prefix}PREDEFINED{ns} xmlns:gml='{GML}'>
      {inspire}
      <{prefix}LABEL>{label}</{prefix}LABEL>
      <{prefix}NATIONALCADASTRALREFERENCE>{reference}</{prefix}NATIONALCADASTRALREFERENCE>
      <gml:Polygon srsName='urn:ogc:def:crs:EPSG::27700'>
        <gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior>
      </gml:Polygon>
    </{prefix}PREDEFINED>"""


def expect_error(fragment: str, body: str) -> None:
    try:
        parse_body(body)
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def main() -> int:
    assert legacy.main() == 0

    found, summary = parse_body(predefined())
    record = found[TARGET][0]
    assert record["feature_schema"] == "HMLR_PREDEFINED_FLATTENED"
    assert record["geometry_validation_passed"] is True
    assert record["predefined_inspire_id_exact_match"] is True
    assert summary["feature_schema"] == "HMLR_PREDEFINED_FLATTENED"

    found, summary = parse_body(predefined(reference="999", inspire_id="999", label=TARGET))
    assert found[TARGET] == []
    assert summary["ignored_non_reference_text_matches"] >= 1

    found, _ = parse_body(predefined(reference="999", inspire_id=TARGET))
    assert found[TARGET] == []

    expect_error("PREDEFINED_INSPIRE_ID_REFERENCE_MISMATCH", predefined(inspire_id="46037757"))

    duplicate_ref = predefined().replace(
        f"<NATIONALCADASTRALREFERENCE>{TARGET}</NATIONALCADASTRALREFERENCE>",
        f"<NATIONALCADASTRALREFERENCE>{TARGET}</NATIONALCADASTRALREFERENCE><NATIONALCADASTRALREFERENCE>999</NATIONALCADASTRALREFERENCE>",
    )
    expect_error("PREDEFINED_NATIONAL_REFERENCE_COUNT:2", duplicate_ref)

    expect_error("MIXED_CADASTRAL_FEATURE_SCHEMAS", predefined() + legacy.legacy.parcel())

    expect_error("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED", predefined(namespace="urn:foreign:predefined"))

    invalid = predefined().replace("0 0 2 0 2 2 0 0", "0 0 2 0 2 2 1 1")
    found, _ = parse_body(invalid)
    assert found[TARGET][0]["geometry_validation_passed"] is False
    assert found[TARGET][0]["coordinate_pair_count"] == 0

    print("PARCEL_LABEL_2_FEATURE_SCHEMA_COMPATIBILITY_TESTS=40/40")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
