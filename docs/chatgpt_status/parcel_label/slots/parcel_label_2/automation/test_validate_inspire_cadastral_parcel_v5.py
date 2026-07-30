from __future__ import annotations

import importlib.util
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v5.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v5", VALIDATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V5_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LEGACY_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v2.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v2_tests", LEGACY_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V2_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)
legacy.module = module
CP, GML = legacy.CP, legacy.GML


def geom(exterior: str, interiors: list[str] | None = None, extra: str = "") -> str:
    holes = "".join(f"<gml:interior><gml:LinearRing><gml:posList>{ring}</gml:posList></gml:LinearRing></gml:interior>" for ring in (interiors or []))
    return f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>{exterior}</gml:posList>{extra}</gml:LinearRing></gml:exterior>{holes}</gml:Polygon></cp:geometry>"


def main() -> int:
    assert legacy.main() == 0
    legacy.assert_invalid_geometry("COORDINATE_TOKEN_INVALID", geom("0 0 2 bad 2 2 0 0"))
    legacy.assert_invalid_geometry("COORDINATE_TOKEN_NON_FINITE", geom("0 0 2 0 2 inf 0 0"))
    bad_dim = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing srsDimension='3'><gml:posList>0 0 1 2 0 1 2 2 1 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("POSLIST_ORDINATE_COUNT_NOT_DIVISIBLE_BY_DIMENSION", bad_dim)
    bad_dim_text = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing srsDimension='two'><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATE_DIMENSION_INVALID", bad_dim_text)
    legacy.assert_invalid_geometry("LINEAR_RING_COORDINATE_ENCODING_MIXED", geom("0 0 2 0 2 2 0 0", extra="<gml:pos>0 0</gml:pos>"))
    multiple = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0</gml:posList><gml:posList>2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("LINEAR_RING_POSLIST_COUNT_NOT_ONE", multiple)
    extra_pos = f"<cp:geometry xmlns:cp='{CP}'><gml:Surface xmlns:gml='{GML}'><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:pos>0 0 9</gml:pos><gml:pos>2 0</gml:pos><gml:pos>2 2</gml:pos><gml:pos>0 0</gml:pos></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></cp:geometry>"
    legacy.assert_invalid_geometry("POS_ORDINATE_COUNT_MISMATCH", extra_pos)
    inconsistent = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:coordinates>0,0 2,0,5 2,2 0,0</gml:coordinates></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATES_TUPLE_WIDTH_INCONSISTENT", inconsistent)

    exterior = "0 0 10 0 10 10 0 10 0 0"
    valid = geom(exterior, ["2 2 4 2 4 4 2 4 2 2"])
    found, _ = legacy.parse_xml(legacy.parcel(geometry=valid))
    assert found[legacy.TARGET][0]["polygon_boundary_topology_validation_passed"] is True
    legacy.assert_invalid_geometry("NOT_STRICTLY_INSIDE_EXTERIOR", geom(exterior, ["12 12 14 12 14 14 12 14 12 12"]))
    legacy.assert_invalid_geometry("INTERSECTS_EXTERIOR", geom(exterior, ["8 8 12 8 12 12 8 12 8 8"]))
    legacy.assert_invalid_geometry("INTERSECTS_EXTERIOR", geom(exterior, ["0 2 2 2 2 4 0 4 0 2"]))
    legacy.assert_invalid_geometry("INTERIOR_RINGS_0_1_INTERSECT", geom(exterior, ["2 2 6 2 6 6 2 6 2 2", "4 4 8 4 8 8 4 8 4 4"]))
    legacy.assert_invalid_geometry("INTERIOR_RINGS_0_1_NESTED", geom(exterior, ["2 2 8 2 8 8 2 8 2 2", "4 4 6 4 6 6 4 6 4 4"]))
    print("PARCEL_LABEL_2_STRICT_COORDINATE_AND_BOUNDARY_TESTS=32/32")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
