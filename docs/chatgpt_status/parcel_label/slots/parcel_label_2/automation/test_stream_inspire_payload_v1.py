from __future__ import annotations

import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path

import stream_inspire_payload_v1 as module

TARGETS = [f"parcel_{i}" for i in range(1, 13)]


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def feature(index: int, inspire: str | None = None) -> dict:
    return {"type":"Feature","geometry":{"type":"Point","coordinates":[0.0,0.0]},"properties":{"parcel_id":f"parcel_{index}","row_no":index,"hmlr_inspire_id":inspire or str(46000000+index),"hmlr_lon":-0.1,"hmlr_lat":51.6,"hmlr_area_m2":"10.0","london_authority":"Enfield","text":"brace } and quote \" safe"}}


def write_bytes(data: bytes, suffix: str = ".bin") -> Path:
    handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    with handle: handle.write(data)
    return Path(handle.name)


def expect_error(fragment: str, fn) -> None:
    try: fn()
    except RuntimeError as exc: assert fragment in str(exc), exc
    else: raise AssertionError(fragment)


def main() -> int:
    checks=0
    data=json.dumps({"type":"FeatureCollection","features":[feature(i) for i in range(1,13)]},separators=(",", ":")).encode(); path=write_bytes(data,".geojson")
    try:
        rows,summary=module.canonical_targets(path,expected_blob_sha=git_blob_sha(data),expected_feature_count=12,target_ids=TARGETS)
        assert len(rows)==12 and summary["canonical_streaming_mmap"] is True; checks+=1
        assert rows["parcel_1"]["hmlr_inspire_id"]=="46000001"; checks+=1
        expect_error("CANONICAL_BLOB_MISMATCH",lambda:module.canonical_targets(path,expected_blob_sha="0"*40,expected_feature_count=12,target_ids=TARGETS)); checks+=1
        expect_error("CANONICAL_FEATURE_COUNT_MISMATCH",lambda:module.canonical_targets(path,expected_blob_sha=git_blob_sha(data),expected_feature_count=13,target_ids=TARGETS)); checks+=1
        expect_error("TARGETS_MISSING",lambda:module.canonical_targets(path,expected_blob_sha=git_blob_sha(data),expected_feature_count=12,target_ids=TARGETS+["parcel_13"])); checks+=1
    finally: path.unlink(missing_ok=True)
    duplicate_data=json.dumps({"features":[feature(1),feature(1)]},separators=(",", ":")).encode(); duplicate_path=write_bytes(duplicate_data,".geojson")
    try: expect_error("TARGET_DUPLICATE",lambda:module.canonical_targets(duplicate_path,expected_blob_sha=git_blob_sha(duplicate_data),expected_feature_count=2,target_ids=["parcel_1"])); checks+=1
    finally: duplicate_path.unlink(missing_ok=True)
    bad=feature(1); bad["properties"]["row_no"]=99; bad_data=json.dumps({"features":[bad]},separators=(",", ":")).encode(); bad_path=write_bytes(bad_data,".geojson")
    try: expect_error("ROW_NO_MISMATCH",lambda:module.canonical_targets(bad_path,expected_blob_sha=git_blob_sha(bad_data),expected_feature_count=1,target_ids=["parcel_1"])); checks+=1
    finally: bad_path.unlink(missing_ok=True)
    missing=b'{"type":"FeatureCollection"}'; missing_path=write_bytes(missing,".geojson")
    try: expect_error("CANONICAL_FEATURES_KEY_MISSING",lambda:module.canonical_targets(missing_path,expected_blob_sha=git_blob_sha(missing),expected_feature_count=0,target_ids=[])); checks+=1
    finally: missing_path.unlink(missing_ok=True)
    gml=b"<?xml version='1.0'?><gml:FeatureCollection xmlns:gml='http://www.opengis.net/gml/3.2'><gml:featureMember/></gml:FeatureCollection>"
    pool=module.MappedPayloadPool(); direct=write_bytes(gml,".gml"); mapped,source=module.normalise_download_file(direct,final_url="https://example.test/enfield.gml",media_type="application/gml+xml",pool=pool)
    assert bytes(mapped[:5])==b"<?xml" and source.endswith("enfield.gml"); checks+=1
    assert pool.sha256(mapped)==hashlib.sha256(gml).hexdigest(); checks+=1
    pool.cleanup(); assert not direct.exists(); checks+=1
    zpath=write_bytes(b"",".zip")
    with zipfile.ZipFile(zpath,"w",zipfile.ZIP_DEFLATED) as z:z.writestr("data/enfield.gml",gml)
    pool=module.MappedPayloadPool(); mapped,source=module.normalise_download_file(zpath,final_url="https://example.test/enfield.zip",media_type="application/zip",pool=pool)
    assert source.endswith("#data/enfield.gml") and pool.sha256(mapped)==hashlib.sha256(gml).hexdigest(); checks+=1
    pool.cleanup(); zpath.unlink(missing_ok=True)
    active=write_bytes(b"<!DOCTYPE x><gml:FeatureCollection xmlns:gml='http://www.opengis.net/gml'/>",".gml"); pool=module.MappedPayloadPool(); expect_error("GML_ACTIVE_XML_FORBIDDEN",lambda:module.normalise_download_file(active,final_url="https://example.test/x.gml",media_type="application/gml+xml",pool=pool)); checks+=1; active.unlink(missing_ok=True); pool.cleanup()
    html=write_bytes(b"<html>error</html>",".gml"); pool=module.MappedPayloadPool(); expect_error("BINARY_ROUTE_RETURNED_HTML",lambda:module.normalise_download_file(html,final_url="https://example.test/x.gml",media_type="text/html",pool=pool)); checks+=1; html.unlink(missing_ok=True); pool.cleanup()
    multi=write_bytes(b"",".zip")
    with zipfile.ZipFile(multi,"w") as z:z.writestr("a.gml",gml);z.writestr("b.gml",gml)
    pool=module.MappedPayloadPool(); expect_error("ZIP_GML_MEMBER_COUNT:2",lambda:module.normalise_download_file(multi,final_url="https://example.test/x.zip",media_type="application/zip",pool=pool)); checks+=1; multi.unlink(missing_ok=True); pool.cleanup()
    unsafe=write_bytes(b"",".zip")
    with zipfile.ZipFile(unsafe,"w") as z:z.writestr("../x.gml",gml)
    pool=module.MappedPayloadPool(); expect_error("ZIP_GML_MEMBER_PATH_UNSAFE",lambda:module.normalise_download_file(unsafe,final_url="https://example.test/x.zip",media_type="application/zip",pool=pool)); checks+=1; unsafe.unlink(missing_ok=True); pool.cleanup()
    many=write_bytes(b"",".zip")
    with zipfile.ZipFile(many,"w") as z:
        for i in range(4):z.writestr(f"n{i}.txt","x")
        z.writestr("x.gml",gml)
    pool=module.MappedPayloadPool(); expect_error("ZIP_MEMBER_COUNT_EXCEEDED:5",lambda:module.normalise_download_file(many,final_url="https://example.test/x.zip",media_type="application/zip",pool=pool,max_zip_members=4)); checks+=1; many.unlink(missing_ok=True); pool.cleanup()
    expect_error("PAYLOAD_SIZE_LIMIT_EXCEEDED:8",lambda:module.stream_response_to_file(io.BytesIO(b"x"*9),limit=8)); checks+=1
    assert module.validate_https_url("https://example.test/x"); checks+=1
    expect_error("OFFICIAL_DOWNLOAD_URL_NOT_HTTPS",lambda:module.validate_https_url("http://example.test/x")); checks+=1
    expect_error("OFFICIAL_DOWNLOAD_URL_CONTAINS_USERINFO",lambda:module.validate_https_url("https://u:p@example.test/x")); checks+=1
    expect_error("OFFICIAL_DOWNLOAD_URL_CONTAINS_FRAGMENT",lambda:module.validate_https_url("https://example.test/x#f")); checks+=1
    expect_error("OFFICIAL_DOWNLOAD_URL_CROSS_ORIGIN",lambda:module.validate_https_url("https://other.test/x",primary_host="example.test",same_origin=True)); checks+=1
    print(f"PARCEL_LABEL_2_STREAMING_CANONICAL_AND_DOWNLOAD_TESTS={checks}/{checks}"); print("FINAL_READY=false"); return 0

if __name__=="__main__":raise SystemExit(main())
