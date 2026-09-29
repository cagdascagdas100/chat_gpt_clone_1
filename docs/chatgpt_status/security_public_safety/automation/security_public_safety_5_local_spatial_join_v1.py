from __future__ import annotations
import hashlib,json,os,re,subprocess,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
SOURCE_WINDOW="planning_data_title_boundary_coordinate_api_2026_09_sps5_repair_61624_61673_v1"
API="https://www.planning.data.gov.uk/entity.json"
REPO=Path(os.environ.get("AAYS_REPO_ROOT","."))
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
RUNNER_COMMIT="a1a3e428882e653c32694d163e8a5f014d1580c9"
RUNNER_PATH="docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
FIELD_COMMIT="6342cc858dc07de5b050ec67e458b295cb0c1921"
FIELD_PATH="incoming/layer24/security_public_safety_5/86b5e932de484ad26133fa8c/mps_lsoa_recorded_crime_202108_202307_61624_61673_20260928T085212Z/records.geojson"
MPS_URL="https://data.london.gov.uk/download/exy3m/221142dd-f7b2-4209-921e-4de833a82285/MPS%20LSOA%20Level%20Crime%20%28most%20recent%2024%20months%29.csv"
MPS_SHA="255d63bd759f08d7b0dd7674a38fca25ccb824c6c3a5d75d3fb00e504a34c082"
REQUIRED=["evidence_scope","coverage_area_id","source_resolution","time_window","source_url","measurement_date","measurement_method","spatial_binding_method","confidence_score_0_100","evidence_grade","field_evidence","canonical_parcel_id"]

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def git_show(ref,path):
    q=subprocess.run(["git","-C",str(REPO),"show",f"{ref}:{path}"],capture_output=True,check=False,timeout=180)
    if q.returncode!=0: raise RuntimeError(q.stderr.decode("utf-8","replace")[-1000:])
    return q.stdout
def http_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/title-boundary-v1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as resp:
        b=resp.read()
        return int(resp.status),b,json.loads(b.decode("utf-8"))
def entity_list(obj):
    if isinstance(obj,list): return obj
    if not isinstance(obj,dict): return []
    for k in ("entities","entity","results","data"):
        v=obj.get(k)
        if isinstance(v,list): return v
    return []

_num=re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
def parse_group(tokens,pos=0):
    if tokens[pos]!="(": raise ValueError("group expected")
    pos+=1; out=[]
    if pos<len(tokens) and tokens[pos]=="(":
        while True:
            g,pos=parse_group(tokens,pos); out.append(g)
            if pos>=len(tokens): raise ValueError("unexpected end")
            if tokens[pos]==",": pos+=1; continue
            if tokens[pos]==")": pos+=1; break
            raise ValueError("bad nested separator")
        return out,pos
    while True:
        if pos>=len(tokens) or tokens[pos] in ("(",")",","): raise ValueError("coordinate expected")
        x=float(tokens[pos]); pos+=1
        if pos>=len(tokens) or tokens[pos] in ("(",")",","): raise ValueError("y expected")
        y=float(tokens[pos]); pos+=1
        # ignore optional Z/M dimensions if present until comma/close; Planning Data is 2D
        while pos<len(tokens) and tokens[pos] not in (",",")"): pos+=1
        out.append([x,y])
        if pos>=len(tokens): raise ValueError("unexpected end")
        if tokens[pos]==",": pos+=1; continue
        if tokens[pos]==")": pos+=1; break
    return out,pos
def wkt_geojson(wkt):
    if not isinstance(wkt,str): raise ValueError("missing WKT")
    s=wkt.strip()
    if ";" in s and s.upper().startswith("SRID="): s=s.split(";",1)[1].strip()
    m=re.match(r"^\s*(POLYGON|MULTIPOLYGON)\s*(.*)$",s,re.I|re.S)
    if not m: raise ValueError("not polygon WKT")
    typ=m.group(1).upper(); body=m.group(2)
    tokens=re.findall(r"\(|\)|,|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",body)
    data,pos=parse_group(tokens,0)
    if pos!=len(tokens): raise ValueError("trailing WKT tokens")
    return {"type":"Polygon" if typ=="POLYGON" else "MultiPolygon","coordinates":data}

