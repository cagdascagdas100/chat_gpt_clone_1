import json,hashlib,pathlib,subprocess,time,urllib.request,datetime
from shapely import wkt
from shapely.geometry import shape
CANON="codex/aays-single-runner-v5-20260706"; SLOT="future_growth_3"; START=181; END=192
P={
"shard":pathlib.Path("AAYS/england_map_web/data/future_growth/shards/future_growth_3_latest.geojson"),
"checkpoint":pathlib.Path("state/slots/future_growth_3/checkpoint_latest.json"),
"status":pathlib.Path("state/slots/future_growth_3/status_latest.json"),
"manifest":pathlib.Path("state/slots/future_growth_3/evidence_manifest_latest.json"),
"report":pathlib.Path("state/slots/future_growth_3/report_latest.json")}
PARCEL=pathlib.Path("england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson")
def rj(p): return json.loads(p.read_text())
def wj(p,o): p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+"\n")
def geom(v):
    try:
        return wkt.loads(v) if isinstance(v,str) and v else shape(v) if isinstance(v,dict) else None
    except Exception:return None
def fetch(url):
    q=urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS/20260818"})
    with urllib.request.urlopen(q,timeout=60) as r:
        b=r.read(); return b,getattr(r,"status",200)
def ent(o):
    if isinstance(o,dict) and isinstance(o.get("entity"),dict):return o["entity"]
    if isinstance(o,dict) and isinstance(o.get("entities"),list) and o["entities"]:return o["entities"][0]
    return o if isinstance(o,dict) else {}
def git(*a,check=True,capture=False):
    x=subprocess.run(["git",*a],text=True,capture_output=capture)
    if check and x.returncode: raise RuntimeError("git "+" ".join(a)+": "+x.stderr)
    return x
def push(paths,msg):
    git("add",*paths)
    staged=subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()
    if not staged: raise RuntimeError("NO_STAGED_STATE")
    if any(x not in paths for x in staged): raise RuntimeError("CROSS_SLOT_STAGED:"+repr(staged))
    git("commit","-m",msg)
    for n in range(1,7):
        git("fetch","origin",CANON); remote="origin/"+CANON
        if git("merge-base","--is-ancestor",remote,"HEAD",check=False).returncode: git("rebase",remote)
        x=git("push","origin","HEAD:"+CANON,check=False,capture=True)
        if not x.returncode: break
        if n==6: raise RuntimeError("PUSH_FAILED:"+x.stderr)
        time.sleep(2*n)
    git("fetch","origin",CANON)
def remote(path): return json.loads(subprocess.check_output(["git","show","origin/"+CANON+":"+path],text=True))
def count(o,k):
    if k=="shard": return len(o.get("features",[]))
    if k=="checkpoint": return int(o.get("feature_count_after",0))
    if k=="status": return int(o.get("feature_count_after",0))
    return int(o.get("feature_count_after",o.get("feature_count",0)))
def verify(batch):
    O={k:remote(str(P[k])) for k in ("shard","checkpoint","status","manifest")}
    C={k:count(v,k) for k,v in O.items()}
    if len(set(C.values()))!=1: raise RuntimeError("COUNT_INVARIANT:"+repr(C))
    if any(int(O[k].get("duplicate_count",0)) for k in ("checkpoint","status","manifest")): raise RuntimeError("DUP_NONZERO")
    B=[int(O["shard"].get("metadata",{}).get("last_batch_index",0)),int(O["checkpoint"].get("next_batch_index",0)),
       int(O["status"].get("bounded_batches_completed_this_continuation",O["status"].get("bounded_batches_completed",0))),
       int(O["manifest"].get("bounded_batches_completed",0))]
    if min(B)<batch: raise RuntimeError("BATCH_READBACK:"+repr(B))
    return C
ck=rj(P["checkpoint"]); st=rj(P["status"]); mf=rj(P["manifest"]); sh=rj(P["shard"])
if int(ck.get("next_batch_index",0))!=180: raise SystemExit("CURSOR_MOVED:"+str(ck.get("next_batch_index")))
if any(x.get("slot_id")!=SLOT for x in (ck,st,mf)): raise SystemExit("SLOT_MISMATCH")
processed=set(ck.get("processed_window_ids",[])); before=len(sh.get("features",[]))
pd=rj(PARCEL); parcels=[]; missing=0; badg=0
for f in pd.get("features",[]):
    props=f.get("properties") or {}; pid=props.get("parcel_id")
    if pid is None or not str(pid).strip(): missing+=1; continue
    g=geom(f.get("geometry"))
    if g is None or g.is_empty: badg+=1; continue
    parcels.append((str(pid),g,f))
inventory={"path":str(PARCEL),"feature_count":len(pd.get("features",[])),
           "usable_rows_with_parcel_id_and_geometry":len(parcels),"missing_parcel_id":missing,
           "invalid_or_out_of_bounds_geometry":badg}
