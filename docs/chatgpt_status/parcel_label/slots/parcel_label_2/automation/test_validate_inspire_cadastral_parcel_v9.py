from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v9.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v9", VALIDATOR_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V9_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

LEGACY_PATH = Path(__file__).with_name("test_validate_inspire_cadastral_parcel_v8.py")
legacy_spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v8_tests", LEGACY_PATH)
if legacy_spec is None or legacy_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V8_TEST_IMPORT_FAILED")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)

TARGET = legacy.TARGET
CP = legacy.CP
GML = legacy.GML
WFS = legacy.WFS


def run(xml: str):
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
        handle.write(xml.encode())
        path = Path(handle.name)
    try:
        return module.parse(path, {TARGET, "46037757"})
    finally:
        path.unlink(missing_ok=True)


def cp(reference: str = TARGET) -> str:
    return legacy.cp_feature().replace(TARGET, reference)


def expect_error(fragment: str, xml: str) -> None:
    try:
        run(xml)
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def wfs(features: list[str], attrs: str = "") -> str:
    members = "".join(f"<wfs:member>{feature}</wfs:member>" for feature in features)
    return f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}' {attrs}>{members}</wfs:FeatureCollection>"


def main() -> int:
    assert legacy.main() == 0
    checks = 0

    found, summary = run(wfs([cp()], "numberReturned='1' numberMatched='1'"))
    assert found[TARGET]
    assert summary["feature_collection_cardinality_validation_passed"] is True
    assert summary["collection_cardinality_records"][0]["observed_direct_feature_count"] == 1
    checks += 3

    found, summary = run(wfs([cp(), cp("46037757")], "numberReturned='2' numberMatched='2'"))
    assert len(found[TARGET]) == 1 and len(found["46037757"]) == 1
    assert summary["supported_cadastral_feature_count_cardinality_scan"] == 2
    checks += 2

    xml = f"<gml:FeatureCollection xmlns:gml='{GML}' xmlns:cp='{CP}' numberOfFeatures='2'><gml:featureMembers>{cp()}{cp('46037757')}</gml:featureMembers></gml:FeatureCollection>"
    found, summary = run(xml)
    assert len(found[TARGET]) == 1 and summary["collection_cardinality_records"][0]["declared_counts"]["numberOfFeatures"] == 2
    checks += 2

    found, summary = run(wfs([cp()]))
    assert found[TARGET] and summary["collection_cardinality_records"][0]["declared_counts"] == {}
    checks += 2

    expect_error("FEATURE_COLLECTION_NUMBERRETURNED_MISMATCH", wfs([cp()], "numberReturned='2'")); checks += 1
    expect_error("FEATURE_COLLECTION_NUMBERMATCHED_MISMATCH", wfs([cp()], "numberMatched='2'")); checks += 1
    expect_error("FEATURE_COLLECTION_NUMBERMATCHED_UNKNOWN", wfs([cp()], "numberMatched='unknown'")); checks += 1
    expect_error("FEATURE_COLLECTION_NUMBERRETURNED_INVALID", wfs([cp()], "numberReturned='1.0'")); checks += 1
    expect_error("FEATURE_COLLECTION_NUMBEROFFEATURES_MISMATCH", f"<gml:FeatureCollection xmlns:gml='{GML}' xmlns:cp='{CP}' numberOfFeatures='0'><gml:featureMember>{cp()}</gml:featureMember></gml:FeatureCollection>"); checks += 1

    xml = f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wfs:member>{cp()}<x:Other xmlns:x='urn:x'/></wfs:member></wfs:FeatureCollection>"
    expect_error("CADASTRAL_FEATURE_MEMBER_CHILD_COUNT:2", xml); checks += 1

    xml = f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}' xmlns:xlink='http://www.w3.org/1999/xlink'><wfs:member xlink:href='https://example.invalid/feature'>{cp()}</wfs:member></wfs:FeatureCollection>"
    expect_error("CADASTRAL_FEATURE_MEMBER_XLINK_FORBIDDEN", xml); checks += 1

    xml = f"<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}'><wrapper><wfs:member>{cp()}</wfs:member></wrapper></wfs:FeatureCollection>"
    expect_error("CADASTRAL_MEMBER_NOT_DIRECT_COLLECTION_CHILD", xml); checks += 1

    xml = f"<gml:FeatureCollection xmlns:gml='{GML}' xmlns:cp='{CP}' numberOfFeatures='2'><gml:featureMembers>{cp()}<x:Other xmlns:x='urn:x'/></gml:featureMembers></gml:FeatureCollection>"
    found, summary = run(xml)
    assert found[TARGET] and summary["collection_cardinality_records"][0]["observed_direct_feature_count"] == 2
    checks += 2

    print(f"PARCEL_LABEL_2_COLLECTION_CARDINALITY_TESTS={checks}/{checks}")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
