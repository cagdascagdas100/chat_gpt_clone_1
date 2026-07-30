from __future__ import annotations

import tempfile
from pathlib import Path

import validate_inspire_cadastral_parcel_v2 as module

TARGET = "46058185"
CP = "http://inspire.ec.europa.eu/schemas/cp/4.0"
BASE = "http://inspire.ec.europa.eu/schemas/base/3.3"
GML = "http://www.opengis.net/gml/3.2"


def parcel(reference: str = TARGET, geometry: str | None = None, *, label: str = "x", local_id: str = TARGET, cp_ns: str = CP, ref_ns: str | None = None) -> str:
    ref_ns = ref_ns or cp_ns
    geometry = geometry or f"""
    <cp:geometry><gml:Polygon srsName='urn:ogc:def:crs:EPSG::27700'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>
    """
    return f"""<cp:CadastralParcel xmlns:cp='{cp_ns}' xmlns:ref='{ref_ns}' xmlns:gml='{GML}' xmlns:base='{BASE}'>
    <cp:inspireId><base:Identifier><base:localId>{local_id}</base:localId></base:Identifier></cp:inspireId>
    <cp:label>{label}</cp:label><ref:nationalCadastralReference>{reference}</ref:nationalCadastralReference>{geometry}</cp:CadastralParcel>"""


def parse_xml(body: str):
    xml = f"<root xmlns:cp='{CP}' xmlns:gml='{GML}'>{body}</root>"
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
    assert record["geometry_validation_passed"] is False


def main() -> int:
    found, summary = parse_xml(parcel())
    record = found[TARGET][0]
    assert record["coordinate_pair_count"] == 4
    assert record["geometry_validation_passed"] is True
    assert record["national_cadastral_reference"] == TARGET
    assert record["feature_namespace"] == CP
    assert summary["identifier_match_field"] == "nationalCadastralReference"

    found, summary = parse_xml(parcel(reference="999", label=TARGET, local_id=TARGET))
    assert found[TARGET] == []
    assert summary["ignored_non_reference_text_matches"] >= 1

    found, _ = parse_xml(parcel(reference="999", local_id=TARGET))
    assert found[TARGET] == []

    found, summary = parse_xml(parcel(cp_ns="urn:fake:cp"))
    assert found[TARGET] == []
    assert summary["ignored_wrong_namespace_parcels"] == 1

    found, summary = parse_xml(parcel(ref_ns="urn:fake:cp"))
    assert found[TARGET] == []
    assert summary["ignored_wrong_namespace_references"] == 1

    duplicate_refs = parcel().replace(
        f"<ref:nationalCadastralReference>{TARGET}</ref:nationalCadastralReference>",
        f"<ref:nationalCadastralReference>{TARGET}</ref:nationalCadastralReference><ref:nationalCadastralReference>46037757</ref:nationalCadastralReference>",
    )
    try:
        parse_xml(duplicate_refs)
    except RuntimeError as exc:
        assert "CADASTRAL_PARCEL_TARGET_REFERENCE_COUNT:2" in str(exc)
    else:
        raise AssertionError("multiple target references accepted")

    assert_invalid_geometry("LINEAR_RING_NOT_CLOSED", f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 1 1</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_COORDINATE_COUNT_LT_4", f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_ZERO_AREA", f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 1 0 2 0 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_ZERO_LENGTH_SEGMENT", f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")
    assert_invalid_geometry("LINEAR_RING_SELF_INTERSECTION", f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 4 4 0 4 3 0 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>")

    three_d = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}' srsName='http://www.opengis.net/def/crs/EPSG/0/27700'><gml:exterior><gml:LinearRing srsDimension='3'><gml:posList>0 0 7 2 0 7 2 2 7 0 0 7</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=three_d))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    wrong_crs = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}' srsName='EPSG:4326'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    assert_invalid_geometry("EPSG:4326", wrong_crs)

    repeated_pos = f"<cp:geometry xmlns:cp='{CP}'><gml:Surface xmlns:gml='{GML}'><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:pos>0 0</gml:pos><gml:pos>2 0</gml:pos><gml:pos>2 2</gml:pos><gml:pos>0 0</gml:pos></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=repeated_pos))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    coordinates = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:coordinates>0,0 2,0 2,2 0,0</gml:coordinates></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    found, _ = parse_xml(parcel(geometry=coordinates))
    assert found[TARGET][0]["coordinate_pair_count"] == 4

    valid_with_bad_hole = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 4 0 4 4 0 0</gml:posList></gml:LinearRing></gml:exterior><gml:interior><gml:LinearRing><gml:posList>1 1 2 1 1 1</gml:posList></gml:LinearRing></gml:interior></gml:Polygon></cp:geometry>"
    assert_invalid_geometry("invalid_interior_reasons", valid_with_bad_hole)

    two_exteriors = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior><gml:exterior><gml:LinearRing><gml:posList>3 3 4 3 4 4 3 3</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    assert_invalid_geometry("'exterior_ring_count': 2", two_exteriors)

    foreign_gml = f"<cp:geometry xmlns:cp='{CP}'><fake:Polygon xmlns:fake='urn:fake:gml'><fake:exterior><fake:LinearRing><fake:posList>0 0 2 0 2 2 0 0</fake:posList></fake:LinearRing></fake:exterior></fake:Polygon></cp:geometry>"
    assert_invalid_geometry("foreign_geometry_tags", foreign_gml)

    found, _ = parse_xml(f"<cp:Other xmlns:cp='{CP}'><cp:nationalCadastralReference>{TARGET}</cp:nationalCadastralReference></cp:Other>")
    assert found[TARGET] == []

    found, _ = parse_xml(parcel() + parcel())
    assert len(found[TARGET]) == 2

    print("PARCEL_LABEL_2_NAMESPACE_TOPOLOGY_PARSER_TESTS=18/18")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