existing={str((f.get("properties") or {}).get("parcel_id")) for f in sh.get("features",[]) if (f.get("properties") or {}).get("parcel_id")}
selected=[]; pages=[]; seen=set(); offset=0
while len(selected)<12 and offset<5000:
    u=f"https://www.planning.data.gov.uk/entity.json?dataset=brownfield-site&quality=authoritative&limit=100&offset={offset}"
    b,code=fetch(u); pages.append({"offset":offset,"url":u,"http_status":code,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)})
    rows=(json.loads(b).get("entities") or [])
    if not rows: break
    for row in rows:
        try:eid=int(row.get("entity"))
        except:continue
        wid=f"planning_data_brownfield_site_entity_{eid}"
        if eid in seen or wid in processed:continue
        seen.add(eid); du=f"https://www.planning.data.gov.uk/entity/{eid}.json"
        try: db,dc=fetch(du); d=ent(json.loads(db)); g=geom(d.get("geometry"))
        except Exception:continue
        if str(d.get("dataset","")).lower()!="brownfield-site" or g is None or g.is_empty or g.geom_type not in ("Polygon","MultiPolygon"):continue
        ed=str(d.get("end-date","") or "").strip()
        if ed:
            try:
                if datetime.date.fromisoformat(ed)<datetime.date.today():continue
            except:pass
        selected.append({"eid":eid,"wid":wid,"url":du,"bytes":db,"code":dc,"d":d,"g":g})
        if len(selected)==12:break
    offset+=100
if len(selected)!=12: raise SystemExit("UNUSED_REAL_POLYGONS:"+str(len(selected)))
mf.setdefault("sources",[]); oldrb=[x for x in mf.get("per_batch_readback",[]) if int(x.get("batch_index",0))<START]
rb=[]; run=[]
for i,s in enumerate(selected):
    batch=START+i; d=s["d"]; matches=[]
    for pid,pg,f in parcels:
        if pid not in existing and pg.centroid.within(s["g"]):matches.append((pid,f))
    added=[]
    for pid,f in matches:
        added.append({"type":"Feature","geometry":f.get("geometry"),"properties":{"parcel_id":pid,"future_growth":None,
          "future_growth_probability":None,"slot_id":SLOT,"evidence_source_url":s["url"],"evidence_source_entity":s["eid"],
          "matching_method":"STRICT_CANONICAL_PARCEL_CENTROID_WITHIN_AUTHORITATIVE_GROWTH_POLYGON_ONLY"}});existing.add(pid)
    sh.setdefault("features",[]).extend(added); n=len(sh["features"])
    src={"batch_index":batch,"window_id":s["wid"],"source_family":"planning_data_brownfield_site_authoritative",
      "publisher":"MHCLG Planning Data","source_url":s["url"],"source_entity":s["eid"],"source_reference":d.get("reference"),
      "source_name":d.get("name"),"source_fetch_ok":True,"source_http_status":s["code"],
      "source_sha256":hashlib.sha256(s["bytes"]).hexdigest(),"source_bytes":len(s["bytes"]),
      "result":"STRICT_CANONICAL_MATCHES_ADDED" if added else "ZERO_STRICT_CANONICAL_MATCHES",
      "reason":"Strict canonical parcel centroid-within match." if added else "Real authoritative polygon read; no unprocessed canonical feature with explicit parcel_id had centroid within it. Zero checkpointed; no nearest/implicit identity.",
      "feature_count_before":n-len(added),"new_records":len(added),"feature_count_after":n,"new_parcel_ids":[x[0] for x in matches],"dup":0}
    run.append(src); processed.add(s["wid"]); now=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z")
    sh["metadata"]={**(sh.get("metadata") or {}),"slot_id":SLOT,"updated_at":now,"feature_count":n,"feature_count_before":before,
      "new_features_added":n-before,"feature_count_after":n,"bounded_batches_completed":batch,"last_batch_index":batch,
      "last_window_id":s["wid"],"last_batch_result":src["result"],"duplicate_count":0,"nearest_match_used":False,"fake_data":False,
      "request_batch_start":START,"request_batch_end":END,"completed_new_bounded_batches_this_request":i+1,
      "matching_requirement":"STRICT_CANONICAL_PARCEL_CENTROID_WITHIN_AUTHORITATIVE_GROWTH_POLYGON_ONLY"}
    L=list(ck.get("processed_window_ids",[]))
    if s["wid"] not in L:L.append(s["wid"])
    ck.update({"schema_version":5,"slot_id":SLOT,"updated_at":now,"state":"METHODOLOGY_REQUIRED","fake_data":False,
      "feature_count_before":before,"new_records":n-before,"feature_count_after":n,"processed_window_ids":L,"next_batch_index":batch,
      "bounded_batches_completed_this_continuation":batch,"request_batch_start":START,"request_batch_end":END,
      "completed_new_bounded_batches_this_request":i+1,"duplicate_count":0,"nearest_match_used":False,"last_batch":src,
      "canonical_parcel_inventory":inventory,"report_counts":{"before":before,"added":n-before,"after":n}})
    st.update({"schema_version":3,"slot_id":SLOT,"updated_at":now,"state":"IN_PROGRESS" if batch<END else ("EVIDENCE_ADDED" if n>before else "METHODOLOGY_REQUIRED"),
      "fake_data":False,"feature_count_before":before,"new_records":n-before,"feature_count_after":n,
      "bounded_batches_completed_this_continuation":batch,"processed_window_count":len(L),"request_batch_start":START,"request_batch_end":END,
      "completed_new_bounded_batches_this_request":i+1,"duplicate_count":0,"nearest_match_used":False,"last_window_id":s["wid"],
      "last_result":src["result"],"write_scope":{"future_growth_3":True,"building_type":False,"planned_buildings":False,"cross_slot_writes":0}})
    mf.update({"schema_version":4,"slot_id":SLOT,"updated_at":now,"bounded_batches_completed":batch,"request_batch_start":START,
      "request_batch_end":END,"completed_new_bounded_batches_this_request":i+1,"fake_data":False,"nearest_match_used":False,
      "duplicate_count":0,"feature_count_before":before,"new_features_added":n-before,"feature_count_after":n,
      "processed_window_ids":L,"canonical_parcel_inventory":inventory,"source_contract":ck.get("source_contract",mf.get("source_contract",{}))})
    mf["sources"].append({"batch":batch,"window_id":s["wid"],"source_family":src["source_family"],"publisher":src["publisher"],
      "url":src["source_url"],"source_entity":s["eid"],"source_reference":d.get("reference"),"source_sha256":src["source_sha256"],
      "source_bytes":src["source_bytes"],"result":src["result"],"new_records":len(added),"dup":0})
    for k in ("shard","checkpoint","status","manifest"):wj(P[k],{"shard":sh,"checkpoint":ck,"status":st,"manifest":mf}[k])
    paths=[str(P[k]) for k in ("shard","checkpoint","status","manifest")]
    push(paths,f"future_growth_3: strict batch {batch} {s['wid']}")
    c=verify(batch); rb.append({"batch_index":batch,"window_id":s["wid"],"shard_count":c["shard"],"checkpoint_count":c["checkpoint"],
      "status_count":c["status"],"manifest_count":c["manifest"],"dup":0,"nearest_match_used":False,"fake_data":False,
      "result":src["result"],"remote_readback_verified":True})
