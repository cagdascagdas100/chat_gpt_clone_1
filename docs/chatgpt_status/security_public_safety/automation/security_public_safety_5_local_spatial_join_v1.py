from __future__ import annotations
import hashlib,json,os,subprocess,tempfile,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path

SLOT_ID="security_public_safety_5"
LINEAGE_ID="86b5e932de484ad26133fa8c"
P0,P1,PC=61524,76903,15380
MAX_RECORDS=50
REPO=Path(os.environ.get("AAYS_REPO_ROOT",r"F:\chatgpt\chat_gpt_clone_1_main"))
OUT=REPO/"docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_5_local_spatial_join_latest.json"
CANON_BRANCH="codex/aays-single-runner-v5-20260706"
CANON_REL="england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
CANON_BLOB="bb48164e7a0af78df875f30421a6a3068c43edb8"
AREA_REL=Path("incoming/source_area/security_public_safety_5/86b5e932de484ad26133fa8c/planning_data_barnet_ward_polygons_20260927T204546Z/records.geojson")
AREA_COMMIT="eb916767b7b22e6706d2fe34c1005729a4142db6"
AREA_ZIP_SHA="a22b7b141719fee5857189e83bc9e94809dc2ce2826c3ffe2c5086bb607d07f7"
LAST_URL="https://data.police.uk/api/crime-last-updated"
CRIME_URL="https://data.police.uk/api/crimes-street/all-crime"

def now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def sha256(b): return hashlib.sha256(b).hexdigest()
def git(args,timeout=900,stdout=None):
    return subprocess.run(["git","-C",str(REPO),*args],stdout=stdout if stdout is not None else subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=timeout)
def blob_sha(path):
    r=git(["hash-object",str(path)],180)
    return r.stdout.decode("utf-8","replace").strip() if r.returncode==0 else None

def materialize():
    cache=Path(tempfile.gettempdir())/"aays_sps5"/Path(CANON_REL).name
    cache.parent.mkdir(parents=True,exist_ok=True)
    ev={"branch":CANON_BRANCH,"repo_path":CANON_REL,"required_git_blob_sha":CANON_BLOB,"cache_path":str(cache),"verified":False,"fetch_attempted":False}
    if cache.is_file() and blob_sha(cache)==CANON_BLOB:
        ev.update(cache_hit=True,verified=True); return cache,ev
    cache.unlink(missing_ok=True)
    for ref in (f"origin/{CANON_BRANCH}",CANON_BRANCH):
        part=cache.with_suffix(".part"); part.unlink(missing_ok=True)
        with part.open("wb") as fh: r=git(["show",f"{ref}:{CANON_REL}"],stdout=fh)
        ev.setdefault("attempts",[]).append({"ref":ref,"returncode":r.returncode,"stderr":r.stderr.decode("utf-8","replace")[-1000:]})
        if r.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref=ref,verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev["fetch_attempted"]=True
    r=git(["fetch","origin",CANON_BRANCH],900); ev["fetch_returncode"]=r.returncode; ev["fetch_stderr"]=r.stderr.decode("utf-8","replace")[-2000:]
    if r.returncode==0:
        part=cache.with_suffix(".part")
        with part.open("wb") as fh: s=git(["show",f"FETCH_HEAD:{CANON_REL}"],stdout=fh)
        if s.returncode==0 and blob_sha(part)==CANON_BLOB:
            os.replace(part,cache); ev.update(source_ref="FETCH_HEAD",verified=True); return cache,ev
        part.unlink(missing_ok=True)
    ev["error"]="EXACT_CANONICAL_BLOB_NOT_MATERIALIZED"; return None,ev

def in_ring(x,y,ring):
    inside=False; j=len(ring)-1
    for i in range(len(ring)):
        xi,yi=ring[i][0],ring[i][1]; xj,yj=ring[j][0],ring[j][1]
        if (yi>y)!=(yj>y):
            d=yj-yi
            if d and x < (xj-xi)*(y-yi)/d+xi: inside=not inside
        j=i
    return inside

def in_poly(x,y,coords):
    return bool(coords) and in_ring(x,y,coords[0]) and not any(in_ring(x,y,h) for h in coords[1:])
