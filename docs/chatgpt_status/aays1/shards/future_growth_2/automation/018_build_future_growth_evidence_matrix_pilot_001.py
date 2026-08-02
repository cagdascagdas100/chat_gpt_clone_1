#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SLOT="future_growth_2"
WORKSTREAM="AAYS_21_SLOT_SAFE_PARALLEL_V1"
SOURCE_KEY="5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
TARGETS={30762:17,46142:20,61522:33}
SHA=re.compile(r"^[0-9a-f]{64}$")

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def read(path):
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError("JSON root must be object")
    return value

def write(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as f:
            json.dump(value,f,ensure_ascii=False,sort_keys=True,separators=(",",":"))
            f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def build(manifest,receipt,task_key,generated_at):
    if not SHA.fullmatch(task_key): raise ValueError("invalid task continuation key")
    if manifest.get("slot_id")!=SLOT or manifest.get("continuation_key")!=SOURCE_KEY:
        raise ValueError("manifest lineage mismatch")
    rows=manifest.get("rows")
    if not isinstance(rows,list) or len(rows)!=3: raise ValueError("manifest must have 3 rows")
    rows={int(x["row_no"]):x for x in rows}
    if set(rows)!=set(TARGETS): raise ValueError("manifest row set mismatch")
    if receipt.get("slot_id")!=SLOT or receipt.get("continuation_key")!=SOURCE_KEY:
        raise ValueError("receipt lineage mismatch")
    if receipt.get("state")!="PUBLISHED" or receipt.get("panel_status")!="PUBLISHED":
        raise ValueError("receipt not PUBLISHED")
    if receipt.get("fake_data") is not False or receipt.get("completed_count")!=3 or receipt.get("target_count")!=3:
        raise ValueError("receipt 3/3 gate failed")
    results=receipt.get("results")
    if not isinstance(results,list) or len(results)!=3: raise ValueError("receipt must have 3 results")
    results={int(x["row_no"]):x for x in results}
    if set(results)!=set(TARGETS): raise ValueError("receipt row set mismatch")
    out=[]
    for row_no in sorted(TARGETS):
        row,res=rows[row_no],results[row_no]; layer_id=TARGETS[row_no]
        layers={int(x[0]):str(x[1]) for x in row.get("layers",[])}
        if layer_id not in layers: raise ValueError(f"layer missing {row_no}")
        service=str(row["service"]).rstrip("/")
        parsed=urlparse(service)
        if parsed.scheme!="https" or parsed.hostname!="services.arcgis.com":
            raise ValueError(f"unapproved service {row_no}")
        url=f"{service}/{layer_id}?f=pjson"
        expected={"parcel_id":str(row["parcel_id"]),"lpa":str(row["lpa"]),
                  "layer_id":layer_id,"layer_name_expected":layers[layer_id],"source_url":url}
        if any(res.get(k)!=v for k,v in expected.items()): raise ValueError(f"receipt join mismatch {row_no}")
        meta=res.get("metadata")
        good=(res.get("data_status")=="VERIFIED_METADATA" and res.get("error") is None
              and res.get("http_status")==200 and isinstance(res.get("byte_count"),int)
              and res["byte_count"]>0 and SHA.fullmatch(str(res.get("raw_sha256","")))
              and isinstance(meta,dict) and isinstance(meta.get("object_id_field"),str)
              and bool(meta["object_id_field"]) and isinstance(meta.get("max_record_count"),int)
              and meta["max_record_count"]>0 and meta.get("supports_pagination") is True
              and meta.get("supports_order_by") is True)
        if not good: raise ValueError(f"metadata gate failed {row_no}")
        out.append({"row_no":row_no,"parcel_id":str(row["parcel_id"]),"lpa":str(row["lpa"]),
          "lon":row.get("lon"),"lat":row.get("lat"),"manifest_service":service,
          "layer_id":layer_id,"layer_name_expected":layers[layer_id],"source_url":url,
          "fetched_at_utc":res.get("fetched_at_utc"),"http_status":200,
          "byte_count":res["byte_count"],"raw_sha256":res["raw_sha256"],
          "metadata":{k:meta.get(k) for k in ("name","type","object_id_field","max_record_count",
          "supports_pagination","supports_order_by","spatial_reference_wkid")},
          "license_or_terms_url":res.get("license_or_terms_url"),
          "evidence_scope":"SERVICE_LAYER_METADATA_ONLY",
          "parcel_binding_status":"MANIFEST_DECLARED_ANCHOR_ONLY",
          "future_growth_membership":None,"future_growth_score":None,"confidence":None,
          "data_status":"VERIFIED_METADATA_NOT_SCORED"})
    return {"schema_version":3,"workstream_id":WORKSTREAM,"slot_id":SLOT,
      "task_continuation_key":task_key,"source_continuation_key":SOURCE_KEY,
      "state":"PUBLISHED","panel_status":"PUBLISHED","generated_at":generated_at,
      "completed_count":3,"target_count":3,"progress_percent":100.0,
      "global_business_completed_count":0,"global_business_target_count":30761,
      "global_progress_percent":0.0,"records":out,"raw_bodies_copied":False,
      "large_raw_files_written":False,"membership_inferred":False,
      "scores_written":False,"fake_data":False}

def fixture():
    base="https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services/"
    specs=[(30762,"parcel_30762","Enfield",-0.0407406,51.6769078,"planning_local_plan_data_10",17,"Medium Growth Housing",18174,"0883db731e9fcb7f7c70902ab312f23b97427e9b7e57eca3dddae9b09b976ad6"),
      (46142,"parcel_46142","Havering",0.1928191,51.593114,"planning_local_plan_data_16",20,"Retained Site Specific Allocations",18424,"1831bbd1a4a8cb577fbae2adb36369fe56dc0714f552ec39c62b3bb008b08a56"),
      (61522,"parcel_61522","Lambeth",-0.139263,51.4153374,"planning_local_plan_data_22",33,"Site Allocations",18158,"bff2eebbaa6d0829a6ce3237278b93f74c95e83adf68da80117cc56e450cd073")]
    rows=[]; results=[]
    for n,p,l,lon,lat,s,layer,name,size,digest in specs:
        service=base+s+"/FeatureServer"; url=f"{service}/{layer}?f=pjson"
        rows.append({"row_no":n,"parcel_id":p,"lpa":l,"lon":lon,"lat":lat,"service":service,"layers":[[layer,name]]})
        results.append({"row_no":n,"parcel_id":p,"lpa":l,"layer_id":layer,
          "layer_name_expected":name,"source_url":url,"fetched_at_utc":"2026-08-02T02:18:08Z",
          "http_status":200,"byte_count":size,"raw_sha256":digest,
          "metadata":{"name":name,"type":"Feature Layer","object_id_field":"objectid",
          "max_record_count":2000,"supports_pagination":True,"supports_order_by":True,
          "spatial_reference_wkid":27700},"license_or_terms_url":
          "https://www.esri.com/en-us/legal/terms/full-master-agreement",
          "data_status":"VERIFIED_METADATA","error":None})
    return ({"slot_id":SLOT,"continuation_key":SOURCE_KEY,"rows":rows},
      {"slot_id":SLOT,"continuation_key":SOURCE_KEY,"state":"PUBLISHED",
       "panel_status":"PUBLISHED","completed_count":3,"target_count":3,
       "results":results,"fake_data":False})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path); p.add_argument("--metadata-receipt",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--task-continuation-key",required=True); p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: manifest,receipt=fixture()
    else:
        if a.manifest is None or a.metadata_receipt is None:
            raise ValueError("manifest and metadata receipt required")
        manifest,receipt=read(a.manifest),read(a.metadata_receipt)
    value=build(manifest,receipt,a.task_continuation_key,now()); write(a.output,value)
    print(json.dumps({"state":value["state"],"completed_count":3,"target_count":3,
      "records_not_scored":True,"network_executed":False,"output":str(a.output)},
      separators=(",",":")))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