after=len(sh.get("features",[]))
mf["per_batch_readback"]=oldrb+rb;mf["remote_readback_verified"]=True;mf["remote_readback_summary"]={"shard":after,"checkpoint":after,"status":after,"manifest":after,"bounded_batches_total":END,"new_batches":12,"dup":0}
report={"schema_version":1,"slot_id":SLOT,"continuation_key":ck.get("continuation_key"),
 "run_id":"common_continuation_20260818_batches_181_192_strict_spatial",
 "requested_common_continuation_path":r"F:\TerraYield_AAYS_Portable\docs\deepseek_prompts\AAYS_CHATGPT_PLAN_00_23_SLOT_COMMON_CONTINUATION_20260818.md",
 "requested_common_continuation_file_read":False,"requested_new_bounded_batches":12,"completed_new_bounded_batches":12,
 "batch_range":{"first":START,"last":END},"counts":{"before_unique_evidenced_parcels":before,"added_unique_evidenced_parcels":after-before,
 "after_unique_evidenced_parcels":after,"mirror_feature_count":after,"duplicate_count":0},
 "quality_gates":{"shard_checkpoint_status_manifest_count_invariant_equal_each_batch":True,"duplicate_count_zero_each_batch":True,
 "nearest_match_used":False,"fake_data":False,"cross_slot_writes":False,"all_zero_windows_checkpointed":all(x["new_records"]==0 for x in run),
 "reused_window_count":0,"own_slot_only":True,"remote_readback_verified":True},
 "artifact_paths":{k:str(v) for k,v in P.items()},"source_contract":ck.get("source_contract",{}),"source_windows":run,
 "discovery_pages":pages,"canonical_parcel_inventory":inventory,"per_batch_readback":rb,"next_cursor":END}
st["report"]={"path":str(P["report"]),"before":before,"added":after-before,"after":after,"dup":0,"new_bounded_batches_this_request":12,
 "request_batch_range":"181-192","bounded_batches_total":END,"processed_windows_total":len(ck["processed_window_ids"]),
 "building_type_added_by_this_slot":0,"planned_buildings_added_by_this_slot":0}
wj(P["manifest"],mf);wj(P["status"],st);wj(P["report"],report)
push([str(P[k]) for k in ("shard","checkpoint","status","manifest","report")],"future_growth_3: finalize strict batches 181-192 report/readback")
c=verify(END); rr=remote(str(P["report"]))
if rr.get("counts",{}).get("after_unique_evidenced_parcels")!=after:raise RuntimeError("REPORT_READBACK")
print(json.dumps({"slot_id":SLOT,"batches":[START,END],"before":before,"added":after-before,"after":after,"dup":0,"remote_counts":c}))