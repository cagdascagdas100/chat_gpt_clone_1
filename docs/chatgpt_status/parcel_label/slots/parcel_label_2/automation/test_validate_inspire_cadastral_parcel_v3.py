from __future__ import annotations

import importlib.util
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v3.py")
validator_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v3", VALIDATOR_PATH)
if validator_spec is None or validator_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V3_IMPORT_FAILED")
module = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(module)

LEGACY_TEST_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v2.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v2_tests", LEGACY_TEST_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V2_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)
legacy.module = module

TARGET = legacy.TARGET
CP = legacy.CP
GML = legacy.GML


def main() -> int:
    assert legacy.main() == 0

    invalid_token = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 bad 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATE_TOKEN_INVALID", invalid_token)

    non_finite = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 inf 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATE_TOKEN_NON_FINITE", non_finite)

    bad_dimension_count = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing srsDimension='3'><gml:posList>0 0 1 2 0 1 2 2 1 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("POSLIST_ORDINATE_COUNT_NOT_DIVISIBLE_BY_DIMENSION", bad_dimension_count)

    invalid_dimension = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing srsDimension='two'><gml:posList>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATE_DIMENSION_INVALID", invalid_dimension)

    mixed_encoding = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0 2 2 0 0</gml:posList><gml:pos>0 0</gml:pos></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("LINEAR_RING_COORDINATE_ENCODING_MIXED", mixed_encoding)

    multiple_poslist = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:posList>0 0 2 0</gml:posList><gml:posList>2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("LINEAR_RING_POSLIST_COUNT_NOT_ONE", multiple_poslist)

    extra_pos_ordinate = f"<cp:geometry xmlns:cp='{CP}'><gml:Surface xmlns:gml='{GML}'><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing><gml:pos>0 0 9</gml:pos><gml:pos>2 0</gml:pos><gml:pos>2 2</gml:pos><gml:pos>0 0</gml:pos></gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></cp:geometry>"
    legacy.assert_invalid_geometry("POS_ORDINATE_COUNT_MISMATCH", extra_pos_ordinate)

    inconsistent_coordinates = f"<cp:geometry xmlns:cp='{CP}'><gml:Polygon xmlns:gml='{GML}'><gml:exterior><gml:LinearRing><gml:coordinates>0,0 2,0,5 2,2 0,0</gml:coordinates></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>"
    legacy.assert_invalid_geometry("COORDINATES_TUPLE_WIDTH_INCONSISTENT", inconsistent_coordinates)

    print("PARCEL_LABEL_2_STRICT_COORDINATE_LEXICAL_TESTS=26/26")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