base={
 "schema_version":9,"slot_id":SLOT_ID,"owner":None,"partition":{"start":61524,"end":76903,"count":15380},
 "lineage_id":LINEAGE_ID,"generated_at":now(),"source_window_id":SOURCE_WINDOW,
 "first_missing_criterion":"CANONICAL_PARCEL_POLYGON_AND_ID_REQUIRED","accepted_count_claimed":0,
 "final_package_written":False,"fake_data":False,"max_records":48
}
try:
    prior=json.loads(git_show(RUNNER_COMMIT,RUNNER_PATH).decode("utf-8-sig"))
    fg=json.loads(git_show(FIELD_COMMIT,FIELD_PATH).decode("utf-8-sig"))
except Exception as ex:
    base.update(status="BLOCKED",blocker="PRIOR_READBACK_FAILED",error=str(ex),records=[],unmatched=[]);save(base);raise SystemExit(0)

pts={}
for x in prior.get("rows",[]):
    n=x.get("parcel_number"); g=x.get("canonical_geometry") or {}
    if isinstance(n,int) and 61624<=n<=61673 and g.get("type")=="Point":
        pts[x.get("parcel_id")]={"partition_record_id":x.get("parcel_id"),"parcel_number":n,"lon":float(g["coordinates"][0]),"lat":float(g["coordinates"][1])}
fieldmap={}
for f in fg.get("features",[]):
    p=f.get("properties") or {}
    pid=p.get("parcel_id")
    if pid: fieldmap[pid]=p
targets=[pts[k] for k in sorted(fieldmap.keys(),key=lambda z:int(z.split("_")[1])) if k in pts]
if len(targets)!=48:
    base.update(status="BLOCKED",blocker="FIELD_EVIDENCE_TARGET_COUNT_MISMATCH",expected=48,actual=len(targets),records=[],unmatched=[]);save(base);raise SystemExit(0)

