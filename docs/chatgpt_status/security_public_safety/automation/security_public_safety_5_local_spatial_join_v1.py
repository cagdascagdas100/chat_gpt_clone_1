from __future__ import annotations
import hashlib, json, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
P0,P1,PC=61524,76903,15380
MAX_RECORDS=50
REPO=Path(os.environ.get("AAYS_REPO_ROOT") or Path(__file__).resolve().parents[4])
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
SOURCE_WINDOW="planning_data_title_boundary_coordinate_sps5_61624_61673_v1"
API="https://www.planning.data.gov.uk/entity.geojson"
EXPECTED_PRIOR_WINDOW="mps_recorded_crime_lsoa_202409_202608_sps5_61624_61673_v1"
EXPECTED_MPS_SHA="255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082"
REQUIRED_FIELDS=[
 "evidence_scope","coverage_area_id","source_resolution","time_window","source_url",
 "measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100",
 "evidence_grade","field_evidence","canonical_parcel_id"
]

def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def sha256(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def http_json(url:str,attempts:int=3):
    last=None
    for n in range(1,attempts+1):
        req=urllib.request.Request(url,headers={
            "User-Agent":"AAYS-security-public-safety-5/title-boundary-v1",
            "Accept":"application/geo+json, application/json"
        })
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                body=resp.read()
                return int(resp.status),body,json.loads(body.decode("utf-8-sig"))
        except Exception as ex:
            last=ex
            if n<attempts: time.sleep(min(8,n*2))
    raise RuntimeError(str(last) if last else "HTTP_FAILED")

def save(obj):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def semcheck(feature):
    reasons=[]
    if not isinstance(feature,dict) or feature.get("type")!="Feature":
        return ["record_not_geojson_feature"]
    g=feature.get("geometry") or {}
    if g.get("type") not in ("Polygon","MultiPolygon"):
        reasons.append(f"geometry_type_invalid:{g.get('type')}")
    p=feature.get("properties") or {}
    for k in REQUIRED_FIELDS:
        if k not in p or p[k] in (None,"",[],{}):
            reasons.append(f"missing_required_field:{k}")
    c=p.get("confidence_score_0_100")
    if not isinstance(c,(int,float)) or isinstance(c,bool) or c<0 or c>100:
        reasons.append("confidence_score_0_100_invalid")
    if "parcel_id" in p:
        reasons.append("forbidden_alias_field:parcel_id")
    if "accepted_parcel" in p:
        reasons.append("forbidden_label_field:accepted_parcel")
    if p.get("evidence_scope")!="parcel":
        reasons.append("evidence_scope_invalid_for_parcel")
    fe=p.get("field_evidence")
    if not isinstance(fe,dict) or not fe:
        reasons.append("field_evidence_invalid")
    return reasons

def main():
    base={
      "schema_version":5,
      "slot_id":SLOT_ID,"owner":None,
      "partition":{"start":P0,"end":P1,"count":PC},
      "lineage_id":LINEAGE_ID,
      "generated_at":now(),
      "source_window_id":SOURCE_WINDOW,
      "max_official_source_records":MAX_RECORDS,
      "first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED",
      "final_package_written":False,"fake_data":False,
      "db_write":False,"migration":False,"production_deploy":False,
      "accepted_count_claimed":0
    }
    try:
        prior=json.loads(OUT.read_text(encoding="utf-8-sig"))
    except Exception as ex:
        base.update(status="BLOCKED",blocker="PRIOR_FIELD_EVIDENCE_READBACK_FAILED",error=str(ex),records={"type":"FeatureCollection","features":[]},unmatched=[])
        save(base); return 0
    base["prior_field_evidence"]={
      "source_window_id":prior.get("source_window_id"),
      "output_generated_at":prior.get("generated_at"),
      "official_csv":prior.get("official_csv"),
      "output_sha256":sha256(OUT.read_bytes())
    }
    official=prior.get("official_csv") or {}
    if prior.get("source_window_id")!=EXPECTED_PRIOR_WINDOW or official.get("sha256")!=EXPECTED_MPS_SHA:
        base.update(status="BLOCKED",blocker="PRIOR_FIELD_EVIDENCE_HASH_OR_WINDOW_MISMATCH",records={"type":"FeatureCollection","features":[]},unmatched=[])
        save(base); return 0
    prior_rows=(prior.get("rows") or [])[:MAX_RECORDS]
    valid=[]
    unmatched=[]
    http_ok=0
    for idx,row in enumerate(prior_rows,1):
        locator=row.get("parcel_id")
        geom=row.get("canonical_geometry") or {}
        coords=geom.get("coordinates") if geom.get("type")=="Point" else None
        reasons=[]
        if not (isinstance(coords,list) and len(coords)>=2):
            reasons.append("legacy_locator_point_missing")
        if not row.get("field_evidence_gate"):
            reasons.append("prior_mps_field_evidence_gate_false")
        if not row.get("official_lsoa_identifier_gate"):
            reasons.append("prior_mps_exact_lsoa_identifier_gate_false")
        if reasons:
            unmatched.append({"record_index":idx,"partition_record_id":locator,"reasons":reasons})
            continue
        lng=float(coords[0]); lat=float(coords[1])
        qs=urllib.parse.urlencode({
          "latitude":f"{lat:.7f}",
          "longitude":f"{lng:.7f}",
          "dataset":"title-boundary",
          "limit":"20"
        })
        url=f"{API}?{qs}"
        try:
            st,body,obj=http_json(url)
            http_ok+=1 if st==200 else 0
        except Exception as ex:
            unmatched.append({"record_index":idx,"partition_record_id":locator,"reasons":[f"planning_data_http_failed:{ex}"],"query_url":url})
            continue
        feats=[]
        if isinstance(obj,dict) and isinstance(obj.get("features"),list):
            feats=obj["features"]
        elif isinstance(obj,list):
            feats=obj
        candidates=[]
        for f in feats:
            if not isinstance(f,dict): continue
            g=f.get("geometry") or {}
            p=f.get("properties") or {}
            if g.get("type") not in ("Polygon","MultiPolygon"): continue
            reference=p.get("reference")
            dataset=p.get("dataset")
            if not reference or (dataset and dataset!="title-boundary"): continue
            candidates.append(f)
        uniq={}
        for f in candidates:
            p=f.get("properties") or {}
            uniq[str(p.get("reference"))]=f
        if len(uniq)!=1:
            unmatched.append({
              "record_index":idx,"partition_record_id":locator,
              "reasons":[f"title_boundary_unique_match_required:found={len(uniq)}"],
              "query_url":url,"response_sha256":sha256(body),"candidate_references":sorted(uniq.keys())
            })
            continue
        reference,tf=next(iter(uniq.items()))
        tp=tf.get("properties") or {}
        canonical_id=f"title-boundary:{reference}"
        measurement_date=(prior.get("generated_at") or "")[:10] or "2026-09-28"
        feature={
          "type":"Feature",
          "id":canonical_id,
          "geometry":tf.get("geometry"),
          "properties":{
            "evidence_scope":"parcel",
            "coverage_area_id":row.get("canonical_lsoa_code"),
            "source_resolution":"official_MPS_LSOA_recorded_crime_joined_to_HMLR_title_boundary_polygon",
            "time_window":"MPS_most_recent_24_months_as_hashed_2026-09-28",
            "source_url":official.get("url"),
            "measurement_date":measurement_date,
            "measurement_method":"official_MPS_LSOA_CSV_exact_identifier_join",
            "spatial_binding_method":"shared_canonical_point_intersects_Planning_Data_HMLR_title_boundary_polygon",
            "confidence_score_0_100":100,
            "evidence_grade":"A",
            "field_evidence":{
              "security_source":"Metropolitan Police Service / London Datastore",
              "official_csv_sha256":EXPECTED_MPS_SHA,
              "lsoa_code":row.get("canonical_lsoa_code"),
              "official_lsoa_row_count":row.get("official_lsoa_row_count"),
              "official_crime_value_sum":row.get("official_crime_value_sum"),
              "official_numeric_cells":row.get("official_numeric_cells"),
              "planning_data_title_boundary_query_url":url,
              "planning_data_response_sha256":sha256(body),
              "planning_data_entity":tp.get("entity"),
              "planning_data_reference":reference,
              "planning_data_quality":tp.get("quality"),
              "planning_data_organisation_curie":tp.get("organisation-curie")
            },
            "canonical_parcel_id":canonical_id,
            "canonical_parcel_reference":reference,
            "canonical_parcel_entity":tp.get("entity"),
            "partition_record_id":locator,
            "canonical_lsoa_code":row.get("canonical_lsoa_code"),
            "canonical_point":{"type":"Point","coordinates":[lng,lat]},
            "canonical_geometry_source_url":url,
            "canonical_geometry_provider":"HM Land Registry via Planning Data",
            "canonical_geometry_dataset":"title-boundary",
            "source_window_id":SOURCE_WINDOW,
            "cursor":f"{SOURCE_WINDOW}:record={idx}"
          }
        }
        check=semcheck(feature)
        if check:
            unmatched.append({"record_index":idx,"partition_record_id":locator,"reasons":check,"canonical_parcel_id":canonical_id,"query_url":url})
            continue
        valid.append(feature)
        time.sleep(.05)
    base.update(
      status="SEMANTIC_PRECHECK_COMPLETE",
      official_source={"publisher":"Planning Data / MHCLG","dataset":"title-boundary","provider":"HM Land Registry","public_no_login":True,"api":API},
      source_records_processed_count=len(prior_rows),
      source_http_200_count=http_ok,
      schema_valid_count=len(valid),
      schema_invalid_or_unmatched_count=len(unmatched),
      official_source_cursor=f"{SOURCE_WINDOW}:record={len(prior_rows)}",
      records={"type":"FeatureCollection","features":valid},
      unmatched=unmatched,
      semantic_precheck={
        "required_geometry":["Polygon","MultiPolygon"],
        "required_fields":REQUIRED_FIELDS,
        "forbidden_properties":["parcel_id","accepted_parcel"],
        "valid_count":len(valid),
        "invalid_count":len(unmatched),
        "all_records_in_records_geojson_valid":all(not semcheck(f) for f in valid)
      },
      next_step="Package writer may commit only records.features that pass semantic_precheck; unmatched rows must remain rejected."
    )
    save(base)
    print(json.dumps({
      "status":base["status"],"processed":len(prior_rows),"valid":len(valid),
      "unmatched":len(unmatched),"cursor":base["official_source_cursor"]
    }))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
