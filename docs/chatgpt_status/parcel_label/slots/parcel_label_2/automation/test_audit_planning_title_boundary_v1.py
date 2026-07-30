from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_planning_title_boundary_v1.py")
spec = importlib.util.spec_from_file_location("planning_crosscheck", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PLANNING_CROSSCHECK_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def expect_error(fragment: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        assert fragment in str(exc), (fragment, exc)
    else:
        raise AssertionError(f"EXPECTED_ERROR_NOT_RAISED:{fragment}")


def main() -> int:
    identity = module.CanonicalIdentity(
        parcel_id="parcel_30762",
        reference="46058185",
        longitude=-0.0407406,
        latitude=51.6769078,
    )
    payload = {
        "entities": [
            {
                "entity": 12046058185,
                "dataset": "title-boundary",
                "reference": "46058185",
                "quality": "authoritative",
                "entry-date": "2026-07-29",
                "geometry": "MULTIPOLYGON (((-0.0409 51.6768, -0.0405 51.6768, -0.0405 51.6771, -0.0409 51.6771, -0.0409 51.6768)))",
            }
        ]
    }
    row = module.validate_entity(identity, payload)
    assert row["reference"] == "46058185"
    assert row["coordinate_pair_count"] == 5
    assert row["canonical_point_inside_tolerant_bbox"] is True
    assert row["accepted_as_hmlr_gml_substitute"] is False

    url = module.build_url("46058185")
    assert "dataset=title-boundary" in url
    assert "reference=46058185" in url
    assert "period=current" in url

    expect_error(
        "PLANNING_EXACT_REFERENCE_MATCH_COUNT:0",
        lambda: module.validate_entity(identity, {"entities": []}),
    )
    expect_error(
        "PLANNING_EXACT_REFERENCE_MATCH_COUNT:2",
        lambda: module.validate_entity(identity, {"entities": payload["entities"] * 2}),
    )
    wrong_reference = {"entities": [dict(payload["entities"][0], reference="999")]} 
    expect_error(
        "PLANNING_EXACT_REFERENCE_MATCH_COUNT:0",
        lambda: module.validate_entity(identity, wrong_reference),
    )
    wrong_geometry = {"entities": [dict(payload["entities"][0], geometry="POINT (-0.04 51.67)")]}
    expect_error(
        "PLANNING_GEOMETRY_NOT_POLYGON",
        lambda: module.validate_entity(identity, wrong_geometry),
    )
    outside = {"entities": [dict(payload["entities"][0], geometry="POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))")]}
    expect_error(
        "PLANNING_CANONICAL_POINT_OUTSIDE_GEOMETRY_BBOX",
        lambda: module.validate_entity(identity, outside),
    )
    expect_error("REFERENCE_NOT_NUMERIC", lambda: module.build_url("abc"))
    expect_error("PLANNING_API_ENTITIES_MISSING", lambda: module._entities({"meta": {}}))

    print("PARCEL_LABEL_2_PLANNING_CROSSCHECK_TESTS=10/10")
    print("OFFICIAL_GML_SUBSTITUTE=false")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
