from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
VALIDATOR = HERE / "validate_inspire_cadastral_parcel_v20.py"
spec = importlib.util.spec_from_file_location("parcel_label_2_v20_real_feature", VALIDATOR)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V20_REAL_FEATURE_IMPORT_FAILED")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TARGET = "46058185"
CP = "http://inspire.ec.europa.eu/schemas/cp/4.0"
BASE = "http://inspire.ec.europa.eu/schemas/base/3.3"
GML = "http://www.opengis.net/gml/3.2"
WFS = "http://www.opengis.net/wfs/2.0"


def feature(reference: str = TARGET) -> str:
    return f"""<cp:CadastralParcel>
  <cp:inspireId><base:Identifier><base:localId>{reference}</base:localId></base:Identifier></cp:inspireId>
  <cp:nationalCadastralReference>{reference}</cp:nationalCadastralReference>
  <cp:geometry><gml:Polygon srsName='urn:ogc:def:crs:EPSG::27700'><gml:exterior><gml:LinearRing><gml:posList srsDimension='2'>0 0 2 0 2 2 0 0</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></cp:geometry>
</cp:CadastralParcel>"""


def document(body: str, *, returned: int = 1, matched: int = 1) -> bytes:
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<wfs:FeatureCollection xmlns:wfs='{WFS}' xmlns:gml='{GML}' xmlns:cp='{CP}' xmlns:base='{BASE}' numberReturned='{returned}' numberMatched='{matched}'>
{body}
</wfs:FeatureCollection>""".encode("utf-8")


def parse_bytes(payload: bytes, *, digest: str | None = None):
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
        handle.write(payload)
        path = Path(handle.name)
    try:
        expected = digest or hashlib.sha256(payload).hexdigest()
        return module.parse(path, {TARGET}, expected_sha256=expected)
    finally:
        path.unlink(missing_ok=True)


def expect_error(fragment: str, function) -> None:
    try:
        function()
    except RuntimeError as exc:
        assert fragment in str(exc), exc
    else:
        raise AssertionError(f"expected {fragment}")


def main() -> int:
    checks = 0
    payload = document(f"<wfs:member>{feature()}</wfs:member>")
    digest = hashlib.sha256(payload).hexdigest()
    found, summary = parse_bytes(payload, digest=digest)
    record = found[TARGET][0]

    assertions = [
        len(found[TARGET]) == 1,
        record["national_cadastral_reference"] == TARGET,
        record["local_id_exact_match"] is True,
        len(record["feature_sha256"]) == 64,
        record["geometry_validation_passed"] is True,
        record["geometry_scope_validation_passed"] is True,
        record["coordinate_pair_count"] == 4,
        summary["feature_membership_validation_passed"] is True,
        summary["feature_collection_cardinality_validation_passed"] is True,
        summary["supported_cadastral_feature_count_cardinality_scan"] == 1,
        summary["xml_descriptor_pinning_validation_passed"] is True,
        summary["xml_parser_source_bound_to_open_descriptor"] is True,
        summary["xml_parser_source_path_reopen_forbidden"] is True,
        summary["xml_parse_bytes_bound_to_download_sha256"] is True,
        summary["xml_source_observed_sha256"] == digest,
        str(summary["xml_backend"]).startswith("lxml.etree"),
        summary["xml_parser_no_network"] is True,
        summary["xml_parser_resolve_entities"] is False,
        summary["xml_parser_load_dtd"] is False,
    ]
    assert all(assertions), (assertions, record, summary)
    checks += len(assertions)

    wrong_digest = "0" * 64 if digest != "0" * 64 else "1" * 64
    expect_error("XML_SOURCE_SHA256_MISMATCH", lambda: parse_bytes(payload, digest=wrong_digest))
    checks += 1

    outside_member = document(feature())
    expect_error("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED", lambda: parse_bytes(outside_member))
    checks += 1

    count_mismatch = document(f"<wfs:member>{feature()}</wfs:member>", returned=2, matched=1)
    expect_error("FEATURE_COLLECTION_NUMBERRETURNED_MISMATCH", lambda: parse_bytes(count_mismatch))
    checks += 1

    print(f"PARCEL_LABEL_2_V20_REAL_FEATURE_CHAIN_TESTS={checks}/{checks}")
    print("FINAL_READY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