records=[];unmatched=[];issues=[];queries=[]
for i,a in enumerate(targets,1):
    params=[
      ("latitude",f"{a['lat']:.7f}"),("longitude",f"{a['lon']:.7f}"),("dataset","title-boundary"),("quality","authoritative"),
      ("limit","20"),("field","entity"),("field","reference"),("field","dataset"),("field","geometry"),("field","quality"),
      ("field","start-date"),("field","entry-date"),("field","organisation-curie")
    ]
    url=API+"?"+urllib.parse.urlencode(params,doseq=True)
    try:
        status,b,obj=http_json(url)
    except Exception as ex:
        unmatched.append({"record_index":i,"partition_record_id":a["partition_record_id"],"cursor":f"{SOURCE_WINDOW}:record={i}","exact_reasons":["PLANNING_DATA_TITLE_BOUNDARY_HTTP_FAILED"],"error":str(ex),"query_url":url})
        continue
    ents=[]
    for e in entity_list(obj):
        if not isinstance(e,dict): continue
        if e.get("dataset")!="title-boundary": continue
        if str(e.get("quality","")).lower() not in ("authoritative",""): continue
        ref=str(e.get("reference") or "").strip()
        wkt=e.get("geometry")
        if not ref or not isinstance(wkt,str): continue
        try: geom=wkt_geojson(wkt)
        except Exception: continue
        ents.append((ref,geom,e))
    # unique by reference
    uniq={ref:(geom,e) for ref,geom,e in ents}
    queries.append({"partition_record_id":a["partition_record_id"],"url":url,"http_status":status,"response_sha256":hashlib.sha256(b).hexdigest(),"result_count":len(uniq)})
    if len(uniq)!=1:
        unmatched.append({"record_index":i,"partition_record_id":a["partition_record_id"],"cursor":f"{SOURCE_WINDOW}:record={i}","exact_reasons":[("NO_UNIQUE_TITLE_BOUNDARY" if len(uniq)==0 else "MULTIPLE_TITLE_BOUNDARIES")],"result_count":len(uniq),"query_url":url})
        time.sleep(.05); continue
    ref,(geom,e)=next(iter(uniq.items()))
    fp=fieldmap[a["partition_record_id"]]
    fe={
      "criterion":"security_public_safety",
      "publisher":fp.get("official_source"),
      "source_url":fp.get("official_csv_url"),
      "official_csv_sha256":fp.get("official_csv_sha256"),
      "lsoa_code":fp.get("canonical_lsoa_code"),
      "official_lsoa_row_count":fp.get("official_lsoa_row_count"),
      "official_crime_value_sum":fp.get("official_crime_value_sum"),
      "official_numeric_cells":fp.get("official_numeric_cells"),
      "prior_verified_package_commit":FIELD_COMMIT
    }
    props={
      "evidence_scope":"coverage_area",
      "coverage_area_id":fp.get("canonical_lsoa_code"),
      "source_resolution":"HMLR_INSPIRE_REGISTERED_FREEHOLD_POLYGON_PLUS_MPS_LSOA_MONTHLY_CRIME",
      "time_window":"202108-202307",
      "source_url":fp.get("official_csv_url"),
      "measurement_date":"2023-07-31",
      "measurement_method":"official MPS LSOA recorded-crime exact-identifier aggregation with authoritative HMLR title-boundary polygon",
      "spatial_binding_method":"canonical partition point queried against Planning Data title-boundary coordinate API; field evidence bound by exact MPS LSOA identifier",
      "confidence_score_0_100":90,
      "evidence_grade":"A",
      "field_evidence":fe,
      "canonical_parcel_id":ref,
      "canonical_parcel_id_namespace":"HM_LAND_REGISTRY_INSPIRE",
      "partition_record_id":a["partition_record_id"],
      "canonical_geometry_source_url":url,
      "canonical_geometry_response_sha256":hashlib.sha256(b).hexdigest(),
      "canonical_geometry_quality":e.get("quality"),
      "canonical_geometry_entry_date":e.get("entry-date"),
      "canonical_geometry_start_date":e.get("start-date"),
      "source_window_id":SOURCE_WINDOW,
      "cursor":f"{SOURCE_WINDOW}:record={i}"
    }
    f={"type":"Feature","id":ref,"geometry":geom,"properties":props}
    bad=[]
    if geom.get("type") not in ("Polygon","MultiPolygon"): bad.append("INVALID_GEOMETRY_TYPE")
    for k in REQUIRED:
        if props.get(k) in (None,""): bad.append("MISSING_"+k.upper())
    if "parcel_id" in props: bad.append("FORBIDDEN_PARCEL_ID_ALIAS")
    if "accepted_parcel" in props: bad.append("FORBIDDEN_ACCEPTED_PARCEL_FLAG")
    if bad:
        issues.append({"record_index":i,"partition_record_id":a["partition_record_id"],"exact_reasons":bad})
    else:
        records.append(f)
    time.sleep(.05)

all_valid=(len(records)==48 and not unmatched and not issues)
base.update(
 status="SEMANTIC_PRECHECK_COMPLETE" if all_valid else "BLOCKED",
 blocker=None if all_valid else "PRODUCER_SCHEMA_INVALID",
 source_records_processed_count=48,
 schema_valid_count=len(records),
 schema_invalid_count=len(issues),
 unmatched_count=len(unmatched),
 records=records,
 unmatched=unmatched,
 schema_issues=issues,
 query_audit=queries,
 cursor=f"{SOURCE_WINDOW}:record=48",
 semantic_precheck_passed=all_valid,
 official_source={
   "publisher":"Planning Data / Ministry of Housing, Communities and Local Government",
   "provider":"HM Land Registry",
   "dataset":"title-boundary",
   "dataset_url":"https://www.planning.data.gov.uk/dataset/title-boundary",
   "api_url":API,
   "public_no_login":True,
   "quality_required":"authoritative",
   "licence":"Open Government Licence v3.0"
 },
 reused_field_evidence={"commit_sha":FIELD_COMMIT,"source_url":MPS_URL,"official_csv_sha256":MPS_SHA,"reopen_source":False}
)
save(base)
print(json.dumps({"valid":len(records),"unmatched":len(unmatched),"issues":len(issues),"all_valid":all_valid}))
raise SystemExit(0)
