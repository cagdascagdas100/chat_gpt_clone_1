from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v7.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v7", VALIDATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V7_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LEGACY_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v6.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v6_tests", LEGACY_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V6_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)

TARGET = legacy.TARGET
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


def polygon(coords: str = "0 0 4 0 4 4 0 0") -> str:
    return f"<gml:Polygon srsName='urn:ogc:def:crs:EPSG::27700'><gml:exterior><gml:LinearRing><gml:posList>{coords}</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon>"


def expect_invalid(record: dict, fragment: str) -> None:
    assert record["geometry_validation_passed"] is False, record
    assert record["coordinate_pair_count"] == 0, record
    assert fragment in str(record), record


def main() -> int:
    assert legacy.main() == 0

    found, _ = parse_body(legacy.legacy.legacy.parcel())
    record = found[TARGET][0]
    assert record["geometry_scope_validation_passed"] is True
    assert record["geometry_root_count"] == 1

    outside = legacy.legacy.legacy.parcel().replace(
        "</cp:CadastralParcel>",
        f"<cp:extension>{polygon('10 10 12 10 12 12 10 10')}</cp:extension></cp:CadastralParcel>",
    )
    found, _ = parse_body(outside)
    expect_invalid(found[TARGET][0], "GEOMETRY_PRIMITIVE_OUTSIDE_ACCEPTED_SCOPE")

    double_property = legacy.legacy.legacy.parcel().replace(
        "</cp:CadastralParcel>",
        f"<cp:geometry>{polygon('10 10 12 10 12 12 10 10')}</cp:geometry></cp:CadastralParcel>",
    )
    found, _ = parse_body(double_property)
    expect_invalid(found[TARGET][0], "INSPIRE_GEOMETRY_PROPERTY_COUNT:2")

    double_root = legacy.legacy.legacy.parcel().replace(
        "</cp:geometry>",
        f"{polygon('10 10 12 10 12 12 10 10')}</cp:geometry>",
        1,
    )
    found, _ = parse_body(double_root)
    expect_invalid(found[TARGET][0], "INSPIRE_GEOMETRY_ROOT_COUNT:2")

    found, _ = parse_body(legacy.predefined())
    record = found[TARGET][0]
    assert record["geometry_scope_validation_passed"] is True

    wrapped = legacy.predefined().replace(
        "<gml:Polygon",
        "<GEOMETRY><gml:Polygon",
        1,
    ).replace("</gml:Polygon>", "</gml:Polygon></GEOMETRY>", 1)
    found, _ = parse_body(wrapped)
    assert found[TARGET][0]["geometry_scope_validation_passed"] is True

    mixed = wrapped.replace("</PREDEFINED>", f"{polygon('10 10 12 10 12 12 10 10')}</PREDEFINED>")
    found, _ = parse_body(mixed)
    expect_invalid(found[TARGET][0], "PREDEFINED_GEOMETRY_SCOPE_MIXED")

    two_direct = legacy.predefined().replace("</PREDEFINED>", f"{polygon('10 10 12 10 12 12 10 10')}</PREDEFINED>")
    found, _ = parse_body(two_direct)
    expect_invalid(found[TARGET][0], "PREDEFINED_DIRECT_GEOMETRY_ROOT_COUNT:2")

    print("PARCEL_LABEL_2_GEOMETRY_SCOPE_TESTS=48/48")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
