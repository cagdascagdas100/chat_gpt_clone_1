#!/usr/bin/env python3
"""Wave337 HMLR INSPIRE Enfield source and direct-GML acquisition gate."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from pathlib import Path

EXPECTED_IDS={"parcel_30762":"46058185","parcel_30763":"46037757","parcel_30764":"45981756"}
EXPECTED_SOURCES={"hmlr_inspire_download_page","hmlr_inspire_dataset_page","hmlr_gml_technical_guidance"}

def sha256_text(value:str)->str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path:str)->dict:
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("fixture must be object")
    return value

def atomic_write(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def build(fixture:dict)->dict:
    if (fixture.get("slot_id"),fixture.get("wave")) != ("gas_emissions_2",337): raise ValueError("slot/wave mismatch")
    rows=fixture.get("canonical_rows")
    if not isinstance(rows,list) or len(rows)!=3: raise ValueError("canonical row count mismatch")
    by_parcel={str(r.get("parcel_id")):r for r in rows if isinstance(r,dict)}
    if set(by_parcel)!=set(EXPECTED_IDS): raise ValueError("parcel set mismatch")
    for parcel_id,inspire_id in EXPECTED_IDS.items():
        row=by_parcel[parcel_id]
        if str(row.get("hmlr_inspire_id"))!=inspire_id: raise ValueError("INSPIRE id mismatch")
        if row.get("geometry_type")!="Point" or row.get("london_authority")!="Enfield": raise ValueError("canonical carrier mismatch")
        if not isinstance(row.get("lon"),(int,float)) or not isinstance(row.get("lat"),(int,float)): raise ValueError("coordinate mismatch")
    manifest=fixture.get("source_evidence_manifest")
    if not isinstance(manifest,list): raise ValueError("source manifest missing")
    by_source={}
    for source in manifest:
        sid=source.get("source_id"); excerpt=source.get("relevant_record_ids_or_excerpt")
        if not sid or not isinstance(excerpt,str) or not excerpt: raise ValueError("source id/excerpt missing")
        if source.get("content_sha256")!=sha256_text(excerpt): raise ValueError("source hash mismatch:"+str(sid))
        for key in ("publisher","source_url","accessed_at","hash_scope","record_scope","supports_fields","license_or_terms_url"):
            if not source.get(key): raise ValueError("source field missing:"+str(sid)+":"+key)
        by_source[str(sid)]=source
    if set(by_source)!=EXPECTED_SOURCES: raise ValueError("source set mismatch")
    if "London Borough of Enfield" not in by_source["hmlr_inspire_download_page"]["relevant_record_ids_or_excerpt"]: raise ValueError("Enfield listing missing")
    dataset=by_source["hmlr_inspire_dataset_page"]["relevant_record_ids_or_excerpt"]
    for token in ("Open Government Licence","Land Registry-INSPIRE ID","published as GML"):
        if token not in dataset: raise ValueError("dataset token missing:"+token)
    guide=by_source["hmlr_gml_technical_guidance"]["relevant_record_ids_or_excerpt"]
    for token in ("British National Grid","15 metres"):
        if token not in guide: raise ValueError("guidance token missing:"+token)
    direct_url=fixture.get("direct_enfield_gml_object_url"); bytes_acquired=fixture.get("gml_bytes_acquired") is True
    if direct_url and bytes_acquired:
        state="SOURCE_READY"; decision="CURRENT_ENFIELD_INSPIRE_GML_OBJECT_ACQUIRED"; blocker=None
        first="VALIDATE_THREE_INSPIRE_IDS_IN_CURRENT_ENFIELD_GML_AND_COMPARE_GEOMETRY"
    else:
        state="NO_DATA_CONTINUE"; decision="HMLR_INSPIRE_ENFIELD_SOURCE_CONFIRMED_DIRECT_GML_OBJECT_UNRESOLVED"
        blocker="DIRECT_ENFIELD_INSPIRE_GML_OBJECT_URL_NOT_ACQUIRED;CURRENT_ENFIELD_GML_BYTES_NOT_ACQUIRED;THREE_INSPIRE_IDS_NOT_VALIDATED_AGAINST_CURRENT_POLYGON_GEOMETRY;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        first="ACQUIRE_CURRENT_ENFIELD_INSPIRE_GML_OBJECT_URL_AND_VALIDATE_3_INSPIRE_IDS_OR_NO_DATA_CONTINUE"
    return {"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_2","wave":337,"state":state,"decision":decision,"blocker":blocker,"first_unverified_step":first,"canonical_sample_path":fixture["canonical_sample_path"],"canonical_sample_blob_sha":fixture["canonical_sample_blob_sha"],"canonical_sample_rows_validated":3,"validated_hmlr_inspire_ids":[EXPECTED_IDS[k] for k in sorted(EXPECTED_IDS)],"official_source_evidence_count":len(manifest),"source_evidence_manifest":[by_source[k] for k in sorted(by_source)],"direct_enfield_gml_object_url":direct_url,"gml_bytes_acquired":bytes_acquired,"business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False}

def self_test()->None:
    excerpts={"hmlr_inspire_download_page":"London Borough of Enfield | Download .gml","hmlr_inspire_dataset_page":"Open Government Licence Land Registry-INSPIRE ID published as GML","hmlr_gml_technical_guidance":"British National Grid 15 metres"}
    fixture={"slot_id":"gas_emissions_2","wave":337,"canonical_sample_path":"x","canonical_sample_blob_sha":"x","canonical_rows":[{"parcel_id":p,"hmlr_inspire_id":i,"geometry_type":"Point","london_authority":"Enfield","lon":0.0,"lat":51.0} for p,i in EXPECTED_IDS.items()],"direct_enfield_gml_object_url":None,"gml_bytes_acquired":False,"source_evidence_manifest":[{"source_id":sid,"publisher":"HM Land Registry","source_url":"https://example.invalid","accessed_at":"2026-08-02T11:33:00Z","content_sha256":sha256_text(text),"hash_scope":"test","relevant_record_ids_or_excerpt":text,"record_scope":"test","supports_fields":["test"],"license_or_terms_url":"https://example.invalid/license"} for sid,text in excerpts.items()]}
    result=build(fixture)
    assert result["state"]=="NO_DATA_CONTINUE" and result["canonical_sample_rows_validated"]==3 and result["official_source_evidence_count"]==3
    print("SELF_TEST_PASS")

def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--fixture"); parser.add_argument("--output"); parser.add_argument("--self-test",action="store_true"); args=parser.parse_args()
    if args.self_test: self_test(); return
    if not args.fixture or not args.output: parser.error("--fixture and --output required")
    result=build(load_json(args.fixture)); atomic_write(Path(args.output),result)
    print("DECISION="+result["decision"]); print("CANONICAL_SAMPLE_ROWS_VALIDATED=3"); print("OFFICIAL_SOURCE_EVIDENCE_COUNT=3"); print("BUSINESS_ROWS_PRODUCED=0")
if __name__=="__main__": main()
