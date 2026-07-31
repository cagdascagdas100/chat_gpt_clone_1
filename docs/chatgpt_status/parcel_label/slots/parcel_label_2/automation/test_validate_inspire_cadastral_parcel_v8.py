from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v8.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v8", VALIDATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V8_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LEGACY_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v7.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v7_tests", LEGACY_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V7_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)

TARGET = legacy.TARGET
CP = legacy.CP
GML = legacy.GML
WFS = "http://www.opengis.net/wfs/2.0"
OGR = "http://ogr.maptools.org/"


def run(xml: str):
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
        handle.write(xml.encode())
        path = Path(handle.name)
    try:
        return module.parse(path, {TARGET, "46037757"})
    finally:
        path.unlink(missing_ok=True)


def cp_feature() -> str:
    return legacy.legacy.legacy.legacy.parcel()


def predefined() -> str:
    return legacy.legacy.predefined()


def wfs_member(body: str) -> str:
    return f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wfs:member>{body}</wfs:member></wfs:FeatureCollection>"


def gml_member(body: str, root_ns: str = GML) -> str:
    return f"<gml:FeatureCollection xmlns:gml='{root_ns}' xmlns:cp='{CP}'><gml:featureMember>{body}</gml:featureMember></gml:FeatureCollection>"


def expect_error(fragment: str, xml: str) -> None:
    try:
        run(xml)
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def main() -> int:
    assert legacy.main() == 0
    checks = 0

    found, summary = run(wfs_member(cp_feature()))
    assert found[TARGET] and summary["feature_membership_validation_passed"]
    assert summary["supported_cadastral_feature_count"] == 1
    checks += 3

    found, summary = run(gml_member(cp_feature(), "http://www.opengis.net/gml"))
    assert found[TARGET] and summary["member_bound_cadastral_feature_count"] == 1
    checks += 2

    xml = f"<ogr:FeatureCollection xmlns:ogr='{OGR}' xmlns:gml='{GML}'><gml:featureMember>{predefined()}</gml:featureMember></ogr:FeatureCollection>"
    found, summary = run(xml)
    assert found[TARGET] and summary["membership_schema_counts"]["HMLR_PREDEFINED_FLATTENED"] == 1
    checks += 2

    xml = f"<FeatureCollection xmlns:gml='{GML}'><featureMember>{predefined()}</featureMember></FeatureCollection>"
    found, summary = run(xml)
    assert found[TARGET] and summary["feature_membership_validation_passed"]
    checks += 2

    xml = f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wfs:member>{cp_feature()}</wfs:member><wfs:member>{cp_feature().replace(TARGET,'46037757')}</wfs:member></wfs:FeatureCollection>"
    found, summary = run(xml)
    assert len(found[TARGET]) == 1 and len(found["46037757"]) == 1 and summary["supported_cadastral_feature_count"] == 2
    checks += 3

    xml = f"<gml:FeatureCollection xmlns:gml='{GML}' xmlns:cp='{CP}'><gml:featureMembers>{cp_feature()}{cp_feature().replace(TARGET,'46037757')}</gml:featureMembers></gml:FeatureCollection>"
    found, summary = run(xml)
    assert len(found[TARGET]) == 1 and summary["member_bound_cadastral_feature_count"] == 2
    checks += 2

    expect_error("CADASTRAL_FEATURE_NOT_DIRECT_MEMBER", f"<root xmlns:cp='{CP}' xmlns:gml='{GML}'>{cp_feature()}</root>")
    checks += 1
    expect_error("CADASTRAL_FEATURE_COLLECTION_INVALID", f"<root xmlns:cp='{CP}' xmlns:gml='{GML}'><gml:featureMember>{cp_feature()}</gml:featureMember></root>")
    checks += 1
    expect_error("CADASTRAL_FEATURE_NOT_DIRECT_MEMBER", f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wfs:member><wrapper>{cp_feature()}</wrapper></wfs:member></wfs:FeatureCollection>")
    checks += 1
    expect_error("CADASTRAL_FEATURE_NOT_DIRECT_MEMBER", f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wfs:member>{cp_feature()}</wfs:member>{cp_feature().replace(TARGET,'46037757')}</wfs:FeatureCollection>")
    checks += 1
    expect_error("CADASTRAL_FEATURE_NOT_DIRECT_MEMBER", f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><x:member xmlns:x='urn:bad'>{cp_feature()}</x:member></wfs:FeatureCollection>")
    checks += 1
    expect_error("CADASTRAL_FEATURE_COLLECTION_INVALID", f"<FeatureCollection xmlns:gml='{GML}' xmlns:cp='{CP}'><gml:featureMember>{cp_feature()}</gml:featureMember></FeatureCollection>")
    checks += 1
    expect_error("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED", f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}'><wfs:member><x:Thing xmlns:x='urn:x'/></wfs:member></wfs:FeatureCollection>")
    checks += 1

    print(f"PARCEL_LABEL_2_FEATURE_MEMBERSHIP_TESTS={checks}/{checks}")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