def in_geom(x,y,g):
    t=g.get("type"); c=g.get("coordinates") or []
    return in_poly(x,y,c) if t=="Polygon" else any(in_poly(x,y,p) for p in c) if t=="MultiPolygon" else False
def pid_num(pid):
    try: return int(pid.split("_",1)[1]) if pid.startswith("parcel_") else None
    except: return None
def get_pid(props):
    for k in ("security_parcel_id","parcel_id"):
        v=props.get(k)
        if isinstance(v,str) and v.startswith("parcel_"): return v
    return None

def http_json(url,attempts=4):
    last=None
    for n in range(1,attempts+1):
        req=urllib.request.Request(url,headers={"User-Agent":"AAYS-security-public-safety-5/local-join-v1","Accept":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=45) as resp:
                body=resp.read(); return int(resp.status),body,json.loads(body.decode("utf-8"))
        except Exception as e:
            last=e
            if n<attempts: time.sleep(min(12,2*n))
    raise RuntimeError(str(last) if last else "HTTP_FAILED")
def cats(items):
    out={}
    for x in items:
        k=str(x.get("category") or "unknown"); out[k]=out.get(k,0)+1
    return dict(sorted(out.items()))
def save(x):
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def main():
    base={"schema_version":1,"slot_id":SLOT_ID,"owner":None,"partition":{"start":P0,"end":P1,"count":PC},"lineage_id":LINEAGE_ID,"generated_at":now(),"first_missing_criterion":"LOCAL_SPATIAL_JOIN_AND_CANONICAL_READBACK_REQUIRED","source_area_commit":AREA_COMMIT,"source_area_records_path":str(AREA_REL).replace("\\","/"),"source_area_zip_sha256":AREA_ZIP_SHA,"max_official_source_records":MAX_RECORDS,"accepted_count_claimed":0,"final_package_written":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    cp,mat=materialize(); base["canonical_materialization"]=mat
    if not cp:
        base.update(status="BLOCKED",blocker="CANONICAL_BLOB_MATERIALIZATION_FAILED",candidate_ready_count=0,rows=[]); save(base); return 2
    sp=REPO/AREA_REL
    if not sp.is_file():
        base.update(status="BLOCKED",blocker="SOURCE_AREA_RECORDS_MISSING",candidate_ready_count=0,rows=[]); save(base); return 2
    sg=json.loads(sp.read_text(encoding="utf-8"))
    areas=[f for f in sg.get("features",[]) if isinstance(f,dict) and (f.get("geometry") or {}).get("type") in {"Polygon","MultiPolygon"}]
    if not areas:
        base.update(status="BLOCKED",blocker="SOURCE_AREA_POLYGON_EMPTY",candidate_ready_count=0,rows=[]); save(base); return 2
    cg=json.loads(cp.read_text(encoding="utf-8-sig"))
    matched=[]; partition_count=0
    for f in cg.get("features",[]):
        if not isinstance(f,dict): continue
        props=f.get("properties") or {}; pid=get_pid(props); n=pid_num(pid or "")
        if n is None or not P0<=n<=P1: continue
        partition_count+=1
        g=f.get("geometry") or {}
        if g.get("type")!="Point" or not isinstance(g.get("coordinates"),list) or len(g["coordinates"])<2: continue
        x,y=float(g["coordinates"][0]),float(g["coordinates"][1]); aids=[]
        for a in areas:
            if in_geom(x,y,a.get("geometry") or {}):
                aids.append(str((a.get("properties") or {}).get("coverage_area_id") or a.get("id") or ""))
        if aids:
            matched.append({"parcel_id":pid,"parcel_number":n,"geometry":g,"coverage_area_ids":sorted(set(filter(None,aids))),"security_score_percent":props.get("safety_score") if props.get("safety_score") is not None else props.get("security_score"),"security_level":props.get("safety_level") or props.get("security_level"),"security_lsoa_code":props.get("security_lsoa_code"),"spatial_match_method":props.get("spatial_match_method"),"canonical_confidence_score":props.get("confidence_score")})
    matched.sort(key=lambda r:r["parcel_number"])
    ls,lb,lo=http_json(LAST_URL); month=str((lo or {}).get("date") or "")[:7]
    if ls!=200 or len(month)!=7:
        base.update(status="BLOCKED",blocker="POLICE_LAST_UPDATED_FAILED",matched_partition_count=len(matched),rows=[]); save(base); return 2
    window=f"data_police_street_crime_explicit_latest_month_sps5_{month.replace('-','_')}_first_{MAX_RECORDS}"
    rows=[]
    for i,row in enumerate(matched[:MAX_RECORDS],1):
        lng,lat=row["geometry"]["coordinates"][:2]
        q=urllib.parse.urlencode({"date":month,"lat":f"{float(lat):.6f}","lng":f"{float(lng):.6f}"})
        url=f"{CRIME_URL}?{q}"
        e={"record_index":i,"parcel_id":row["parcel_id"],"parcel_number":row["parcel_number"],"canonical_geometry":row["geometry"],"coverage_area_ids":row["coverage_area_ids"],"security_score_percent":row["security_score_percent"],"security_level":row["security_level"],"security_lsoa_code":row["security_lsoa_code"],"canonical_spatial_match_method":row["spatial_match_method"],"canonical_confidence_score":row["canonical_confidence_score"],"source_window_id":window,"cursor":f"{window}:record={i}","official_source":"data.police.uk","official_source_url":url,"official_source_month":month,"official_source_semantic_limit":"street-level crime is approximate area evidence within about one mile of the point; not an exact parcel crime count","http_status":None,"response_sha256":None,"crime_count":None,"crime_category_counts":{},"canonical_gate":True,"coverage_polygon_gate":bool(row["coverage_area_ids"]),"field_evidence_gate":False,"candidate_ready":False,"error":None}
        try:
            st,b,p=http_json(url); e["http_status"]=st; e["response_sha256"]=sha256(b) if st==200 else None
            if st==200 and isinstance(p,list):
                e["crime_count"]=len(p); e["crime_category_counts"]=cats(p); e["field_evidence_gate"]=True
        except Exception as ex: e["error"]=str(ex)
        e["candidate_ready"]=bool(e["canonical_gate"] and e["coverage_polygon_gate"] and e["field_evidence_gate"]); rows.append(e); time.sleep(.4)
    ready=sum(bool(r["candidate_ready"]) for r in rows)
    base.update(status="LOCAL_SPATIAL_JOIN_EXECUTED",canonical_blob_sha=blob_sha(cp),canonical_blob_verified=blob_sha(cp)==CANON_BLOB,canonical_partition_feature_count=partition_count,coverage_polygon_count=len(areas),coverage_polygon_ids=[str((f.get("properties") or {}).get("coverage_area_id") or f.get("id") or "") for f in areas],matched_partition_count=len(matched),official_source_window_id=window,official_source_cursor=f"{window}:record={len(rows)}",police_last_updated_url=LAST_URL,police_last_updated_http_status=ls,police_last_updated_response_sha256=sha256(lb),official_source_month=month,evidence_processed_count=len(rows),candidate_ready_count=ready,remaining_matched_unprocessed_count=max(0,len(matched)-len(rows)),rows=rows,next_step="GitHub-MCP readback must verify this runner output. Only candidate_ready rows may be packaged by the verified GitHub writer as AAYS_LAYER24_EVIDENCE_V1; no local runner package delivery claim.")
    save(base)
    print(f"SLOT_ID={SLOT_ID}"); print(f"CANONICAL_BLOB_VERIFIED={base['canonical_blob_verified']}"); print(f"PARTITION_FEATURE_COUNT={partition_count}"); print(f"MATCHED_PARTITION_COUNT={len(matched)}"); print(f"EVIDENCE_PROCESSED_COUNT={len(rows)}"); print(f"CANDIDATE_READY_COUNT={ready}"); print(f"SOURCE_WINDOW_ID={window}"); print(f"OUTPUT={OUT}")
    return 0 if base["canonical_blob_verified"] and ready>0 else 2
if __name__=="__main__": raise SystemExit(main())
