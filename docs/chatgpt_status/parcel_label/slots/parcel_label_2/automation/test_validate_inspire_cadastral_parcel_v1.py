from __future__ import annotations

import tempfile
from pathlib import Path

import validate_inspire_cadastral_parcel_v1 as module

TARGET = "46058185"


def parcel(reference: str = TARGET, geometry: str | None = None, *, label: str = "x", local_id: str = TARGET) -> str:
    geometry = geometry or """
    <cp:geometry><gml:Polygon srsName='urn:ogc:def:crs:EPSG::27700'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>
    """
    return f"""<cp:CadastralParcel xmlns:cp='urn:cp' xmlns:gml='http://www.opengis.net/gml' xmlns:base='urn:base'>
    <cp:inspireId><base:Identifier><base:localId>{local_id}</base:localId></base:Identifier></cp:inspireId>
    <cp:label>{label}</cp:label><cp:nationalCadastralReference>{reference}</cp:nationalCadastralReference>{geometry}</cp:CadastralParcel>"""


def parse_xml(body: str):
    xml = f"<root xmlns:cp='urn:cp' xmlns:gml='http://www.opengis.net/gml'>{body}</root>"
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
        handle.write(xml.encode())
        path = Path(handle.name)
    try:
        return module.parse(path, {TARGET, "46037757"})
    finally:
        path.unlink(missing_ok=True)


def assert_invalid_geometry(fragment: str, geometry: str) -> None:
    found, _ = parse_xml(parcel(geometry=geometry))
    record = found[TARGET][0]
    assert record["coordinate_pair_count"] == 0, record
    assert fragment in str(record), record


def main() -> int:
    found, summary = parse_xml(parcel())
    record = found[TARGET][0]
    assert record["coordinate_pair_count"] == 4
    assert record["geometry_validation_passed"] is True
    assert record["national_cadastral_reference"] == TARGET
    assert summary["identifier_match_field"] == "nationalCadastralReference"

    found, summary = parse_xml(parcel(reference="999", label=TARGET, local_id=TARGET))
    assert found[TARGET] == []
    assert summary["ignored_non_reference_text_matches"] >= 1

    found, _ = parse_xml(parcel(reference="999", local_id=TARGET))
    assert found[TARGET] == []

    duplicate_refs = parcel().replace(
        f"<cp:nationalCadastralReference>{TARGET}</cp:nationalCadastralReference>",
        f"<cp:nationalCadastralReference>{TARGET}</cp:nationalCadastralReference><cp:nationalCadastralReference>46037757</cp:nationalCadastralReference>",
    )
    try:
        parse_xml(duplicate_refs)
    except RuntimeError as exc:
        assert "CADASTRAL_PARCEL_TARGET_REFERENCE_COUNT:2" in str(exc)
    else:
        raise AssertionError("multiple target references accepted")

    assert_invalid_geometry("LINEAR_RING_NOT_CLOSED", "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 1 1</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_COORDINATE_COUNT_LT_4", "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_ZERO_AREA", "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml'><gml:exterior><gml:LinearRing><gml:posList>0 0 1 0 2 0 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")

    three_d = "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml' srsName='http://www.opengis.net/def/crs/EPSG/0/27700'><gml:exterior><gml:LinearRing srsDimension='3'><gml:posList>0 0 7 2 0 7 2 2 7 0 0 7</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=three_d))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    wrong_crs = "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml' srsName='EPSG:4326'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    assert_invalid_geometry("EPSG:4326", wrong_crs)

    repeated_pos = "<cp:geometry><gml:Surface xmlns:gml='http://www.opengis.net/gml'><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:pos>0 0</gml:pos><gml:pos>2 0</gml:pos><gml:pos>2 2</gml:pos><gml:pos>0 0</gml:pos></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=repeated_pos))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    coordinates = "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml'><gml:exterior><gml:LinearRing><gml:coordinates>0,0 2,0 2,2 0,0</gml:coordinates></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=coordinates))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    valid_with_bad_hole = "<cp:geometry><gml:Polygon xmlns:gml='http://www.opengis.net/gml'><gml:exterior><gml:LinearRing><gml:posList>0 0 4 0 4 4 0 0</gml:posList></gml:LinearRing></gml:exterior><gml:interior><gml:LinearRing><gml:posList>1 1 2 1 1 1</gml:posList></gml:LinearRing></gml:interior></gml:Polygon></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=valid_with_bad_hole))
    record = found[TARGET][0]
    assert record["geometry_validation_passed"] is True
    assert record["invalid_interior_ring_reasons"]

    found, _ = parse_xml(f"<cp:Other xmlns:cp='urn:cp'><cp:nationalCadastralReference>{TARGET}</cp:nationalCadastralReference></cp:Other>")
    assert found[TARGET] == []

    found, _ = parse_xml(parcel() + parcel())
    assert len(found[TARGET]) == 2

    print("PARCEL_LABEL_2_STRICT_GML_PARSER_TESTS=13/13")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
